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
sfx_counters = {"fanfare": 0, "applause": 0, "correct": 0, "wrong": 0}
track_positions = {"lounge.mp3": 0.0, "active.mp3": 0.0, "party.mp3": 0.0}

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

# АБСОЛЮТНАЯ ЗАЧИСТКА МЕРТВОГО ТАЙМЕРА (чтобы не всплывал)
def clean_timer_state():
    if system_state['timer']['active'] and system_state['timer']['end_time'] <= time.time():
        system_state['timer']['active'] = False
        system_state['timer']['end_time'] = 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory('.', filename)

@socketio.on('connect')
def handle_connect():
    clean_timer_state()
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
    clean_timer_state()
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

@socketio.on('timer_done')
def timer_done():
    system_state['timer']['active'] = False
    system_state['timer']['end_time'] = 0
    socketio.emit('state_update', system_state)

@socketio.on('host_audio_control')
def audio_control(data):
    clean_timer_state()
    curr_track = system_state['current_track']

    if 'volume' in data:
        system_state['audio_volume'] = float(data['volume'])
    
    # Относительная перемотка (+30 сек или -30 сек)
    if 'seek_relative' in data:
        new_seek = system_state['seek_position'] + float(data['seek_relative'])
        if new_seek < 0: new_seek = 0
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

@socketio.on('screen_sync_time')
def screen_sync_time(data):
    if system_state['is_playing']:
        system_state['seek_position'] = float(data['current_time'])
        track_positions[system_state['current_track']] = float(data['current_time'])

@socketio.on('host_trigger_sfx')
def trigger_sfx(data):
    sfx = data.get('sfx')
    if sfx in sfx_counters:
        sfx_counters[sfx] = (sfx_counters[sfx] % 3) + 1
        var_id = sfx_counters[sfx]
    else:
        var_id = 1
    socketio.emit('play_sfx_stream', {'file': f"{sfx}_{var_id}.mp3"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
