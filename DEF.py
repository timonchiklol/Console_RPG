from random import randint, choice
from gemini import Gemini
from dotenv import load_dotenv
import os
import json
import sys
from gemini_schema import PlayerState, RoomState
import logging
from prompts import SYSTEM_PROMPTS, GAME_START_PROMPTS
from character_config import get_race_stats, get_class_bonuses, get_enemy, ENEMIES
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

class DnDGame:
    def __init__(self, language="en"):
        load_dotenv()
        self.setup_logging()
        
        # Game state
        self.language = language
        self.gold = 0
        self.magic_1lvl = 0
        self.magic_2lvl = 0
        self.level = 0
        self.health_points = 0
        self.damage = 0
        self.player_race = ""
        self.player_class = ""
        self.in_combat = False
        self.enemy = None
        
        # Dice state
        self.last_dice_roll = None
        self.dice_roll_needed = False
        self.dice_type = None
        
        # Message history settings
        self.context_limit = 50
        self.message_history = []
        
        # Save directory setup
        self.save_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saves")
        os.makedirs(self.save_folder, exist_ok=True)
        
        # Initialize chat immediately
        self.initialize_chat()

    def setup_logging(self):
        """Set up logging configuration"""
        # Get the root logger that was configured in app.py
        root_logger = logging.getLogger()
        
        # Create a child logger for this class
        self.logger = logging.getLogger(__name__)
        
        # If root logger has no handlers (app.py logging not initialized),
        # set up basic logging
        if not root_logger.handlers:
            # Create logs directory if it doesn't exist
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)
            
            # Create formatters
            detailed_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # Create file handler with daily rotation
            log_file = logs_dir / "game.log"
            file_handler = TimedRotatingFileHandler(
                log_file,
                when="midnight",
                interval=1,
                backupCount=30  # Keep 30 days of logs
            )
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(detailed_formatter)
            file_handler.addFilter(GetRoomStateFilter())
            
            # Create console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(detailed_formatter)
            console_handler.addFilter(GetRoomStateFilter())
            
            # Configure root logger
            root_logger.setLevel(logging.DEBUG)
            root_logger.addHandler(file_handler)
            root_logger.addHandler(console_handler)

    def initialize_chat(self):
        """Initialize chat with language-specific system prompt"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            self.logger.error("GEMINI_API_KEY not found in environment variables")
            raise ValueError("GEMINI_API_KEY not found in environment variables")
            
        system_prompt = SYSTEM_PROMPTS.get(self.language, SYSTEM_PROMPTS["en"])
        self.chat = Gemini(API_KEY=api_key, system_instruction=system_prompt)
        self.logger.info(f"Chat initialized with language: {self.language}")

    def update_system_prompt(self):
        """Update system prompt with current character stats"""
        current_stats = f"""Current player stats:
        Race: {self.player_race}
        Class: {self.player_class}
        Level: {self.level}
        HP: {self.health_points}
        Damage: {self.damage}
        Gold: {self.gold}
        Magic slots (1st/2nd level): {self.magic_1lvl}/{self.magic_2lvl}
        """
        return self.chat.send_message(f"Remember these player stats and always respond in {self.language} language: {current_stats}")
    
    def add_to_history(self, user_message, dm_response):
        """Save last messages within context_limit"""
        self.message_history.append({"user": user_message, "dm": dm_response})
        if len(self.message_history) > self.context_limit:
            self.message_history.pop(0)
    
    def roll_dice(self, dice_type):
        """Roll dice of specified type (e.g. "d20", "2d6")"""
        if not dice_type:
            dice_type = 'd20'  # Default to d20 if no dice type specified
            self.logger.info("No dice type specified, defaulting to d20")
            
        try:
            num_dice, sides = dice_type.lower().split('d')
            num_dice = int(num_dice) if num_dice else 1
            sides = int(sides)
            
            if sides <= 0 or num_dice <= 0:
                self.logger.error(f"Invalid dice parameters: {num_dice}d{sides}")
                return None
                
            result = sum(randint(1, sides) for _ in range(num_dice))
            self.last_dice_roll = result
            self.dice_roll_needed = False  # Reset the flag after rolling
            self.dice_type = None  # Clear the dice type after rolling
            self.logger.info(f"Rolled {dice_type}: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error rolling dice: {e}")
            return None

    def update_state(self, state_update):
        """Update game state from structured response"""
        if not state_update:
            return
            
        self.logger.info(f"Updating state with: {state_update}")
        old_hp = self.health_points
            
        # Update basic stats if provided
        if 'health_points' in state_update:
            self.health_points = state_update['health_points']
            self.logger.info(f"Health changed from {old_hp} to {self.health_points}")
        if 'gold' in state_update:
            self.gold = state_update['gold']
        if 'damage' in state_update:
            self.damage = state_update['damage']
        if 'in_combat' in state_update:
            self.in_combat = state_update['in_combat']
        if 'magic_1lvl' in state_update:
            self.magic_1lvl = state_update['magic_1lvl']
        if 'magic_2lvl' in state_update:
            self.magic_2lvl = state_update['magic_2lvl']
            
        # Update enemy state if in combat
        enemy_health = state_update.get('enemy_health')
        if enemy_health is not None and self.enemy:
            self.enemy["hp"] = enemy_health
            
        # Update dice roll state
        self.dice_roll_needed = state_update.get('dice_roll_needed', False)
        self.dice_type = state_update.get('dice_type')

    def send_message(self, message, player_id=None, room_state=None):
        """Send message and get structured response"""
        self.logger.info(f"\nSending message: {message}")
        
        # Build context with all players' stats if room_state is provided
        current_stats = "Current player stats:\n"
        if room_state:
            for pid, player in room_state.players.items():
                current_stats += f"\nPlayer {player.name} ({pid}):\n"
                current_stats += f"Race: {player.race}\n"
                current_stats += f"Class: {player.class_name}\n"
                current_stats += f"Level: {player.level}\n"
                current_stats += f"HP: {player.health_points}\n"
                current_stats += f"Damage: {player.damage}\n"
                current_stats += f"Gold: {player.gold}\n"
                current_stats += f"Magic slots (1st/2nd level): {player.magic_1lvl}/{player.magic_2lvl}\n"
                if pid == player_id:
                    current_stats += f"Last Roll: {player.last_dice_roll if player.last_dice_roll is not None else 'None'}\n"
        else:
            # Fallback to single player mode for backward compatibility
            current_stats += f"""
            Race: {self.player_race}
            Class: {self.player_class}
            Level: {self.level}
            HP: {self.health_points}
            Damage: {self.damage}
            Gold: {self.gold}
            Magic slots (1st/2nd level): {self.magic_1lvl}/{self.magic_2lvl}
            In Combat: {self.in_combat}
            Last Roll: {self.last_dice_roll if self.last_dice_roll is not None else 'None'}
            """
        
        # Add last roll information to context
        if "rolled" in message.lower() and player_id and room_state:
            try:
                roll_value = int(message.split()[2])
                current_stats += f"\nLast roll result: {roll_value}"
                if roll_value == 1:
                    current_stats += " (Critical failure)"
                elif roll_value == 20:
                    current_stats += " (Critical success)"
            except:
                pass
        
        if room_state and room_state.in_combat:
            current_stats += f"\nRoom Combat State:"
            current_stats += f"\nEnemy: {room_state.enemy_name} (HP: {room_state.enemy_health})"
        elif self.in_combat and self.enemy:
            current_stats += f"\nEnemy: {self.enemy['name']} (HP: {self.enemy['hp']})"
        
        self.logger.debug(f"Current stats:\n{current_stats}")
        
        # Get context from room's message history
        context = "Previous messages:\n"
        if room_state and hasattr(room_state, 'message_history'):
            # Get last 10 messages from room history
            for msg in room_state.message_history[-10:]:
                if isinstance(msg, dict):
                    # Handle dictionary format
                    if msg.get('type') == 'player':
                        context += f"{msg.get('player_name', 'Player')}: {msg.get('user_message', '')}\n"
                        if msg.get('dm_response'):
                            context += f"DM: {msg.get('dm_response')}\n"
                    elif msg.get('type') == 'dm':
                        context += f"DM: {msg.get('message', '')}\n"
                    elif msg.get('type') == 'system':
                        context += f"System: {msg.get('message', '')}\n"
                else:
                    # Handle RoomMessage objects
                    if msg.player_name:
                        context += f"{msg.player_name}: {msg.user_message}\n"
                    else:
                        context += f"Player: {msg.user_message}\n"
                    if msg.dm_response:
                        context += f"DM: {msg.dm_response}\n"
        else:
            # Fallback to local message history
            start_idx = max(0, len(self.message_history) - self.context_limit)
            for msg in self.message_history[start_idx:]:
                context += f"Player: {msg['user']}\nDM: {msg['dm']}\n"
        
        full_message = f"{current_stats}\n{context}\nCurrent message: {message}"
        self.logger.debug(f"Full message to Gemini:\n{full_message}")
        
        # Get structured response
        response = self.chat.send_structured_message(full_message)
        self.logger.info(f"Gemini response: {response}")
        
        # Extract the actual message text from the response
        message_text = response.get('message', '')
        if not message_text:
            message_text = "I don't understand. Please try again."
            self.logger.warning("Empty message from Gemini")
        
        # Handle dice roll requests
        dice_roll = response.get('dice_roll', {})
        dice_roll_needed = False
        dice_type = None
        
        if dice_roll and isinstance(dice_roll, dict):
            if dice_roll.get('required', False):
                dice_roll_needed = True
                dice_type = dice_roll.get('type', 'd20')  # Default to d20 if not specified
                reason = dice_roll.get('reason', 'A dice roll is needed')
                message_text += f"\n\n{reason}"
                self.logger.info(f"Dice roll required: {dice_type} - {reason}")
        
        # Handle combat results
        combat_result = response.get('combat_result', {})
        if combat_result:
            self.logger.info(f"Combat result: {combat_result}")
            
            if room_state:
                if combat_result.get('damage_dealt') and room_state.enemy_health is not None:
                    old_enemy_hp = room_state.enemy_health
                    room_state.enemy_health -= combat_result['damage_dealt']
                    self.logger.info(f"Enemy HP changed from {old_enemy_hp} to {room_state.enemy_health}")
            elif self.enemy and combat_result.get('damage_dealt'):
                old_enemy_hp = self.enemy["hp"]
                self.enemy["hp"] -= combat_result['damage_dealt']
                self.logger.info(f"Enemy HP changed from {old_enemy_hp} to {self.enemy['hp']}")
        
        # Handle player updates
        players_update = response.get('players_update', [])
        if not players_update and player_id:
            # Create a single player update for backward compatibility
            players_update = [{
                'player_id': player_id,
                'health_points': self.health_points,
                'gold': self.gold,
                'damage': self.damage,
                'level': self.level,
                'magic_1lvl': self.magic_1lvl,
                'magic_2lvl': self.magic_2lvl,
                'in_combat': self.in_combat,
                'dice_roll_needed': dice_roll_needed,
                'dice_type': dice_type
            }]
        
        # Add to room's message history if available
        if room_state and hasattr(room_state, 'message_history'):
            player_name = room_state.players[player_id].name if player_id in room_state.players else None
            room_state.message_history.append({
                'type': 'player',
                'user_message': message,
                'dm_response': message_text,
                'player_name': player_name,
                'timestamp': datetime.now()
            })
            # Keep only last 100 messages
            if len(room_state.message_history) > 100:
                room_state.message_history = room_state.message_history[-100:]
        else:
            # Fallback to local message history
            self.add_to_history(message, message_text)
        
        return {
            'message': message_text,
            'players_update': players_update,
            'combat_result': combat_result,
            'dice_roll': dice_roll
        }

    def start_game(self):
        """Generate opening scene based on character"""
        start_prompt = GAME_START_PROMPTS.get(self.language, GAME_START_PROMPTS["en"]).format(
            race=self.player_race,
            class_name=self.player_class
        )
        return self.send_message(start_prompt)

    def start_combat(self, enemy_type=None):
        """Start combat with a random or specific enemy"""
        if enemy_type is None:
            enemy_type = choice(list(ENEMIES.keys()))
        
        self.enemy = get_enemy(enemy_type)
        self.enemy["name"] = enemy_type
        self.in_combat = True
        
        combat_start = self.send_message(f"""
        A {enemy_type} appears! Combat starts!
        Enemy HP: {self.enemy['hp']}
        Your HP: {self.health_points}
        
        What do you do? (attack/spell/flee)
        """)
        return combat_start

    def process_combat_action(self, action):
        """Process player's combat action"""
        if not self.in_combat or not self.enemy:
            return "You're not in combat!"

        action = action.lower()
        
        if action == "flee":
            return self._handle_flee()
        elif action == "attack":
            return self._handle_attack()
        elif action == "spell":
            return self._handle_spell()
        else:
            return "Invalid combat action!"

    def _handle_flee(self):
        """Handle flee attempt in combat"""
        if randint(1, 20) > 12:  # 40% chance to flee
            self.in_combat = False
            self.enemy = None
            return "You successfully fled from combat!"
        
        enemy_damage = randint(*self.enemy["damage"])
        self.health_points -= enemy_damage
        return f"Failed to flee! The {self.enemy['name']} hits you for {enemy_damage} damage!"

    def _handle_attack(self):
        """Handle attack action in combat"""
        player_damage = randint(1, self.damage)
        self.enemy["hp"] -= player_damage
        
        if self.enemy["hp"] <= 0:
            return self._handle_victory()
        
        return self._handle_enemy_counter_attack(player_damage)

    def _handle_spell(self):
        """Handle spell casting in combat"""
        if self.magic_1lvl <= 0:
            return "You have no spell slots left!"
        
        self.magic_1lvl -= 1
        spell_damage = randint(3, 10)
        self.enemy["hp"] -= spell_damage
        
        if self.enemy["hp"] <= 0:
            return self._handle_victory()
        
        return self._handle_enemy_counter_attack(spell_damage, is_spell=True)

    def _handle_victory(self):
        """Handle enemy defeat and rewards"""
        gold_reward = randint(*self.enemy["gold"])
        xp_reward = self.enemy["xp"]
        self.gold += gold_reward
        
        if xp_reward >= 100:
            self.level += 1
            self.health_points += 5
            self.damage += 1
            level_up_msg = f'Level up! You are now level {self.level}!'
        else:
            level_up_msg = ''
        
        self.in_combat = False
        victory_message = f"""
        You defeated the {self.enemy['name']}!
        Gained {gold_reward} gold and {xp_reward} XP!
        {level_up_msg}
        """
        self.enemy = None
        return victory_message

    def _handle_enemy_counter_attack(self, player_damage, is_spell=False):
        """Handle enemy's counter attack"""
        enemy_damage = randint(*self.enemy["damage"])
        self.health_points -= enemy_damage
        
        if self.health_points <= 0:
            self.in_combat = False
            self.enemy = None
            return "You have been defeated! Game Over!"
        
        action_type = "spell" if is_spell else "hit"
        return f"""
        Your {action_type} the {self.enemy['name']} for {player_damage} damage!
        The {self.enemy['name']} hits you for {enemy_damage} damage!
        
        Enemy HP: {self.enemy['hp']}
        Your HP: {self.health_points}
        {f'Spell slots remaining: {self.magic_1lvl}' if is_spell else ''}
        """

    def save_game(self, save_name="quicksave"):
        """Save current game state"""
        save_data = self.get_state_dict()
        save_path = os.path.join(self.save_folder, f"{save_name}.json")
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=4)
        
        return f"Game saved to {save_name}.json"

    def load_game(self, save_name="quicksave"):
        """Load saved game state"""
        save_path = os.path.join(self.save_folder, f"{save_name}.json")
        
        if not os.path.exists(save_path):
            return "Save file not found!"
            
        try:
            with open(save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            self.load_state_from_dict(save_data)
            return "Game successfully loaded!"
        except Exception as e:
            return f"Error loading save file: {str(e)}"

    def list_saves(self):
        """List available save files"""
        saves = [f.replace('.json', '') for f in os.listdir(self.save_folder) if f.endswith('.json')]
        if not saves:
            return "No save files found!"
        saves_list = "\n".join(saves)
        return f"Available saves:\n{saves_list}"

    def toggle_message_style(self):
        """Toggle between streaming and non-streaming message generation"""
        self.streaming_mode = not self.streaming_mode
        style_ru = "Стиль сообщений: "
        style_en = "Message style: "
        streaming_ru = "Потоковый"
        streaming_en = "Streaming"
        single_ru = "Одиночный ответ"
        single_en = "Single response"
        
        print(f"\n{self.get_text(style_ru, style_en)}{self.get_text(streaming_ru if self.streaming_mode else single_ru, streaming_en if self.streaming_mode else single_en)}")

    def initialize_character(self):
        """Initialize character stats based on race and class"""
        if not self.player_race or not self.player_class:
            self.logger.error("Cannot initialize character without race and class")
            raise ValueError("Race and class must be set before initializing character")
            
        # Get base stats from race
        race_stats = get_race_stats(self.player_race)
        self.health_points = race_stats['hp']
        self.gold = race_stats['gold']
        # Parse damage range from string (e.g., "2-7")
        damage_range = race_stats['damage'].split('-')
        self.damage = int(damage_range[1])  # Use the max damage as base damage
            
        # Apply class bonuses
        class_bonuses = get_class_bonuses(self.player_class)
        self.health_points += class_bonuses['hp_bonus']
        self.gold += class_bonuses['gold_bonus']
        self.magic_1lvl = class_bonuses['magic']  # Base magic slots from class
        self.magic_2lvl = max(0, class_bonuses['magic'] - 1)  # One less 2nd level slot than 1st level
        
        self.level = 1
        self.logger.info(f"Character initialized: {self.player_race} {self.player_class}")
        self.update_system_prompt()

    def get_state_dict(self):
        """Get current game state as a dictionary"""
        return {
            'started': True,
            'character_created': bool(self.player_race and self.player_class),
            'in_combat': self.in_combat,
            'player_race': self.player_race,
            'player_class': self.player_class,
            'health_points': self.health_points,
            'gold': self.gold,
            'level': self.level,
            'damage': self.damage,
            'magic_1lvl': self.magic_1lvl,
            'magic_2lvl': self.magic_2lvl,
            'enemy': self.enemy,
            'dice_roll_needed': self.dice_roll_needed,
            'dice_type': self.dice_type,
            'last_dice_roll': self.last_dice_roll,
            'message_history': self.message_history,
            'language': self.language
        }

    def load_state_from_dict(self, state_dict):
        """Load game state from a dictionary"""
        for key, value in state_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.initialize_chat()
