from DEF import DnDGame

def main():
    game = DnDGame()
    
    # Выбор языка в начале игры
    game.choose_language()
    
    # Приветственное сообщение на выбранном языке
    welcome_ru = "Добро пожаловать в D&D Консольное Приключение!"
    welcome_en = "Welcome to D&D Console Adventure!"
    print(game.get_text(welcome_ru, welcome_en))
    
    # Показываем доступные команды
    commands_ru = """
    Доступные команды:
    - бой: Начать сражение
    - сохранить: Сохранить игру
    - загрузить: Загрузить сохранённую игру
    - стиль: Переключить стиль сообщений
    - выход: Выйти из игры
    - помощь: Показать это сообщение
    """
    commands_en = """
    Available commands:
    - fight: Start combat
    - save: Save your game
    - load: Load a saved game
    - style: Toggle message style
    - quit: Exit the game
    - help: Show this message
    """
    print(game.get_text(commands_ru, commands_en))
    
    # Спрашиваем, хочет ли игрок загрузить сохранение
    load_prompt_ru = "Хотите загрузить сохраненную игру? (да/нет): "
    load_prompt_en = "Would you like to load a saved game? (yes/no): "
    load_choice = input(game.get_text(load_prompt_ru, load_prompt_en)).strip().lower()
    
    if load_choice in ['yes', 'да']:
        print(game.list_saves())
        save_prompt_ru = "Введите имя сохранения (или нажмите Enter для быстрого сохранения): "
        save_prompt_en = "Enter save name (or press Enter for quicksave): "
        save_name = input(game.get_text(save_prompt_ru, save_prompt_en)).strip()
        if not save_name:
            save_name = "quicksave"
        response = game.load_game(save_name)
        print(response)
    else:
        # Создание нового персонажа
        game.choose_race()
        game.choose_class()
        opening_scene = game.start_game()
    
    # Основной игровой цикл
    while True:
        action_prompt_ru = "\nВаше действие (введите 'помощь' для списка команд): "
        action_prompt_en = "\nYour action (type 'help' for commands): "
        user_input = input(game.get_text(action_prompt_ru, action_prompt_en)).strip()
        
        if user_input.lower() in ['quit', 'выход']:
            save_prompt_ru = "Хотите сохранить игру перед выходом? (да/нет): "
            save_prompt_en = "Would you like to save before quitting? (yes/no): "
            save_choice = input(game.get_text(save_prompt_ru, save_prompt_en)).strip().lower()
            if save_choice in ['yes', 'да']:
                save_name = input(game.get_text(save_prompt_ru, save_prompt_en)).strip()
                if not save_name:
                    save_name = "quicksave"
                print(game.save_game(save_name))
            break
            
        elif user_input.lower() in ['save', 'сохранить']:
            save_prompt_ru = "Введите имя сохранения (или нажмите Enter для быстрого сохранения): "
            save_prompt_en = "Enter save name (or press Enter for quicksave): "
            save_name = input(game.get_text(save_prompt_ru, save_prompt_en)).strip()
            if not save_name:
                save_name = "quicksave"
            print(game.save_game(save_name))
            continue
            
        elif user_input.lower() in ['load', 'загрузить']:
            print(game.list_saves())
            load_prompt_ru = "Введите имя сохранения для загрузки (или нажмите Enter для быстрого сохранения): "
            load_prompt_en = "Enter save name to load (or press Enter for quicksave): "
            save_name = input(game.get_text(load_prompt_ru, load_prompt_en)).strip()
            if not save_name:
                save_name = "quicksave"
            print(game.load_game(save_name))
            continue
            
        elif user_input.lower() in ['style', 'стиль']:
            game.toggle_message_style()
            continue
            
        elif user_input.lower() in ['help', 'помощь']:
            print(game.get_text(commands_ru, commands_en))
            continue
            
        elif user_input.lower() in ['fight', 'бой']:
            game.start_combat()
        else:
            game.send_message(user_input)
        
        if game.health_points <= 0:
            game_over_ru = "\nИгра окончена! Ваш персонаж погиб!"
            game_over_en = "\nGame Over! Your character has been defeated!"
            print(game.get_text(game_over_ru, game_over_en))
            break

if __name__ == "__main__":
    main()