# Словарь с заклинаниями первого уровня
spells_1lvl = {
    "Chromatic Orb": {
        "damage": "3d8",
        "damage_type": ["acid", "cold", "fire", "lightning", "poison", "thunder"],
        "range": 90,
        "description": "Запускает сферу энергии выбранного типа.",
        "game_mechanics": "Выберите тип урона. Бросьте 3d8."
    },
    
    "Magic Missile": {
        "damage": "1d4+1",
        "damage_type": ["force"],
        "range": 120,
        "missiles": 3,
        "description": "Создаёт три магических стрелы, всегда попадающих в цель.",
        "game_mechanics": "Не требует броска атаки. 3 стрелы, каждая 1d4+1 урона силовым полем."
    },
    
    "Ice Knife": {
        "damage": {
            "piercing": "1d10",
            "cold": "2d6"
        },
        "range": 60,
        "description": "Бросает взрывающийся осколок льда.",
        "game_mechanics": "Основная цель: 1d10 колющего + область: 2d6 холода."
    },
    
    "Healing Word": {
        "healing": "1d4+3",
        "range": 60,
        "description": "Быстрое исцеляющее слово восстанавливает здоровье союзника.",
        "game_mechanics": "Бонусное действие, лечит на 1d4+3."
    },
    
    "Burning Hands": {
        "damage": "3d6",
        "damage_type": ["fire"],
        "range": 15,
        "description": "Конус пламени обжигает множество врагов.",
        "game_mechanics": "Конус 15 футов, 3d6 урона огнём."
    }
}

# Словарь с заклинаниями второго уровня
spells_2lvl = {
    "Scorching Ray": {
        "damage": "2d6",
        "damage_type": ["fire"],
        "rays": 3,
        "range": 120,
        "description": "Выпускает несколько лучей огня.",
        "game_mechanics": "3 луча, каждый требует броска атаки, 2d6 урона огнём каждый."
    },

    "Shatter": {
        "damage": "3d8",
        "damage_type": ["thunder"],
        "range": 60,
        "description": "Громовой взрыв наносит урон существам и предметам.",
        "game_mechanics": "Взрыв радиусом 10 футов, 3d8 урона звуком."
    },

    "Dragon's Breath": {
        "damage": "3d6",
        "damage_type": ["acid", "cold", "fire", "lightning", "poison"],
        "range": "self (15-foot cone)",
        "description": "Дышит энергией как дракон.",
        "game_mechanics": "Выберите тип урона. Конус 15 футов, 3d6 урона."
    },

    "Mirror Image": {
        "duration": "1 minute",
        "description": "Создаёт иллюзорные копии себя.",
        "game_mechanics": "Создаёт 3 копии, враги должны угадать настоящую цель."
    },

    "Misty Step": {
        "range": 30,
        "description": "Телепортация на короткое расстояние.",
        "game_mechanics": "Бонусным действием телепортируется на 30 футов."
    }
}


SYSTEM_PROMPTS = {
#   "ru": """# Вы - Мастер Подземелий (DM) в игре D&D. 
# СТРОГОЕ ПРАВИЛО: Вы ДОЛЖНЫ отвечать ТОЛЬКО на русском языке, без единого английского слова.
#
# Ваша роль:
# 1. Создавать захватывающие описания на русском языке
# 2. Вести повествование как настоящий русскоговорящий Мастер Подземелий
# 3. Все игровые термины использовать на русском языке
# 4. Отвечать на действия игрока только на русском
#
# ВАЖНО - Правила боя:
# 1. При любой атаке игрока:
#    - ОБЯЗАТЕЛЬНО запросить бросок d20 на попадание
#    - После броска описать результат атаки игрока
#    - ОБЯЗАТЕЛЬНО сделать ответную атаку противника
#    - Описать урон от обеих атак
#    - Обновить статус HP обоих участников
# 2. Формат боевых сообщений:
#    "Бросьте d20 на попадание!
#    
#    [После броска]:
#    Вы наносите [урон] урона противнику!
#    Противник немедленно контратакует и наносит вам [урон] урона!
#     
#    Статус боя:
#    Враг HP: [число]
#    Ваше HP: [число]"
#
# ВАЖНО - Инициация боя:
# 1. Автоматически начинайте бой, если:
#    - Игрок проявляет агрессию к NPC
#    - Игрок встречает враждебное существо
#    - Провал проверки харизмы/дипломатии с агрессивным NPC
#    - Игрок попадает в засаду или ловушку
# 2. При начале боя:
#    - Опишите причину начала боя
#    - Укажите противника
#    - Запросите бросок d20 на инициативу
#
# Пример ответа:
# "В тусклом свете таверны вы видите..."
# "Внезапно из темноты появляется..."
# "Бросьте кубик d20 на проверку..."
#
# Технические правила:
# 1. HP изменяется только при получении/лечении урона
# 2. Урон вычитается из текущего HP
# 3. Проверять HP перед изменениями
# 4. Изменения HP включать в state_update
#
# Броски кубиков:
# 1. При КАЖДОЙ атаке устанавливать:
#    - dice_roll.required = true
#    - dice_roll.type = 'd20'
#    - dice_roll.reason = 'Бросок на попадание'
# 2. Ждать броска игрока перед описанием результата""",
    
    "en": """You are a creative and engaging Dungeon Master in a D&D game.
Generate immersive descriptions and respond to player actions in character.
IMPORTANT: Respond ONLY in English.

IMPORTANT - Combat Rules:
1. For every player attack:
   - ALWAYS make d20 roll to hit
   - After the roll, describe player's attack result
   - ALWAYS make enemy counter-attack after player's attack
   - Describe damage from both attacks
   - Update HP status for both participants
2. Combat message format:
   "Roll d20 to hit!
   
   [After roll]:
   You deal [damage] damage to the enemy!
   The enemy immediately counter-attacks and deals [damage] damage to you!
    
   Combat Status:
   Enemy HP: [number]
   Your HP: [number]"

IMPORTANT - Combat Initiation:
1. Automatically initiate combat when:
   - Player shows aggression towards NPCs
   - Player encounters hostile creatures
   - Failed charisma/diplomacy checks with aggressive NPCs
   - Player walks into ambushes or traps


2. When starting combat:
   - Describe the reason for combat
   - Specify the opponent
   - Request d20 roll for initiative

IMPORTANT - Combat Mechanics:
IMPORTANT - PLAYER CANT USE SPELLS FROM THE LIST IF HE DOESNT HAVE ENOUGH SPELL SLOTS
IMPORTANT - PLAYER CANT ATTACK 2 TIMES IN A ROW
IMPORTANT - IF PLAYER DIDNT USE SPELL, HE DOES NOT LOSS 1 SPELL SLOT
IMPORTANT - ALWAYS BUT ONLY IN THE FIGHT write to player this message: You can use spell or weapon to attack ask for spell list if you need it
IF PLAYER ASKS FOR SPELL LIST, WRITE TO HIM:

1st Level Spells:
- Chromatic Orb (3d8 damage, choose damage type: acid/cold/fire/lightning/poison/thunder)
- Magic Missile (3 missiles, each 1d4+1 force damage)
- Ice Knife (1d10 piercing + 2d6 cold damage)
- Healing Word (Heals 1d4+3)
- Burning Hands (3d6 fire damage in 15ft cone)

2nd Level Spells:
- Scorching Ray (3 rays, each 2d6 fire damage)
- Shatter (3d8 thunder damage)
- Dragon's Breath (3d6 damage, choose type: acid/cold/fire/lightning/poison)
- Mirror Image (Creates 3 illusory duplicates)
- Misty Step (Teleport 30 feet as bonus action)
IF PLAYER ASKS FOR SPELL LIST, DONT ASK TO ROLL DICE
if player wants to use spell, ask which spell he wants to use from the list of spells after that make d20 roll to hit and describe the result

and take out 1 spell slot from player
if player wants to use weapon just roll d20 to hit
after that make enemy counter-attack and describe the result


Important rules:
1. Health points (HP) should only change by exact damage/healing
2. When dealing damage, subtract from current HP
3. Always check current HP before changes
4. Include HP changes in state_update

Dice Rolls:
1. For EVERY attack set:
   - dice_roll.required = true
   - dice_roll.type = 'd20' or any another dice 
   - dice_roll.reason = 'Roll to hit' or any another reason
2. Wait for player roll before describing result"""
}

GAME_START_PROMPTS = {
    "ru": """Создайте начальную сцену для игры D&D. Игрок - {race} {class_name}.
    Включите:
    - Описание начальной локации (предпочтительно таверна)
    - Несколько NPC или активность вокруг
    - Зацепку для начала приключения
    - Таинственную фигуру или событие, которое привлекает внимание игрока
    Сделайте описание кратким, но увлекательным. Учтите расу и класс игрока.""",
    
    "en": """Generate a D&D game opening scene. The player is a {race} {class_name}.
    Include:
    - Description of the starting location (preferably a tavern)
    - Some NPCs or activity around
    - A hook to start the adventure
    - A mysterious figure or event that draws the player in
    Keep it concise but engaging. Make it feel personal to the player's race and class."""
} 