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
        print("DEBUG: Starting enemy turn, effects:", session.get('effects', {'enemy': {}, 'player': {}}).get('enemy', {}))
        
        character = session.get('character', {})
        enemy = session.get('enemy', {})
        effects = session.get('effects', {'enemy': {}, 'player': {}})
        enemy_effects = effects.get('enemy', {})
        
        # Добавляем отладку для проверки состояния эффектов
        print(f"DEBUG: Enemy effects at start: {enemy_effects}")
        
        combat_log = ""
        
        # Обработка эффектов урона с течением времени (DOT)

        # Проверяем эффект горения
        if 'burning' in enemy_effects:
            print("DEBUG: Обрабатываем эффект горения")
            burning_effect = enemy_effects['burning']
            burning_effect['duration'] -= 1
            
            # Наносим ФИКСИРОВАННЫЙ урон от горения (2 единицы) вместо случайного
            burn_damage = 2  # Фиксированный урон вместо random.randint(1, 4)
            enemy['hp'] -= burn_damage
            combat_log += f"Враг получает {burn_damage} урона от горения! "
            
            if burning_effect['duration'] <= 0:
                combat_log += "Пламя погасло. "
                del enemy_effects['burning']
                print("DEBUG: Эффект горения закончился")
            else:
                print(f"DEBUG: Осталось {burning_effect['duration']} ходов горения")

        # Проверяем эффект кровотечения
        if 'bleeding' in enemy_effects:
            print("DEBUG: Обрабатываем эффект кровотечения")
            bleeding_effect = enemy_effects['bleeding']
            bleeding_effect['duration'] -= 1
            
            # Наносим ФИКСИРОВАННЫЙ урон от кровотечения
            bleed_damage = 1  # Фиксированный урон вместо random.randint(1, 3)
            enemy['hp'] -= bleed_damage
            combat_log += f"Враг теряет {bleed_damage} здоровья от кровотечения! "
            
            if bleeding_effect['duration'] <= 0:
                combat_log += "Кровотечение остановилось. "
                del enemy_effects['bleeding']
                print("DEBUG: Эффект кровотечения закончился")
            else:
                print(f"DEBUG: Осталось {bleeding_effect['duration']} ходов кровотечения")

        # Проверяем, не умер ли враг от эффектов
        if enemy['hp'] <= 0:
            combat_log += "Враг повержен! "
            session['character'] = character
            session['enemy'] = enemy
            session['effects'] = effects
            session.modified = True
            
            return jsonify({
                "combat_log": combat_log,
                "character_hp": character['hp'],
                "enemy_hp": 0,
                "enemy_pos": enemy['pos'],
                "enemy_defeated": True
            })
        
        # Проверяем наличие эффекта паралича
        if 'paralyze' in enemy_effects:
            print("DEBUG: Обрабатываем эффект паралича")
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
                    "enemy_pos": enemy['pos'],
                    "enemy_status": "paralyzed"  # Добавляем статус для клиента
                })

        # Проверяем наличие эффекта испуга
        elif 'fear' in enemy_effects:
            print("DEBUG: Обрабатываем эффект испуга")
            fear_effect = enemy_effects['fear']
            fear_effect['duration'] -= 1
            
            if fear_effect['duration'] <= 0:
                combat_log += "Враг преодолел свой страх! "
                del enemy_effects['fear']
            else:
                combat_log += "Враг в панике атакует сам себя! "
                
                # Враг атакует сам себя своей базовой атакой
                enemy_type = enemy.get('name', 'goblin').lower()
                basic_attack = list(ENEMIES[enemy_type]['abilities'].values())[0]
                
                # Бросок атаки
                roll = random.randint(1, 20)
                if roll >= 10:  # Упрощенный порог попадания
                    # Наносим урон
                    dice_parts = basic_attack['damage'].split('d')
                    dice_count = int(dice_parts[0])
                    dice_size = int(dice_parts[1])
                    damage = sum(random.randint(1, dice_size) for _ in range(dice_count))
                    
                    enemy['hp'] -= damage
                    combat_log += f"Враг наносит себе {damage} урона! "
                else:
                    combat_log += "Но промахивается! "
                
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
        
        # Проверяем наличие эффекта заморозки
        elif 'frozen' in enemy_effects:
            print("DEBUG: Обрабатываем эффект заморозки")
            frozen_effect = enemy_effects['frozen']
            frozen_effect['duration'] -= 1
            
            if frozen_effect['duration'] <= 0:
                combat_log += "Враг оттаивает! "
                del enemy_effects['frozen']
            else:
                combat_log += "Враг заморожен и не может двигаться или атаковать! "
                
                # Сохраняем изменения и завершаем ход
                session['character'] = character
                session['enemy'] = enemy
                session['effects'] = effects
                session.modified = True
                
                print("DEBUG: Враг заморожен, пропускаем ход полностью")
                return jsonify({
                    "combat_log": combat_log,
                    "character_hp": character['hp'],
                    "enemy_hp": enemy['hp'],
                    "enemy_pos": enemy['pos'],
                    "enemy_status": "frozen"  # Добавляем статус для клиента
                })
        
        # Если код дошел до этого места, значит враг не парализован и не испуган
        print("DEBUG: Враг не парализован и не испуган, выполняем его ход")
        
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
            "enemy_pos": enemy['pos'],
            "enemy_status": "frozen" if 'frozen' in enemy_effects else None
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

# Общая функция для нанесения урона от заклинаний
def apply_spell_damage(spell_name, spell_dict):
    """Извлекает формулу урона из словаря заклинаний и рассчитывает урон"""
    damage_formula = None
    
    # Определяем, из какого словаря брать информацию
    if spell_name in spells_1lvl:
        damage_formula = spells_1lvl[spell_name].get("damage")
    elif spell_name in spells_2lvl:
        damage_formula = spells_2lvl[spell_name].get("damage")
    elif spell_name in basic_attacks:
        damage_formula = basic_attacks[spell_name].get("damage")
    
    # Если формула определена, рассчитываем урон
    if damage_formula:
        return calculate_damage(damage_formula)
    
    # Если формула не найдена, возвращаем базовый урон
    return random.randint(1, 6)  # Базовый урон по умолчанию

# Добавим функцию для проверки расстояния
def get_distance(pos1, pos2):
    """Упрощенное вычисление расстояния"""
    col1, row1 = pos1['col'], pos1['row']
    col2, row2 = pos2['col'], pos2['row']
    
    # Евклидово расстояние, деленное на 2 для приближения к игровой механике
    dx = col1 - col2
    dy = row1 - row2
    return math.ceil(math.sqrt(dx * dx + dy * dy) / 2)

def get_hex_neighbors(col, row):
    """Возвращает соседние клетки для гексагональной сетки"""
    neighbors = []
    
    # Смещения зависят от четности столбца
    if col % 2 == 0:  # Четный столбец
        directions = [
            (0, -1),  # вверх
            (1, -1),  # вверх-вправо
            (1, 0),   # вправо
            (0, 1),   # вниз
            (-1, 0),  # влево
            (-1, -1)  # вверх-влево
        ]
    else:  # Нечетный столбец
        directions = [
            (0, -1),  # вверх
            (1, 0),   # вверх-вправо
            (1, 1),   # вправо
            (0, 1),   # вниз
            (-1, 1),  # влево
            (-1, 0)   # вверх-влево
        ]
    
    # Добавляем всех соседей
    for dc, dr in directions:
        next_col, next_row = col + dc, row + dr
        
        # Проверяем границы сетки (можно настроить под ваш размер)
        if 0 <= next_col < 20 and 0 <= next_row < 20:
            neighbors.append((next_col, next_row))
    
    return neighbors

@app.route("/api/cast_spell", methods=["POST"])
def api_cast_spell():
    try:
        data = request.get_json()
        spell_name = data.get('spell_name')
        target = data.get('target')
        
        character = session.get('character', {})
        enemy = session.get('enemy', {})
        effects = session.get('effects', {'enemy': {}, 'player': {}})
        
        combat_log = f"{character.get('name', 'Character')} "
        
        # Специальная обработка для Melee Attack
        if spell_name == "Melee Attack":
            damage = apply_spell_damage(spell_name, basic_attacks)
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
        spell_range = 0
        
        if spell_name in spells_1lvl:
            spell_level = '1'
            spell_range = spells_1lvl[spell_name].get('range', 0)
        elif spell_name in spells_2lvl:
            spell_level = '2'
            spell_range = spells_2lvl[spell_name].get('range', 0)
        
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

        # Проверяем, находится ли противник в радиусе действия заклинания
        # За исключением заклинаний с самонаведением или тех, что не требуют проверки расстояния
        distance_check_required = True
        
        # Список заклинаний, которые не требуют проверки расстояния (самолечение и т.д.)
        distance_exceptions = ["Healing Word", "Misty Step"]
        
        if spell_name in distance_exceptions:
            distance_check_required = False
        
        if distance_check_required:
            # Сохраняем старое расстояние для сравнения
            old_method = math.sqrt((character['pos']['col'] - enemy['pos']['col'])**2 + 
                                  (character['pos']['row'] - enemy['pos']['row'])**2)
            # Новый метод
            distance = get_distance(character['pos'], enemy['pos'])
            
            print(f"DEBUG: Spell: {spell_name}, Range: {spell_range}")
            print(f"DEBUG: Player at {character['pos']}, Enemy at {enemy['pos']}")
            print(f"DEBUG: New distance calc: {distance}, Old Euclidean/2: {old_method/2}")
            
            if distance > spell_range:
                # Если враг вне радиуса действия, регистрируем промах
                # Все равно расходуем слот заклинания
                if spell_level:
                    character['spell_slots'][spell_level] -= 1
                
                combat_log += f"пытается применить {spell_name}, но противник вне радиуса действия ({math.ceil(distance)} > {spell_range})."
                
                session['character'] = character
                session.modified = True
                
                return jsonify({
                    "combat_log": combat_log,
                    "character_hp": character['hp'],
                    "enemy_hp": enemy['hp'],
                    "enemy_defeated": False,
                    "spell_slots": character['spell_slots'],
                    "spell_missed": True
                })

        # Специальная обработка для каждого заклинания
        if spell_name == "Hold Person":
            effects['enemy']['paralyze'] = {
                'duration': 3,
                'source': spell_name,
                'breaks_on_damage': True
            }
            combat_log += "casts Hold Person and paralyzes the enemy! "

        elif spell_name == "Ice Knife":
            damage = apply_spell_damage(spell_name, spells_1lvl)
            enemy['hp'] -= damage
            effects['enemy']['frozen'] = {'duration': 2, 'source': spell_name}
            combat_log += f"hits with Ice Knife for {damage} damage and freezes the enemy! "

        elif spell_name == "Healing Word":
            healing_formula = spells_1lvl[spell_name].get("healing")
            healing = calculate_damage(healing_formula)
            old_hp = character['hp']
            character['hp'] = min(character['hp'] + healing, character['max_hp'])
            actual_healing = character['hp'] - old_hp
            combat_log += f"uses Healing Word and heals for {actual_healing} HP! "

        elif spell_name == "Chromatic Orb":
            damage = apply_spell_damage(spell_name, spells_1lvl)
            enemy['hp'] = max(0, enemy['hp'] - damage)
            
            # Добавляем эффект испуга с увеличенной продолжительностью
            effects['enemy']['fear'] = {
                'duration': 2,
                'source': 'Chromatic Orb'
            }
            
            combat_log += f"hits with Chromatic Orb for {damage} damage! The enemy is frightened!"

        elif spell_name == "Magic Missile":
            damage = apply_spell_damage(spell_name, spells_1lvl)
            enemy['hp'] -= damage
            combat_log += f"launches Magic Missiles for {damage} damage! "

        elif spell_name == "Burning Hands":
            damage = apply_spell_damage(spell_name, spells_1lvl)
            enemy['hp'] -= damage
            
            # Уточняем эффект горения - 3 хода по 2 урона
            effects['enemy']['burning'] = {
                'duration': 3, 
                'source': spell_name,
                'damage_per_turn': 2  # Для ясности добавляем параметр урона
            }
            
            combat_log += f"burns enemy for {damage} damage and sets them on fire! "

        elif spell_name == "Scorching Ray":
            total_damage = 0
            hits = []
            for i in range(3):
                if random.randint(1, 20) >= 10:  # Hit roll for each ray
                    damage = apply_spell_damage("Scorching Ray", spells_2lvl)
                    total_damage += damage
                    hits.append(damage)
            if hits:
                enemy['hp'] -= total_damage
                combat_log += f"hits with Scorching Ray for {total_damage} damage ({', '.join(map(str, hits))})! "
            else:
                combat_log += "misses with all Scorching Rays! "

        elif spell_name == "Dragon's Breath":
            damage = apply_spell_damage("Dragon's Breath", spells_2lvl)
            enemy['hp'] = max(0, enemy['hp'] - damage)
            
            # Добавляем эффект испуга
            effects['enemy']['fear'] = {
                'duration': 2,
                'source': 'Dragon\'s Breath'
            }
            
            combat_log = f"{character.get('name', 'Character')} uses Dragon's Breath for {damage} damage! The enemy is frightened!"

        elif spell_name == "Cloud of Daggers":
            damage = apply_spell_damage("Cloud of Daggers", spells_2lvl)
            enemy['hp'] -= damage
            effects['enemy']['bleeding'] = {
                'duration': 3, 
                'source': spell_name,
                'damage_per_turn': 1
            }
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
        print(f"Error in cast_spell: {e}")
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

def calculate_damage(damage_formula):
    """Рассчитывает урон на основе строковой формулы типа 'XdY+Z'"""
    try:
        if not damage_formula or isinstance(damage_formula, (int, float)):
            return damage_formula
            
        # Обрабатываем простые случаи фиксированного урона
        if isinstance(damage_formula, (int, float)):
            return damage_formula
            
        # Разделяем на части для кубиков и модификаторов
        if '+' in damage_formula:
            dice_part, mod_part = damage_formula.split('+')
            modifier = int(mod_part.strip())
        elif '-' in damage_formula:
            dice_part, mod_part = damage_formula.split('-')
            modifier = -int(mod_part.strip())
        else:
            dice_part = damage_formula
            modifier = 0
            
        # Обрабатываем кубики
        if 'd' in dice_part:
            count, sides = dice_part.lower().split('d')
            count = int(count.strip()) if count.strip() else 1
            sides = int(sides.strip())
            
            # Бросаем кубики
            total = sum(random.randint(1, sides) for _ in range(count))
            return total + modifier
        else:
            # Если нет кубиков, просто возвращаем число
            return int(dice_part) + modifier
    except Exception as e:
        print(f"Error calculating damage from formula {damage_formula}: {e}")
        return random.randint(1, 6)  # Аварийное значение

if __name__ == "__main__":
    # This web UI runs on port 5000 and is accessible from other devices
    app.run(host='0.0.0.0', port=5000, debug=True)