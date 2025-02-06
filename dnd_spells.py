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

