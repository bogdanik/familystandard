import os
import json
import urllib.request
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'event_secret_key'

socketio = SocketIO(app, cors_allowed_origins="*")

# 3 режима работы: idle (заставка), video (плеер), search (меню поиска)
STATE = {
    'mode': 'idle',
    'videoId': None,
    'action': 'pause',
    'time': 0,
    'searchQuery': '',
    'searchResults': []
}

@app.route('/')
def index():
    return jsonify({"status": "Server running", "mode": STATE['mode']})

# Парсер YouTube с CORS-заголовком (чтобы браузер не блокировал поиск)
@app.route('/api/search')
def youtube_search():
    query = request.args.get('q', '').strip()
    if not query:
        resp = jsonify([])
        resp.headers.add('Access-Control-Allow-Origin', '*')
        return resp

    url = 'https://www.youtube.com/youtubei/v1/search'
    payload = {
        "context": {"client": {"clientName": "WEB", "clientVersion": "2.20240101.00.00", "hl": "ru", "gl": "RU"}},
        "query": query
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            res_data = json.loads(response.read().decode('utf-8'))

        results = []
        contents = res_data.get('contents', {}).get('twoColumnSearchResultsRenderer', {}).get('primaryContents', {}).get('sectionListRenderer', {}).get('contents', [])
        for section in contents:
            items = section.get('itemSectionRenderer', {}).get('contents', [])
            for item in items:
                v_data = item.get('videoRenderer')
                if not v_data: continue

                video_id = v_data.get('videoId')
                title_runs = v_data.get('title', {}).get('runs', [])
                title = title_runs[0].get('text') if title_runs else 'Без названия'
                duration = v_data.get('lengthText', {}).get('simpleText', '')
                
                thumbnails = v_data.get('thumbnail', {}).get('thumbnails', [])
                thumb_url = thumbnails[-1].get('url') if thumbnails else f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg'

                if video_id:
                    results.append({'videoId': video_id, 'title': title, 'duration': duration, 'thumbnail': thumb_url})

        resp = jsonify(results[:30])
        resp.headers.add('Access-Control-Allow-Origin', '*')
        return resp
    except Exception as e:
        print("Search error:", str(e))
        resp = jsonify([])
        resp.headers.add('Access-Control-Allow-Origin', '*')
        return resp

@socketio.on('connect')
def on_connect():
    emit('sync', STATE)

@socketio.on('auth_pin')
def on_auth(data):
    # Теперь пускаем вообще всех без пароля
    emit('auth_result', {'success': True})
    emit('sync', STATE)

@socketio.on('host_action')
def on_host_action(data):
    global STATE
    STATE['mode'] = 'video'
    STATE['videoId'] = data.get('videoId')
    STATE['action'] = data.get('action')
    STATE['time'] = data.get('time', 0)
    emit('sync', STATE, broadcast=True, include_self=False)

@socketio.on('host_search')
def on_host_search(data):
    global STATE
    STATE['mode'] = 'search'
    STATE['searchQuery'] = data.get('query', '')
    STATE['searchResults'] = data.get('results', [])
    emit('sync', STATE, broadcast=True, include_self=False)

@socketio.on('clear_screen')
def on_clear():
    global STATE
    STATE = {'mode': 'idle', 'videoId': None, 'action': 'pause', 'time': 0, 'searchQuery': '', 'searchResults': []}
    emit('sync', STATE, broadcast=True)

@socketio.on('full_reset')
def on_full_reset():
    global STATE
    STATE = {'mode': 'idle', 'videoId': None, 'action': 'pause', 'time': 0, 'searchQuery': '', 'searchResults': []}
    emit('force_reload', broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
