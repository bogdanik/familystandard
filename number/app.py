import os
import random
from flask import Flask
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key_here'

# Разрешаем CORS для подключения с GitHub Pages
socketio = SocketIO(app, cors_allowed_origins="*")

CHARACTERS = [
    'А','Б','В','Г','Д','Е','Ё','Ж','З','И','Й','К','Л','М','Н','О','П','Р','С','Т','У','Ф','Х','Ц','Ч','Ш','Щ','Ъ','Ы','Ь','Э','Ю','Я',
    'A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z',
    '0','1','2','3','4','5','6','7','8','9'
]

server_state = {
    'status': 'idle',
    'current_char': ''
}

@socketio.on('connect')
def handle_connect():
    emit('sync_state', server_state)

@socketio.on('request_spin')
def handle_spin():
    if server_state['status'] == 'spinning':
        return

    server_state['status'] = 'spinning'
    server_state['current_char'] = random.choice(CHARACTERS)

    emit('spin_started', {
        'finalChar': server_state['current_char']
    }, broadcast=True)

@socketio.on('spin_completed')
def handle_spin_completed():
    server_state['status'] = 'stopped'

@socketio.on('request_reset')
def handle_reset():
    server_state['status'] = 'idle'
    server_state['current_char'] = ''
    emit('state_reset', broadcast=True)

if __name__ == '__main__':
    # На Render по умолчанию используется порт 10000
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port)
