from random import randint, choice
from gemini import Gemini
from dotenv import load_dotenv
import os

class DnDGame:
    def __init__(self):
        # Загружаем переменные окружения
        load_dotenv()
        
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
        
        # Получаем API ключ из .env файла
        api_key = os.getenv("GEMINI_API_KEY")
        
        # Изменяем системный промпт для лучшей генерации
        system_prompt = """You are a creative and engaging Dungeon Master in a D&D game.
        Generate immersive descriptions and respond to player actions in character.
        Current player stats:
        Race: {race}
        Class: {class}
        Level: {level}
        HP: {hp}
        Damage: {damage}
        Gold: {gold}
        
        Keep responses concise but atmospheric.
        Remember last 3 messages for context.
        Adapt the story based on player choices and stats."""
        
        # Передаем API ключ при создании экземпляра Gemini
        self.chat = Gemini(API_KEY=api_key, system_instruction=system_prompt)
        self.message_history = []  # Хранение последних сообщений
        
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
        
    def update_system_prompt(self):
        """Обновляет системный промпт с текущими характеристиками игрока"""
        current_stats = f"""Current player stats:
        Race: {self.player_race}
        Class: {self.player_class}
        Level: {self.level}
        HP: {self.health_points}
        Damage: {self.damage}
        Gold: {self.gold}"""
        return self.chat.send_message(f"Remember these player stats: {current_stats}")
    
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
        """
        
        context = "Previous messages:\n"
        for msg in self.message_history:
            context += f"Player: {msg['user']}\nDM: {msg['dm']}\n"
        
        full_message = f"{current_stats}\n{context}\nCurrent message: {message}"
        response = self.chat.send_message(full_message)
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

    def choose_race(self):
        print("""Race options: 
        1. Human (Balanced stats, +5 HP)
        2. Elf (High damage, lower HP)
        3. Dwarf (High HP, good gold)
        4. Orc (Highest damage, lowest HP)
        5. Halfling (Lucky, bonus gold)
        6. Dragonborn (Fire breath, medium stats)
        7. Tiefling (Dark vision, magic bonus)
        8. Gnome (Smart, extra magic slots)
        """)
        self.player_race = input("Choose your race: ").strip()
        
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
        # Добавляем приветствие от DM после выбора расы
        welcome_race = self.send_message(f"Welcome our new {self.player_race}! Give a brief lore-friendly comment about this race choice.")
        print(f"\nDungeon Master: {welcome_race}\n")

    def choose_class(self):
        print("""Class options:
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
        """)
        self.player_class = input("Choose your class: ").strip()
        
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
        # Добавляем комментарий от DM после выбора класса
        welcome_class = self.send_message(f"The player has chosen to be a {self.player_class}. Give a brief encouraging comment about this class choice.")
        print(f"\nDungeon Master: {welcome_class}\n")

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
