import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder='.')
app.config['SECRET_KEY'] = 'super-secret-show-key'

# Переключили на gevent для стабильной работы на Render
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('admin_command')
def handle_admin_command(data):
    emit('viewer_action', data, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port)
