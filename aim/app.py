from flask import Flask
from flask_socketio import SocketIO, emit
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
# Разрешаем подключения с любых доменов
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Глобальное состояние интерактива
game_state = {
    "round": 1,
    "track": None,    # 'aim' или 'm'
    "playing": False, # играет или на паузе
    "trigger_animation": False # флаг для запуска анимации раунда
}

@socketio.on('connect')
def handle_connect():
    # При подключении (зрителя или админа) сразу отдаем текущее состояние
    emit('state_update', game_state)

@socketio.on('admin_command')
def handle_admin_command(data):
    global game_state
    action = data.get('action')

    if action == 'next_round':
        if game_state['round'] < 12:
            game_state['round'] += 1
        game_state['playing'] = False
        game_state['track'] = None
        game_state['trigger_animation'] = True # Запускаем анимацию на экранах
    elif action == 'play':
        game_state['track'] = data.get('track')
        game_state['playing'] = True
        game_state['trigger_animation'] = False
    elif action == 'pause':
        game_state['playing'] = False
        game_state['trigger_animation'] = False

    # Рассылаем обновленное состояние всем зрителям и самому админу
    emit('state_update', game_state, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000)
