import os
import json
import time
from flask import Flask, render_template, send_from_directory, request
from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder='.', static_folder='.')
app.config['SECRET_KEY'] = 'event-os-secret-2026'

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

def load_config():
    try:
        with open('event_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"cdn_base_url": "https://pub-372ba5f717cf4a8694558f47682d65d9.r2.dev/", "modules": []}

config = load_config()

# Очередь для эффектов (1 -> 2 -> 3)
sfx_counters = {"fanfare": 0, "applause": 0, "correct": 0, "wrong": 0}

system_state = {
    "active_module": "",
    "event_title": config.get("event_title", "FAMILY STANDARD OS"),
    "event_subtitle": config.get("event_subtitle", "С праздником!"),
    "audio_volume": 0.3,
    "current_mood": "lounge",
    "current_track": "lounge.mp3",
    "is_playing": False,
    "seek_position": 0.0,
    "track_duration": 0.0,
    "timer": {"active": False, "end_time": 0}
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory('.', filename)

@socketio.on('connect')
def handle_connect():
    emit('state_update', system_state)
    emit('modules_config_update', config.get('modules', []))

@socketio.on('login')
def handle_login(data):
    pin = str(data.get('pin', '')).strip()
    if pin == str(config.get('host_pin', '111')):
        emit('login_response', {'success': True, 'role': 'HOST'})
    elif pin == str(config.get('screen_pin', '222')):
        emit('login_response', {'success': True, 'role': 'SCREEN'})
    else:
        emit('login_response', {'success': False, 'message': 'Неверный PIN'})

@socketio.on('switch_module')
def switch_module(data):
    system_state['active_module'] = data.get('module', '')
    socketio.emit('state_update', system_state)

@socketio.on('add_timer_10s')
def add_timer():
    now = time.time()
    if system_state['timer']['active'] and system_state['timer']['end_time'] > now:
        system_state['timer']['end_time'] += 10
    else:
        system_state['timer']['active'] = True
        system_state['timer']['end_time'] = now + 10
    socketio.emit('state_update', system_state)

# Получили сигнал от экрана, что таймер кончился — вырубаем его у всех
@socketio.on('timer_done')
def timer_done():
    system_state['timer']['active'] = False
    socketio.emit('state_update', system_state)

@socketio.on('host_audio_control')
def audio_control(data):
    if 'volume' in data:
        system_state['audio_volume'] = float(data['volume'])
    if 'seek' in data:
        system_state['seek_position'] = float(data['seek'])
    if 'toggle_play' in data:
        system_state['is_playing'] = not system_state['is_playing']
    if 'mood' in data:
        system_state['current_mood'] = data['mood']
        system_state['current_track'] = f"{data['mood']}.mp3"
        system_state['is_playing'] = True
        system_state['seek_position'] = 0.0
    socketio.emit('state_update', system_state)

# Экран скидывает длину трека при загрузке
@socketio.on('sync_duration')
def sync_duration(data):
    system_state['track_duration'] = float(data['duration'])
    socketio.emit('state_update', system_state)

@socketio.on('host_trigger_sfx')
def trigger_sfx(data):
    sfx = data.get('sfx')
    if sfx in sfx_counters:
        sfx_counters[sfx] = (sfx_counters[sfx] % 3) + 1
        var_id = sfx_counters[sfx]
    else:
        var_id = 1
    
    file_name = f"{sfx}_{var_id}.mp3"
    socketio.emit('play_sfx_stream', {'file': file_name})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
