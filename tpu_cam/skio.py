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
import itertools

import logging
from flask import Flask, render_template, url_for, copy_current_request_context, Response, request
from threading import Thread, active_count, Event
import signal
import threading
import queue
from camera import make_camera
from gstreamer import Display, run_gen
from streaming.server import StreamingServer
from flask_socketio import SocketIO, emit


async_mode = 'gevent'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None


q = queue.Queue(maxsize=150)
def svg(q):
    while True:
        
        c = q.get()
        yield c
@socketio.on('update')
def update(msg):
    print(msg, "callllled")
    t = svg(q)
    for buffer in t:
        print(len(buffer), "gifff")

        socketio.sleep(.02)
        #  buffer = b'\x82\x0e\n\x06\x08\x80\x05\x10\xe0\x03P\x82\xcf\xb0\xcb\x17'
        socketio.emit('my_response', buffer, namespace='/test')

@socketio.on('my_event')
def test_message(message):
    print(message, "emit test")
    t = svg(q)
    for buffer in t:
        socketio.sleep(.02)
        
        #  buffer = b'\x82\x0e\n\x06\x08\x80\x05\x10\xe0\x03P\x82\xcf\xb0\xcb\x17'
        socketio.emit('my_response', buffer, broadcast=True)

    # print(message, "emit test")
        
@app.route('/')
def init():
    return render_template('skio.html')
@app.route('/bytestream')
def byte():
        return Response(svg(q), content_type='text/event-stream')






def run_server(q):
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--source',
                        help='/dev/videoN:FMT:WxH:N/D or .mp4 file or image file',
                        default='/dev/video0:YUY2:640x480:30/1')
    parser.add_argument('--bitrate', type=int, default=1000000,
                        help='Video streaming bitrate (bit/s)')
   

    
    args = parser.parse_args()

  
    camera = make_camera(args.source)
  

    with StreamingServer(camera, q, args.bitrate) as server:
        
        signal.pause()

def main():
    

    
    t1 = threading.Thread(target=run_server, name=run_server, args=(q,))

    t1.start()
    t1.deamon = True
    socketio.run(app, host="0.0.0.0", debug=False)
    
    #app.run(host="0.0.0.0", debug=False)
    
    
       
if __name__ == '__main__':
    main()
