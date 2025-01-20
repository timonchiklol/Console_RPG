from random import randint, choice
from gemini import Gemini
from dotenv import load_dotenv
import os
import json
import sys

class DnDGame:
    def __init__(self):
        # Загружаем переменные окружения
        load_dotenv()
        
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
        
        # Message generation settings
        self.streaming_mode = True  # Default to streaming
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

    def initialize_chat(self):
        """Initialize the chat with the selected language"""
        # Получаем API ключ из .env файла
        api_key = os.getenv("GEMINI_API_KEY")
        
        # Simplified system prompt focusing only on role and language
        system_prompt = """You are a creative and engaging Dungeon Master in a D&D game.
        Generate immersive descriptions and respond to player actions in character.
        Always respond in {language} language only.
        Keep responses concise but atmospheric.""".format(language="Russian" if self.language == "ru" else "English")
        
        # Initialize the chat with the system prompt
        self.chat = Gemini(API_KEY=api_key, system_instruction=system_prompt)

    def update_system_prompt(self):
        """Обновляет системный промпт с текущими характеристиками игрока"""
        current_stats = f"""Current player stats:
        Race: {self.player_race}
        Class: {self.player_class}
        Level: {self.level}
        HP: {self.health_points}
        Damage: {self.damage}
        Gold: {self.gold}
        Language: {self.language}"""
        return self.chat.send_message(f"Remember these player stats and always respond in {self.language} language: {current_stats}")
    
    def add_to_history(self, user_message, dm_response):
        """Сохраняет последние 3 сообщения"""
        self.message_history.append({"user": user_message, "dm": dm_response})
        if len(self.message_history) > 3:
            self.message_history.pop(0)
    
    def send_message(self, message):
        """Отправляет сообщение DM с контекстом последних сообщений"""
        # Если получена команда fight, начинаем бой
        if message.lower() == 'fight':
            return self.start_combat()
        
        # Если мы в бою, обрабатываем боевые действия
        if self.in_combat:
            return self.process_combat_action(message)
        
        # Если не в бою, обрабатываем обычное сообщение
        current_stats = f"""Current player stats:
        Race: {self.player_race}
        Class: {self.player_class}
        Level: {self.level}
        HP: {self.health_points}
        Damage: {self.damage}
        Gold: {self.gold}
        Magic slots (1st/2nd level): {self.magic_1lvl}/{self.magic_2lvl}
        """
        
        # Get limited context from message history
        start_idx = max(0, len(self.message_history) - self.context_limit)
        context = f"Previous messages (last {self.context_limit}):\n"
        for msg in self.message_history[start_idx:]:
            context += f"Player: {msg['user']}\nDM: {msg['dm']}\n"
        
        full_message = f"{current_stats}\n{context}\nCurrent message: {message}"
        
        if self.streaming_mode:
            print(f"\n{self.get_text('Мастер: ', 'Dungeon Master: ')}", end="")
            response_chunks = []
            for chunk in self.chat.send_message_stream(full_message):
                print(chunk.text, end="", flush=True)
                response_chunks.append(chunk.text)
            print()
            response = "".join(response_chunks)
        else:
            response = self.chat.send_message(full_message)
            print(f"\n{self.get_text('Мастер: ', 'Dungeon Master: ')}{response}")
        
        self.add_to_history(message, response)
        return response

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
            'enemy': self.enemy
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
        self.update_system_prompt()
