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
            'hp': 100,  # начальное значение HP
            'max_hp': 100,  # добавляем max_hp
            'spell_slots': 100,
            'pos': {'col': 5, 'row': 1},
            'speed': 30,
            'movement_left': 30,
            'spells': ['Magic Missile', 'Shield'],
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
            'hp': 100,
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

# API endpoint to cast a spell.
@app.route("/api/cast_spell", methods=["POST"])
def api_cast_spell():
    try:
        damage = 0
        data = request.get_json()
        spell_name = data.get('spell_name')
        spell_data = data.get('spell_data')
        target = data.get('target', {})
        
        character = session['character']
        enemy = session['enemy']
        effects = session.get('effects', {'enemy': {}, 'player': {}})
        
        combat_log = f"{character['name']} "
        
        # Проверяем слоты только для настоящих заклинаний
        if spell_name in basic_attacks:
            is_spell = False
        else:
            is_spell = True
            if character['spell_slots'] <= 0:
                return jsonify({"error": "No spell slots remaining!"})
        
        # Специальная обработка для Healing Word
        if spell_name == "Healing Word":
            # Если max_hp не установлен, устанавливаем его равным начальному HP
            if 'max_hp' not in character:
                character['max_hp'] = 100  # или другое начальное значение HP
            
            # Парсим формулу лечения (1d4+3)
            healing_formula = spells_1lvl["Healing Word"]["healing"]
            dice_part, modifier = healing_formula.split('+')
            num_dice, dice_size = map(int, dice_part.split('d'))
            
            # Вычисляем количество лечения
            healing = sum(random.randint(1, dice_size) for _ in range(num_dice)) + int(modifier)
            
            # Применяем лечение
            old_hp = character['hp']
            character['hp'] = min(character['hp'] + healing, character['max_hp'])
            actual_healing = character['hp'] - old_hp
            
            combat_log += f"uses Healing Word and heals for {actual_healing} HP! "
            
            # Используем слот заклинания
            character['spell_slots'] -= 1
            
            session['character'] = character
            return jsonify({
                "combat_log": combat_log,
                "character_hp": character['hp'],
                "enemy_hp": enemy['hp'],
                "spell_slots": character['spell_slots']
            })
        
        # Получаем данные заклинания
        spell_info = None
        if spell_name in spells_1lvl:
            spell_info = spells_1lvl[spell_name]
        elif spell_name in spells_2lvl:
            spell_info = spells_2lvl[spell_name]
        elif spell_name in basic_attacks:
            spell_info = basic_attacks[spell_name]
        
        if not spell_info:
            return jsonify({"error": "Invalid spell!"})
        
        # Обработка урона, только если у заклинания есть урон
        if "damage" in spell_info and spell_info["damage"] != "0":
            damage_dice = spell_info["damage"].split('d')
            num_dice = int(damage_dice[0])
            dice_size = int(damage_dice[1])
            damage = sum(random.randint(1, dice_size) for _ in range(num_dice))
            combat_log += f"deals {damage} damage! "
        
        # Обработка эффектов
        if "effect" in spell_info:
            effect_name = spell_info["effect"]
            effect_duration = spell_info.get("effect_duration", 1)
            
            # Специальная обработка для определенных эффектов
            if effect_name == "paralyze" or effect_name == "hold_person":
                effect_duration = 3
            
            effects['enemy'][effect_name] = {
                'duration': effect_duration,
                'source': spell_name
            }
            combat_log += f"Enemy is affected by {effect_name}! "
        
        # Применяем урон
        if damage > 0:
            enemy['hp'] -= damage
        
        # Используем слот заклинания если это не базовая атака
        if is_spell:
            character['spell_slots'] -= 1
        
        session['character'] = character
        session['enemy'] = enemy
        session['effects'] = effects
        
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
    
    character = session.get('character')
    enemy = session.get('enemy')
    effects = session.get('effects', {'enemy': {}, 'player': {}})
    
    try:
        player_col = int(request.form.get("player_col"))
        player_row = int(request.form.get("player_row"))
        
        # Сбрасываем движение в начале хода
        enemy['movement_left'] = ENEMY_SPEED
        combat_log = ""

        # Создаем новый словарь для обновленных эффектов
        updated_effects = {}
        
        # Проверяем эффекты контроля сначала
        if any(effect in effects['enemy'] for effect in ['paralyze', 'hold_person', 'frozen']):
            effect_name = next(effect for effect in ['paralyze', 'hold_person', 'frozen'] 
                             if effect in effects['enemy'])
            data = effects['enemy'][effect_name].copy()
            
            # Пропускаем ход из-за эффекта
            combat_log = f"Enemy is {effect_name} and skips their turn! "
            
            # Уменьшаем длительность после пропуска хода
            data['duration'] = data['duration'] - 1
            
            if data['duration'] > 0:
                updated_effects[effect_name] = data
                combat_log += f"({data['duration']} turns remaining)"
            else:
                combat_log += f"Effect {effect_name} will wear off next turn!"
            
            # Обновляем эффекты в сессии
            effects['enemy'] = updated_effects
            session['effects'] = effects
            session.modified = True
            
            return jsonify({
                "combat_log": combat_log,
                "character_hp": character['hp'],
                "enemy_hp": enemy['hp'],
                "enemy_pos": enemy['pos']
            })
        
        # Обрабатываем другие эффекты
        for effect_name, data in effects['enemy'].items():
            if effect_name not in ['paralyze', 'hold_person', 'frozen']:
                data = data.copy()
                data['duration'] = data['duration'] - 1
                
                if effect_name == 'burn':
                    enemy['hp'] -= 2
                    combat_log += "Enemy takes 2 burning damage! "
                elif effect_name == 'bleed':
                    enemy['hp'] -= 3
                    combat_log += "Enemy takes 3 bleeding damage! "
                elif effect_name == 'fear':
                    # Логика убегания от игрока
                    dx = enemy['pos']['col'] - player_col
                    dy = enemy['pos']['row'] - player_row
                    
                    # Определяем направление движения (от игрока)
                    if abs(dx) >= abs(dy):
                        # Двигаемся по горизонтали
                        if dx > 0:
                            new_col = min(9, enemy['pos']['col'] + 1)
                            new_row = enemy['pos']['row']
                        else:
                            new_col = max(0, enemy['pos']['col'] - 1)
                            new_row = enemy['pos']['row']
                    else:
                        # Двигаемся по вертикали
                        if dy > 0:
                            new_col = enemy['pos']['col']
                            new_row = min(7, enemy['pos']['row'] + 1)
                        else:
                            new_col = enemy['pos']['col']
                            new_row = max(0, enemy['pos']['row'] - 1)
                    
                    # Применяем движение
                    enemy['pos']['col'] = new_col
                    enemy['pos']['row'] = new_row
                    combat_log += "Enemy flees in fear! "
                
                if data['duration'] > 0:
                    updated_effects[effect_name] = data
                else:
                    combat_log += f"Effect {effect_name} has worn off! "
        
        # Обновляем сессию с новыми эффектами
        effects['enemy'] = updated_effects
        session['effects'] = effects
        session['enemy'] = enemy
        session.modified = True
        
        # Если нет эффектов контроля, продолжаем с обычной логикой боя
        if not any(effect in ['paralyze', 'hold_person', 'frozen'] for effect in updated_effects):
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
            
            # Проверяем эффект weakness для уменьшения урона
            damage_multiplier = 0.5 if 'weakness' in effects['enemy'] else 1.0
            
            # Выбираем тип атаки на основе дистанции
            if distance <= ENEMY_ATTACKS["Melee Attack"]["range"]:
                # Ближний бой
                hit_roll = random.randint(1, 20)
                if hit_roll >= 10:
                    damage_roll = int(random.randint(1, 8) * damage_multiplier)
                    character['hp'] -= damage_roll
                    combat_log += f"Goblin strikes with fists and hits with {hit_roll}, dealing {damage_roll} damage!"
                else:
                    combat_log += f"Goblin tries to punch but misses with {hit_roll}!"
            elif distance <= ENEMY_ATTACKS["Bow Attack"]["range"]:
                # Дальний бой
                hit_roll = random.randint(1, 20)
                if hit_roll >= 10:
                    damage_roll = int(random.randint(1, 6) * damage_multiplier)
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
    # This web UI runs on port 5000.
    app.run(port=5000, debug=True) 