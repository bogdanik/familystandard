import os
import random
from flask import Flask
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key_here'

# Разрешаем CORS для подключения с внешних доменов (GitHub Pages)
socketio = SocketIO(app, cors_allowed_origins="*")

# Список символов: русский алфавит + английский алфавит + цифры
CHARACTERS = [
    'А','Б','В','Г','Д','Е','Ё','Ж','З','И','Й','К','Л','М','Н','О','П','Р','С','Т','У','Ф','Х','Ц','Ч','Ш','Щ','Ъ','Ы','Ь','Э','Ю','Я',
    'A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z',
    '0','1','2','3','4','5','6','7','8','9'
]

# Единое состояние сервера
server_state = {
    'status': 'idle',  # Возможные состояния: 'idle', 'spinning', 'stopped'
    'current_char': ''
}

@socketio.on('connect')
def handle_connect():
    """Отправка текущего состояния экрана каждому новому подключенному пользователю"""
    emit('sync_state', server_state)

@socketio.on('request_spin')
def handle_spin():
    """Обработка нажатия на кнопку СТАРТ / Пробел / Символ"""
    if server_state['status'] == 'spinning':
        return

    server_state['status'] = 'spinning'
    # Выбираем случайный символ один раз для всех клиентов
    server_state['current_char'] = random.choice(CHARACTERS)

    # broadcast=True мгновенно отправляет этот символ ВСЕМ подключённым пользователям
    emit('spin_started', {
        'finalChar': server_state['current_char']
    }, broadcast=True)

@socketio.on('spin_completed')
def handle_spin_completed():
    """Фиксация завершения анимации вращения"""
    server_state['status'] = 'stopped'

@socketio.on('request_reset')
def handle_reset():
    """Сброс состояния при нажатии на крестик"""
    server_state['status'] = 'idle'
    server_state['current_char'] = ''
    emit('state_reset', broadcast=True)

if __name__ == '__main__':
    # Render передаёт порт через переменные окружения PORT (по умолчанию 10000)
    port = int(os.environ.get('PORT', 10000))
    # allow_unsafe_werkzeug=True позволяет запускать веб-сервер на Render без ошибок
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
