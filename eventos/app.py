import os
import json
import time
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder='.')
app.config['SECRET_KEY'] = 'familystandard-secret-key-2026'

socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='threading',
    ping_timeout=60,
    ping_interval=25
)

CONFIG_FILE = 'event_data.json'

def load_event_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"event_title": "Family Standard OS", "host_pin": "111", "screen_pin": "222"}

event_config = load_event_config()

connected_guests = {}

system_state = {
    "event_started": False,
    "active_module": "LOBBY",
    "video_playing": False,
    "audio_volume": 0.4,
    "audio_emotion": "lounge",
    "screen_text": event_config.get("event_title", "Family Standard OS"),
    "screen_badge": "ДО СТАРТА",
    "timer": {"active": False, "end_time": 0, "total_seconds": 0},
    "guest_count": 0
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ping')
def ping():
    return jsonify({"status": "ok", "system": "Event OS Active"})

@socketio.on('connect')
def handle_connect():
    system_state["guest_count"] = len(connected_guests)
    emit('state_update', system_state, to=request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in connected_guests:
        del connected_guests[request.sid]
        system_state["guest_count"] = len(connected_guests)
        socketio.emit('state_update', system_state)

@socketio.on('login')
def handle_login(data):
    if not isinstance(data, dict):
        data = {}

    pin = str(data.get('pin', '')).strip() if data.get('pin') else None
    name = str(data.get('name', '')).strip() if data.get('name') else None

    host_pin = str(event_config.get('host_pin', '111'))
    screen_pin = str(event_config.get('screen_pin', '222'))

    if pin is not None and pin != "":
        if pin == host_pin:
            emit('login_response', {'success': True, 'role': 'HOST', 'config': event_config}, to=request.sid)
        elif pin == screen_pin:
            emit('login_response', {'success': True, 'role': 'SCREEN', 'config': event_config}, to=request.sid)
        else:
            emit('login_response', {'success': False, 'message': 'Неверный код доступа'}, to=request.sid)
    else:
        guest_name = name if name else 'Гость'
        connected_guests[request.sid] = guest_name
        system_state["guest_count"] = len(connected_guests)
        emit('login_response', {'success': True, 'role': 'GUEST', 'name': guest_name}, to=request.sid)

    socketio.emit('state_update', system_state)

@socketio.on('host_official_start')
def handle_official_start():
    system_state["event_started"] = True
    system_state["active_module"] = "VIDEO_INTRO"
    system_state["screen_badge"] = "СОБЫТИЕ НАЧАТО"
    system_state["screen_text"] = "ДОБРО ПОЖАЛОВАТЬ!"
    system_state["video_playing"] = True
    socketio.emit('state_update', system_state)

@socketio.on('host_launch_module')
def handle_launch_module(data):
    module_name = data.get('module')
    system_state["active_module"] = module_name
    system_state["video_playing"] = (module_name == "VIDEO_INTRO")
    
    if module_name == "LOBBY":
        system_state["screen_badge"] = "СБОР ГОСТЕЙ"
        system_state["screen_text"] = event_config.get("event_title", "Family Standard OS")
    elif module_name == "VIDEO_INTRO":
        system_state["screen_badge"] = "ВИДЕО-ПРЕЗЕНТАЦИЯ"
        system_state["screen_text"] = "СМОТРИТЕ НА ЭКРАН"
    elif module_name == "GAME":
        system_state["screen_badge"] = "ИНТЕРАКТИВ"
        system_state["screen_text"] = "ИГРА НА ЭКРАНЕ"

    socketio.emit('state_update', system_state)

@socketio.on('host_start_timer')
def handle_start_timer(data):
    seconds = int(data.get('seconds', 60))
    system_state["timer"] = {
        "active": True,
        "end_time": time.time() + seconds,
        "total_seconds": seconds
    }
    socketio.emit('state_update', system_state)

@socketio.on('host_stop_timer')
def handle_stop_timer():
    system_state["timer"]["active"] = False
    socketio.emit('state_update', system_state)

@socketio.on('host_audio_control')
def handle_audio_control(data):
    if 'volume' in data:
        system_state['audio_volume'] = data['volume']
    if 'emotion' in data:
        system_state['audio_emotion'] = data['emotion']
    socketio.emit('audio_state_changed', data)

@socketio.on('host_trigger_sfx')
def handle_trigger_sfx(data):
    sfx_type = data.get('sfx')
    socketio.emit('play_sfx_on_screen', {'sfx': sfx_type})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
