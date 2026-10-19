import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'event_secret_key_2026'

# Разрешаем CORS для подключения с любых доменов/файлов
socketio = SocketIO(app, cors_allowed_origins="*")

SECRET_PIN = "7777"  # Ваш ПИН-код для ведущего

current_state = {
    'videoId': None,
    'action': 'pause',
    'time': 0
}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('auth_pin')
def handle_auth(data):
    if data.get('pin') == SECRET_PIN:
        emit('auth_result', {'success': True})
        # Сразу передаем текущее состояние зашедшему ведущему
        emit('sync_to_viewers', current_state)
    else:
        emit('auth_result', {'success': False, 'message': 'Неверный ПИН'})

@socketio.on('host_control')
def handle_host_control(data):
    global current_state
    current_state['videoId'] = data.get('videoId')
    current_state['action'] = data.get('action')
    current_state['time'] = data.get('time', 0)

    # Транслируем всем зрителям на экраны
    emit('sync_to_viewers', current_state, broadcast=True, include_self=False)

if __name__ == '__main__':
    # Render автоматически задает переменную PORT (по умолчанию 10000)
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port)
