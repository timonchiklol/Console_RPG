from random import randint, choice
from gemini import Gemini
from dotenv import load_dotenv
import os
import json
import sys
from gemini_schema import GameState
import logging

class DnDGame:
    def __init__(self):
        # Загружаем переменные окружения
        load_dotenv()
        
        # Set up logging
        self.setup_logging()
        
        self.language = "ru"  # Язык по умолчанию
        self.gold = 0
        self.magic_1lvl = 0
        self.magic_2lvl = 0
        self.level = 0
        self.health_points = 0
        self.damage = randint(1,10)
        self.player_race = ""
        self.player_class = ""
        self.in_combat = False
        self.enemy = None
        self.save_folder = "saves"  # Папка для сохранений
        self.last_dice_roll = None
        self.dice_roll_needed = False
        self.dice_type = None
        
        # Message generation settings
        self.context_limit = 50  # Number of messages to keep in context
        self.message_history = []  # Хранение последних сообщений
        
        # Создаем папку для сохранений, если её нет
        if not os.path.exists(self.save_folder):
            os.makedirs(self.save_folder)
            
        # Добавим список возможных врагов
        self.enemies = {
            "Goblin": {"hp": 7, "damage": (1,6), "xp": 50, "gold": (1,6)},
            "Skeleton": {"hp": 13, "damage": (1,8), "xp": 100, "gold": (2,8)},
            "Orc": {"hp": 15, "damage": (1,12), "xp": 150, "gold": (2,10)},
            "Wolf": {"hp": 11, "damage": (2,4), "xp": 75, "gold": (0,2)},
            "Bandit": {"hp": 11, "damage": (1,8), "xp": 100, "gold": (4,10)},
            "Zombie": {"hp": 22, "damage": (1,6), "xp": 125, "gold": (0,4)},
            "Dark Cultist": {"hp": 9, "damage": (1,10), "xp": 150, "gold": (3,8)},
            "Giant Spider": {"hp": 10, "damage": (1,8), "xp": 100, "gold": (0,3)}
        }

    def setup_logging(self):
        """Set up logging configuration"""
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('game.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def initialize_chat(self):
        """Initialize the chat with the selected language"""
        api_key = os.getenv("GEMINI_API_KEY")
        
        system_prompts = {
            "ru": """Вы - Мастер Подземелий (DM) в игре D&D. 
            СТРОГОЕ ПРАВИЛО: Вы ДОЛЖНЫ отвечать ТОЛЬКО на русском языке, без единого английского слова.
            
            Ваша роль:
            1. Создавать захватывающие описания на русском языке
            2. Вести повествование как настоящий русскоговорящий Мастер Подземелий
            3. Все игровые термины использовать на русском языке
            4. Отвечать на действия игрока только на русском
            
            Пример ответа:
            "В тусклом свете таверны вы видите..."
            "Внезапно из темноты появляется..."
            "Бросьте кубик d20 на проверку..."
            
            Технические правила:
            1. HP изменяется только при получении/лечении урона
            2. Урон вычитается из текущего HP
            3. Проверять HP перед изменениями
            4. Изменения HP включать в state_update
            
            Броски кубиков:
            1. dice_roll.required = true при необходимости броска
            2. dice_roll.type = тип кубика ('d20', '2d6')
            3. dice_roll.reason = причина броска на русском языке
            4. Ждать броска игрока""",
            
            "en": """You are a creative and engaging Dungeon Master in a D&D game.
            Generate immersive descriptions and respond to player actions in character.
            IMPORTANT: Respond ONLY in English.
            
            Important rules:
            1. Health points (HP) should only change by exact damage/healing
            2. When dealing damage, subtract from current HP
            3. Always check current HP before changes
            4. Include HP changes in state_update
            
            When requesting dice rolls:
            1. Set dice_roll.required to true
            2. Specify dice_type ('d20', '2d6')
            3. Explain roll reason
            4. Wait for player roll"""
        }
        
        # Выбираем промпт в зависимости от языка
        system_prompt = system_prompts.get(self.language, system_prompts["en"])
        
        # Добавляем дополнительное указание для русского языка
        if self.language == "ru":
            system_prompt += "\n\nВАЖНО: Все ответы должны быть ТОЛЬКО на русском языке!"
        
        # Initialize the chat with the system prompt
        self.chat = Gemini(API_KEY=api_key, system_instruction=system_prompt)
        
        # Отправляем первое сообщение для установки языка
        if self.language == "ru":
            self.chat.send_message("Пожалуйста, подтвердите, что вы будете отвечать только на русском языке.")

    def update_system_prompt(self):
        """Обновляет системный промпт с текущими характеристиками игрока"""
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
        """Сохраняет последние сообщения в пределах context_limit"""
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

    def send_message(self, message):
        """Send message and get structured response"""
        self.logger.info(f"\nSending message: {message}")
        
        # Get current stats for context
        current_stats = f"""Current player stats:
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
        
        if self.in_combat and self.enemy:
            current_stats += f"Enemy: {self.enemy['name']} (HP: {self.enemy['hp']})"
        
        self.logger.debug(f"Current stats:\n{current_stats}")
        
        # Get limited context from message history
        context = "Previous messages:\n"
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
        
        # Handle dice roll requests - check both new and old format
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
        elif response.get('required_action') == "roll_dice":
            # Fallback for old format
            dice_roll_needed = True
            dice_type = response.get('state_update', {}).get('dice_type', 'd20')
            self.logger.info(f"Dice roll required (fallback): {dice_type}")
        
        # Update dice roll state
        self.dice_roll_needed = dice_roll_needed
        self.dice_type = dice_type
        
        # Handle combat results first
        if response.get('combat_result'):
            combat_result = response['combat_result']
            self.logger.info(f"Combat result: {combat_result}")
            
            if combat_result.get('damage_dealt') and self.enemy:
                old_enemy_hp = self.enemy["hp"]
                self.enemy["hp"] -= combat_result['damage_dealt']
                self.logger.info(f"Enemy HP changed from {old_enemy_hp} to {self.enemy['hp']}")
                
            if combat_result.get('damage_taken'):
                old_hp = self.health_points
                self.health_points -= combat_result['damage_taken']
                self.logger.info(f"Player HP changed from {old_hp} to {self.health_points}")
            
            # Check if combat should end
            if self.enemy and self.enemy["hp"] <= 0:
                self.in_combat = False
                self.enemy = None
                self.logger.info("Combat ended - enemy defeated")
            elif self.health_points <= 0:
                self.in_combat = False
                message_text += "\nYou have been defeated! Game Over!"
                self.logger.info("Combat ended - player defeated")
        
        # Update non-combat state if provided
        state_update = response.get('state_update', {})
        if state_update:
            self.logger.info(f"State update received: {state_update}")
            # Remove health updates if they were handled in combat_result
            if response.get('combat_result'):
                if 'health_points' in state_update:
                    self.logger.info("Skipping health update from state_update as it was handled in combat_result")
                    state_update.pop('health_points')
                if 'enemy_health' in state_update:
                    self.logger.info("Skipping enemy health update from state_update as it was handled in combat_result")
                    state_update.pop('enemy_health')
            
            # Always include dice roll state in state update
            state_update['dice_roll_needed'] = dice_roll_needed
            state_update['dice_type'] = dice_type
            
            self.update_state(state_update)
        else:
            # If no state update, create one for dice roll state
            state_update = {
                'dice_roll_needed': dice_roll_needed,
                'dice_type': dice_type
            }
            self.update_state(state_update)
        
        # Add to history and return formatted response
        self.add_to_history(message, message_text)
        
        return {
            'message': message_text,
            'dice_roll_needed': dice_roll_needed,
            'dice_type': dice_type,
            'state_update': state_update,
            'combat_result': response.get('combat_result')
        }

    def start_game(self):
        """Генерирует начало игры на основе характеристик персонажа"""
        start_prompt = f"""Generate a D&D game opening scene. The player is a {self.player_race} {self.player_class}.
        Include:
        - Description of the starting location (preferably a tavern)
        - Some NPCs or activity around
        - A hook to start the adventure
        - A mysterious figure or event that draws the player in
        Keep it concise but engaging. Make it feel personal to the player's race and class."""
        
        opening_scene = self.send_message(start_prompt)
        return opening_scene

    def choose_language(self):
        """Позволяет игроку выбрать язык игры"""
        print("""Available languages / Доступные языки:
        1. Русский (Russian)
        2. English (Английский)
        0. Quit / Выход
        """)
        choice = input("Choose language / Выберите язык (0/1/2): ").strip().lower()
        
        if choice == "1":
            self.language = "ru"
            print("Язык установлен на русский")
            self.initialize_chat()
            return "ru"
        elif choice == "2":
            self.language = "en"
            print("Language set to English")
            self.initialize_chat()
            return "en"
        elif choice in ["0", "quit", "exit", "выход"]:
            print("Exiting game / Выход из игры")
            sys.exit()
        else:
            print("Некорректный выбор / Invalid choice")
            return self.choose_language()

    def get_text(self, ru_text, en_text):
        """Возвращает текст на выбранном языке"""
        return ru_text if self.language == "ru" else en_text

    def choose_race(self):
        race_options_ru = """Варианты рас: 
        1. Человек (Сбалансированные характеристики, +5 HP)
        2. Эльф (Высокий урон, низкое HP)
        3. Дварф (Высокое HP, хорошее золото)
        4. Орк (Наивысший урон, самое низкое HP)
        5. Полурослик (Удачливый, бонус золота)
        6. Драконорожденный (Огненное дыхание, средние характеристики)
        7. Тифлинг (Темное зрение, магический бонус)
        8. Гном (Умный, дополнительные слоты заклинаний)
        
        0. Выход из игры / Quit game
        """
        
        race_options_en = """Race options: 
        1. Human (Balanced stats, +5 HP)
        2. Elf (High damage, lower HP)
        3. Dwarf (High HP, good gold)
        4. Orc (Highest damage, lowest HP)
        5. Halfling (Lucky, bonus gold)
        6. Dragonborn (Fire breath, medium stats)
        7. Tiefling (Dark vision, magic bonus)
        8. Gnome (Smart, extra magic slots)
        
        0. Quit game
        """
        
        # Словарь соответствия номеров и рас
        race_map = {
            "1": "Human",
            "2": "Elf",
            "3": "Dwarf",
            "4": "Orc",
            "5": "Halfling",
            "6": "Dragonborn",
            "7": "Tiefling",
            "8": "Gnome"
        }
        
        print(self.get_text(race_options_ru, race_options_en))
        choice_prompt_ru = "Выберите номер расы (0-8): "
        choice_prompt_en = "Choose race number (0-8): "
        
        while True:
            choice = input(self.get_text(choice_prompt_ru, choice_prompt_en)).strip().lower()
            if choice in ["0", "quit", "exit", "выход"]:
                print(self.get_text("Выход из игры", "Exiting game"))
                sys.exit()
            if choice in race_map:
                self.player_race = race_map[choice]
                break
            else:
                error_ru = "Пожалуйста, введите число от 0 до 8."
                error_en = "Please enter a number between 0 and 8."
                print(self.get_text(error_ru, error_en))

        # Установка характеристик в зависимости от расы
        if self.player_race == "Human":
            self.health_points = 15
            self.level = 1
            self.gold = 5
            self.damage = randint(2,7)
        elif self.player_race == "Elf":
            self.health_points = 10
            self.level = 1
            self.gold = 5
            self.damage = randint(1,12)
        elif self.player_race == "Dwarf":
            self.health_points = 18
            self.level = 1
            self.gold = 8
            self.damage = randint(1,8)
        elif self.player_race == "Orc":
            self.health_points = 8
            self.level = 1
            self.gold = 3
            self.damage = randint(3,12)
        elif self.player_race == "Halfling":
            self.health_points = 12
            self.level = 1
            self.gold = 10
            self.damage = randint(1,6)
        elif self.player_race == "Dragonborn":
            self.health_points = 14
            self.level = 1
            self.gold = 6
            self.damage = randint(2,8)
        elif self.player_race == "Tiefling":
            self.health_points = 12
            self.level = 1
            self.gold = 5
            self.magic_1lvl = 1
            self.damage = randint(1,10)
        elif self.player_race == "Gnome":
            self.health_points = 10
            self.level = 1
            self.gold = 7
            self.magic_1lvl = 2
            self.damage = randint(1,6)
        else:
            print("I dont understand:( Please choose from the list.")
            self.choose_race()
        self.update_system_prompt()

    def choose_class(self):
        class_options_ru = """Варианты классов:
        1. Воин (Высокое HP, хороший урон)
        2. Маг (Низкое HP, сильная магия)
        3. Следопыт (Среднее HP, дальний бой)
        4. Плут (Низкое HP, высокий урон)
        5. Паладин (Высокое HP, немного магии)
        6. Чернокнижник (Среднее HP, темная магия)
        7. Бард (Среднее HP, магия очарования)
        8. Жрец (Высокое HP, целебная магия)
        9. Монах (Среднее HP, боевые искусства)
        10. Друид (Среднее HP, природная магия)
        
        0. Выход из игры / Quit game
        """
        
        class_options_en = """Class options:
        1. Warrior (High HP, good damage)
        2. Mage (Low HP, high magic)
        3. Ranger (Medium HP, ranged damage)
        4. Rogue (Low HP, high damage)
        5. Paladin (High HP, some magic)
        6. Warlock (Medium HP, dark magic)
        7. Bard (Medium HP, charm magic)
        8. Cleric (High HP, healing magic)
        9. Monk (Medium HP, martial arts)
        10. Druid (Medium HP, nature magic)
        
        0. Quit game
        """
        
        # Словарь соответствия номеров и классов
        class_map = {
            "1": "Warrior",
            "2": "Mage",
            "3": "Ranger",
            "4": "Rogue",
            "5": "Paladin",
            "6": "Warlock",
            "7": "Bard",
            "8": "Cleric",
            "9": "Monk",
            "10": "Druid"
        }
        
        print(self.get_text(class_options_ru, class_options_en))
        choice_prompt_ru = "Выберите номер класса (0-10): "
        choice_prompt_en = "Choose class number (0-10): "
        
        while True:
            choice = input(self.get_text(choice_prompt_ru, choice_prompt_en)).strip().lower()
            if choice in ["0", "quit", "exit", "выход"]:
                print(self.get_text("Выход из игры", "Exiting game"))
                sys.exit()
            if choice in class_map:
                self.player_class = class_map[choice]
                break
            else:
                error_ru = "Пожалуйста, введите число от 0 до 10."
                error_en = "Please enter a number between 0 and 10."
                print(self.get_text(error_ru, error_en))

        # Установка характеристик в зависимости от класса
        if self.player_class == "Warrior":
            self.health_points += 5
            self.gold += 2
            self.magic_1lvl = 0
        elif self.player_class == "Mage":
            self.health_points += 2
            self.gold += 1
            self.magic_1lvl += 3
            self.magic_2lvl = 1
        elif self.player_class == "Ranger":
            self.health_points += 3
            self.gold += 3
            self.magic_1lvl += 1
        elif self.player_class == "Rogue":
            self.health_points += 2
            self.gold += 5
            self.damage += 2
        elif self.player_class == "Paladin":
            self.health_points += 4
            self.gold += 2
            self.magic_1lvl += 1
        elif self.player_class == "Warlock":
            self.health_points += 3
            self.gold += 1
            self.magic_1lvl += 2
            self.magic_2lvl = 1
        elif self.player_class == "Bard":
            self.health_points += 3
            self.gold += 4
            self.magic_1lvl += 2
        elif self.player_class == "Cleric":
            self.health_points += 4
            self.gold += 1
            self.magic_1lvl += 2
            self.magic_2lvl = 1
        elif self.player_class == "Monk":
            self.health_points += 3
            self.gold += 1
            self.damage += 1
        elif self.player_class == "Druid":
            self.health_points += 3
            self.gold += 2
            self.magic_1lvl += 2
            self.magic_2lvl = 1
        else:
            print("I dont understand:( Please choose from the list.")
            self.choose_class()
        self.update_system_prompt()

    def start_combat(self, enemy_type=None):
        """Начинает бой с случайным или конкретным противником"""
        if enemy_type is None:
            enemy_type = choice(list(self.enemies.keys()))
        
        enemy = self.enemies[enemy_type].copy()
        enemy["name"] = enemy_type
        enemy["current_hp"] = enemy["hp"]
        self.enemy = enemy
        self.in_combat = True
        
        combat_start = self.send_message(f"""
        A {enemy_type} appears! Combat starts!
        Enemy HP: {enemy['current_hp']}
        Your HP: {self.health_points}
        
        What do you do? (attack/spell/flee)
        """)
        return combat_start

    def process_combat_action(self, action):
        """Обрабатывает действие игрока в бою"""
        if not self.in_combat or not self.enemy:
            return "You're not in combat!"

        action = action.lower()
        
        # Обработка попытки бегства
        if action == "flee":
            if randint(1, 20) > 12:  # 40% шанс сбежать
                self.in_combat = False
                self.enemy = None
                return "You successfully fled from combat!"
            else:
                enemy_damage = randint(*self.enemy["damage"])
                self.health_points -= enemy_damage
                return f"Failed to flee! The {self.enemy['name']} hits you for {enemy_damage} damage!"

        # Обработка атаки
        elif action == "attack":
            player_damage = randint(1, self.damage)
            self.enemy["current_hp"] -= player_damage
            
            # Проверка победы
            if self.enemy["current_hp"] <= 0:
                gold_reward = randint(*self.enemy["gold"])
                xp_reward = self.enemy["xp"]
                self.gold += gold_reward
                
                # Повышение уровня
                if xp_reward >= 100:
                    self.level += 1
                    self.health_points += 5
                    self.damage += 1
                
                self.in_combat = False
                victory_message = f"""
                You defeated the {self.enemy['name']}!
                Gained {gold_reward} gold and {xp_reward} XP!
                {f'Level up! You are now level {self.level}!' if xp_reward >= 100 else ''}
                """
                self.enemy = None
                return victory_message
            
            # Ответная атака врага
            enemy_damage = randint(*self.enemy["damage"])
            self.health_points -= enemy_damage
            
            # Проверка поражения
            if self.health_points <= 0:
                self.in_combat = False
                self.enemy = None
                return "You have been defeated! Game Over!"
            
            return f"""
            You hit the {self.enemy['name']} for {player_damage} damage!
            The {self.enemy['name']} hits you for {enemy_damage} damage!
            
            Enemy HP: {self.enemy['current_hp']}
            Your HP: {self.health_points}
            """

        # Обработка заклинаний
        elif action == "spell":
            if self.magic_1lvl <= 0:
                return "You have no spell slots left!"
            
            self.magic_1lvl -= 1
            spell_damage = randint(3, 10)  # Магия наносит больше урона
            self.enemy["current_hp"] -= spell_damage
            
            if self.enemy["current_hp"] <= 0:
                gold_reward = randint(*self.enemy["gold"])
                xp_reward = self.enemy["xp"]
                self.gold += gold_reward
                
                if xp_reward >= 100:
                    self.level += 1
                    self.health_points += 5
                    self.damage += 1
                
                self.in_combat = False
                victory_message = f"""
                Your spell defeats the {self.enemy['name']}!
                Gained {gold_reward} gold and {xp_reward} XP!
                {f'Level up! You are now level {self.level}!' if xp_reward >= 100 else ''}
                Spell slots remaining: {self.magic_1lvl}
                """
                self.enemy = None
                return victory_message
            
            enemy_damage = randint(*self.enemy["damage"])
            self.health_points -= enemy_damage
            
            if self.health_points <= 0:
                self.in_combat = False
                self.enemy = None
                return "You have been defeated! Game Over!"
            
            return f"""
            Your spell hits the {self.enemy['name']} for {spell_damage} damage!
            The {self.enemy['name']} hits you for {enemy_damage} damage!
            
            Enemy HP: {self.enemy['current_hp']}
            Your HP: {self.health_points}
            Spell slots remaining: {self.magic_1lvl}
            """

    def save_game(self, save_name="quicksave"):
        """Сохраняет текущее состояние игры"""
        save_data = {
            "player_race": self.player_race,
            "player_class": self.player_class,
            "level": self.level,
            "health_points": self.health_points,
            "damage": self.damage,
            "gold": self.gold,
            "magic_1lvl": self.magic_1lvl,
            "magic_2lvl": self.magic_2lvl,
            "in_combat": self.in_combat,
            "enemy": self.enemy,
            "message_history": self.message_history,
            "language": self.language
        }
        
        save_path = os.path.join(self.save_folder, f"{save_name}.json")
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=4)
        
        save_ru = "Игра сохранена в файл {}.json"
        save_en = "Game saved to {}.json"
        return self.get_text(save_ru, save_en).format(save_name)

    def load_game(self, save_name="quicksave"):
        """Загружает сохраненное состояние игры"""
        save_path = os.path.join(self.save_folder, f"{save_name}.json")
        
        if not os.path.exists(save_path):
            return self.get_text("Сохранение не найдено!", "Save file not found!")
            
        try:
            with open(save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            self.player_race = save_data["player_race"]
            self.player_class = save_data["player_class"]
            self.level = save_data["level"]
            self.health_points = save_data["health_points"]
            self.damage = save_data["damage"]
            self.gold = save_data["gold"]
            self.magic_1lvl = save_data["magic_1lvl"]
            self.magic_2lvl = save_data["magic_2lvl"]
            self.in_combat = save_data["in_combat"]
            self.enemy = save_data["enemy"]
            self.message_history = save_data["message_history"]
            self.language = save_data.get("language", self.language)  # Fallback to current language if not saved
            
            return self.get_text("Игра успешно загружена!", "Game successfully loaded!")
        except Exception as e:
            error_ru = "Ошибка при загрузке сохранения: {}"
            error_en = "Error loading save file: {}"
            return self.get_text(error_ru, error_en).format(str(e))

    def list_saves(self):
        """Показывает список доступных сохранений"""
        saves = [f.replace('.json', '') for f in os.listdir(self.save_folder) if f.endswith('.json')]
        if not saves:
            return self.get_text("Сохранений не найдено!", "No save files found!")
        saves_list = "\n".join(saves)
        return self.get_text(f"Доступные сохранения:\n{saves_list}", f"Available saves:\n{saves_list}")

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
        # Initialize chat if not already initialized
        if not hasattr(self, 'chat'):
            self.initialize_chat()
            
        # Race stats
        if self.player_race == "Human":
            self.health_points = 15
            self.level = 1
            self.gold = 5
            self.damage = randint(2,7)
        elif self.player_race == "Elf":
            self.health_points = 10
            self.level = 1
            self.gold = 5
            self.damage = randint(1,12)
        elif self.player_race == "Dwarf":
            self.health_points = 18
            self.level = 1
            self.gold = 8
            self.damage = randint(1,8)
        elif self.player_race == "Orc":
            self.health_points = 8
            self.level = 1
            self.gold = 3
            self.damage = randint(3,12)
        elif self.player_race == "Halfling":
            self.health_points = 12
            self.level = 1
            self.gold = 10
            self.damage = randint(1,6)
        elif self.player_race == "Dragonborn":
            self.health_points = 14
            self.level = 1
            self.gold = 6
            self.damage = randint(2,8)
        elif self.player_race == "Tiefling":
            self.health_points = 12
            self.level = 1
            self.gold = 5
            self.magic_1lvl = 1
            self.damage = randint(1,10)
        elif self.player_race == "Gnome":
            self.health_points = 10
            self.level = 1
            self.gold = 7
            self.magic_1lvl = 2
            self.damage = randint(1,6)

        # Class bonuses
        if self.player_class == "Warrior":
            self.health_points += 5
            self.gold += 2
            self.magic_1lvl = 0
        elif self.player_class == "Mage":
            self.health_points += 2
            self.gold += 1
            self.magic_1lvl += 3
            self.magic_2lvl = 1
        elif self.player_class == "Ranger":
            self.health_points += 3
            self.gold += 3
            self.magic_1lvl += 1
        elif self.player_class == "Rogue":
            self.health_points += 2
            self.gold += 5
            self.damage += 2
        elif self.player_class == "Paladin":
            self.health_points += 4
            self.gold += 2
            self.magic_1lvl += 1
        elif self.player_class == "Warlock":
            self.health_points += 3
            self.gold += 1
            self.magic_1lvl += 2
            self.magic_2lvl = 1
        elif self.player_class == "Bard":
            self.health_points += 3
            self.gold += 4
            self.magic_1lvl += 2
        elif self.player_class == "Cleric":
            self.health_points += 4
            self.gold += 1
            self.magic_1lvl += 2
            self.magic_2lvl = 1
        elif self.player_class == "Monk":
            self.health_points += 3
            self.gold += 1
            self.damage += 1
        elif self.player_class == "Druid":
            self.health_points += 3
            self.gold += 2
            self.magic_1lvl += 2
            self.magic_2lvl = 1

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
            'message_history': self.message_history  # Include message history in state
        }

    def load_state_from_dict(self, state_dict):
        """Load game state from a dictionary"""
        self.player_race = state_dict['player_race']
        self.player_class = state_dict['player_class']
        self.health_points = state_dict['health_points']
        self.gold = state_dict['gold']
        self.level = state_dict['level']
        self.damage = state_dict['damage']
        self.magic_1lvl = state_dict['magic_1lvl']
        self.magic_2lvl = state_dict['magic_2lvl']
        self.in_combat = state_dict['in_combat']
        self.enemy = state_dict['enemy']
        self.dice_roll_needed = state_dict.get('dice_roll_needed', False)
        self.dice_type = state_dict.get('dice_type')
        self.last_dice_roll = state_dict.get('last_dice_roll')
        self.message_history = state_dict.get('message_history', [])
        self.initialize_chat()  # Initialize chat before updating prompt
        self.update_system_prompt()
