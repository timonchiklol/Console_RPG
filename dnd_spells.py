from random import randint

spells_1lvl = {
    "Chromatic Orb": {
        "damage": randint(0, 9),
        "range": 3,
        "area_radius": 2
    },
    
    "Magic Missile": {
        "damage": randint(3, 9),
        "range": 4,
        "area_radius": 0
    },
    
    "Ice Knife": {
        "damage": randint(1, 9),
        "range": 2,
        "area_radius": 1
    },
    
    "Healing Word": {
        "healing": randint(1, 4) + 3,
        "range": 1,
        "area_radius": 1
    },
    
    "Burning Hands": {
        "damage": randint(5, 13),
        "range": 1,
        "area_radius": 1
    }
}

# Словарь с заклинаниями второго уровня
spells_2lvl = {
    "Scorching Ray": {
        "damage": randint(1, 20),
        "range": 5,
        "area_radius": 0,
    },

    "Dragon's Breath": {
        "damage": randint(1, 12),
        "range": 3,
        "area_radius": 2,
    },

    "Misty Step": {
        "damage": 0,
        "range": 100,
    },

    "Cloud of Daggers": {
        "damage": randint(3, 16),
        "range": 3,
        "area_radius": 1,
    },

    "Hold Person": {
        "damage": 0,
        "range": 5,
    }
}

# Добавим словарь для базовых атак
basic_attacks = {
    "Melee Attack": {
        "damage": randint(1, 6),
        "range": 2,
        "area_radius": 0,
        "game_mechanics": "базовая атака ближнего боя",
        "is_spell": False  # Маркер что это не заклинание
    }
}