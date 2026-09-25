import os
import time
from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__, template_folder='.')
app.config['SECRET_KEY'] = 'ai-vinyl-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Стейт точно как в Event OS
system_state = {
    "track_id": 1,
    "track_type": "",  # 'aim' или 'orig'
    "is_playing": False,
    "seek_position": 0.0
}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    socketio.emit('state_update', system_state)

@socketio.on('command')
def handle_command(data):
    global system_state
    
    action = data.get('action')
    system_state['track_id'] = data.get('track', system_state['track_id'])
    
    if action == 'stop' or action == 'set_track':
        system_state['is_playing'] = False
        system_state['seek_position'] = 0.0
    elif action == 'play_aim':
        system_state['track_type'] = 'aim'
        system_state['is_playing'] = True
        system_state['seek_position'] = 0.0
    elif action == 'play_orig':
        system_state['track_type'] = 'orig'
        system_state['is_playing'] = True
        system_state['seek_position'] = 0.0

    socketio.emit('state_update', system_state)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
