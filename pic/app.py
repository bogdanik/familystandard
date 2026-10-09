import os
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder='.', static_folder='.')
app.config['SECRET_KEY'] = 'family_standard_center_stack_2026'
socketio = SocketIO(app, cors_allowed_origins="*")

state = {
    'admin_sid': None,
    'current_slide': 0,    # 0 = Заставка (СТАРТ), 1..20 = Слайд-шоу
    'total_slides': 20,
    'auto_play': False,
    'media_type': 'photo', # 'photo' или 'video'
    'video_id': 1
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
        'media_type': state['media_type'],
        'video_id': state['video_id']
    })

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid == state['admin_sid']:
        state['admin_sid'] = None
        emit('admin_status_changed', {'has_admin': False}, broadcast=True)

@socketio.on('start_session')
def handle_start():
    if state['admin_sid'] is None or state['current_slide'] == 0:
        state['admin_sid'] = request.sid
        state['current_slide'] = 1
        state['media_type'] = 'photo'
        emit('session_started', {
            'current_slide': state['current_slide'],
            'admin_sid': state['admin_sid']
        }, broadcast=True)

@socketio.on('change_slide')
def handle_change_slide(data):
    if request.sid != state['admin_sid']:
        return

    media_type = data.get('media_type', 'photo')
    
    if media_type == 'video':
        state['media_type'] = 'video'
        state['video_id'] = data.get('video_id', 1)
    else:
        state['media_type'] = 'photo'
        action = data.get('action')
        
        if action == 'next':
            if state['current_slide'] < state['total_slides']:
                state['current_slide'] += 1
            else:
                state['current_slide'] = 1
        elif action == 'prev':
            if state['current_slide'] > 1:
                state['current_slide'] -= 1
            else:
                state['current_slide'] = state['total_slides']
        elif isinstance(action, int) and 1 <= action <= state['total_slides']:
            state['current_slide'] = action

    emit('slide_updated', {
        'current_slide': state['current_slide'],
        'media_type': state['media_type'],
        'video_id': state['video_id']
    }, broadcast=True)

@socketio.on('toggle_autoplay')
def handle_toggle_autoplay(data):
    if request.sid != state['admin_sid']:
        return
    state['auto_play'] = data.get('auto_play', False)
    emit('autoplay_updated', {'auto_play': state['auto_play']}, broadcast=True)

@socketio.on('reset_session')
def handle_reset():
    state['admin_sid'] = None
    state['current_slide'] = 0
    state['auto_play'] = False
    state['media_type'] = 'photo'
    emit('session_reset', {}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000, allow_unsafe_werkzeug=True)
