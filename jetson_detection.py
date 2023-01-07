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


def detect_streaming(rtmp_streaming_url: str, time_to_detect: int):
    path = f"rtmp://{rtmp_streaming_url}/live/stream"
    cap = VideoCapture(path)
    start_time = time.monotonic()
    frame_number = 0
    while (True):
        ret, frame = cap.read()
        if ret == True:
            frame_number += 1
            print("** HANDLE FRAME NUMBER : {}\n***TIMESTAMP: {}".format(
                frame_number, time.strftime("%Y%m%d-%H%M%S")))
            cuda_frame = cudaFromNumpy(frame)
            detections = net.Detect(cuda_frame)
            for detection in detections:
                print(detection)
            if time.monotonic() - start_time > time_to_detect or IS_TERMINATE:
                break
    cap.release()
    return


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
    net = detectNet("ssd-mobilenet-v2", threshold=0.5)
