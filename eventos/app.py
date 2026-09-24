import os
import json
import time
import random
from flask import Flask, render_template, jsonify, send_from_directory, request
from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder='.', static_folder='.')
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
        "cdn_base_url": "https://pub-372ba5f717cf4a8694558f47682d65d9.r2.dev/",
        "modules": []
    }

config_data = load_config()
connected_users = {}

# Хранение текущего времени воспроизведения для каждого трека
track_positions = {
    "lounge.mp3": 0.0,
    "active.mp3": 0.0,
    "party.mp3": 0.0
}

system_state = {
    "active_module": "",
    "host_name": config_data.get("host_name", "Богдан"),
    "event_title": config_data.get("event_title", "FAMILY STANDARD OS"),
    "event_subtitle": config_data.get("event_subtitle", "С праздником!"),
    "audio_volume": 0.3,
    "current_mood": "lounge",
    "current_track": "lounge.mp3",
    "is_playing": True,
    "seek_position": 0.0,
    "track_duration": 0.0,
    "timer": {"active": False, "end_time": 0}
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ping')
def ping():
    return jsonify({"status": "ok", "system": "Event OS Core Active"}), 200

@app.route('/<path:filename>')
def serve_root_file(filename):
    return send_from_directory('.', filename)

# --- СОКЕТЫ ---

@socketio.on('connect')
def handle_connect():
    emit('state_update', system_state, to=request.sid)
    emit('modules_config_update', config_data.get('modules', []), to=request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in connected_users:
        del connected_users[request.sid]

@socketio.on('login')
def handle_login(data):
    pin = str(data.get('pin', '')).strip()

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
        emit('login_response', {'success': False, 'message': 'Неверный PIN-код'}, to=request.sid)

    socketio.emit('state_update', system_state)

@socketio.on('switch_module')
def handle_switch_module(data):
    module_path = data.get('module', '')
    system_state['active_module'] = module_path
    socketio.emit('state_update', system_state)

@socketio.on('add_timer_10s')
def handle_add_timer_10s():
    now = time.time()
    if system_state['timer']['active'] and system_state['timer']['end_time'] > now:
        system_state['timer']['end_time'] += 10
    else:
        system_state['timer']['active'] = True
        system_state['timer']['end_time'] = now + 10

    socketio.emit('state_update', system_state)

@socketio.on('host_audio_control')
def handle_audio_control(data):
    curr_track = system_state['current_track']

    if 'duration' in data:
        system_state['track_duration'] = float(data['duration'])

    if 'seek' in data:
        seek_val = float(data['seek'])
        system_state['seek_position'] = seek_val
        track_positions[curr_track] = seek_val

    if 'volume' in data:
        system_state['audio_volume'] = float(data['volume'])

    if 'mood' in data:
        if 'current_time' in data:
            track_positions[curr_track] = float(data['current_time'])
        
        mood = data['mood']
        new_track = f"{mood}.mp3"
        system_state['current_mood'] = mood
        system_state['current_track'] = new_track
        system_state['is_playing'] = True
        system_state['seek_position'] = track_positions.get(new_track, 0.0)

    if 'toggle_play' in data:
        system_state['is_playing'] = not system_state['is_playing']

    socketio.emit('state_update', system_state)

@socketio.on('host_trigger_sfx')
def handle_trigger_sfx(data):
    sfx_type = data.get('sfx')
    var_id = random.randint(1, 3)
    file_name = f"{sfx_type}_{var_id}.mp3"
    
    socketio.emit('play_sfx_stream', {
        'file': file_name,
        'volume': 0.6
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
