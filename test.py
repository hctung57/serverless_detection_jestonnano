from flask import Flask
import os
import time
app = Flask(__name__)

@app.route('/api/test', methods=['GET'])
def handle_streaming_thread_init():
    time.sleep(5)
    return 'OK', 200

@app.route('/api/active', methods=['GET'])
def active_process():
    return 'Active process', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
