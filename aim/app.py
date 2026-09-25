import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

# template_folder='.' говорит Фласку искать HTML в этой же папке
app = Flask(__name__, template_folder='.')
app.config['SECRET_KEY'] = 'super-secret-show-key'

# async_mode='eventlet' нужен для корректной работы сокетов на сервере
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('admin_command')
def handle_admin_command(data):
    # Рассылаем команду всем подключенным экранам
    emit('viewer_action', data, broadcast=True)

if __name__ == '__main__':
    # Render сам выдает нужный порт через переменные окружения
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port)
