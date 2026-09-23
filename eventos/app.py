import os
import json
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit

# template_folder='.' заставляет Flask искать index.html прямо в этой же папке
app = Flask(__name__, template_folder='.')
app.config['SECRET_KEY'] = 'familystandard-secret-key-2026'

# Стандартный режим threading — работает везде из коробки
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
        except Exception as e:
            print(f"[Event OS] Ошибка чтения event_data.json: {e}")
    return {"event_title": "Family Standard OS", "host_pin": "111", "screen_pin": "222"}

event_config = load_event_config()

system_state = {
    "active_module": None,
    "audio_volume": 0.4,
    "audio_emotion": "lounge",
    "screen_text": event_config.get("event_title", "Family Standard OS"),
    "screen_badge": "ДО СТАРТА"
}

# --- МАРШРУТЫ HTTP ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ping')
def ping():
    return jsonify({"status": "ok", "system": "Event OS Active", "title": system_state["screen_text"]})

# --- СОБЫТИЯ SOCKET.IO ---

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

    if pin:
        if pin == host_pin:
            emit('login_response', {'success': True, 'role': 'HOST', 'config': event_config})
        elif pin == screen_pin:
            emit('login_response', {'success': True, 'role': 'SCREEN', 'config': event_config})
        else:
            emit('login_response', {'success': False, 'message': 'Неверный ПИН-код доступа'})
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
    # Читаем динамический порт от Render или ставим 10000 по умолчанию
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
