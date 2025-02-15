spells_1lvl = {
    "Chromatic Orb": {
        "damage": "3d8",
        "range": 4,
        "area_radius": 2,
        "game_mechanics": "наносит урон в радиусе 2 клетки в каждую сторону от точки попадания."
    },
    
    "Magic Missile": {
        "damage": "3d3",
        "range": 4,
        "area_radius": 0,
        "game_mechanics": "выпускает 3 пули которые попадают с вероятностью 100%."
    },
    
    "Ice Knife": {
        "damage": "1d10",
        "range": 4,
        "area_radius": 1,
        "game_mechanics": "По выбору игрока наносит урон в радиусе 1 клетки от точки попадания."
    },
    
    "Healing Word": {
        "healing": "1d4+3",
        "range": 0,
        "game_mechanics": "лечит игрока на 1d4+3."
    },
    
    "Burning Hands": {
        "damage": "3d7",
        "range": 0,
        "area_radius": 1,
        "game_mechanics": "наносит урон в конусе 3x3 клетки."
    },
    
    "Thunderwave": {
        "damage": "2d5",
        "range": 0,
        "area_radius": 2,
        "game_mechanics": "наносит урон в радиусе 2 клетки от персонажа."
    },
    
    "Grease": {
        "range": 4,
        "game_mechanics": "Игрок выбирает квадрат 10х10, падение при провале спасброска"
    },
    
    "Shield": {
        "range": 0,
        "duration": 1,
        "bonus_ac": 5,
        "description": "Magic shield"
    }
}

# Словарь с заклинаниями второго уровня
spells_2lvl = {
    "Scorching Ray": {
        "damage": "3d9",
        "range": 5,
        "area_radius": 0,
        "game_mechanics": "выпускает 3 луча по отдельным целям."
    },

    "Shatter": {
        "damage": "1d15",
        "range": 3,
        "area_radius": 1,
        "game_mechanics": "наносит урон в радиусе 1 клетки от точки попадания."
    },

    "Dragon's Breath": {
        "damage": "2d7",
        "range": 4,
        "area_radius": 2,
        "game_mechanics": "наносит урон в конусе 5x5 клеток."
    },

    "Mirror Image": {
        "damage": "3d5",
        "range": 0,
        "game_mechanics": "создает копию персоонажа с 5 хп которая будет делать тоже самое что и персоонажа и наносить такой же урон."
    },

    "Misty Step": {
        "damage": "0",
        "range": 0,
        "game_mechanics": "дает игроку бесконечную скорость перемещения на текущий ход."
    },

    "Cloud of Daggers": {
        "damage": "2d5",
        "range": 3,
        "area_radius": 1,
        "game_mechanics": "создает зону 3x3 клетки с уроном."
    },

    "Hold Person": {
        "damage": "0",
        "range": 5,
        "game_mechanics": "не дает противнику нечего делать до тех пор пока его не ударят."
    }
}