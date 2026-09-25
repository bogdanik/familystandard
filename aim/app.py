import os
import time
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder='.')
app.config['SECRET_KEY'] = 'super-secret-show-key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Глобальная память сервера
show_state = {
    'is_running': False,
    'current_track': 1,
    'status': 'stopped', # 'stopped', 'playing_aim', 'playing_orig'
    'start_time': 0
}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    # Когда кто-то открывает ссылку, отдаем ему текущее состояние шоу
    emit('sync_state', {
        'state': show_state,
        'server_time': time.time()
    })

@socketio.on('admin_command')
def handle_admin_command(data):
    global show_state
    action = data.get('action')
    
    if action == 'start_show':
        show_state['is_running'] = True
    elif action == 'next_track':
        show_state['current_track'] = data.get('trackNum', 1)
        show_state['status'] = 'stopped'
    elif action == 'play_aim':
        show_state['status'] = 'playing_aim'
        show_state['start_time'] = time.time()
    elif action == 'play_orig':
        show_state['status'] = 'playing_orig'
        show_state['start_time'] = time.time()
    elif action == 'stop_audio':
        show_state['status'] = 'stopped'

    # Пересылаем команду всем экранам
    emit('viewer_action', data, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port)
