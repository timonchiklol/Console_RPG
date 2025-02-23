spells_1lvl = {
    "Chromatic Orb": {
        "damage": "2d4",
        "range": 4,
        "area_radius": 2
    },
    
    "Magic Missile": {
        "damage": "d3",
        "range": 6,
        "area_radius": 0
    },
    
    "Ice Knife": {
        "damage": "1d8",
        "range": 4,
        "area_radius": 1
    },
    
    "Healing Word": {
        "healing": "1d4+3",
        "range": 1,
        "area_radius": 1
    },
    
    "Burning Hands": {
        "damage": "3d4",
        "range": 0,
        "area_radius": 1
    },
    
    "Thunderwave": {
        "damage": "2d4",
        "range": 100,
        "area_radius": 100
    }
}

# Словарь с заклинаниями второго уровня
spells_2lvl = {
    "Scorching Ray": {
        "damage": "3d6",
        "range": 5,
        "area_radius": 0,
    },

    "Dragon's Breath": {
        "damage": "2d6",
        "range": 6,
        "area_radius": 2,
    },

    "Misty Step": {
        "damage": "0",
        "range": 100,
    },

    "Cloud of Daggers": {
        "damage": "6d2",
        "range": 3,
        "area_radius": 1,
    },

    "Hold Person": {
        "damage": "0",
        "range": 5,
    }
}

# Добавим словарь для базовых атак
basic_attacks = {
    "Melee Attack": {
        "damage": "1d6",
        "range": 1,
        "area_radius": 0,
        "game_mechanics": "базовая атака ближнего боя",
        "is_spell": False  # Маркер что это не заклинание
    }
}