import os
import time
from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder='.', static_folder='.')
app.config['SECRET_KEY'] = 'karaoke_sync_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Глобальное состояние сессии
audio_state = {
    'is_playing': False,
    'current_time': 0.0,
    'last_update': time.time()
}

def get_synced_time():
    """Вычисляет реальное время трека для вновь зашедших пользователей"""
    if audio_state['is_playing']:
        elapsed = time.time() - audio_state['last_update']
        return audio_state['current_time'] + elapsed
    return audio_state['current_time']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/lyrics.json')
def get_lyrics():
    return send_from_directory('.', 'lyrics.json')

@socketio.on('connect')
def handle_connect():
    """Передаёт синхронизированное состояние новому подключившемуся клиенту"""
    emit('sync_state', {
        'is_playing': audio_state['is_playing'],
        'current_time': get_synced_time()
    })

@socketio.on('play_audio')
def handle_play(data):
    audio_state['is_playing'] = True
    audio_state['current_time'] = float(data.get('current_time', 0.0))
    audio_state['last_update'] = time.time()
    
    emit('sync_state', {
        'is_playing': True,
        'current_time': audio_state['current_time']
    }, broadcast=True)

@socketio.on('pause_audio')
def handle_pause(data):
    audio_state['is_playing'] = False
    audio_state['current_time'] = float(data.get('current_time', 0.0))
    audio_state['last_update'] = time.time()
    
    emit('sync_state', {
        'is_playing': False,
        'current_time': audio_state['current_time']
    }, broadcast=True)

@socketio.on('reset_audio')
def handle_reset():
    audio_state['is_playing'] = False
    audio_state['current_time'] = 0.0
    audio_state['last_update'] = time.time()
    
    emit('sync_state', {
        'is_playing': False,
        'current_time': 0.0
    }, broadcast=True)

if __name__ == '__main__':
    # Render автоматически передаёт переменную PORT (по умолчанию 10000)
    port = int(os.environ.get('PORT', 10000))
    # allow_unsafe_werkzeug=True отключает RuntimeError при запуске через python app.py
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
