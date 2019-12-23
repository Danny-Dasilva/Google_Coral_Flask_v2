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

"""A demo which runs object classification on camera frames.

export TEST_DATA=/usr/lib/python3/dist-packages/edgetpu/test_data

python3 -m edgetpuvision.classify \
  --model ${TEST_DATA}/mobilenet_v2_1.0_224_inat_bird_quant.tflite \
  --labels ${TEST_DATA}/inat_bird_labels.txt
"""
import argparse
import collections
import itertools
import time

from edgetpu.classification.engine import ClassificationEngine

import utils


def accumulator(size, top_k):
    window = collections.deque(maxlen=size)
    window.append((yield []))
    while True:
        window.append((yield top_results(window, top_k)))



def render_gen(args):
    acc = accumulator(size=args.window, top_k=args.top_k)
    acc.send(None)  # Initialize.

    fps_counter = utils.avg_fps_counter(30)

    engines, titles = utils.make_engines(args.model, ClassificationEngine)
    assert utils.same_input_image_sizes(engines)
    engines = itertools.cycle(engines)
    engine = next(engines)

    labels = utils.load_labels(args.labels)
    draw_overlay = True

    yield utils.input_image_size(engine)

    output = None
    

       
      
def add_render_gen_args(parser):
    parser.add_argument('--model', required=False,
                        help='.tflite model path', default='/home/mendel/demo_files/mobilenet_v2_1.0_224_quant_edgetpu.tflite')
    parser.add_argument('--labels', required=False,
                        help='label file path', default='/home/mendel/demo_files/imagenet_labels.txt')
    parser.add_argument('--window', type=int, default=10,
                        help='number of frames to accumulate inference results')
    parser.add_argument('--top_k', type=int, default=3,
                        help='number of classes with highest score to display')
    parser.add_argument('--threshold', type=float, default=0.1,
                        help='class score threshold')
    parser.add_argument('--print', default=False, action='store_true',
                        help='Print inference results')

