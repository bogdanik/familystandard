import os
from flask import Flask, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'event_secret_key'

socketio = SocketIO(app, cors_allowed_origins="*")

STATE = {
    'videoId': None,
    'action': 'pause',
    'time': 0
}

@app.route('/')
def index():
    return jsonify({"status": "Server running", "video": STATE['videoId']})

@socketio.on('connect')
def on_connect():
    if STATE['videoId']:
        emit('sync', STATE)

# Авторизация в 1 клик (без ПИН-кода)
@socketio.on('auth_pin')
def on_auth(data):
    emit('auth_result', {'success': True})
    if STATE['videoId']:
        emit('sync', STATE)

@socketio.on('host_action')
def on_host_action(data):
    global STATE
    STATE['videoId'] = data.get('videoId')
    STATE['action'] = data.get('action')
    STATE['time'] = data.get('time', 0)
    emit('sync', STATE, broadcast=True, include_self=False)

@socketio.on('clear_screen')
def on_clear():
    global STATE
    STATE = {'videoId': None, 'action': 'pause', 'time': 0}
    emit('sync', STATE, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
