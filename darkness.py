# imports
from random import randint
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
        
        # Получаем API ключ из .env файла
        api_key = os.getenv("GEMINI_API_KEY")
        
        system_prompt = """You are a Dungeon Master in a D&D game. 
        Current player stats:
        Race: {race}
        Class: {class}
        Level: {level}
        HP: {hp}
        Damage: {damage}
        Gold: {gold}
        
        Remember these stats and refer to them in your responses.
        Keep your responses concise and engaging.
        Remember last 3 messages from conversation for context."""
        
        # Передаем API ключ при создании экземпляра Gemini
        self.chat = Gemini(API_KEY=api_key, system_instruction=system_prompt)
        self.message_history = []  # Хранение последних сообщений
        
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
        context = "Previous messages:\n"
        for msg in self.message_history:
            context += f"Player: {msg['user']}\nDM: {msg['dm']}\n"
        
        # Добавляем текущие характеристики к каждому сообщению
        current_stats = f"""Current player stats:
        Race: {self.player_race}
        Class: {self.player_class}
        Level: {self.level}
        HP: {self.health_points}
        Damage: {self.damage}
        Gold: {self.gold}
        
        """
        
        full_message = f"{current_stats}\n{context}\nCurrent message: {message}"
        response = self.chat.send_message(full_message)
        self.add_to_history(message, response)
        return response

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

def main():
    game = DnDGame()
    print("Welcome to D&D Console Adventure!")
    
    # Выбор персонажа
    game.choose_race()
    game.choose_class()
    
    # Начало игры
    print("\nThe tavern buzzes with life, laughter, and clinking tankards. A cloaked figure enters, their boots heavy on the wooden floor, and all eyes turn to them. They approach your table, drop a sealed parchment, and say, You're needed for something...")
    
    # Основной игровой цикл
    while True:
        user_input = input("\nYour action: ").strip()
        if user_input.lower() == 'quit':
            break
        response = game.send_message(user_input)
        print(f"\nDungeon Master: {response}")

if __name__ == "__main__":
    main()