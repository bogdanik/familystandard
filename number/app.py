import os
import random
from flask import Flask
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key_here'

# Разрешаем CORS, чтобы GitHub Pages мог подключаться к серверу Render
socketio = SocketIO(app, cors_allowed_origins="*")

CHARACTERS = [
    'А','Б','В','Г','Д','Е','Ё','Ж','З','И','Й','К','Л','М','Н','О','П','Р','С','Т','У','Ф','Х','Ц','Ч','Ш','Щ','Ъ','Ы','Ь','Э','Ю','Я',
    'A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z',
    '0','1','2','3','4','5','6','7','8','9'
]

# Храним глобальное состояние на сервере
server_state = {
    'status': 'idle',  # 'idle', 'spinning', 'stopped'
    'current_char': ''
}

@socketio.on('connect')
def handle_connect():
    """При подключении нового пользователя отправляем ему текущее состояние экрана"""
    emit('sync_state', server_state)

@socketio.on('request_spin')
def handle_spin():
    """Запрос на старт прокрутки"""
    if server_state['status'] == 'spinning':
        return

    server_state['status'] = 'spinning'
    # Сервер выбирает единую букву для всех
    server_state['current_char'] = random.choice(CHARACTERS)

    # Broadcast = True отправляет событие абсолютно всем подключенным клиентам
    emit('spin_started', {
        'finalChar': server_state['current_char']
    }, broadcast=True)

@socketio.on('spin_completed')
def handle_spin_completed():
    """Сигнал о завершении анимации прокрутки"""
    server_state['status'] = 'stopped'

@socketio.on('request_reset')
def handle_reset():
    """Запрос на сброс состояния (крестик)"""
    server_state['status'] = 'idle'
    server_state['current_char'] = ''
    emit('state_reset', broadcast=True)

if __name__ == '__main__':
    # Render передаёт порт через переменную окружения PORT
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
