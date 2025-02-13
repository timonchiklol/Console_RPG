from flask import Flask, render_template, request, jsonify, session, Response, send_from_directory
from DEF import DnDGame
from character_config import (RACE_STATS, CLASS_BONUSES, RACE_TRANSLATIONS, CLASS_TRANSLATIONS,
                            RACE_CONFIGS, CLASS_CONFIGS)
from room_manager import RoomManager
import os
import json
import uuid
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime
from threading import Lock
from gemini_schema import PlayerState
from pydantic import Extra

# Monkey-patch DnDGame to update system prompt for Gemini
_original_init = DnDGame.__init__
def _patched_init(self, *args, **kwargs):
    _original_init(self, *args, **kwargs)
    if hasattr(self, "system_prompt") and "Do not change player's HP" not in self.system_prompt:
         self.system_prompt += "\nNote: Do not change player's HP unless necessary due to explicit combat events. Only update HP when it is clearly altered by combat damage or healing."
DnDGame.__init__ = _patched_init

# Create a custom filter to exclude get_room_state messages
class GetRoomStateFilter(logging.Filter):
    def filter(self, record):
        return "GET /get_room_state" not in record.getMessage()

# Configure logging
def setup_logging():
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create file handler with daily rotation
    log_file = logs_dir / "game.log"
    file_handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=30  # Keep 30 days of logs
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(detailed_formatter)
    file_handler.addFilter(GetRoomStateFilter())
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(detailed_formatter)
    console_handler.addFilter(GetRoomStateFilter())
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Remove any existing handlers
    root_logger.handlers = []
    
    # Add the handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Log startup message
    root_logger.info("Game server starting up...")

# Set up logging before creating the app
setup_logging()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management
room_manager = RoomManager()
room_locks = {}  # Dictionary to store room locks

@app.before_request
def set_default_language():
    if 'language' not in session:
        session['language'] = 'en'

def get_room_lock(room_id):
    """Get or create a lock for a room"""
    if room_id not in room_locks:
        room_locks[room_id] = Lock()
    return room_locks[room_id]

# Store messages for each room
room_messages = {}

@app.route('/')
def index():
    if 'player_id' not in session:
        session['player_id'] = str(uuid.uuid4())
    lang = session.get('language', 'en')
    return render_template('index.html', lang=lang)

@app.route('/start_game', methods=['POST'])
def start_game():
    language = request.json.get('language', 'en')
    if language not in ['en', 'ru']:  # Only allow English and Russian
        language = 'en'
    session['language'] = language
    return jsonify({'status': 'success'})

@app.route('/create_room', methods=['POST'])
def create_room():
    if 'player_id' not in session:
        session['player_id'] = str(uuid.uuid4())
    
    player_id = session['player_id']
    player_name = request.json.get('player_name', f'Player_{player_id[:6]}')
    language = session.get('language', 'en')
    
    room_id = room_manager.create_room(player_id, language)
    room = room_manager.join_room(room_id, player_id, player_name)
    
    # Initialize room messages
    room_messages[room_id] = []
    
    session['room_id'] = room_id
    return jsonify({
        'status': 'success',
        'room_id': room_id,
        'player_id': player_id,
        'is_host': True
    })

@app.route('/join_room', methods=['POST'])
def join_room():
    # Only generate new player_id if one doesn't exist
    if 'player_id' not in session:
        session['player_id'] = str(uuid.uuid4())
    
    player_id = session['player_id']
    room_id = request.json.get('room_id')
    player_name = request.json.get('player_name', f'Player_{player_id[:6]}')
    
    logging.info(f"Join room request - Room: {room_id}, Player: {player_name} ({player_id})")
    
    # Get room first to check if it exists
    room = room_manager.get_room(room_id)
    if not room:
        logging.error(f"Room {room_id} not found")
        return jsonify({
            'status': 'error',
            'message': 'Room not found'
        }), 404
    
    # Check if player is already in the room
    if player_id in room.players:
        logging.info(f"Player {player_name} ({player_id}) is already in room {room_id}")
        session['room_id'] = room_id
        session['language'] = room.language
    else:
        # Join room with new player
        room = room_manager.join_room(room_id, player_id, player_name)
        if not room:
            logging.error(f"Failed to join room {room_id}")
            return jsonify({
                'status': 'error',
                'message': 'Failed to join room'
            }), 400
        
        session['room_id'] = room_id
        session['language'] = room.language
        
        # Add system message about player joining
        add_room_message(room_id, f"{player_name} joined the room", 'system')
    
    # Get all existing messages for the new player
    existing_messages = room_messages.get(room_id, [])
    
    # Convert player states to dict with proper translation
    players_dict = {}
    for pid, p in room.players.items():
        player_data = p.model_dump()
        if p.race and p.class_name:
            # Translate race and class names if they exist
            player_data['race'] = RACE_TRANSLATIONS[room.language].get(p.race, p.race)
            player_data['class_name'] = CLASS_TRANSLATIONS[room.language].get(p.class_name, p.class_name)
        if hasattr(p, 'ability_scores') and p.ability_scores is not None:
            player_data['ability_scores'] = p.ability_scores
        players_dict[pid] = player_data
    
    response_data = {
        'status': 'success',
        'room_id': room_id,
        'host_id': room.host_id,
        'player_id': player_id,
        'is_host': room.host_id == player_id,
        'players': players_dict,
        'messages': existing_messages
    }
    
    logging.info(f"Join room response - Room: {room_id}, Host: {room.host_id}, Players: {list(players_dict.keys())}")
    
    return jsonify(response_data)

@app.route('/leave_room', methods=['POST'])
def leave_room():
    if 'room_id' not in session or 'player_id' not in session:
        return jsonify({'error': 'Not in a room'}), 400
    
    room_id = session['room_id']
    player_id = session['player_id']
    room = room_manager.get_room(room_id)
    
    if room and player_id in room.players:
        player_name = room.players[player_id].name
        success = room_manager.leave_room(room_id, player_id)
        if success:
            add_room_message(room_id, f"{player_name} left the room", 'system')
            session.pop('room_id', None)
            return jsonify({'status': 'success'})
    
    return jsonify({'status': 'error', 'message': 'Failed to leave room'}), 400


@app.route('/get_room_state', methods=['GET'])
def get_room_state():
    if 'room_id' not in session:
        logging.error("Session missing room_id")
        return jsonify({'status': 'error', 'message': 'Not in a room'}), 400

    room = room_manager.get_room(session['room_id'])
    if not room:
        logging.error(f"Room {session['room_id']} not found")
        return jsonify({'status': 'error', 'message': 'Room not found'}), 404

    # Get messages since last_message_id if provided
    last_message_id = request.args.get('last_message_id')
    messages = []

    if session['room_id'] in room_messages:
        if last_message_id is None:
            # First time getting messages, only get the last few
            messages = room_messages[session['room_id']][-5:]
        else:
            # Get only new messages since last_message_id
            try:
                last_id = int(last_message_id)
                messages = [msg for msg in room_messages[session['room_id']]
                          if msg.get('id', 0) > last_id]
            except ValueError:
                logging.error(f"Invalid last_message_id: {last_message_id}")
                messages = room_messages[session['room_id']][-5:]

    # Convert player states to dict with proper translation
    players_dict = {}
    for pid, p in room.players.items():
        player_data = p.model_dump()  # Use model_dump instead of dict
        if p.race and p.class_name:
            # Translate race and class names if they exist
            player_data['race'] = RACE_TRANSLATIONS[room.language].get(p.race, p.race)
            player_data['class_name'] = CLASS_TRANSLATIONS[room.language].get(p.class_name, p.class_name)
        if hasattr(p, 'ability_scores') and p.ability_scores is not None:
            player_data['ability_scores'] = p.ability_scores
        players_dict[pid] = player_data

    # Convert room state with translated player data
    room_data = room.model_dump()  # Use model_dump instead of dict
    room_data['players'] = players_dict

    response_data = {
        'status': 'success',
        'room': room_data,
        'is_host': room.host_id == session.get('player_id'),
        'messages': messages,
        'last_message_id': messages[-1].get('id') if messages else None
    }

    logging.debug(f"Room state response - Players: {list(players_dict.keys())}")

    return jsonify(response_data)

@app.route('/get_races')
def get_races():
    language = session.get('language', 'en')
    races = {}
    translations = RACE_TRANSLATIONS[language]
    
    for eng_name, stats in RACE_STATS.items():
        local_name = translations[eng_name]
        race_data = stats.copy()
        # Add ability scores from RACE_CONFIGS
        race_data['ability_scores'] = RACE_CONFIGS[eng_name]['ability_scores']
        races[local_name] = race_data
    
    return jsonify(races)

@app.route('/get_classes')
def get_classes():
    language = session.get('language', 'en')
    classes = {}
    translations = CLASS_TRANSLATIONS[language]
    
    for eng_name, stats in CLASS_BONUSES.items():
        local_name = translations[eng_name]
        class_data = stats.copy()
        # Add primary ability and saving throws from CLASS_CONFIGS
        class_data['primary_ability'] = CLASS_CONFIGS[eng_name]['primary_ability']
        class_data['saving_throws'] = CLASS_CONFIGS[eng_name]['saving_throws']
        classes[local_name] = class_data
    
    return jsonify(classes)

@app.route('/choose_character', methods=['POST'])
def choose_character():
    if 'room_id' not in session or 'player_id' not in session:
        return jsonify({'error': 'Not in a room'}), 400
    
    room_id = session['room_id']
    player_id = session['player_id']
    
    room = room_manager.get_room(room_id)
    if not room:
        return jsonify({'error': 'Room not found'}), 404
    
    player = room.players.get(player_id)
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    
    try:
        data = request.get_json()
        race = data.get('race')
        class_name = data.get('class')
        
        logging.info(f"Received character creation request - Room: {room_id}, Player: {player_id}, Data: {data}")
        
        # Convert race and class names if needed
        language = room.language
        logging.info(f"Converting from {language}. Race: {race}, Class: {class_name}")
        
        # Convert localized names to English if needed
        for eng_name, local_name in RACE_TRANSLATIONS[language].items():
            if local_name == race:
                race = eng_name
                break
        
        for eng_name, local_name in CLASS_TRANSLATIONS[language].items():
            if local_name == class_name:
                class_name = eng_name
                break
        
        logging.info(f"Converted names - Race: {race}, Class: {class_name}")
        
        # Update player state
        player.race = race
        player.class_name = class_name
        
        # Initialize character stats
        game = DnDGame(language=room.language)
        game.player_race = race
        game.player_class = class_name
        game.initialize_character()
        
        # Copy stats to player state
        player.health_points = game.health_points
        player.gold = game.gold
        player.damage = game.damage
        player.level = game.level
        player.magic_1lvl = game.magic_1lvl
        player.magic_2lvl = game.magic_2lvl
        if player.__pydantic_extra__ is None:
            object.__setattr__(player, "__pydantic_extra__", {})
        object.__setattr__(player, "ability_scores", game.get_ability_scores())
        
        # Only generate opening scene if this is the host and game hasn't started
        response = None
        if player_id == room.host_id and not room.has_started:
            game.player_id = player_id  # Set player_id
            game.room_state = room      # Set room_state
            response = game.start_game()
            room.has_started = True  # Mark game as started
            # Add opening scene to room messages
            add_room_message(room_id, "Game started", "system")
            if response.get('message'):
                add_room_message(room_id, response['message'], 'dm')
        
        # Update room state
        room_manager.update_room(room)
        
        logging.info(f"Character created successfully - Player: {player.name} ({player_id})")
        
        return jsonify({
            'status': 'success',
            'player': player.dict(),
            'room': room.dict(),
            'message': response.get('message', '') if response else ''
        })
        
    except Exception as e:
        logging.error(f"Error creating character: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/game_action', methods=['POST'])
def game_action():
    if 'room_id' not in session or 'player_id' not in session:
        return jsonify({'error': 'Not in a room'}), 400
    
    room_id = session['room_id']
    player_id = session['player_id']
    
    # Get room lock
    room_lock = get_room_lock(room_id)
    
    with room_lock:
        room = room_manager.get_room(room_id)
        if not room:
            return jsonify({'error': 'Room not found'}), 404
        
        player = room.players.get(player_id)
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        
        try:
            data = request.get_json()
            action = data.get('action')
            
            game = DnDGame(language=room.language)
            # Load player stats into DnDGame
            game.player_race = player.race
            game.player_class = player.class_name
            game.health_points = player.health_points
            game.gold = player.gold
            game.damage = player.damage
            game.level = player.level
            game.magic_1lvl = player.magic_1lvl
            game.magic_2lvl = player.magic_2lvl
            game.last_dice_roll = player.last_dice_roll
            
            # Set game state from room state
            game.in_combat = room.in_combat
            if room.in_combat:
                game.enemy = {"name": room.enemy_name, "hp": room.enemy_health} if room.enemy_name else None
            
            # First add the player's action to room messages
            player_message_id = add_room_message(room_id, action, 'player', player.name)
            
            # Send message with room state context
            response = game.send_message(action, player_id=player_id, room_state=room)
            
            # Then add DM's response if there is one
            dm_message_id = None
            if response.get('message'):
                dm_message_id = add_room_message(room_id, response['message'], 'dm')
            
            # Update player states based on players_update
            for player_update in response.get('players_update', []):
                target_pid = player_update.get('player_id')
                if not target_pid or target_pid not in room.players:
                    continue

                target_player = room.players[target_pid]

                # Update player stats if provided
                if 'health_points' in player_update:
                    target_player.health_points = player_update['health_points']
                if 'gold' in player_update:
                    target_player.gold = player_update['gold']
                if 'damage' in player_update:
                    target_player.damage = player_update['damage']
                if 'level' in player_update:
                    target_player.level = player_update['level']
                if 'magic_1lvl' in player_update:
                    target_player.magic_1lvl = player_update['magic_1lvl']
                if 'magic_2lvl' in player_update:
                    target_player.magic_2lvl = player_update['magic_2lvl']
                if 'dice_roll_needed' in player_update:
                    target_player.dice_roll_needed = player_update['dice_roll_needed']
                if 'dice_type' in player_update:
                    target_player.dice_type = player_update['dice_type']
            
            # Update room combat state if needed
            combat_result = response.get('combat_result', {})
            if combat_result:
                if combat_result.get('damage_dealt') and room.enemy_health:
                    room.enemy_health -= combat_result['damage_dealt']
                    if room.enemy_health <= 0:
                        room.in_combat = False
                        room.enemy_name = None
                        room.enemy_health = None
            
            # Update room state
            room_manager.update_room(room)
            
            # Get dice roll info
            dice_roll = response.get('dice_roll', {})
            dice_roll_needed = dice_roll.get('required', False)
            dice_type = dice_roll.get('type')
            dice_modifier = dice_roll.get('modifier', None)
            
            # Get the latest messages for this room
            latest_messages = get_new_messages(room_id)
            
            return jsonify({
                'response': response.get('message', ''),
                'player': player.dict(),
                'room': room.dict(),
                'dice_needed': dice_roll_needed,
                'dice_type': dice_type,
                'dice_modifier': dice_modifier,
                'combat_result': combat_result,
                'messages': latest_messages,
                'last_message_id': latest_messages[-1]['id'] if latest_messages else None,
                'player_message_id': player_message_id,
                'dm_message_id': dm_message_id
            })
            
        except Exception as e:
            logging.error(f"Error in game_action: {str(e)}", exc_info=True)
            return jsonify({'error': str(e)})

@app.route('/roll_dice', methods=['POST'])
def roll_dice():
    if 'room_id' not in session or 'player_id' not in session:
        return jsonify({'error': 'Not in a room'}), 400
    
    room_id = session['room_id']
    player_id = session['player_id']
    
    # Get room lock
    room_lock = get_room_lock(room_id)
    
    with room_lock:
        room = room_manager.get_room(room_id)
        if not room:
            return jsonify({'error': 'Room not found'}), 404
        
        player = room.players.get(player_id)
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        
        game = DnDGame(language=room.language)
        
        data = request.get_json()
        dice_type = data.get('dice_type', 'd20')
        
        roll_result = game.roll_dice(dice_type)
        
        if roll_result is None:
            return jsonify({'error': 'Invalid dice type'}), 400
        
        # Add dice roll to room messages
        roll_message_id = add_room_message(
            room_id,
            f"rolled {roll_result} on {dice_type}",
            'player',
            player.name
        )
        
        # Update player's last roll
        player.last_dice_roll = roll_result
        player.dice_roll_needed = False
        player.dice_type = None
        room_manager.update_room(room)
        
        # Get the latest messages for this room
        latest_messages = get_new_messages(room_id)
        
        return jsonify({
            'roll': roll_result,
            'dice_type': dice_type,
            'player': player.dict(),
            'messages': latest_messages,
            'last_message_id': latest_messages[-1]['id'] if latest_messages else None,
            'roll_message_id': roll_message_id
        })

@app.route('/process_roll', methods=['POST'])
def process_roll():
    if 'room_id' not in session or 'player_id' not in session:
        return jsonify({'error': 'Not in a room'}), 400
    
    room_id = session['room_id']
    player_id = session['player_id']
    
    # Get room lock
    room_lock = get_room_lock(room_id)
    
    with room_lock:
        room = room_manager.get_room(room_id)
        if not room:
            return jsonify({'error': 'Room not found'}), 404
        
        player = room.players.get(player_id)
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        
        data = request.get_json()
        roll_value = data.get('roll')
        dice_type = data.get('dice_type')
        
        game = DnDGame(language=room.language)
        # Load player stats into DnDGame
        game.player_race = player.race
        game.player_class = player.class_name
        game.health_points = player.health_points
        game.gold = player.gold
        game.damage = player.damage
        game.level = player.level
        game.magic_1lvl = player.magic_1lvl
        game.magic_2lvl = player.magic_2lvl
        game.last_dice_roll = player.last_dice_roll
        
        # Set game state from room state
        game.in_combat = room.in_combat
        if room.in_combat:
            game.enemy = {"name": room.enemy_name, "hp": room.enemy_health} if room.enemy_name else None
        
        # Send message with room state context
        response = game.send_message(
            f"I rolled {roll_value} on {dice_type}",
            player_id=player_id,
            room_state=room
        )
        
        # Add DM's response if there is one
        dm_message_id = None
        if response.get('message'):
            dm_message_id = add_room_message(room_id, response['message'], 'dm')
        
        # Update player states based on players_update
        for player_update in response.get('players_update', []):
            target_pid = player_update.get('player_id')
            if not target_pid or target_pid not in room.players:
                continue
            
            target_player = room.players[target_pid]
            
            # Update player stats if provided
            if 'health_points' in player_update:
                target_player.health_points = player_update['health_points']
            if 'gold' in player_update:
                target_player.gold = player_update['gold']
            if 'damage' in player_update:
                target_player.damage = player_update['damage']
            if 'level' in player_update:
                target_player.level = player_update['level']
            if 'magic_1lvl' in player_update:
                target_player.magic_1lvl = player_update['magic_1lvl']
            if 'magic_2lvl' in player_update:
                target_player.magic_2lvl = player_update['magic_2lvl']
            if 'dice_roll_needed' in player_update:
                target_player.dice_roll_needed = player_update['dice_roll_needed']
            if 'dice_type' in player_update:
                target_player.dice_type = player_update['dice_type']
        
        # Update room combat state if needed
        combat_result = response.get('combat_result', {})
        if combat_result:
            if combat_result.get('damage_dealt') and room.enemy_health:
                room.enemy_health -= combat_result['damage_dealt']
                if room.enemy_health <= 0:
                    room.in_combat = False
                    room.enemy_name = None
                    room.enemy_health = None
        
        # Reset last roll after processing
        player.last_dice_roll = None
        
        # Update room state
        room_manager.update_room(room)
        
        # Get dice roll info for next action
        dice_roll = response.get('dice_roll', {})
        dice_roll_needed = dice_roll.get('required', False)
        dice_type = dice_roll.get('type')
        dice_modifier = dice_roll.get('modifier', None)
        
        # Get the latest messages for this room
        latest_messages = get_new_messages(room_id)
        
        return jsonify({
            'message': response.get('message', ''),
            'player': player.dict(),
            'room': room.dict(),
            'dice_needed': dice_roll_needed,
            'dice_type': dice_type,
            'dice_modifier': dice_modifier,
            'combat_result': combat_result,
            'messages': latest_messages,
            'last_message_id': latest_messages[-1]['id'] if latest_messages else None,
            'dm_message_id': dm_message_id
        })

@app.route('/save_game', methods=['POST'])
def save_game():
    if 'room_id' not in session:
        return jsonify({'error': 'Not in a room'}), 400
    
    success = room_manager.save_room(session['room_id'])
    message = 'Game saved successfully' if success else 'Failed to save game'
    if success:
        add_room_message(session['room_id'], message, 'system')
    return jsonify({'message': message})

@app.route('/load_game', methods=['POST'])
def load_game():
    data = request.json
    room_id = data.get('room_id', session.get('room_id'))
    
    if not room_id:
        return jsonify({'error': 'No room ID provided'}), 400
    
    room = room_manager.load_room(room_id)
    if not room:
        return jsonify({'error': 'Failed to load game'}), 400
    
    session['room_id'] = room_id
    add_room_message(room_id, 'Game loaded successfully', 'system')
    
    return jsonify({
        'status': 'success',
        'message': 'Game loaded successfully',
        'room': room.dict()
    })

@app.route('/list_saves')
def list_saves():
    saves = [f.stem.replace('room_', '') for f in Path('saves').glob('room_*.json')]
    return jsonify({'saves': '\n'.join(saves)})

def add_room_message(room_id: str, message: str, message_type: str = 'system', player_name: str = None):
    """Add a message to the room's message history with an ID"""
    if room_id not in room_messages:
        room_messages[room_id] = []
    # Prevent duplicate DM messages from being added by checking the last few messages
    if message_type == 'dm' and room_messages[room_id]:
        for msg in room_messages[room_id][-5:]:
            if msg['type'] == 'dm' and msg['message'] == message:
                return msg['id']

    # Get the next message ID
    next_id = len(room_messages[room_id]) + 1

    # Create message data
    message_data = {
        'id': next_id,
        'message': message,
        'type': message_type,
        'timestamp': datetime.now().isoformat(),
        'player_name': player_name if message_type == 'player' else None
    }

    room_messages[room_id].append(message_data)

    # Keep only the last 100 messages
    if len(room_messages[room_id]) > 100:
        room_messages[room_id] = room_messages[room_id][-100:]

    # Also update room's message history
    room = room_manager.get_room(room_id)
    if room:
        if not hasattr(room, 'message_history'):
            room.message_history = []
        room.message_history.append({
            'type': message_type,
            'message': message,
            'player_name': player_name,
            'timestamp': datetime.now()
        })
        # Keep only last 100 messages
        if len(room.message_history) > 100:
            room.message_history = room.message_history[-100:]
        room_manager.update_room(room)
    
    return next_id

def get_new_messages(room_id: str, last_message_id: str = None):
    """Get messages newer than last_message_id"""
    if room_id not in room_messages:
        return []
    
    if last_message_id is None:
        return room_messages[room_id][-50:]  # Return last 50 messages
    
    try:
        last_id = int(last_message_id)
        return [msg for msg in room_messages[room_id] if msg['id'] > last_id]
    except (ValueError, TypeError):
        return room_messages[room_id][-50:]

# New endpoints for multi-page support
@app.route('/character')
def character():
    lang = session.get('language', 'en')
    return render_template('character.html', lang=lang)

@app.route('/game')
def game():
    lang = session.get('language', 'en')
    return render_template('game.html', lang=lang)

@app.route('/translations/<path:filename>')
def serve_translation(filename):
    return send_from_directory('translations', filename)

def load_translations(lang):
    try:
        with open(Path('translations') / f'{lang}.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

@app.template_filter('trans')
def translate_filter(key):
    lang = session.get('language', 'en')
    translations = load_translations(lang)
    return translations.get(key, key)

PlayerState.model_config = {**PlayerState.model_config, "extra": "allow"}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)