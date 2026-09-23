import os
import json
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder='.')
socketio = SocketIO(app, cors_allowed_origins="*")

CONFIG_FILE = 'event_data.json'

def load_event_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка чтения {CONFIG_FILE}: {e}")
    return {"event_title": "Свадебный Вечер", "host_pin": "111", "screen_pin": "222"}

event_config = load_event_config()

system_state = {
    "active_module": None,
    "audio_volume": 0.4,
    "audio_emotion": "lounge",
    "screen_text": event_config.get("event_title", "Event OS"),
    "screen_badge": "ДО СТАРТА"
}

@app.route('/')
def home():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    emit('state_update', system_state)

@socketio.on('login')
def handle_login(data):
    if not isinstance(data, dict):
        data = {}

    pin = str(data.get('pin', '')).strip() if data.get('pin') else None
    name = str(data.get('name', '')).strip() if data.get('name') else None

    host_pin = str(event_config.get('host_pin', '111'))
    screen_pin = str(event_config.get('screen_pin', '222'))

    if pin is not None:
        if pin == host_pin:
            emit('login_response', {'success': True, 'role': 'HOST', 'config': event_config})
        elif pin == screen_pin:
            emit('login_response', {'success': True, 'role': 'SCREEN', 'config': event_config})
        else:
            emit('login_response', {'success': False, 'message': 'Неверный код доступа'})
    else:
        guest_name = name if name else 'Гость'
        emit('login_response', {'success': True, 'role': 'GUEST', 'name': guest_name})

    emit('state_update', system_state)

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
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
