from flask import Flask
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

game_state = {
    "round": 0,
    "track": None,
    "playing": False,
    "trigger_animation": False
}

@socketio.on('connect')
def handle_connect():
    emit('state_update', game_state)

@socketio.on('admin_command')
def handle_admin_command(data):
    global game_state
    action = data.get('action')

    if action == 'next_round' or action == 'start_game':
        if game_state['round'] < 12:
            game_state['round'] += 1
        game_state['playing'] = False
        game_state['track'] = None
        game_state['trigger_animation'] = True
    elif action == 'play':
        game_state['track'] = data.get('track')
        game_state['playing'] = True
        game_state['trigger_animation'] = False
    elif action == 'pause':
        game_state['playing'] = False
        game_state['trigger_animation'] = False

    emit('state_update', game_state, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000)
