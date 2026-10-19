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

STATE = {'mode': 'idle', 'videoId': None, 'action': 'pause', 'time': 0, 'searchQuery': '', 'searchResults': []}

@app.route('/')
def index():
    return jsonify({"status": "Server running", "mode": STATE['mode']})

@app.route('/api/search')
def youtube_search():
    query = request.args.get('q', '').strip()
    resp = jsonify([])
    resp.headers.add('Access-Control-Allow-Origin', '*')
    if not query: return resp

    try:
        url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
        # PREF=f2=0 отключает безопасный поиск для максимизации выдачи
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'ru-RU,ru;q=0.9',
            'Cookie': 'PREF=f2=0; CONSENT=YES+cb.20210328-17-p0.ru+FX+343'
        }
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=5) as response:
            html = response.read().decode('utf-8')

        match = re.search(r'var ytInitialData = (.*?);</script>', html)
        if not match: return resp

        data = json.loads(match.group(1))
        results = []
        contents = data.get('contents', {}).get('twoColumnSearchResultsRenderer', {}).get('primaryContents', {}).get('sectionListRenderer', {}).get('contents', [])
        
        for section in contents:
            for item in section.get('itemSectionRenderer', {}).get('contents', []):
                v_data = item.get('videoRenderer')
                if not v_data or not v_data.get('videoId'): continue

                video_id = v_data.get('videoId')
                title = v_data.get('title', {}).get('runs', [{}])[0].get('text', 'Без названия')
                duration = v_data.get('lengthText', {}).get('simpleText', '')
                
                results.append({
                    'videoId': video_id, 
                    'title': title, 
                    'duration': duration, 
                    'thumbnail': f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg'
                })

        resp = jsonify(results[:30])
        resp.headers.add('Access-Control-Allow-Origin', '*')
        return resp
    except Exception as e:
        print("Search error:", str(e))
        return resp

@socketio.on('connect')
def on_connect(): emit('sync', STATE)

@socketio.on('auth_pin')
def on_auth(data):
    emit('auth_result', {'success': True})
    emit('sync', STATE)

@socketio.on('host_action')
def on_host_action(data):
    global STATE
    STATE.update({'mode': 'video', 'videoId': data.get('videoId'), 'action': data.get('action'), 'time': data.get('time', 0)})
    emit('sync', STATE, broadcast=True, include_self=False)

@socketio.on('host_search')
def on_host_search(data):
    global STATE
    STATE.update({'mode': 'search', 'searchQuery': data.get('query', ''), 'searchResults': data.get('results', [])})
    emit('sync', STATE, broadcast=True, include_self=False)

@socketio.on('clear_screen')
@socketio.on('full_reset')
def on_full_reset():
    global STATE
    STATE = {'mode': 'idle', 'videoId': None, 'action': 'pause', 'time': 0, 'searchQuery': '', 'searchResults': []}
    emit('force_reload' if request.event["message"] == 'full_reset' else 'sync', STATE, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
