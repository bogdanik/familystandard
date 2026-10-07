import os
import json
import time
from flask import Flask, render_template, send_from_directory, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder='.', static_folder='.')
app.config['SECRET_KEY'] = 'event-os-secret-2026'

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

def load_config():
    try:
        with open('event_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading event_data.json: {e}")
        return {}

config = load_config()

def save_config():
    try:
        # Защита: перед сохранением читаем актуальный файл с диска, чтобы сохранить список modules нетронутым
        current_disk_config = load_config()
        config_to_save = {
            "_description": current_disk_config.get("_description", config.get("_description", "")),
            "event_title": system_state.get("event_title", ""),
            "event_subtitle": system_state.get("event_subtitle", ""),
            "host_name": system_state.get("host_name", ""),
            "host_pin": current_disk_config.get("host_pin", config.get("host_pin", "")),
            "screen_pin": current_disk_config.get("screen_pin", config.get("screen_pin", "")),
            "cdn_base_url": system_state.get("cdn_base_url", ""),
            "scenario_url": system_state.get("scenario_url", ""),
            "modules": current_disk_config.get("modules", config.get("modules", []))
        }
        with open('event_data.json', 'w', encoding='utf-8') as f:
            json.dump(config_to_save, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving event_data.json: {e}")

sfx_counters = {"jingle": 0, "fanfare": 0, "applause": 0, "correct": 0, "wrong": 0}
sfx_max = {"jingle": 4, "fanfare": 3, "applause": 3, "correct": 3, "wrong": 3}

track_positions = {"lounge.mp3": 0.0, "active.mp3": 0.0, "party.mp3": 0.0}

system_state = {
    "active_module": "",
    "event_title": config.get("event_title", ""),
    "event_subtitle": config.get("event_subtitle", ""),
    "host_name": config.get("host_name", ""),
    "cdn_base_url": config.get("cdn_base_url", ""),
    "scenario_url": config.get("scenario_url", ""),
    "audio_volume": 0.3,
    "current_mood": "lounge",
    "current_track": "lounge.mp3",
    "is_playing": False,
    "seek_position": 0.0,
    "track_duration": 0.0,
    "jingle_playing": False,
    "timer": {"active": False, "end_time": 0}
}

def clean_timer_state():
    if system_state['timer']['active'] and system_state['timer']['end_time'] <= time.time():
        system_state['timer']['active'] = False
        system_state['timer']['end_time'] = 0

@app.route('/')
def index(): 
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/ping')
def ping(): 
    return jsonify({"status": "ok", "system": "Event OS Core Active"}), 200

@app.route('/<path:filename>')
def serve_file(filename): 
    return send_from_directory('.', filename)

@socketio.on('connect')
def handle_connect():
    clean_timer_state()
    emit('state_update', system_state)
    fresh_config = load_config()
    emit('modules_config_update', fresh_config.get('modules', []))

# Новый точечный обработчик: запрашивает свежие интерактивы из event_data.json строго при клике
@socketio.on('get_modules')
def handle_get_modules():
    fresh_config = load_config()
    emit('modules_config_update', fresh_config.get('modules', []))

@socketio.on('login')
def handle_login(data):
    pin = str(data.get('pin', '')).strip()
    host_pin = str(config.get('host_pin', '')).strip()
    screen_pin = str(config.get('screen_pin', '')).strip()

    if pin and pin == host_pin:
        emit('login_response', {'success': True, 'role': 'HOST'})
    elif pin and pin == screen_pin:
        emit('login_response', {'success': True, 'role': 'SCREEN'})
    else:
        emit('login_response', {'success': False, 'message': 'Неверный КОД ДОСТУПА'})

@socketio.on('update_event_info')
def update_event_info(data):
    if 'event_title' in data:
        system_state['event_title'] = data['event_title']
    if 'event_subtitle' in data:
        system_state['event_subtitle'] = data['event_subtitle']
    if 'host_name' in data:
        system_state['host_name'] = data['host_name']
    if 'scenario_url' in data:
        system_state['scenario_url'] = data['scenario_url']
    save_config()
    socketio.emit('state_update', system_state)

@socketio.on('switch_module')
def switch_module(data):
    clean_timer_state()
    system_state['active_module'] = data.get('module', '')
    socketio.emit('state_update', system_state)

@socketio.on('add_timer_15s')
def add_timer():
    now = time.time()
    if system_state['timer']['active'] and system_state['timer']['end_time'] > now:
        system_state['timer']['end_time'] += 15
    else:
        system_state['timer']['active'] = True
        system_state['timer']['end_time'] = now + 15
    socketio.emit('state_update', system_state)

@socketio.on('timer_done')
def timer_done():
    if system_state['timer']['end_time'] <= time.time() + 1:
        system_state['timer']['active'] = False
        system_state['timer']['end_time'] = 0
        socketio.emit('state_update', system_state)

@socketio.on('host_audio_control')
def audio_control(data):
    clean_timer_state()
    curr_track = system_state['current_track']

    if 'volume' in data: 
        system_state['audio_volume'] = float(data['volume'])
    
    if 'seek_relative' in data:
        new_seek = system_state['seek_position'] + float(data['seek_relative'])
        if new_seek < 0: 
            new_seek = 0
        if system_state['track_duration'] > 0 and new_seek > system_state['track_duration']:
            new_seek = system_state['track_duration'] - 5
        system_state['seek_position'] = new_seek
        track_positions[curr_track] = new_seek

    if 'toggle_play' in data: 
        system_state['is_playing'] = not system_state['is_playing']

    if 'mood' in data:
        system_state['current_mood'] = data['mood']
        system_state['current_track'] = f"{data['mood']}.mp3"
        system_state['is_playing'] = True
        system_state['seek_position'] = track_positions.get(f"{data['mood']}.mp3", 0.0)

    socketio.emit('state_update', system_state)

@socketio.on('sync_duration')
def sync_duration(data):
    system_state['track_duration'] = float(data['duration'])
    socketio.emit('state_update', system_state)

@socketio.on('screen_sync_time')
def screen_sync_time(data):
    if system_state['is_playing']:
        system_state['seek_position'] = float(data['current_time'])
        track_positions[system_state['current_track']] = float(data['current_time'])

@socketio.on('host_toggle_jingle')
def host_toggle_jingle():
    if system_state.get('jingle_playing', False):
        system_state['jingle_playing'] = False
        socketio.emit('stop_sfx')
    else:
        system_state['jingle_playing'] = True
        sfx_counters['jingle'] = (sfx_counters['jingle'] % sfx_max['jingle']) + 1
        socketio.emit('play_sfx_stream', {'file': f"jingle_{sfx_counters['jingle']}.mp3"})
    socketio.emit('state_update', system_state)

@socketio.on('sfx_ended')
def sfx_ended():
    system_state['jingle_playing'] = False
    socketio.emit('state_update', system_state)

@socketio.on('host_trigger_sfx')
def trigger_sfx(data):
    sfx = data.get('sfx')
    sfx_counters[sfx] = (sfx_counters.get(sfx, 0) % sfx_max.get(sfx, 3)) + 1
    socketio.emit('play_sfx_stream', {'file': f"{sfx}_{sfx_counters[sfx]}.mp3"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
