import sys
import argparse
import os
import threading
import time
import numpy as np
import warnings
import cv2
import jsonpickle
from flask import Flask, request, Response
from jetson.inference import detectNet
from jetson.utils import videoSource, cudaFromNumpy, saveImage

app = Flask(__name__)
warnings.simplefilter("ignore", DeprecationWarning)


@app.route('/api/image', methods=['POST'])
def handle_image_thread_init():
    print()
    print()
    request_json = request
    try:
        threading.Thread(target=detect_image, args=(
            request_json.data,)).start()
    except:
        print("error")
    return 'OK', 200


def detect_image(jsonData):
    output_filename = "img/image-{}.jpg".format(time.strftime("%Y%m%d-%H%M%S"))
    print("Image handle request: {}".format(
        time.strftime("%d/%m/%Y %H:%M:%S")))
    # convert string of image data to uint8
    nparr = np.fromstring(jsonData, np.uint8)
    # decode image
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    height = image.shape[0]
    width = image.shape[1]
    # convert to cuda Image format
    cuda_image = cudaFromNumpy(image)
    print("Output file: {}".format(output_filename))
    detections = net.Detect(cuda_image, overlay="box,labels,conf")
    for detection in detections:
        print(detection)
    saveImage(output_filename, cuda_image, width, height)

    # build a response dict to send back to client
    response = {'message': 'image received. size={}x{}'.format(image.shape[1], image.shape[0])
                }
    # encode response using jsonpickle
    response_pickled = jsonpickle.encode(response)

    return Response(response=response_pickled, status=200, mimetype="application/json")


@app.route('/api/stream/<source>/<int:time>', methods=['GET'])
def handle_streaming_thread_init(source, time):
    rtmp_streaming_url = source
    time_to_detect = time
    try:
        threading.Thread(target=detect_streaming, args=(
            rtmp_streaming_url,time_to_detect,)).start()
    except:
        print("error")
    return 'OK', 200


def detect_streaming(rtmp_streaming_url: str, time_to_detect: int):
    path = f"rtmp://{rtmp_streaming_url}/live/stream"
    cap = cv2.VideoCapture(path)
    start_time = time.monotonic()
    frame_number = 0
    while (True):
        ret, frame = cap.read()
        if ret == True:
            frame_number += 1
            print("** HANDLE FRAME NUMBER : {}\n***TIMESTAMP: {}".format(
                frame_number,time.strftime("%Y%m%d-%H%M%S")))
            cuda_frame = cudaFromNumpy(frame)
            detections = net.Detect(cuda_frame, overlay="box,labels,conf")
            for detection in detections:
                print(detection)
            if time.monotonic() - start_time > time_to_detect:
                break
            if cv2.waitKey(1) & 0xFF == ord('s'):
                break
    cap.release()
    # Closes all the frames
    cv2.destroyAllWindows()
    return


if __name__ == '__main__':
    net = detectNet("ssd-mobilenet-v2", threshold=0.5)
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
