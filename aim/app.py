import os
import time
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder='.')
app.config['SECRET_KEY'] = 'super-secret-show'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Серверная память состояний
state = {
    'is_started': False,
    'track': 1,
    'status': 'stop', # варианты: 'stop', 'aim', 'orig'
    'start_time': 0
}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def on_connect():
    # Как только любой зритель или админ открывает страницу,
    # отдаем ему текущее состояние лобби и серверное время для синхронизации
    emit('sync', {'state': state, 'server_time': time.time()})

@socketio.on('command')
def on_command(data):
    global state
    action = data.get('action')
    
    if action == 'start':
        state['is_started'] = True
    elif action == 'next':
        state['track'] = data.get('track', 1)
        state['status'] = 'stop'
    elif action == 'play_aim':
        state['status'] = 'aim'
        state['start_time'] = time.time()
    elif action == 'play_orig':
        state['status'] = 'orig'
        state['start_time'] = time.time()
    elif action == 'stop':
        state['status'] = 'stop'
        
    # Рассылаем обновление всем (зрителям и админу)
    emit('update', {'state': state, 'server_time': time.time()}, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port)
