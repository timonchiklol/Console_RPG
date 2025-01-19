from DEF import DnDGame

def main():
    game = DnDGame()
    print("Welcome to D&D Console Adventure!")
    
    # Выбор персонажа
    game.choose_race()
    game.choose_class()
    
    # Генерируем начало игры
    opening_scene = game.start_game()
    print(f"\nDungeon Master: {opening_scene}")
    
    # Основной игровой цикл
    while True:
        user_input = input("\nYour action: ").strip()
        
        if user_input.lower() == 'quit':
            break
            
        # Специальные команды для начала боя
        if user_input.lower() == 'fight':
            response = game.start_combat()
        else:
            response = game.send_message(user_input)
            
        print(f"\nDungeon Master: {response}")
        
        # Проверка здоровья
        if game.health_points <= 0:
            print("\nGame Over! Your character has been defeated!")
            break

if __name__ == "__main__":
    main()