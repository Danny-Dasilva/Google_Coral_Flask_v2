# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse

import logging
from flask import Flask, render_template, url_for, Response, request
import signal
import threading
import queue
from camera import make_camera
from streaming.server import StreamingServer
from geventwebsocket.handler import WebSocketHandler
from gevent.pywsgi import WSGIServer
from flask_sockets import Sockets


app = Flask(__name__)
sockets = Sockets(app)

q = queue.Queue(maxsize=150)
def svg(q):
    while True:  
        c = q.get()
        yield c
@app.route('/')
def init():
    return render_template('index.html')
@app.route('/bytestream')
def byte():
        return Response(svg(q), content_type='text/event-stream')


@sockets.route('/stream')
def stream(socket):
    t = svg(q)
    for buffer in t:
        if buffer:
            
            socket.send(buffer)


# @sockets.route('/stream')
# def stream(socket):
#     # t = svg(q)
#     # for buffer in t:
#     #     if buffer:
#     buffer = b'\x82\x0e\n\x06\x08\x80\x05\x10\xe0\x03P\x81\xe1\xbf\xff\x0f'
#     buffer = b'\x82)\x1a!\n\x1f\x00\x00\x00\x01gB\xc0\x1e\xda\x02\x80\xf6\xc0Z\x83\x00\x82\xd2\x80\x00\x00\x03\x00\x80\x00\x00\x1eG\x8b\x17PP\xd5\x91\xec\xf7\x170\x00\x00\x01gB\xc0\x1e\xda\x02\x80\xf6\xc0Z\x83\x00\x82\xd2\x80\x00\x00\x03\x00\x80\x00\x00\x1eG\x8b\x17PP\xd5\x91\xec\xf7\x17'
#     buffer = b'\x82\x0e\n\x06\x08\x80\x05\x10\xe0\x03P\x82\xcf\xb0\xcb\x17'
#     message = socket.receive()
#     print(message)
#     socket.send(buffer)

def run_server(q):
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--source',
                        help='/dev/videoN:FMT:WxH:N/D or .mp4 file or image file',
                        default='/dev/video0:YUY2:640x480:30/1')
    parser.add_argument('--bitrate', type=int, default=1000000,
                        help='Video streaming bitrate (bit/s)')
    parser.add_argument('--loop', default=False, action='store_true',
                            help='Loop input video file')
   

    
    args = parser.parse_args()

  
    camera = make_camera(args.source, [300,300], args.loop)

    
     
    

    def render_overlay(tensor, layout, command):
        pass
        
        # test = tensor.reshape(224, 224, 3)
        
        # im = PIL.Image.fromarray(numpy.uint8(test))
        # self.img = im

        #print(tensor.shape)
        #self.overlay = self.gen.send((tensor, layout, command))
        
    def stupid_overlay(tensor, layout, command):
        pass
        #print(tensor.shape)
        # test = tensor.reshape(480, 640, 3)
        # im = PIL.Image.fromarray(test)

    camera.stupid_overlay = stupid_overlay
    camera.render_overlay = render_overlay
        

    with StreamingServer(camera, q, args.bitrate) as server:
        
        signal.pause()

def main():
    

    
    t1 = threading.Thread(target=run_server, name=run_server, args=(q,))

    t1.start()
    t1.deamon = True
    http_server = WSGIServer(('',5000), app, handler_class=WebSocketHandler)
    http_server.serve_forever()

    #app.run(host="0.0.0.0", debug=False)
    
    
       
if __name__ == '__main__':
    main()
