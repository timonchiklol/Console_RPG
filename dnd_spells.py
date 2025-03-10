from random import randint

spells_1lvl = {
    "Chromatic Orb": {
        "damage": "3d8",  # 3 кубика d8
        "range": 3,
        "area_radius": 2
    },
    
    "Magic Missile": {
        "damage": "3d4",  # 3 кубика d4
        "range": 4,
        "area_radius": 0
    },
    
    "Ice Knife": {
        "damage": "1d6+2",  # 1 кубик d6 + 2
        "range": 2,
        "area_radius": 1
    },
    
    "Healing Word": {
        "healing": "1d4+3",  # 1 кубик d4 + 3
        "range": 1,
        "area_radius": 1
    },
    
    "Burning Hands": {
        "damage": "3d6",  # 3 кубика d6
        "range": 1,
        "area_radius": 1
    }
}

# Словарь с заклинаниями второго уровня
spells_2lvl = {
    "Scorching Ray": {
        "damage": "2d6",  # 2 кубика d6 для каждого луча
        "range": 5,
        "area_radius": 0,
    },

    "Dragon's Breath": {
        "damage": "3d6",  # 3 кубика d6
        "range": 3,
        "area_radius": 2,
    },

    "Misty Step": {
        "damage": "0",  # Нет урона
        "range": 100,
    },

    "Cloud of Daggers": {
        "damage": "4d4",  # 4 кубика d4
        "range": 3,
        "area_radius": 1,
    },

    "Hold Person": {
        "damage": "0",  # Нет урона
        "range": 5,
    }
}

# Добавим словарь для базовых атак
basic_attacks = {
    "Melee Attack": {
        "damage": "1d6",  # 1 кубик d6
        "range": 2,
        "area_radius": 0,
        "game_mechanics": "базовая атака ближнего боя",
        "is_spell": False  # Маркер что это не заклинание
    }
}