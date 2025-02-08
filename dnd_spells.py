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
        "range": 6,
        "missiles": 3,
        "description": "Three magical darts"
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
        "range": 2,
        "area_type": "cone",
        "description": "Fire cone"
    },
    
    "Thunderwave": {
        "damage": "2d8",
        "range": 1,
        "push": 2,
        "description": "Thunder blast"
    },
    
    "Grease": {
        "range": 60,
        "description": "Покрывает область скользким жиром",
        "game_mechanics": "Квадрат 10х10, падение при провале спасброска",
        "area_type": "square",
        "area_size": 10,
        "duration": "1 minute",
        "save_type": "dexterity",
        "terrain_effect": "difficult_terrain"
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
        "damage": "2d6",
        "range": 4,
        "rays": 3,
        "description": "Fire rays"
    },

    "Shatter": {
        "damage": "3d8",
        "range": 3,
        "area": 2,
        "description": "Sound explosion"
    },

    "Dragon's Breath": {
        "damage": "3d6",
        "range": 2,
        "area_type": "cone",
        "description": "Dragon breath"
    },

    "Mirror Image": {
        "duration": "1 minute",
        "description": "Создаёт иллюзорные копии себя.",
        "game_mechanics": "Создаёт 3 копии, враги должны угадать настоящую цель.",
        "range": 0
    },

    "Misty Step": {
        "range": 6,
        "type": "teleport",
        "description": "Teleport"
    },

    "Cloud of Daggers": {
        "damage": "4d4",
        "damage_type": ["slashing"],
        "range": 60,
        "description": "Создает облако вращающихся кинжалов",
        "game_mechanics": "Куб 5х5, урон при входе и в начале хода",
        "area_type": "cube",
        "area_size": 5,
        "duration": "1 minute",
        "concentration": True
    },

    "Hold Person": {
        "range": 60,
        "description": "Парализует гуманоида",
        "game_mechanics": "Цель парализована при провале спасброска",
        "save_type": "wisdom",
        "duration": "1 minute",
        "concentration": True,
        "condition": "paralyzed",
        "target_type": "humanoid"
    }
}