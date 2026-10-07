import os
from flask import Flask, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'family_standard_event_os_2026'

# CORS открыт для внешних подключений
socketio = SocketIO(app, cors_allowed_origins="*")

# Глобальный кадр состояния
game_state = {
    'screen': 'screen-intro',
    'round': 0,
    'rules_overlay': False
}

@app.route('/')
def status():
    return jsonify({
        "status": "online",
        "service": "Kviz Render State Manager",
        "current_state": game_state
    })

@socketio.on('connect')
def handle_connect():
    emit('state_update', game_state)

@socketio.on('action')
def handle_action(data):
    action_type = data.get('type')
    
    if action_type == 'go_to_screen':
        game_state['screen'] = data.get('screen', 'screen-intro')
        socketio.emit('state_update', game_state)

    elif action_type == 'start_quiz':
        game_state['round'] = 0
        game_state['screen'] = 'screen-round-title'
        socketio.emit('state_update', game_state)
        
        socketio.sleep(3)
        if game_state['screen'] == 'screen-round-title':
            game_state['screen'] = 'screen-question'
            socketio.emit('state_update', game_state)

    elif action_type == 'next_round':
        game_state['round'] += 1
        if game_state['round'] < 7:
            game_state['screen'] = 'screen-round-title'
            socketio.emit('state_update', game_state)
            
            socketio.sleep(3)
            if game_state['screen'] == 'screen-round-title':
                game_state['screen'] = 'screen-question'
                socketio.emit('state_update', game_state)
        else:
            game_state['screen'] = 'screen-final'
            socketio.emit('state_update', game_state)

    elif action_type == 'prev_step':
        if game_state['screen'] == 'screen-options':
            game_state['screen'] = 'screen-question'
        elif game_state['screen'] == 'screen-question':
            if game_state['round'] > 0:
                game_state['round'] -= 1
                game_state['screen'] = 'screen-options'
            else:
                game_state['screen'] = 'screen-rules'
        socketio.emit('state_update', game_state)

    elif action_type == 'show_options':
        game_state['screen'] = 'screen-options'
        socketio.emit('state_update', game_state)

    elif action_type == 'peek_question':
        game_state['screen'] = 'screen-question'
        socketio.emit('state_update', game_state)
        
        socketio.sleep(2.5)
        if game_state['screen'] == 'screen-question':
            game_state['screen'] = 'screen-options'
            socketio.emit('state_update', game_state)

    elif action_type == 'toggle_rules':
        game_state['rules_overlay'] = not game_state['rules_overlay']
        socketio.emit('state_update', game_state)

    elif action_type == 'reset':
        game_state['round'] = 0
        game_state['screen'] = 'screen-intro'
        game_state['rules_overlay'] = False
        socketio.emit('state_update', game_state)

if __name__ == '__main__':
    # Render автоматически передает порт через системную переменную PORT (по умолчанию 10000)
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port)
