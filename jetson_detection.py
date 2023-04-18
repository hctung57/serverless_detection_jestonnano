import os
import threading
import time
from cv2 import VideoCapture
from flask import Flask
from jetson.inference import detectNet
from jetson.utils import cudaFromNumpy

app = Flask(__name__)
IS_TERMINATE = False


@app.route('/api/stream/<source>/<int:time>', methods=['GET'])
def handle_streaming_thread_init(source, time):
    rtmp_streaming_url = source
    time_to_detect = time
    try:
        th = threading.Thread(target=detect_streaming, args=(
            rtmp_streaming_url, time_to_detect,))
        th.start()
    except:
        print("error when start thread")
    th.join()
    return 'OK', 200


@app.route('/api/stream/active/<source>/<int:time>', methods=['GET'])
def active_streaming_thread_init(source, time):
    rtmp_streaming_url = source
    time_to_detect = time
    try:
        threading.Thread(target=detect_streaming, args=(
            rtmp_streaming_url, time_to_detect,))
    except:
        print("error when start thread")
    return 'OK', 200


@app.route('/api/active', methods=['GET'])
def active_process():
    return 'Active process', 200


@app.route('/api/terminate', methods=['GET'])
def terminate_process():
    global IS_TERMINATE
    IS_TERMINATE = True
    os._exit(0)
    return
0


if __name__ == '__main__':
    net = detectNet("ssd-mobilenet-v2", threshold=0.5)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

