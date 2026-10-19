import os
import json
import urllib.request
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'familystandard_secret_key'

socketio = SocketIO(app, cors_allowed_origins="*")

SECRET_PIN = "7777"  # Ваш ПИН-код ведущего

current_state = {
    'videoId': None,
    'action': 'pause',
    'time': 0
}

@app.route('/')
def health_check():
    return jsonify({"status": "online", "service": "Family Standard Universal Backend"})

# Прямой поиск по всей базе YouTube через внутренний API Google (без сторонних сайтов)
@app.route('/api/search')
def youtube_search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])

    url = 'https://www.youtube.com/youtubei/v1/search'
    payload = {
        "context": {
            "client": {
                "clientName": "WEB",
                "clientVersion": "2.20240101.00.00",
                "hl": "ru",
                "gl": "RU"
            }
        },
        "query": query
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            res_data = json.loads(response.read().decode('utf-8'))

        results = []
        contents = res_data.get('contents', {}).get('twoColumnSearchResultsRenderer', {}).get('primaryContents', {}).get('sectionListRenderer', {}).get('contents', [])
        
        for section in contents:
            items = section.get('itemSectionRenderer', {}).get('contents', [])
            for item in items:
                v_data = item.get('videoRenderer')
                if not v_data:
                    continue

                video_id = v_data.get('videoId')
                title_runs = v_data.get('title', {}).get('runs', [])
                title = title_runs[0].get('text') if title_runs else 'Без названия'

                channel_runs = v_data.get('ownerText', {}).get('runs', [])
                channel = channel_runs[0].get('text') if channel_runs else ''

                duration = v_data.get('lengthText', {}).get('simpleText', '')
                thumbnails = v_data.get('thumbnail', {}).get('thumbnails', [])
                thumb_url = thumbnails[-1].get('url') if thumbnails else f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg'

                if video_id:
                    results.append({
                        'videoId': video_id,
                        'title': title,
                        'channel': channel,
                        'duration': duration,
                        'thumbnail': thumb_url
                    })

        return jsonify(results[:20])
    except Exception as e:
        print("Search error:", str(e))
        return jsonify([])

@socketio.on('connect')
def handle_connect():
    if current_state['videoId']:
        emit('sync_to_viewers', current_state)

@socketio.on('auth_pin')
def handle_auth(data):
    if str(data.get('pin')).strip() == SECRET_PIN:
        emit('auth_result', {'success': True})
        if current_state['videoId']:
            emit('sync_to_viewers', current_state)
    else:
        emit('auth_result', {'success': False, 'message': 'Неверный ПИН-код'})

@socketio.on('host_control')
def handle_host_control(data):
    global current_state
    current_state['videoId'] = data.get('videoId')
    current_state['action'] = data.get('action', 'play')
    current_state['time'] = data.get('time', 0)

    emit('sync_to_viewers', current_state, broadcast=True, include_self=False)

@socketio.on('clear_screen')
def handle_clear_screen():
    global current_state
    current_state = {'videoId': None, 'action': 'pause', 'time': 0}
    emit('sync_to_viewers', current_state, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
