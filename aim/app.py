import os
import time
from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__, template_folder='.')
app.config['SECRET_KEY'] = 'ai-music-secret'

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

system_state = {
    "track": 1,
    "status": "stop",  # 'stop', 'aim', 'orig'
    "start_time": 0.0
}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    socketio.emit('sync', {'state': system_state, 'server_time': time.time()})

@socketio.on('command')
def handle_command(data):
    global system_state
    
    action = data.get('action')
    track = data.get('track', system_state['track'])
    
    system_state['track'] = track
    
    if action == 'stop':
        system_state['status'] = 'stop'
    elif action == 'set_track':
        system_state['status'] = 'stop'
    elif action == 'play_aim':
        system_state['status'] = 'aim'
        system_state['start_time'] = time.time()
    elif action == 'play_orig':
        system_state['status'] = 'orig'
        system_state['start_time'] = time.time()

    socketio.emit('sync', {'state': system_state, 'server_time': time.time()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
