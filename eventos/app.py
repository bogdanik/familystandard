import os
import json
import random
from flask import Flask, render_template, jsonify, send_from_directory, request
from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder='.', static_folder='static')
app.config['SECRET_KEY'] = 'familystandard-os-secret-2026'

socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='threading'
)

CONFIG_FILE = 'event_data.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "event_title": "FAMILY STANDARD OS", 
        "event_subtitle": "С праздником!",
        "host_name": "Богдан", 
        "host_pin": "111", 
        "screen_pin": "222",
        "modules": []
    }

config_data = load_config()
connected_users = {}

system_state = {
    "active_module": "lobby/lobby.html",
    "host_name": config_data.get("host_name", "Богдан"),
    "event_title": config_data.get("event_title", "FAMILY STANDARD OS"),
    "event_subtitle": config_data.get("event_subtitle", "С праздником!"),
    "audio_volume": 0.3,
    "current_mood": "lounge",
    "current_track": "/static/audio/music/lounge.mp3",
    "is_playing": False,
    "guest_count": 0
}

# --- МАРШРУТИЗАЦИЯ ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ping')
def ping():
    return jsonify({"status": "ok", "system": "Event OS Core Active"}), 200

@app.route('/modules/<path:filename>')
def serve_module(filename):
    return send_from_directory('modules', filename)

# --- СОКЕТЫ ---

@socketio.on('connect')
def handle_connect():
    emit('state_update', system_state, to=request.sid)
    emit('modules_config_update', config_data.get('modules', []), to=request.sid)
    emit('users_list_update', get_guests_list(), to=request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in connected_users:
        del connected_users[request.sid]
        system_state['guest_count'] = len([u for u in connected_users.values() if u['role'] == 'GUEST'])
        socketio.emit('users_list_update', get_guests_list())
        socketio.emit('state_update', system_state)

def get_guests_list():
    return [u for u in connected_users.values()]

@socketio.on('login')
def handle_login(data):
    pin = str(data.get('pin', '')).strip() if data.get('pin') else None
    name = str(data.get('name', '')).strip() if data.get('name') else 'Гость'

    host_pin = str(config_data.get('host_pin', '111'))
    screen_pin = str(config_data.get('screen_pin', '222'))

    if pin == host_pin:
        user_name = f"{config_data.get('host_name', 'Богдан')} (Ведущий)"
        connected_users[request.sid] = {'name': user_name, 'role': 'HOST'}
        emit('login_response', {'success': True, 'role': 'HOST', 'name': user_name}, to=request.sid)
    elif pin == screen_pin:
        connected_users[request.sid] = {'name': 'Проектор', 'role': 'SCREEN'}
        emit('login_response', {'success': True, 'role': 'SCREEN'}, to=request.sid)
    else:
        connected_users[request.sid] = {'name': name, 'role': 'GUEST'}
        emit('login_response', {'success': True, 'role': 'GUEST', 'name': name}, to=request.sid)

    system_state['guest_count'] = len([u for u in connected_users.values() if u['role'] == 'GUEST'])
    socketio.emit('users_list_update', get_guests_list())
    socketio.emit('state_update', system_state)

@socketio.on('switch_module')
def handle_switch_module(data):
    module_name = data.get('module')
    system_state['active_module'] = module_name
    socketio.emit('state_update', system_state)

@socketio.on('host_audio_control')
def handle_audio_control(data):
    if 'volume' in data:
        system_state['audio_volume'] = float(data['volume'])
    if 'mood' in data:
        mood = data['mood']
        system_state['current_mood'] = mood
        system_state['current_track'] = f"/static/audio/music/{mood}.mp3"
        system_state['is_playing'] = True

    socketio.emit('state_update', system_state)

@socketio.on('host_trigger_sfx')
def handle_trigger_sfx(data):
    sfx_type = data.get('sfx')
    var_id = random.randint(1, 3)
    file_path = f"/static/audio/sfx/{sfx_type}_{var_id}.mp3"
    
    socketio.emit('play_sfx_stream', {
        'file': file_path,
        'volume': system_state['audio_volume']
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
