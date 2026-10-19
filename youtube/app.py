import os
import json
import urllib.request
import urllib.parse
import re
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'event_secret_key'

socketio = SocketIO(app, cors_allowed_origins="*")

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

@app.route('/api/search')
def youtube_search():
    query = request.args.get('q', '').strip()
    if not query:
        resp = jsonify([])
        resp.headers.add('Access-Control-Allow-Origin', '*')
        return resp

    try:
        url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
        
        # Подкидываем куки согласия, чтобы обойти заглушки 18+ и SafeSearch
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cookie': 'CONSENT=YES+cb.20230501-08-p0.ru+FX+343; PREF=hl=ru&gl=RU&f2=0'
        }
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=5) as response:
            html = response.read().decode('utf-8')

        match = re.search(r'var ytInitialData = (.*?);</script>', html)
        if not match:
            resp = jsonify([])
            resp.headers.add('Access-Control-Allow-Origin', '*')
            return resp

        data = json.loads(match.group(1))
        results = []
        
        contents = data.get('contents', {}).get('twoColumnSearchResultsRenderer', {}).get('primaryContents', {}).get('sectionListRenderer', {}).get('contents', [])
        
        for section in contents:
            items = section.get('itemSectionRenderer', {}).get('contents', [])
            for item in items:
                v_data = item.get('videoRenderer')
                if not v_data: continue

                video_id = v_data.get('videoId')
                if not video_id: continue
                
                title_runs = v_data.get('title', {}).get('runs', [])
                title = title_runs[0].get('text') if title_runs else 'Без названия'
                duration = v_data.get('lengthText', {}).get('simpleText', '')
                
                # ЖЕСТКИЙ ОБХОД ЗАБЛЮРЕННЫХ КАРТИНОК: берем raw-исходник напрямую по ID
                thumb_url = f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg'

                results.append({
                    'videoId': video_id, 
                    'title': title, 
                    'duration': duration, 
                    'thumbnail': thumb_url
                })

        resp = jsonify(results[:30])
        resp.headers.add('Access-Control-Allow-Origin', '*')
        return resp

    except Exception as e:
        print("Ошибка поиска:", str(e))
        resp = jsonify([])
        resp.headers.add('Access-Control-Allow-Origin', '*')
        return resp

@socketio.on('connect')
def on_connect():
    emit('sync', STATE)

@socketio.on('auth_pin')
def on_auth(data):
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
