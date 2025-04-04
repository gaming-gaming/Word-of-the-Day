import asyncio
import datetime
from dateutil import tz
from flask import Flask, jsonify, send_from_directory
import json
import os
import subprocess
import sys
import threading

from wotd import query_queued

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')

with open(CONFIG_FILE, 'r') as f:
    config = json.load(f)
    PORT = config['port']

app = Flask(__name__, static_folder='www', static_url_path='')

global word
global ipa
global type
global definition
global date

word = ''
ipa = ''
type = ''
definition = ''
date = ''

def run_asyncio_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

async def update_wotd():
    global word
    global ipa
    global type
    global definition
    global date

    while True:
        # Wait for 8:00 AM PST
        now = datetime.datetime.now(datetime.timezone.utc)
        pst = tz.gettz('America/Los_Angeles')
        current_pst = now.astimezone(pst)
        next_8am_pst = current_pst.replace(hour=8, minute=0, second=0, microsecond=0)
        if current_pst >= next_8am_pst:
            next_8am_pst += datetime.timedelta(days=1)
        sleep_duration = (next_8am_pst - now).total_seconds()
        await asyncio.sleep(sleep_duration)

        # Update the word of the day
        word, ipa, type, definition, date = query_queued()

def query_wotd():
    '''Queries the word of the day.'''
    return word, ipa, type, definition, date

# Serve the index.html file
@app.route('/')
def index():
    return send_from_directory(os.path.join(app.static_folder), 'index.html')

# Serve the about.html file
@app.route('/about')
def about():
    return send_from_directory(os.path.join(app.static_folder), 'about.html')

"""
# Subscribe page
@app.route('/subscribe')
def subscribe():
    return send_from_directory(os.path.join(app.static_folder), 'subscribe.html')
"""

@app.route('/api/wotd', methods=['GET'])
def get_word_of_the_day():
    '''Returns the word of the day, IPA, type, and definition.'''
    return jsonify({
        'word': word,
        'ipa': ipa,
        'type': type,
        'definition': definition,
        'date': date
    })

@app.route('/api/wotd/word', methods=['GET'])
def get_word():
    '''Returns only the word of the day.'''
    return jsonify({'word': word})

@app.route('/api/wotd/ipa', methods=['GET'])
def get_ipa():
    '''Returns only the IPA of the word of the day.'''
    return jsonify({'ipa': ipa})

@app.route('/api/wotd/type', methods=['GET'])
def get_type():
    '''Returns only the type of the word of the day.'''
    return jsonify({'type': type})

@app.route('/api/wotd/definition', methods=['GET'])
def get_definition():
    '''Returns only the definition of the word of the day.'''
    return jsonify({'definition': definition})

@app.route('/api/wotd/date', methods=['GET'])
def get_date():
    '''Returns the date of the word of the day.'''
    return jsonify({'date': date})

update_wotd_loop = asyncio.new_event_loop()
update_wotd_thread = threading.Thread(target=run_asyncio_loop, args=(update_wotd_loop,))
update_wotd_thread.start()
asyncio.run_coroutine_threadsafe(update_wotd(), update_wotd_loop)

def run():
    from waitress import serve
    serve(app, host='0.0.0.0', port=PORT, threads=4, backlog=128)

"""
def run():
    if sys.platform.startswith('win'):
        from waitress import serve
        serve(app, host='0.0.0.0', port=PORT, threads=4, backlog=128)
    elif sys.platform.startswith('linux'):
        subprocess.Popen([
            'gunicorn', 
            '-w', '4',  # Number of workers
            '--threads', '4',  # Number of threads per worker
            '--backlog', '128',
            '-b', f'0.0.0.0:{PORT}', 
            f'{__name__}:app'
        ], env={**os.environ, 'PYTHONPATH': os.path.dirname(BASE_DIR)})"
"""

'''
# Run the server in a separate thread
thread = threading.Thread(target=run)
thread.daemon = True
thread.start()

# Run the asyncio event loop
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
loop.run_forever()
'''

# Run the server in a separate thread
server_thread = threading.Thread(target=run)
server_thread.daemon = True
server_thread.start()

# Run the asyncio event loop in a separate thread
def start_asyncio_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_forever()

asyncio_thread = threading.Thread(target=start_asyncio_loop)
asyncio_thread.daemon = True
asyncio_thread.start()