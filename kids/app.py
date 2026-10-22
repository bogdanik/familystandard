import os
import json
from flask import Flask, render_template, send_from_directory, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder='.', static_folder='.')
app.config['SECRET_KEY'] = 'kids-sound-control-2026'

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

def load_config():
    try:
        with open('event_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading event_data.json: {e}")
        return {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/config')
def get_config():
    return jsonify(load_config())

@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory('.', filename)

@socketio.on('connect')
def handle_connect():
    config = load_config()
    emit('config_data', config)

@socketio.on('reload_config')
def handle_reload():
    config = load_config()
    emit('config_data', config, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
