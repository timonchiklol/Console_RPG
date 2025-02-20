spells_1lvl = {
    "Chromatic Orb": {
        "damage": "2d7",
        "range": 4,
        "area_radius": 2,
        "effect": "blind",  # Ослепление на 1 ход
        "effect_duration": 1,
        "game_mechanics": "наносит урон в радиусе 2 клетки и ослепляет цель на 1 ход"
    },
    
    "Magic Missile": {
        "damage": "3d3",
        "range": 4,
        "area_radius": 0,
        "effect": "stagger",  # Замедление на 1 ход
        "effect_duration": 1,
        "game_mechanics": "выпускает 3 пули и замедляет цель на 1 ход"
    },
    
    "Ice Knife": {
        "damage": "1d10",
        "range": 4,
        "area_radius": 1,
        "effect": "frozen",
        "effect_duration": 1,  # Уменьшили длительность заморозки до 1 хода
        "game_mechanics": "наносит урон и замораживает цель"
    },
    
    "Healing Word": {
        "healing": "1d4+3",
        "range": 0,
        "area_radius": 0,
        "game_mechanics": "восстанавливает здоровье"
    },
    
    "Burning Hands": {
        "damage": "2d7",
        "range": 0,
        "area_radius": 1,
        "effect": "burn",  # Горение 2 урона в ход
        "effect_duration": 2,
        "game_mechanics": "наносит урон и поджигает цели"
    },
    
    "Thunderwave": {
        "damage": "2d5",
        "range": 0,
        "area_radius": 2,
        "effect": "push",  # Отталкивание на 2 клетки
        "effect_duration": 1,
        "game_mechanics": "наносит урон и отталкивает цели"
    },
}

# Словарь с заклинаниями второго уровня
spells_2lvl = {
    "Scorching Ray": {
        "damage": "3d6",
        "range": 5,
        "area_radius": 0,
        "effect": "weakness",  # Уменьшение урона цели на 50%
        "effect_duration": 2,
        "game_mechanics": "выпускает 3 луча и ослабляет цель"
    },

    "Dragon's Breath": {
        "damage": "2d7",
        "range": 4,
        "area_radius": 2,
        "effect": "fear",  # Страх: цель не может приближаться к игроку
        "effect_duration": 2,
        "game_mechanics": "наносит урон и вызывает страх"
    },

    "Misty Step": {
        "damage": "0",
        "range": 0,
        "game_mechanics": "дает игроку бесконечную скорость перемещения на текущий ход."
    },

    "Cloud of Daggers": {
        "damage": "8d2",
        "range": 3,
        "area_radius": 1,
        "effect": "bleed",  # Кровотечение 3 урона в ход
        "effect_duration": 3,
        "game_mechanics": "создает зону с уроном и вызывает кровотечение"
    },

    "Hold Person": {
        "damage": "0",
        "range": 5,
        "effect": "paralyze",  # Паралич: цель не может двигаться и атаковать
        "effect_duration": 3,
        "game_mechanics": "парализует цель на 3 хода"
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