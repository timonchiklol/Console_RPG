from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import random
import math
from dnd_spells import spells_1lvl, spells_2lvl, basic_attacks
from gemini import Gemini  # Добавляем импорт Gemini
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
hp = 100
# Получаем API ключ из переменных окружения
gemini = Gemini(
    API_KEY=os.getenv('GEMINI_API_KEY'),
    system_instruction="""You are a D&D combat AI controlling a enemy.
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
            'hp': hp,
            'max_hp': hp,
            'spell_slots': {
                '1': 4,  # 4 ячейки 1-го уровня
                '2': 2   # 2 ячейки 2-го уровня
            },
            'pos': {'col': 5, 'row': 1},
            'speed': 30,
            'movement_left': 30,
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
        # Добавляем словарь для отслеживания эффектов
        session['effects'] = {
            'enemy': {},  # эффекты на враге
            'player': {}  # эффекты на игроке
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
            'hp': hp,
            'pos': {'col': 5, 'row': 4},
            'speed': ENEMY_SPEED,
            'movement_left': ENEMY_SPEED
        }
    
    # Инициализируем эффекты, если их нет
    if 'effects' not in session:
        session['effects'] = {
            'enemy': {},
            'player': {}
        }
    
    # Добавляем ability_scores в character, если их нет
    if 'ability_scores' not in session['character']:
        session['character']['ability_scores'] = {
            'strength': session['character'].get('strength', 10),
            'dexterity': session['character'].get('dexterity', 10),
            'constitution': session['character'].get('constitution', 10),
            'intelligence': session['character'].get('intelligence', 10),
            'wisdom': session['character'].get('wisdom', 10),
            'charisma': session['character'].get('charisma', 10)
        }
    
    # Добавляем переменную lang для шаблона
    return render_template('battle.html', 
        character=session['character'], 
        enemy=session['enemy'],
        spells_1lvl=spells_1lvl,
        spells_2lvl=spells_2lvl,
        basic_attacks=basic_attacks,
        lang='en'  # Добавляем язык по умолчанию
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

# Обновляем функцию api_enemy_attack, добавляем обработку новых эффектов
@app.route("/api/enemy_attack", methods=["POST"])
def api_enemy_attack():
    try:
        character = session.get('character', {})
        enemy = session.get('enemy', {})
        effects = session.get('effects', {'enemy': {}, 'player': {}})
        combat_log = ""
        
        # Проверяем эффекты на противнике
        enemy_effects = effects['enemy']
        
        # Обработка урона от эффектов
        if 'burning' in enemy_effects:
            enemy['hp'] -= 2
            combat_log += "Enemy takes 2 damage from burning! "
            
            # Проверяем, нужно ли снять эффект Hold Person
            if 'paralyze' in enemy_effects and enemy_effects['paralyze'].get('breaks_on_damage'):
                del enemy_effects['paralyze']
                combat_log += "Hold Person effect breaks from damage! "
            
        if 'bleeding' in enemy_effects:
            enemy['hp'] -= 1
            combat_log += "Enemy takes 1 damage from bleeding! "
            
            # Также проверяем Hold Person
            if 'paralyze' in enemy_effects and enemy_effects['paralyze'].get('breaks_on_damage'):
                del enemy_effects['paralyze']
                combat_log += "Hold Person effect breaks from damage! "
        
        # Если противник парализован, заморожен, испуган или оглушен
        if any(effect in enemy_effects for effect in ['paralyze', 'frozen', 'fear', 'stunned']):
            if 'fear' in enemy_effects:
                damage = random.randint(1, 8)
                enemy['hp'] -= damage
                combat_log += f"Enemy is feared and attacks itself for {damage} damage! "
            elif 'frozen' in enemy_effects:
                combat_log += "Enemy is frozen and cannot act! "
            elif 'stunned' in enemy_effects:
                combat_log += "Enemy is stunned and cannot attack! "
            else:
                combat_log += "Enemy is paralyzed and cannot move or attack! "
            
            # Уменьшаем длительность эффектов
            for effect_name in list(enemy_effects.keys()):
                effect = enemy_effects[effect_name]
                effect['duration'] -= 1
                if effect['duration'] <= 0:
                    del enemy_effects[effect_name]
                    combat_log += f"\nEnemy is no longer {effect_name}! "
            
            effects['enemy'] = enemy_effects
            session['effects'] = effects
            session['enemy'] = enemy
            session.modified = True
            
            return jsonify({
                "combat_log": combat_log,
                "character_hp": character['hp'],
                "enemy_hp": enemy['hp'],
                "enemy_pos": enemy['pos']
            })
        
        # Обычная атака если нет эффектов
        damage = random.randint(1, 8)
        character['hp'] -= damage
        combat_log += f"Enemy attacks and deals {damage} damage!"
        
        session['character'] = character
        session['effects'] = effects
        session.modified = True
        
        return jsonify({
            "combat_log": combat_log,
            "character_hp": character['hp'],
            "enemy_hp": enemy['hp'],
            "enemy_pos": enemy['pos']
        })

    except Exception as e:
        print(f"Error in enemy attack: {e}")
        return jsonify({"error": f"Enemy attack error: {str(e)}"})

# Обновляем функцию api_cast_spell для новых эффектов
@app.route("/api/cast_spell", methods=["POST"])
def api_cast_spell():
    try:
        data = request.get_json()
        spell_name = data.get('spell_name')
        target = data.get('target', {})
        
        character = session['character']
        enemy = session['enemy']
        effects = session.get('effects', {'enemy': {}, 'player': {}})
        
        combat_log = f"{character['name']} "
        
        # Специальная обработка для Melee Attack
        if spell_name == "Melee Attack":
            damage = random.randint(1, 6)  # 1d6 урона
            enemy['hp'] -= damage
            combat_log += f"performs melee attack for {damage} damage! "
            
            session['character'] = character
            session['enemy'] = enemy
            return jsonify({
                "combat_log": combat_log,
                "character_hp": character['hp'],
                "enemy_hp": enemy['hp'],
                "enemy_defeated": enemy['hp'] <= 0,
                "spell_slots": character['spell_slots']
            })

        # Определяем уровень заклинания для всех остальных заклинаний
        spell_level = None
        if spell_name in spells_1lvl:
            spell_level = '1'
        elif spell_name in spells_2lvl:
            spell_level = '2'
        
        # Проверяем наличие ячеек нужного уровня
        if spell_level and character['spell_slots'].get(spell_level, 0) <= 0:
            return jsonify({"error": f"No {spell_level}-level spell slots remaining!"})
        
        # Проверяем слоты только для настоящих заклинаний
        if spell_name in basic_attacks:
            is_spell = False
        else:
            is_spell = True
            if character['spell_slots']['1'] <= 0 and character['spell_slots']['2'] <= 0:
                return jsonify({"error": "No spell slots remaining!"})

        # Специальная обработка для каждого заклинания
        if spell_name == "Hold Person":
            effects['enemy']['paralyze'] = {
                'duration': 3,
                'source': spell_name,
                'breaks_on_damage': True  # Новый флаг для эффектов, которые спадают при уроне
            }
            combat_log += "casts Hold Person and paralyzes the enemy! "

        elif spell_name == "Ice Knife":
            damage = random.randint(1, 6)
            enemy['hp'] -= damage
            effects['enemy']['frozen'] = {'duration': 1, 'source': spell_name}
            combat_log += f"hits with Ice Knife for {damage} damage and freezes the enemy! "

        elif spell_name == "Healing Word":
            healing = random.randint(1, 4) + 2
            old_hp = character['hp']
            character['hp'] = min(character['hp'] + healing, character['max_hp'])
            actual_healing = character['hp'] - old_hp
            combat_log += f"uses Healing Word and heals for {actual_healing} HP! "

        elif spell_name == "Chromatic Orb":
            damage = random.randint(1, 8)
            enemy['hp'] -= damage
            effects['enemy']['fear'] = {'duration': 1, 'source': spell_name}
            combat_log += f"hits with Chromatic Orb for {damage} damage and frightens the enemy! "

        elif spell_name == "Magic Missile":
            damage = random.randint(1, 4) + random.randint(1, 4) + random.randint(1, 4)
            enemy['hp'] -= damage
            combat_log += f"launches Magic Missiles for {damage} damage! "

        elif spell_name == "Burning Hands":
            damage = random.randint(1, 6)
            enemy['hp'] -= damage
            effects['enemy']['burning'] = {'duration': 2, 'source': spell_name}
            combat_log += f"burns enemy for {damage} damage and sets them on fire! "

        elif spell_name == "Thunder Wave":
            damage = random.randint(1, 8)
            enemy['hp'] -= damage
            effects['enemy']['stunned'] = {'duration': 1, 'source': spell_name}
            combat_log += f"hits with Thunder Wave for {damage} damage and stuns the enemy! "

        elif spell_name == "Scorching Ray":
            total_damage = 0
            hits = []
            for i in range(3):
                if random.randint(1, 20) >= 10:  # Hit roll for each ray
                    damage = random.randint(1, 6)
                    total_damage += damage
                    hits.append(damage)
            if hits:
                enemy['hp'] -= total_damage
                combat_log += f"hits with Scorching Ray for {total_damage} damage ({', '.join(map(str, hits))})! "
            else:
                combat_log += "misses with all Scorching Rays! "

        elif spell_name == "Dragon's Breath":
            damage = random.randint(1, 10)
            enemy['hp'] -= damage
            effects['enemy']['fear'] = {'duration': 1, 'source': spell_name}
            combat_log += f"breathes fire for {damage} damage and frightens the enemy! "

        elif spell_name == "Cloud of Daggers":
            damage = random.randint(1, 6)
            enemy['hp'] -= damage
            effects['enemy']['bleeding'] = {'duration': 3, 'source': spell_name}
            combat_log += f"creates Cloud of Daggers for {damage} damage and causes bleeding! "

        # Используем слот заклинания соответствующего уровня
        if spell_level:
            character['spell_slots'][spell_level] -= 1
        
        # Сохраняем изменения
        session['character'] = character
        session['enemy'] = enemy
        session['effects'] = effects
        session.modified = True
        
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

if __name__ == "__main__":
    # This web UI runs on port 5000.
    app.run(port=5000, debug=True) 