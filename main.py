from DEF import DnDGame

def main():
    game = DnDGame()
    print("Welcome to D&D Console Adventure!")
    
    # Спрашиваем, хочет ли игрок загрузить сохранение
    load_choice = input("Would you like to load a saved game? (yes/no): ").strip().lower()
    
    if load_choice == 'yes':
        print(game.list_saves())
        save_name = input("Enter save name (or press Enter for quicksave): ").strip()
        if not save_name:
            save_name = "quicksave"
        response = game.load_game(save_name)
        print(response)
    else:
        # Создание нового персонажа
        game.choose_race()
        game.choose_class()
        opening_scene = game.start_game()
        print(f"\nDungeon Master: {opening_scene}")
    
    # Основной игровой цикл
    while True:
        user_input = input("\nYour action (type 'help' for commands): ").strip()
        
        if user_input.lower() == 'quit':
            # Предлагаем сохранить игру перед выходом
            save_choice = input("Would you like to save before quitting? (yes/no): ").strip().lower()
            if save_choice == 'yes':
                save_name = input("Enter save name (or press Enter for quicksave): ").strip()
                if not save_name:
                    save_name = "quicksave"
                print(game.save_game(save_name))
            break
            
        elif user_input.lower() == 'save':
            save_name = input("Enter save name (or press Enter for quicksave): ").strip()
            if not save_name:
                save_name = "quicksave"
            print(game.save_game(save_name))
            continue
            
        elif user_input.lower() == 'load':
            print(game.list_saves())
            save_name = input("Enter save name to load (or press Enter for quicksave): ").strip()
            if not save_name:
                save_name = "quicksave"
            print(game.load_game(save_name))
            continue
            
        elif user_input.lower() == 'help':
            print("""
            Available commands:
            - fight: Start combat
            - save: Save your game
            - load: Load a saved game
            - quit: Exit the game
            - help: Show this message
            
            In combat:
            - attack: Attack the enemy
            - spell: Cast a spell
            - flee: Try to run away
            """)
            continue
            
        elif user_input.lower() == 'fight':
            response = game.start_combat()
        else:
            response = game.send_message(user_input)
            
        print(f"\nDungeon Master: {response}")
        
        if game.health_points <= 0:
            print("\nGame Over! Your character has been defeated!")
            break

if __name__ == "__main__":
    main()