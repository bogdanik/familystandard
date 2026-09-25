import os
import json
import time
from flask import Flask, render_template, send_from_directory, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder='.', static_folder='.')
app.config['SECRET_KEY'] = 'aim-show-secret-2026'

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Состояние шоу
system_state = {
    "track": 1,
    "status": "stop",  # 'stop', 'aim', 'orig'
    "is_started": False,
    "start_time": 0,
    "seek_position": 0.0,
    "audio_volume": 0.8
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ping')
def ping():
    return jsonify({"status": "ok"}), 200

@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory('.', filename)

@socketio.on('connect')
def handle_connect():
    emit('sync', {'state': system_state, 'server_time': time.time()})

@socketio.on('login')
def handle_login(data):
    pin = str(data.get('pin', '')).strip()
    # Пин-код доступа (можешь поменять на свой)
    if pin == "111" or pin == "222" or pin == "":
        emit('login_response', {'success': True})
    else:
        emit('login_response', {'success': False, 'message': 'Неверный код'})

@socketio.on('command')
def handle_command(data):
    global system_state
    action = data.get('action')
    
    if action == 'start':
        system_state['is_started'] = True
    elif action == 'set_track':
        system_state['track'] = data.get('track', 1)
        system_state['status'] = 'stop'
        system_state['seek_position'] = 0.0
    elif action == 'play_aim':
        system_state['status'] = 'aim'
        system_state['start_time'] = time.time()
    elif action == 'play_orig':
        system_state['status'] = 'orig'
        system_state['start_time'] = time.time()
    elif action == 'stop':
        system_state['status'] = 'stop'
        system_state['seek_position'] = 0.0
        
    socketio.emit('update', {'state': system_state, 'server_time': time.time()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
