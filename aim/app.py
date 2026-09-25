import os
import time
from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__, template_folder='.')
app.config['SECRET_KEY'] = 'ai-vinyl-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Единый простой стейт для всех
state = {
    "track": 1,
    "status": "stop",  # 'stop', 'aim', 'orig'
    "start_time": 0.0
}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    socketio.emit('sync', {'state': state, 'server_time': time.time()})

@socketio.on('command')
def handle_command(data):
    global state
    
    action = data.get('action')
    state['track'] = data.get('track', state['track'])
    
    if action == 'stop' or action == 'set_track':
        state['status'] = 'stop'
    elif action == 'play_aim':
        state['status'] = 'aim'
        state['start_time'] = time.time()
    elif action == 'play_orig':
        state['status'] = 'orig'
        state['start_time'] = time.time()

    # Моментально раздаем команду всем
    socketio.emit('sync', {'state': state, 'server_time': time.time()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
