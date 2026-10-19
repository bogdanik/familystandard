import os
from flask import Flask, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'familystandard_secret_key'

# CORS разрешен для всех внешних подключений
socketio = SocketIO(app, cors_allowed_origins="*")

SECRET_PIN = "7777"  # Ваш ПИН-код ведущего

current_state = {
    'videoId': None,
    'action': 'pause',
    'time': 0
}

@app.route('/')
def health_check():
    return jsonify({"status": "ok", "service": "Family Standard Render Backend"})

# При подключении нового зрителя сразу отправляем текущее состояние
@socketio.on('connect')
def handle_connect():
    if current_state['videoId']:
        emit('sync_to_viewers', current_state)

@socketio.on('auth_pin')
def handle_auth(data):
    if data.get('pin') == SECRET_PIN:
        emit('auth_result', {'success': True})
        emit('sync_to_viewers', current_state)
    else:
        emit('auth_result', {'success': False, 'message': 'Неверный ПИН'})

@socketio.on('host_control')
def handle_host_control(data):
    global current_state
    current_state['videoId'] = data.get('videoId')
    current_state['action'] = data.get('action')
    current_state['time'] = data.get('time', 0)

    # Транслируем событие ВСЕМ подключенным зрителям
    emit('sync_to_viewers', current_state, broadcast=True, include_self=False)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
