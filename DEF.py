from random import randint, choice
from gemini import Gemini
from dotenv import load_dotenv
import os
import json
import sys
from gemini_schema import PlayerState, RoomState
import logging
from prompts import GAME_START_PROMPTS, NARRATIVE_PROMPTS, PLAYER_UPDATE_PROMPTS, DICE_ROLL_PROMPTS, COMBAT_PROMPTS
from character_config import get_race_stats, get_class_bonuses, get_enemy, ENEMIES, RACE_CONFIGS, CLASS_CONFIGS, calculate_ability_modifier, get_saving_throw
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from translations import load_translations

# Add this at the top of the file, before the DnDGame class
class GetRoomStateFilter(logging.Filter):
    def filter(self, record):
        return "GET /get_room_state" not in record.getMessage()

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
            
        # Combine all prompts into a single system instruction
        system_instruction = f"""
{NARRATIVE_PROMPTS[self.language]}

{PLAYER_UPDATE_PROMPTS[self.language]}

{DICE_ROLL_PROMPTS[self.language]}

{COMBAT_PROMPTS[self.language]}

Response Format:
1. Always generate a narrative message in the 'message' field
2. Set player_update_required=true if player stats need to change
3. Set dice_roll_required=true if a dice roll is needed
4. Set combat_started=true if combat should begin
5. Include players_update array only if player_update_required is true
6. Include dice_roll_request object only if dice_roll_required is true
"""
        
        self.chat = Gemini(API_KEY=api_key, system_instruction=system_instruction)
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
        return self.chat.send_structured_message({
            "message": f"Acknowledged. I will remember these stats and respond in {self.language}.",
            "player_update_required": False,
            "dice_roll_required": False,
            "combat_started": False
        })
    
    def add_to_history(self, user_message, dm_response):
        """Save last messages within context_limit"""
        self.message_history.append({"user": user_message, "dm": dm_response})
        if len(self.message_history) > self.context_limit:
            self.message_history.pop(0)
    
    def roll_dice(self, dice_type, ability_modifier=None, modifier=0, proficient=False, reason=''):
        """Roll dice of specified type (e.g. "d20", "2d6") or for ability checks/saving throws based on the new Gemini response format."""
        if not dice_type:
            dice_type = 'd20'
            self.logger.info("No dice type specified, defaulting to d20")
        try:
            # if ':' in dice_type:
            #     parts = dice_type.split(':')
            #     roll_type = parts[0]
            #     ability = parts[1]
            #     proficient = False
            #     if len(parts) > 2 and parts[2] == "proficient":
            #         proficient = True

            #     base_roll = randint(1, 20)
            #     if roll_type == "ability_check":
            #         proficiency_bonus = 2 if proficient else 0
            #         ability_score = self.get_ability_scores().get(ability, 10)
            #         ability_mod = calculate_ability_modifier(ability_score)
            #         total = base_roll + ability_mod + proficiency_bonus
            #         self.last_dice_detail = {
            #             "roll_type": roll_type,
            #             "ability": ability,
            #             "base_roll": base_roll,
            #             "ability_mod": ability_mod,
            #             "proficiency_bonus": proficiency_bonus,
            #             "total": total
            #         }
            #         self.logger.info(f"Ability check ({ability}): d20={base_roll}, ability_mod={ability_mod}, prof_bonus={proficiency_bonus}, total={total}")
            #     elif roll_type == "saving_throw":
            #         total_bonus = get_saving_throw(self.player_race, self.player_class, self.get_ability_scores(), ability)
            #         total = base_roll + total_bonus
            #         self.last_dice_detail = {
            #             "roll_type": roll_type,
            #             "ability": ability,
            #             "base_roll": base_roll,
            #             "total_bonus": total_bonus,
            #             "total": total
            #         }
            #         self.logger.info(f"Saving throw ({ability}): d20={base_roll}, total_bonus={total_bonus}, total={total}")
            #     else:
            #         self.logger.error(f"Unknown roll type: {roll_type}")
            #         return None

            #     self.last_dice_roll = total
            #     self.dice_roll_needed = False
            #     self.dice_type = None
            #     return total
            if ability_modifier:
                # Handle ability check rolls
                base_roll = randint(1, 20)
                proficiency_bonus = 2 if proficient else 0
                total = base_roll + modifier
                
                self.last_dice_detail = {
                    "roll_type": "ability_check",
                    "ability": ability_modifier,
                    "base_roll": base_roll,
                    "ability_mod": modifier - proficiency_bonus,
                    "proficiency_bonus": proficiency_bonus,
                    "total": total
                }
                self.logger.info(f"Ability check ({ability_modifier}): d20={base_roll}, modifier={modifier}, total={total}")
                
                self.last_dice_roll = total
                self.dice_roll_needed = False
                self.dice_type = None
                return total
            else:
                # Handle regular dice rolls like '2d6' or 'd20'
                parts = dice_type.lower().split('d')
                num_dice = int(parts[0]) if parts[0] != "" else 1
                sides = int(parts[1])
                if sides <= 0 or num_dice <= 0:
                    self.logger.error(f"Invalid dice parameters: {dice_type}")
                    return None
                rolls = [randint(1, sides) for _ in range(num_dice)]
                total = sum(rolls)
                self.last_dice_detail = {
                    "rolls": rolls,
                    "total": total
                }
                self.logger.info(f"Regular roll {dice_type}: Rolls: {rolls}, Total: {total}")

                self.last_dice_roll = total
                self.dice_roll_needed = False
                self.dice_type = None
                return total
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
        if 'strength' in state_update:
            self.strength = state_update['strength']
        if 'dexterity' in state_update:
            self.dexterity = state_update['dexterity']
        if 'constitution' in state_update:
            self.constitution = state_update['constitution']
        if 'intelligence' in state_update:
            self.intelligence = state_update['intelligence']
        if 'wisdom' in state_update:
            self.wisdom = state_update['wisdom']
        if 'charisma' in state_update:
            self.charisma = state_update['charisma']
            
        # Update enemy state if in combat
        enemy_health = state_update.get('enemy_health')
        if enemy_health is not None and self.enemy:
            self.enemy["hp"] = enemy_health
            
        # Update dice roll state
        self.dice_roll_needed = state_update.get('dice_roll_needed', False)
        self.dice_type = state_update.get('dice_type')

    def get_ability_scores(self):
        """Return the player's final ability scores, using stored base stats if available."""
        final_scores = {}
        for ability in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
            base_stat = getattr(self, ability, None)
            if base_stat is None:
                class_defaults = CLASS_CONFIGS.get(self.player_class, {}).get("default_stats", {
                    "strength": 10,
                    "dexterity": 10,
                    "constitution": 10,
                    "intelligence": 10,
                    "wisdom": 10,
                    "charisma": 10
                })
                race_bonus = RACE_CONFIGS.get(self.player_race, {}).get("ability_scores", {})
                base_stat = class_defaults.get(ability, 10) + race_bonus.get(ability, 0)
            final_scores[ability] = base_stat
        return final_scores

    def get_all_stats(self):
        """Return all current player stats including ability scores"""
        return {
            'player_id': self.player_id if hasattr(self, 'player_id') else None,
            'player_race': self.player_race,
            'player_class': self.player_class,
            'level': self.level,
            'health_points': self.health_points,
            'gold': self.gold,
            'damage': self.damage,
            'magic_1lvl': self.magic_1lvl,
            'magic_2lvl': self.magic_2lvl,
            'in_combat': self.in_combat,
            'dice_roll_needed': self.dice_roll_needed,
            'dice_type': self.dice_type,
            'ability_scores': self.get_ability_scores()
        }

    def send_message(self, message, player_id=None, room_state=None):
        """Send message and get structured response"""
        self.logger.info(f"\nSending message: {message}")
        
        # Build context with current stats
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
                if pid == player_id:
                    current_stats += f"Last Roll: {player.last_dice_roll if player.last_dice_roll is not None else 'None'}\n"
                    ability_scores = self.get_ability_scores()
                    current_stats += "Ability Scores:\n"
                    for ability, score in ability_scores.items():
                        current_stats += f"  {ability.capitalize()}: {score}\n"
        else:
            self.logger.error("No room_state provided to send_message")
            return {
                'message': 'Error: Game state not found',
                'player_update_required': False,
                'dice_roll_required': False,
                'combat_started': False
            }
        
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
        
        # Build context from message history
        context = "Previous messages:\n"
        if room_state and hasattr(room_state, 'message_history'):
            for msg in room_state.message_history[-10:]:
                if isinstance(msg, dict):
                    if msg.get('type') == 'player':
                        context += f"{msg.get('player_name', 'Player')}: {msg.get('user_message', '')}\n"
                        if msg.get('dm_response'):
                            context += f"DM: {msg.get('dm_response')}\n"
                    elif msg.get('type') == 'dm':
                        context += f"DM: {msg.get('message', '')}\n"
                    elif msg.get('type') == 'system':
                        context += f"System: {msg.get('message', '')}\n"
                else:
                    if msg.player_name:
                        context += f"{msg.player_name}: {msg.user_message}\n"
                    else:
                        context += f"Player: {msg.user_message}\n"
                    if msg.dm_response:
                        context += f"DM: {msg.dm_response}\n"
        else:
            self.logger.warning("No message history found in room_state")
            context += "No previous messages available.\n"
        
        full_message = f"{current_stats}\n{context}\nCurrent message: {message}"
        self.logger.debug(f"Full message to Gemini:\n{full_message}")
        
        # Send message to Gemini and get response in new format
        response = self.chat.send_structured_message(full_message)
        self.logger.info(f"Gemini response: {response}")
        
        # Extract the required fields from the response
        message_text = response.get('message', '')
        if not message_text:
            message_text = "I don't understand. Please try again."
            self.logger.warning("Empty message from Gemini")
        
        # Get the required boolean flags
        player_update_required = response.get('player_update_required', False)
        dice_roll_required = response.get('dice_roll_required', False)
        combat_started = response.get('combat_started', False)
        
        # Transform player updates using the PLAYER_UPDATE_SCHEMA
        players_update = response.get('players_update', []) if player_update_required else []
        dice_roll_request = response.get('dice_roll_request', {}) if dice_roll_required else {}
        
        # Do not append the dice roll reason to the public message.
        # The dice_roll_request is returned as a separate field.
        
        return {
            'message': message_text,
            'player_update_required': player_update_required,
            'players_update': players_update,
            'dice_roll_required': dice_roll_required,
            'dice_roll_request': dice_roll_request,
            'combat_started': combat_started
        }

    def start_game(self):
        """Generate opening scene based on character"""
        start_prompt = GAME_START_PROMPTS.get(self.language, GAME_START_PROMPTS["en"]).format(
            race=self.player_race,
            class_name=self.player_class
        )
        return self.send_message(start_prompt, player_id=self.player_id, room_state=self.room_state)

    def start_combat(self, enemy_type=None):
        """Start combat with a random or specific enemy"""
        if enemy_type is None:
            enemy_type = choice(list(ENEMIES.keys()))
        
        self.enemy = get_enemy(enemy_type)
        self.enemy["name"] = enemy_type  # Store the translation key
        self.in_combat = True
        
        # Load translations for the current language
        translations = load_translations(self.language)
        enemy_name = translations.get(enemy_type, enemy_type)  # Get translated name or fallback to key
        
        combat_start = self.send_message(f"""
        A {enemy_name} appears! Combat starts!
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
            
            # Load translations for the current language
            translations = load_translations(self.language)
            enemy_name = translations.get(self.enemy["name"], self.enemy["name"])  # Get translated name or fallback to key
            
            return "You successfully fled from combat!"
        
        enemy_damage = randint(*self.enemy["damage"])
        self.health_points -= enemy_damage
        
        # Load translations for the current language
        translations = load_translations(self.language)
        enemy_name = translations.get(self.enemy["name"], self.enemy["name"])  # Get translated name or fallback to key
        
        return f"Failed to flee! The {enemy_name} hits you for {enemy_damage} damage!"

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
        
        # Load translations for the current language
        translations = load_translations(self.language)
        enemy_name = translations.get(self.enemy["name"], self.enemy["name"])  # Get translated name or fallback to key
        
        if xp_reward >= 100:
            self.level += 1
            self.health_points += 5
            self.damage += 1
            level_up_msg = f'Level up! You are now level {self.level}!'
        else:
            level_up_msg = ''
        
        self.in_combat = False
        victory_message = f"""
        You defeated the {enemy_name}!
        Gained {gold_reward} gold and {xp_reward} XP!
        {level_up_msg}
        """
        self.enemy = None
        return victory_message

    def _handle_enemy_counter_attack(self, player_damage, is_spell=False):
        """Handle enemy's counter attack"""
        enemy_damage = randint(*self.enemy["damage"])
        self.health_points -= enemy_damage
        
        # Load translations for the current language
        translations = load_translations(self.language)
        enemy_name = translations.get(self.enemy["name"], self.enemy["name"])  # Get translated name or fallback to key
        
        if self.health_points <= 0:
            self.in_combat = False
            self.enemy = None
            return "You have been defeated! Game Over!"
        
        action_type = "spell" if is_spell else "hit"
        return f"""
        Your {action_type} the {enemy_name} for {player_damage} damage!
        The {enemy_name} hits you for {enemy_damage} damage!
        
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
        defaults = CLASS_CONFIGS.get(self.player_class, {}).get("default_stats", {
            "strength": 10,
            "dexterity": 10,
            "constitution": 10,
            "intelligence": 10,
            "wisdom": 10,
            "charisma": 10
        })
        race_bonus = RACE_CONFIGS.get(self.player_race, {}).get("ability_scores", {})
        self.strength = defaults.get("strength", 10) + race_bonus.get("strength", 0)
        self.dexterity = defaults.get("dexterity", 10) + race_bonus.get("dexterity", 0)
        self.constitution = defaults.get("constitution", 10) + race_bonus.get("constitution", 0)
        self.intelligence = defaults.get("intelligence", 10) + race_bonus.get("intelligence", 0)
        self.wisdom = defaults.get("wisdom", 10) + race_bonus.get("wisdom", 0)
        self.charisma = defaults.get("charisma", 10) + race_bonus.get("charisma", 0)
        
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
            'language': self.language,
            'strength': getattr(self, 'strength', None),
            'dexterity': getattr(self, 'dexterity', None),
            'constitution': getattr(self, 'constitution', None),
            'intelligence': getattr(self, 'intelligence', None),
            'wisdom': getattr(self, 'wisdom', None),
            'charisma': getattr(self, 'charisma', None)
        }

    def load_state_from_dict(self, state_dict):
        """Load game state from a dictionary"""
        for key, value in state_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.initialize_chat()
