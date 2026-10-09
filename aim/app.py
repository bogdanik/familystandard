from flask import Flask, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Исходное состояние интерактива
def get_initial_state():
    return {
        "round": 0,              # 0 = режим ожидания, 1-12 = обычные раунды, 13 = бонус
        "track": None,          # 'aim', 'm' или 'bonus'
        "playing": False,        # Воспроизводится ли трек
        "trigger_animation": False,
        "admin_sid": None        # Socket ID ведущего
    }

game_state = get_initial_state()

@socketio.on('connect')
def handle_connect():
    emit('state_update', game_state)

@socketio.on('request_start')
def handle_request_start():
    global game_state
    
    # Первый нажавший становится Админом
    if game_state["round"] == 0 or game_state["admin_sid"] is None:
        game_state["admin_sid"] = request.sid
        game_state["round"] = 1
        game_state["playing"] = False
        game_state["track"] = None
        game_state["trigger_animation"] = True
        
        emit('role_assigned', {'is_admin': True}, room=request.sid)
    else:
        # Остальные — Зрители
        emit('role_assigned', {'is_admin': False}, room=request.sid)

    emit('state_update', game_state, broadcast=True)

# Глобальный сброс состояния по запросу с любого экрана
@socketio.on('request_reset')
def handle_request_reset():
    global game_state
    game_state = get_initial_state()
    emit('state_update', game_state, broadcast=True)

@socketio.on('admin_command')
def handle_admin_command(data):
    global game_state
    
    # Игнорируем команды не от админа
    if request.sid != game_state["admin_sid"]:
        return

    action = data.get('action')

    if action == 'next_round':
        if game_state['round'] <= 12:
            game_state['round'] += 1
            game_state['playing'] = False
            game_state['track'] = None
            game_state['trigger_animation'] = True
    elif action == 'end_game':
        game_state = get_initial_state()
    elif action == 'play':
        game_state['track'] = data.get('track')
        game_state['playing'] = True
        game_state['trigger_animation'] = False
    elif action == 'pause':
        game_state['playing'] = False
        game_state['trigger_animation'] = False

    emit('state_update', game_state, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    global game_state
    if request.sid == game_state["admin_sid"]:
        game_state["admin_sid"] = None

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000, allow_unsafe_werkzeug=True)
