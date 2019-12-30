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
import signal

from camera import make_camera
from gstreamer import Display, run_gen
from streaming.server import StreamingServer
from gst import parse_format
from camera import DeviceCamera
import svg
import PIL
import numpy

EMPTY_SVG = str(svg.Svg())



class Run_Server():
    def __init__(self, model):
        logging.basicConfig(level=logging.INFO)

        parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('--source',
                            help='/dev/videoN:FMT:WxH:N/D or .mp4 file or image file',
                            default='/dev/video0:YUY2:640x480:30/1')
        parser.add_argument('--bitrate', type=int, default=1000000,
                            help='Video streaming bitrate (bit/s)')
        parser.add_argument('--loop', default=False, action='store_true',
                            help='Loop input video file')

        model.add_render_gen_args(parser)
        self.args = parser.parse_args()

        self.gen = model.render_gen(self.args)
        self.camera = self.make_camera(self.args.source, next(self.gen), self.args.loop)
        self._camera = self.camera
        assert self.camera is not None
        self.overlay = 0
        self.img = None
        self._bitrate=1000000
        self._start_recording()
    
    def make_camera(self, source, inference_size, loop):
        fmt = parse_format(source)
        if fmt:
            return DeviceCamera(fmt, inference_size)

        filename = os.path.expanduser(source)
        if os.path.isfile(filename):
            return FileCamera(filename, inference_size, loop)

        return None


    def _start_recording(self):
        
        self._camera.start_recording(self, format='h264', profile='baseline',
            inline_headers=True, bitrate=self._bitrate, intra_period=0)

    def _stop_recording(self):
        
        self._camera.stop_recording()
    
    def return_frame(self):

        self._camera.request_key_frame()
    def image(self):
            
            
        
        self.camera.stupid_overlay = self.stupid_overlay1
        self.camera.render_overlay = self.render_overlay
        return(self.img, self.overlay)
        # signal.pause()
    

    def render_overlay(self, tensor, layout, command):
        
        # test = tensor.reshape(224, 224, 3)
        
        # im = PIL.Image.fromarray(numpy.uint8(test))
        # self.img = im

        
        self.overlay = self.gen.send((tensor, layout, command))
        
    def stupid_overlay1(self, tensor, layout, command):
        
        test = tensor.reshape(480, 640, 3)
        im = PIL.Image.fromarray(test)
        self.img = im



        
# def run_server(model):
#     logging.basicConfig(level=logging.INFO)

#     parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
#     parser.add_argument('--source',
#                         help='/dev/videoN:FMT:WxH:N/D or .mp4 file or image file',
#                         default='/dev/video0:YUY2:640x480:30/1')
#     parser.add_argument('--bitrate', type=int, default=1000000,
#                         help='Video streaming bitrate (bit/s)')
#     parser.add_argument('--loop', default=False, action='store_true',
#                         help='Loop input video file')

#     model.add_render_gen_args(parser)
#     args = parser.parse_args()

#     gen = model.render_gen(args)
#     camera = make_camera(args.source, next(gen), args.loop)
#     assert camera is not None

#     with StreamingServer(camera, args.bitrate) as server:
        
#         def render_overlay(tensor, layout, command):
#             print(tensor.shape, "render overlay")
            
#             # overlay = gen.send((tensor, layout, command))
#             # server.send_overlay(overlay if overlay else EMPTY_SVG)
#         def stupid_overlay(tensor, layout, command):
#             print(tensor.shape, "stupoid_overlaty")

#         camera.render_overlay = render_overlay
#         camera.stupid_overlay = stupid_overlay
#         signal.pause()
