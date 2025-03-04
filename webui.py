from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import random
import math
from dnd_spells import spells_1lvl, spells_2lvl, basic_attacks
from gemini import Gemini
from dotenv import load_dotenv
import os
from config import BATTLEFIELD, PLAYER, ENEMIES, GAME_RULES  # Import our new config
from battlefield_configs import BATTLEFIELD_CONFIGS
from character_config import CLASS_CONFIGS
import copy

app = Flask(__name__)
app.secret_key = 'secret-key-for-session'

# Load environment variables
load_dotenv()

# Initialize Gemini AI with updated enemy configuration
gemini = Gemini(
    API_KEY=os.getenv('GEMINI_API_KEY'),
    system_instruction=f"""You are a D&D combat AI controlling a enemy.
Your goal is to make tactical decisions based on position and range.
The enemy has these attacks:
{ENEMIES['goblin']['abilities']}

Choose the best action based on:
1. Distance to player
2. Current HP
3. Tactical advantage

Respond with a JSON object containing:
{{
    "action": "move/attack",
    "target_position": {{"col": x, "row": y}},
    "attack_type": "attack_name",
    "combat_log": "Description of enemy's actions"
}}
"""
)

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
    return [(c, r) for (c, r) in neighbors if 0 <= c < BATTLEFIELD['dimensions']['cols'] and 0 <= r < BATTLEFIELD['dimensions']['rows']]

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
    
    return best_path

@app.route("/", methods=["GET", "POST"])
def character_creation():
    if request.method == "POST":
        # Get selected battlefield configuration
        battlefield_id = request.form.get('battlefield', 'forest_ambush')
        selected_config = BATTLEFIELD_CONFIGS[battlefield_id]
        
        # Get character class and use its default stats
        char_class = request.form.get('class')
        default_stats = PLAYER['stats'].copy()  # Default fallback stats
        if char_class in CLASS_CONFIGS:
            default_stats = CLASS_CONFIGS[char_class]['default_stats']
        
        # Store character info in session
        session['character'] = {
            'name': request.form.get('name'),
            'race': request.form.get('race'),
            'class': char_class,
            'stats': PLAYER['stats'].copy(),  # Copy default stats
            'hp': PLAYER['stats']['hp'],
            'max_hp': PLAYER['stats']['max_hp'],
            'speed': PLAYER['stats']['speed'],
            'movement_left': PLAYER['stats']['speed'],
            'pos': selected_config['player_start'].copy(),  # Use battlefield-specific starting position
            'spell_slots': PLAYER['spell_slots'].copy(),  # Add spell slots
            'abilities': PLAYER['abilities'].copy(),  # Add abilities
            'ability_scores': {
                'strength': default_stats['strength'],
                'dexterity': default_stats['dexterity'],
                'constitution': default_stats['constitution'],
                'intelligence': default_stats['intelligence'],
                'wisdom': default_stats['wisdom'],
                'charisma': default_stats['charisma']
            }
        }
        
        # Store enemy info
        enemy_type = 'goblin'  # You could randomize this based on battlefield
        session['enemy'] = {
            'name': ENEMIES[enemy_type]['name'],
            'hp': ENEMIES[enemy_type]['stats']['hp'],
            'max_hp': ENEMIES[enemy_type]['stats']['max_hp'],
            'speed': ENEMIES[enemy_type]['stats']['speed'],
            'movement_left': ENEMIES[enemy_type]['stats']['speed'],
            'pos': selected_config['enemy_start'].copy(),  # Use battlefield-specific starting position
            'abilities': ENEMIES[enemy_type]['abilities'].copy()
        }
        
        # Store battlefield configuration
        session['battlefield_config'] = selected_config
        session['current_terrain'] = selected_config['default_terrain']
        
        # Initialize effects
        session['effects'] = {
            'enemy': {},
            'player': {}
        }
        
        return redirect(url_for("battle"))
        
    # For GET request, render the template with battlefield configurations
    return render_template("create.html",
                         races=['Human', 'Elf', 'Dwarf', 'Orc', 'Halfling'],
                         classes=['Warrior', 'Mage', 'Ranger', 'Rogue', 'Paladin'],
                         battlefield_configs=BATTLEFIELD_CONFIGS)

@app.route("/battle", methods=["GET"])
def battle():
    if 'character' not in session:
        return redirect(url_for('character_creation'))
    
    # Use the stored battlefield configuration
    battlefield_config = session.get('battlefield_config', BATTLEFIELD_CONFIGS['forest_ambush'])
    
    # Prepare config data
    config_data = {
        'battlefield': {
            **battlefield_config,
            'terrain_types': BATTLEFIELD['terrain_types']  # Keep the terrain types from main config
        },
        'player': session['character'],
        'enemy': session['enemy'],
        'rules': GAME_RULES,
        'currentTerrain': session['current_terrain'],
        'spells': {
            'level1': spells_1lvl,
            'level2': spells_2lvl
        },
        'basicAttacks': basic_attacks
    }
    
    return render_template('battle.html', 
        character=session['character'],
        enemy=session['enemy'],
        battlefield_config=battlefield_config,
        current_terrain=session['current_terrain'],
        game_rules=GAME_RULES,
        spells_1lvl=spells_1lvl,
        spells_2lvl=spells_2lvl,
        basic_attacks=basic_attacks,
        config_data=config_data,
        lang='en'
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
    try:
        if 'character' not in session or 'enemy' not in session:
            return jsonify({"error": "No battle in progress."})
        
        character = session['character']
        enemy = session['enemy']
        
        # Get attack type from request
        attack_type = request.form.get("attack_type", "melee_attack")
        print(f"Received attack_type: {attack_type}")  # Debugging
        
        # Get the attack configuration
        attack_config = None
        
        # Try different approaches to find the attack config
        if attack_type in character.get('abilities', {}):
            attack_config = character['abilities'][attack_type]
            print(f"Found attack in character abilities: {attack_config}")
        elif attack_type in PLAYER['abilities']:
            attack_config = PLAYER['abilities'][attack_type]
            print(f"Found attack in PLAYER abilities: {attack_config}")
        else:
            # Fallback to basic melee attack
            attack_config = {
                "name": "Melee Attack",
                "damage": "1d6",
                "range": 1,
                "description": "Basic melee attack"
            }
            print(f"Using fallback attack: {attack_config}")
        
        # Auto-roll attack
        roll = random.randint(1, 20)
        if roll >= 10:  # TODO: Use proper AC calculation
            try:
                dice_count, dice_sides = map(int, attack_config['damage'].split('d'))
                damage = sum(random.randint(1, dice_sides) for _ in range(dice_count))
            except Exception as e:
                print(f"Error calculating damage: {e}")
                damage = random.randint(1, 6)  # Fallback damage
            
            enemy['hp'] -= damage
            combat_log = f"You used {attack_config['name']} and dealt {damage} damage."
        else:
            combat_log = f"Your {attack_config['name']} missed!"
        
        # Deduct speed cost
        attack_cost = GAME_RULES['combat']['attack_cost']
        character['movement_left'] -= attack_cost
        
        session['character'] = character
        session['enemy'] = enemy
        session.modified = True
        
        return jsonify({
            "combat_log": combat_log,
            "character_hp": character['hp'],
            "enemy_hp": enemy['hp'],
            "enemy_defeated": enemy['hp'] <= 0,
            "movement_left": character['movement_left']
        })
        
    except Exception as e:
        print(f"Attack error: {e}")
        return jsonify({"error": f"Attack failed: {str(e)}"})

# Обновляем функцию api_enemy_attack, добавляем обработку новых эффектов
@app.route("/api/enemy_attack", methods=["POST"])
def api_enemy_attack():
    try:
        character = session.get('character', {})
        enemy = session.get('enemy', {})
        effects = session.get('effects', {'enemy': {}, 'player': {}})
        combat_log = ""
        
        # Проверяем, что HP определены, иначе устанавливаем дефолтные значения
        if 'hp' not in character:
            character['hp'] = PLAYER['stats']['hp']
        if 'hp' not in enemy:
            enemy['hp'] = ENEMIES['goblin']['stats']['hp']
        
        # Обработка эффектов врага
        enemy_effects = effects.get('enemy', {})
        
        # Проверяем наличие эффекта паралича
        if 'paralyze' in enemy_effects:
            paralyze_effect = enemy_effects['paralyze']
            paralyze_effect['duration'] -= 1
            
            # Проверяем, не закончился ли эффект
            if paralyze_effect['duration'] <= 0:
                del enemy_effects['paralyze']
                combat_log += "Враг освободился от эффекта паралича! "
            else:
                combat_log += f"Враг парализован и не может действовать! (Осталось ходов: {paralyze_effect['duration']}) "
                
                # Сохраняем изменения и завершаем - враг пропускает ход
                session['character'] = character
                session['enemy'] = enemy
                session['effects'] = effects
                session.modified = True
                
                print("DEBUG: Враг парализован, пропускаем ход")
                return jsonify({
                    "combat_log": combat_log,
                    "character_hp": character['hp'],
                    "enemy_hp": enemy['hp'],
                    "enemy_pos": enemy['pos']
                })
        
        # Если код дошел до этого места, значит враг не парализован
        print("DEBUG: Враг не парализован, выполняем его ход")
        
        # Используем упрощенный подход к тактике ИИ
        player_pos = character['pos']
        enemy_pos = enemy['pos']
        
        # Сохраняем начальную позицию для проверки
        initial_pos = copy.deepcopy(enemy_pos)
        
        # Проверяем, есть ли атака в диапазоне
        attack_in_range = False
        best_attack = None
        
        # Получаем доступные атаки
        available_attacks = ENEMIES[enemy.get('name', 'goblin').lower()]['abilities']
        
        for attack_name, attack in available_attacks.items():
            if attack['range'] >= math.sqrt((player_pos['col'] - enemy_pos['col'])**2 + 
                                           (player_pos['row'] - enemy_pos['row'])**2):
                attack_in_range = True
                best_attack = attack
                break
        
        # Если игрок не в диапазоне атаки - двигаемся к нему
        if not attack_in_range:
            # Простое движение - уменьшаем разницу в координатах
            if player_pos['col'] > enemy_pos['col']:
                enemy_pos['col'] += 1
            elif player_pos['col'] < enemy_pos['col']:
                enemy_pos['col'] -= 1
                
            if player_pos['row'] > enemy_pos['row']:
                enemy_pos['row'] += 1
            elif player_pos['row'] < enemy_pos['row']:
                enemy_pos['row'] -= 1
                
            combat_log += "Enemy moves closer to attack! "
            
            # Проверяем, не стал ли игрок доступен для атаки после перемещения
            distance = math.sqrt((player_pos['col'] - enemy_pos['col'])**2 + 
                               (player_pos['row'] - enemy_pos['row'])**2)
            
            # Проверяем атаки снова
            for attack_name, attack in available_attacks.items():
                if attack['range'] >= distance:
                    attack_in_range = True
                    best_attack = attack
                    break
        
        # Если игрок в диапазоне атаки - атакуем
        if attack_in_range and best_attack:
            # Атака
            roll = random.randint(1, 20)
            if roll >= 10:  # TODO: Использовать правильный расчет AC
                dice_count, dice_sides = map(int, best_attack['damage'].split('d'))
                damage = sum(random.randint(1, dice_sides) for _ in range(dice_count))
                character['hp'] -= damage
                combat_log += f"Enemy uses {best_attack['name']} and deals {damage} damage! "
            else:
                combat_log += f"Enemy's {best_attack['name']} missed! "
        
        # Проверяем, изменилась ли позиция врага
        if enemy_pos != initial_pos:
            print(f"DEBUG: Враг переместился с {initial_pos} на {enemy_pos}")
        else:
            print("DEBUG: Враг не двигался")
        
        # Сохраняем изменения
        session['character'] = character
        session['enemy'] = enemy
        session['effects'] = effects
        session.modified = True
        
        return jsonify({
            "combat_log": combat_log,
            "character_hp": character['hp'],
            "enemy_hp": enemy['hp'],
            "enemy_pos": enemy['pos']
        })
        
    except Exception as e:
        print(f"Ошибка в атаке противника: {e}")
        # В случае ошибки возвращаем последние известные значения
        return jsonify({
            "error": f"Enemy attack error: {str(e)}",
            "combat_log": "Enemy is confused and does nothing.",
            "character_hp": session.get('character', {}).get('hp', PLAYER['stats']['hp']),
            "enemy_hp": session.get('enemy', {}).get('hp', ENEMIES['goblin']['stats']['hp']),
            "enemy_pos": session.get('enemy', {}).get('pos', ENEMIES['goblin']['position'])
        })

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

@app.route("/api/end_turn", methods=["POST"])
def api_end_turn():
    try:
        if 'character' not in session:
            return jsonify({"error": "No character in session"})
            
        character = session['character']
        
        # Восстанавливаем движение персонажа
        character['movement_left'] = character['speed']
        
        # Обрабатываем эффекты, которые действуют в течение хода
        effects = session.get('effects', {'player': {}, 'enemy': {}})
        player_effects = effects['player']
        
        # Уменьшаем длительность эффектов игрока
        for effect_name in list(player_effects.keys()):
            effect = player_effects[effect_name]
            effect['duration'] -= 1
            if effect['duration'] <= 0:
                del player_effects[effect_name]
        
        # Сохраняем изменения
        effects['player'] = player_effects
        session['effects'] = effects
        session['character'] = character
        session.modified = True
        
        # Вызываем атаку врага
        return api_enemy_attack()
        
    except Exception as e:
        print(f"Error in end_turn: {e}")
        return jsonify({"error": f"Failed to end turn: {str(e)}"})

# Если у вас есть отдельная функция для движения врага, добавьте в неё:
def move_enemy():
    # Получаем эффекты врага
    enemy_effects = session.get('effects', {}).get('enemy', {})
    
    # Если враг парализован, пропускаем движение
    if 'paralyze' in enemy_effects:
        return "Враг парализован и не может двигаться"
    
    # Код движения врага
    # ...

if __name__ == "__main__":
    # This web UI runs on port 5000.
    app.run(port=5000, debug=True) 