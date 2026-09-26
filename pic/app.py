import os
import random
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

# template_folder='.' позволяет держать index.html прямо в корне проекта без подпапки templates
app = Flask(__name__, template_folder='.', static_folder='.')
app.config['SECRET_KEY'] = 'family_standard_chocolate_2026'
socketio = SocketIO(app, cors_allowed_origins="*")

# Состояние сессии
state = {
    'admin_sid': None,
    'current_slide': 0,    # 0 = Заставка (СТАРТ), 1..20 = Картинки
    'total_slides': 20,
    'auto_play': False,
    'is_random': False
}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    is_admin = (request.sid == state['admin_sid'])
    emit('init_state', {
        'current_slide': state['current_slide'],
        'total_slides': state['total_slides'],
        'is_admin': is_admin,
        'has_admin': state['admin_sid'] is not None,
        'auto_play': state['auto_play'],
        'is_random': state['is_random']
    })

@socketio.on('start_session')
def handle_start():
    if state['admin_sid'] is None or state['current_slide'] == 0:
        state['admin_sid'] = request.sid
        state['current_slide'] = 1
        emit('session_started', {
            'current_slide': state['current_slide'],
            'admin_sid': state['admin_sid']
        }, broadcast=True)

@socketio.on('change_slide')
def handle_change_slide(data):
    if request.sid != state['admin_sid']:
        return

    action = data.get('action')
    
    if action == 'next':
        if state['is_random']:
            candidates = [i for i in range(1, state['total_slides'] + 1) if i != state['current_slide']]
            if candidates:
                state['current_slide'] = random.choice(candidates)
        else:
            if state['current_slide'] < state['total_slides']:
                state['current_slide'] += 1
    elif action == 'prev':
        if state['current_slide'] > 1:
            state['current_slide'] -= 1
    elif isinstance(action, int) and 1 <= action <= state['total_slides']:
        state['current_slide'] = action

    effect_index = (state['current_slide'] % 3)

    emit('slide_updated', {
        'current_slide': state['current_slide'],
        'effect_type': effect_index
    }, broadcast=True)

@socketio.on('toggle_autoplay')
def handle_toggle_autoplay(data):
    if request.sid != state['admin_sid']:
        return
    state['auto_play'] = data.get('auto_play', False)
    emit('autoplay_updated', {'auto_play': state['auto_play']}, broadcast=True)

@socketio.on('toggle_random')
def handle_toggle_random(data):
    if request.sid != state['admin_sid']:
        return
    state['is_random'] = data.get('is_random', False)
    emit('random_updated', {'is_random': state['is_random']}, broadcast=True)

@socketio.on('reset_session')
def handle_reset():
    if request.sid != state['admin_sid']:
        return
    state['admin_sid'] = None
    state['current_slide'] = 0
    state['auto_play'] = False
    state['is_random'] = False
    emit('session_reset', {}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000, allow_unsafe_werkzeug=True)
