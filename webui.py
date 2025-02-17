from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import random
import math
from dnd_spells import spells_1lvl, spells_2lvl, basic_attacks
from gemini import Gemini  # Добавляем импорт Gemini
from prompts import SYSTEM_PROMPTS
from dotenv import load_dotenv
import os

app = Flask(__name__)
app.secret_key = 'secret-key-for-session'

# Загружаем переменные окружения из .env файла
load_dotenv()

# Добавим в начало файла константы для атак противника
ENEMY_ATTACKS = {
    "Bow Attack": {
        "damage": "1d6",
        "range": 4,
        "description": "shoots an arrow"
    },
    "Melee Attack": {
        "damage": "1d8",
        "range": 1,
        "description": "strikes with fists"
    }
}

# Добавим константу для скорости противника
ENEMY_SPEED = 25  # 5 клеток в ход

# Получаем API ключ из переменных окружения
gemini = Gemini(
    API_KEY=os.getenv('GEMINI_API_KEY'),
    system_instruction="""You are a D&D combat AI controlling a goblin enemy.
Your goal is to make tactical decisions based on position and range.
The goblin has two attacks:
1. Bow Attack (1d6 damage, 4 tiles range)
2. Melee Attack (1d8 damage, 1 tile range)

Choose the best action based on:
1. Distance to player
2. Current HP
3. Tactical advantage

Respond with a JSON object containing:
{
    "action": "move/bow_attack/melee_attack",
    "target_position": {"col": x, "row": y},
    "attack_type": "Bow Attack/Melee Attack",
    "combat_log": "Description of enemy's actions"
}
""")

def get_neighbors(cell):
    """Get neighboring cells. Accepts either a tuple (col, row) or a dict with col/row keys"""
    # Handle both tuple and dict formats
    if isinstance(cell, tuple):
        col, row = cell
    else:
        col, row = cell[0], cell[1]
        
    if col % 2 == 0:
        neighbors = [(col, row-1), (col, row+1), (col+1, row-1), (col+1, row), (col-1, row-1), (col-1, row)]
    else:
        neighbors = [(col, row-1), (col, row+1), (col+1, row), (col+1, row+1), (col-1, row), (col-1, row+1)]
    return [(c, r) for (c, r) in neighbors if 0 <= c < 10 and 0 <= r < 8]

def compute_path(start_col, start_row, target_col, target_row, max_steps=None):
    """Compute path from start to target using BFS, limited by max_steps"""
    queue = [(start_col, start_row, [])]
    visited = {(start_col, start_row)}
    best_path = []
    min_distance = float('inf')
    
    while queue:
        col, row, path = queue.pop(0)
        
        # Calculate distance to target
        dx = col - target_col
        dy = row - target_row
        dist = math.sqrt(dx * dx + dy * dy)
        
        # Update best path if this is closer to target
        if dist < min_distance:
            min_distance = dist
            best_path = path + [(col, row)]
        
        if max_steps is not None and len(path) >= max_steps:
            continue
            
        if (col, row) == (target_col, target_row):
            return path
            
        for next_col, next_row in get_neighbors((col, row)):
            if (next_col, next_row) not in visited and (next_col, next_row) != (target_col, target_row):
                visited.add((next_col, next_row))
                new_path = path + [(next_col, next_row)]
                queue.append((next_col, next_row, new_path))
    
    # Return the path that gets closest to target
    return best_path

# Route for character creation – collects basic DnD-like attributes.
@app.route("/", methods=["GET", "POST"])
def character_creation():
    if request.method == "POST":
        name = request.form.get("name", "Adventurer")
        strength = int(request.form.get("strength", 10))
        dexterity = int(request.form.get("dexterity", 10))
        constitution = int(request.form.get("constitution", 10))
        intelligence = int(request.form.get("intelligence", 10))
        wisdom = int(request.form.get("wisdom", 10))
        charisma = int(request.form.get("charisma", 10))
        # Save character in session
        session['character'] = {
            'name': name,
            'strength': strength,
            'dexterity': dexterity,
            'constitution': constitution,
            'intelligence': intelligence,
            'wisdom': wisdom,
            'charisma': charisma,
            'hp': constitution + 10,
            'spell_slots': 6,         # Изменили с 2 на 6
            'spells': ['Magic Missile', 'Shield'],
            'speed': 30
        }
        # Create a simple enemy for demonstration with position
        session['enemy'] = {
            'name': 'Goblin',
            'hp': 75,
            'attack': 4,
            'pos': {'col': 5, 'row': 4},
            'speed': ENEMY_SPEED,
            'movement_left': ENEMY_SPEED
        }
        return redirect(url_for("battle"))
    return render_template("create.html")

# Route for battle – shows the character and enemy status and a hexagonal battle field.
@app.route("/battle", methods=["GET"])
def battle():
    if 'character' not in session:
        return redirect(url_for('character_creation'))
    
    # Initialize enemy if not exists
    if 'enemy' not in session:
        session['enemy'] = {
            'name': 'Goblin',
            'hp': 100,
            'pos': {'col': 5, 'row': 4},
            'speed': ENEMY_SPEED,
            'movement_left': ENEMY_SPEED
        }
    
    return render_template('battle.html', 
        character=session['character'], 
        enemy=session['enemy'],
        spells_1lvl=spells_1lvl,
        spells_2lvl=spells_2lvl,
        basic_attacks=basic_attacks  # Добавляем basic_attacks
    )

# Add new roll_dice endpoint
@app.route("/api/roll_dice", methods=["POST"])
def roll_dice():
    sides = int(request.form.get("sides", 6))
    result = random.randint(1, sides)
    return jsonify({"result": result})

# Update attack endpoint to use manual dice rolls
@app.route("/api/attack", methods=["POST"])
def api_attack():
    if 'character' not in session or 'enemy' not in session:
        return jsonify({"error": "No battle in progress."})
    
    character = session['character']
    enemy = session['enemy']
    
    hit_roll = request.form.get("hit_roll")
    damage_roll = request.form.get("damage_roll")
    
    if hit_roll is not None and damage_roll is not None:
        hit_roll = int(hit_roll)
        damage_roll = int(damage_roll)
        if hit_roll >= 10:
            enemy['hp'] -= damage_roll
            combat_log = f"You attacked and dealt {damage_roll} damage."
        else:
            combat_log = "Your attack missed!"
    else:
        # fallback auto-roll if manual roll not provided
        roll = random.randint(1, 20)
        if roll >= 10:
            damage = random.randint(1, 6)
            enemy['hp'] -= damage
            combat_log = f"You attacked and dealt {damage} damage."
        else:
            combat_log = "Your attack missed!"
    
    session['character'] = character
    session['enemy'] = enemy
    return jsonify({
        "combat_log": combat_log,
        "character_hp": character['hp'],
        "enemy_hp": enemy['hp'],
        "enemy_defeated": enemy['hp'] <= 0
    })

# API endpoint to cast a spell.
@app.route("/api/cast_spell", methods=["POST"])
def api_cast_spell():
    try:
        damage = 0  # Initialize damage variable
        data = request.get_json()
        spell_name = data.get('spell_name')
        spell_data = data.get('spell_data')
        target = data.get('target', {})
        
        character = session['character']
        enemy = session['enemy']
        
        combat_log = f"{character['name']} "
        
        # Проверяем слоты только для настоящих заклинаний
        if spell_name == "Melee Attack":
            is_spell = False
        else:
            is_spell = True
            if character['spell_slots'] <= 0:
                return jsonify({"error": "No spell slots remaining!"})
        
        if spell_name == "Melee Attack":
            damage = random.randint(1, 6)  # d6 урон
            combat_log += f"attacks with melee and deals {damage} damage! "
        elif spell_name == "Chromatic Orb":
            damage = sum(random.randint(1, 8) for _ in range(3))
            combat_log += f"Orb explodes for {damage} damage in 2-tile radius! "
        
        elif spell_name == "Magic Missile":
            for _ in range(3):
                missile_damage = random.randint(1, 3)
                damage += missile_damage
                combat_log += f"Missile hits for {missile_damage} force damage! "
        
        elif spell_name == "Ice Knife":
            primary_damage = random.randint(1, 10)
            area_damage = sum(random.randint(1, 6) for _ in range(2))
            damage = primary_damage + area_damage
            combat_log += f"Ice Knife hits for {primary_damage} + {area_damage} area damage! "
        
        elif spell_name == "Healing Word":
            healing_roll = random.randint(1, 4)  # d4
            healing = healing_roll + 3  # +3 к броску
            character['hp'] += healing
            # Используем слот заклинания
            character['spell_slots'] -= 1
            # Сохраняем изменения в сессии
            session['character'] = character
            combat_log += f"Heals for {healing} HP! (Roll: {healing_roll} + 3) "
            return jsonify({
                "combat_log": combat_log,
                "character_hp": character['hp'],
                "enemy_hp": enemy['hp'],
                "enemy_defeated": enemy['hp'] <= 0,
                "spell_slots": character['spell_slots']
            })
        
        elif spell_name == "Thunderwave":
            damage = sum(random.randint(1, 5) for _ in range(2))
            combat_log += f"Thunder damages all enemies for {damage}! "
        
        elif spell_name == "Scorching Ray":
            for i in range(3):
                ray_damage = random.randint(1, 9)
                damage += ray_damage
                combat_log += f"Ray {i+1} hits for {ray_damage} fire damage! "
        
        elif spell_name == "Shatter":
            damage = random.randint(1, 15)
            combat_log += f"Shatter deals {damage} thunder damage! "
        
        elif spell_name == "Dragon's Breath":
            damage = sum(random.randint(1, 7) for _ in range(2))
            enemy['disadvantage'] = True
            combat_log += f"Dragon's Breath deals {damage} damage and applies disadvantage! "
        
        elif spell_name == "Cloud of Daggers":
            damage = sum(random.randint(1, 5) for _ in range(2))
            session['cloud_daggers'] = {
                'pos': target,
                'duration': 3,
                'damage': damage
            }
            combat_log += f"Created a cloud of daggers dealing {damage} damage! "
        
        elif spell_name == "Hold Person":
            enemy['paralyzed'] = True
            enemy['paralyzed_duration'] = 3
            combat_log += "Enemy is paralyzed and cannot move! "
        
        elif spell_name == "Misty Step":
            # Проверяем, что цель в пределах поля
            if 0 <= target['col'] < 10 and 0 <= target['row'] < 8:
                # Телепортируем игрока на выбранную позицию
                combat_log += f"teleports to position ({target['col']}, {target['row']})! "
                # Возвращаем новую позицию игрока клиенту
                return jsonify({
                    "combat_log": combat_log,
                    "character_hp": character['hp'],
                    "enemy_hp": enemy['hp'],
                    "enemy_defeated": enemy['hp'] <= 0,
                    "spell_slots": character['spell_slots'],
                    "player_pos": {
                        "col": target['col'],
                        "row": target['row']
                    }
                })
            else:
                return jsonify({"error": "Invalid target position for teleport!"})
        
        # Применяем урон если он есть
        if damage > 0:
            enemy['hp'] -= damage

        # Используем слот только для настоящих заклинаний
        if is_spell:
            character['spell_slots'] -= 1
        
        session['character'] = character
        session['enemy'] = enemy
        
        return jsonify({
            "combat_log": combat_log,
            "character_hp": character['hp'],
            "enemy_hp": enemy['hp'],
            "enemy_defeated": enemy['hp'] <= 0,
            "spell_slots": character['spell_slots']
        })
        
    except Exception as e:
        print(f"Error casting spell: {e}")
        return jsonify({"error": f"Failed to cast spell: {str(e)}"})

# Обновляем функцию api_enemy_attack
@app.route("/api/enemy_attack", methods=["POST"])
def api_enemy_attack():
    if 'character' not in session or 'enemy' not in session:
        return jsonify({"error": "No battle in progress."})
    
    character = session['character']
    enemy = session['enemy']
    
    try:
        player_col = int(request.form.get("player_col"))
        player_row = int(request.form.get("player_row"))
        
        # Сбрасываем движение в начале хода
        enemy['movement_left'] = ENEMY_SPEED
        combat_log = ""
        
        # Сначала проверяем, нужно ли двигаться для лучшей позиции
        distance = math.sqrt(
            (player_col - enemy['pos']['col'])**2 + 
            (player_row - enemy['pos']['row'])**2
        )
        
        # Если враг далеко - подходим на дистанцию лука
        if distance > ENEMY_ATTACKS["Bow Attack"]["range"]:
            steps_taken = 0
            while enemy['movement_left'] > 0 and steps_taken < 5:
                dx = player_col - enemy['pos']['col']
                dy = player_row - enemy['pos']['row']
                
                if dx == 0 and dy == 0:
                    break
                
                # Нормализуем движение
                if abs(dx) > 0:
                    dx = dx // abs(dx)
                if abs(dy) > 0:
                    dy = dy // abs(dy)
                    
                new_col = enemy['pos']['col'] + dx
                new_row = enemy['pos']['row'] + dy
                
                # Проверяем границы поля
                if 0 <= new_col < 10 and 0 <= new_row < 8:
                    enemy['pos']['col'] = new_col
                    enemy['pos']['row'] = new_row
                    enemy['movement_left'] -= 5
                    steps_taken += 1
                    
                    # Проверяем, достигли ли мы дистанции для лука
                    new_distance = math.sqrt(
                        (player_col - enemy['pos']['col'])**2 + 
                        (player_row - enemy['pos']['row'])**2
                    )
                    if new_distance <= ENEMY_ATTACKS["Bow Attack"]["range"]:
                        break
                else:
                    break
            
            if steps_taken > 0:
                combat_log += f"Goblin moves {steps_taken} tiles. "
        
        # После движения проверяем дистанцию снова для выбора атаки
        distance = math.sqrt(
            (player_col - enemy['pos']['col'])**2 + 
            (player_row - enemy['pos']['row'])**2
        )
        
        # Выбираем тип атаки на основе дистанции
        if distance <= ENEMY_ATTACKS["Melee Attack"]["range"]:
            # Ближний бой
            hit_roll = random.randint(1, 20)
            if hit_roll >= 10:
                damage_roll = random.randint(1, 8)
                character['hp'] -= damage_roll
                combat_log += f"Goblin strikes with fists and hits with {hit_roll}, dealing {damage_roll} damage!"
            else:
                combat_log += f"Goblin tries to punch but misses with {hit_roll}!"
        elif distance <= ENEMY_ATTACKS["Bow Attack"]["range"]:
            # Дальний бой
            hit_roll = random.randint(1, 20)
            if hit_roll >= 10:
                damage_roll = random.randint(1, 6)
                character['hp'] -= damage_roll
                combat_log += f"Goblin shoots an arrow and hits with {hit_roll}, dealing {damage_roll} damage!"
            else:
                combat_log += f"Goblin shoots but misses with {hit_roll}!"
        else:
            combat_log += "Goblin is too far to attack!"
        
        session['character'] = character
        session['enemy'] = enemy
        
        return jsonify({
            "combat_log": combat_log,
            "character_hp": character['hp'],
            "enemy_hp": enemy['hp'],
            "character_defeated": character['hp'] <= 0,
            "enemy_pos": enemy['pos']
        })
        
    except Exception as e:
        print(f"Error in enemy logic: {e}")
        return jsonify({"error": f"Enemy logic error: {str(e)}"})

if __name__ == "__main__":
    # This web UI runs on port 8000.
    app.run(port=5000, debug=True) 