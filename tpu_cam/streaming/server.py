import contextlib

import logging
import queue
import struct
import threading
import time
from time import sleep
from itertools import cycle
from enum import Enum

from .proto import messages_pb2 as pb2

Logger = logging.getLogger(__name__)

class NAL:
    CODED_SLICE_NON_IDR = 1  # Coded slice of a non-IDR picture
    CODED_SLICE_IDR     = 5  # Coded slice of an IDR picture
    SEI                 = 6  # Supplemental enhancement information (SEI)
    SPS                 = 7  # Sequence parameter set
    PPS                 = 8  # Picture parameter set

ALLOWED_NALS = {NAL.CODED_SLICE_NON_IDR,
                NAL.CODED_SLICE_IDR,
                NAL.SPS,
                NAL.PPS,
                NAL.SEI}

def StartMessage(resolution):
    print(resolution)
    width, height = resolution
    return pb2.ClientBound(timestamp_us=int(time.monotonic() * 1000000),
                           start=pb2.Start(width=width, height=height))

def StopMessage():
    return pb2.ClientBound(timestamp_us=int(time.monotonic() * 1000000),
                           stop=pb2.Stop())

def VideoMessage(data):
    return pb2.ClientBound(timestamp_us=int(time.monotonic() * 1000000),
                           video=pb2.Video(data=data))

def OverlayMessage(svg):
    return pb2.ClientBound(timestamp_us=int(time.monotonic() * 1000000),
                           overlay=pb2.Overlay(svg=svg))

def _parse_server_message(data):
    message = pb2.ServerBound()
    message.ParseFromString(data)
    return message

class DroppingQueue:

    def __init__(self, maxsize):
        if maxsize <= 0:
            raise ValueError('Maxsize must be positive.')
        self.maxsize = maxsize
        self._items = []
        self._cond = threading.Condition(threading.Lock())

    def put(self, item, replace_last=False):
        with self._cond:
            was_empty = len(self._items) == 0
            if len(self._items) < self.maxsize:
                self._items.append(item)
                if was_empty:
                    self._cond.notify()
                return False  # Not dropped.

            if replace_last:
                self._items[len(self._items) - 1] = item
                return False  # Not dropped.

            return True  # Dropped.

    def get(self):
        with self._cond:
            while not self._items:
                self._cond.wait()
            return self._items.pop(0)


class AtomicSet:

    def __init__(self):
        self._lock = threading.Lock()
        self._set = set()

    def add(self, value):
        with self._lock:
            self._set.add(value)
            return value

    def __len__(self):
        with self._lock:
            return len(self._set)

    def __iter__(self):
        with self._lock:
            return iter(self._set.copy())


class StreamingServer:

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __init__(self, camera, q, bitrate=1000000,):
        
        self._bitrate = bitrate
        self._camera = camera
        self.q = q
        self._clients = AtomicSet()
        self._enabled_clients = AtomicSet()
        self._done = threading.Event()
        self._commands = queue.Queue()
        self.client = Clientt(self._commands, self._camera.resolution, self.q)

        #self._thread = threading.Thread(target=self._run)
        #self._thread.start()
        self._start_recording()
        
        self.client.start()
        
    def close(self):
        self._done.set()
        self._thread.join()

  

    def _start_recording(self):
        Logger.info('Camera start recording')
        self._camera.start_recording(self, format='h264', profile='baseline',
            inline_headers=True, bitrate=self._bitrate, intra_period=0)

    def _stop_recording(self):
        Logger.info('Camera stop recording')
        self._camera.stop_recording()

    def _process_command(self, client, command):
        if command is ClientCommand.ENABLE:
            self._enabled_clients.add(client)
        
        elif command == ClientCommand.STOP:
       
            client.stop()
            Logger.info('Number of active clients: %d', len(self._clients))


    def _run(self):
        try:               

            while not self._done.is_set():
                # Process available client commands.
                try:
                    while True:
                        client, command = self._commands.get_nowait()
                        self._process_command(client, command)
                except queue.Empty:
                    pass  # Done processing commands.

                sleep(.02) # supposed to be 200 ms
        finally:
            Logger.info('Server is shutting down')
            if self._enabled_clients:
                self._stop_recording()

            for client in self._clients:
                client.stop()
            Logger.info('Done')

    def write(self, data):
        
        """Called by camera thread for each compressed frame."""
        assert data[0:4] == b'\x00\x00\x00\x01'
        frame_type = data[4] & 0b00011111
        if frame_type in ALLOWED_NALS:
            client = self.client.send_video(frame_type, data)
            #states = {client.send_video(frame_type, data) for client in self._enabled_clients}

class ClientLogger(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return '[%s] %s' % (self.extra['name'], msg), kwargs

class ClientState(Enum):
    DISABLED = 1
    ENABLED_NEEDS_SPS = 2
    ENABLED = 3

class ClientCommand(Enum):
    STOP = 1
    ENABLE = 2
    DISABLE = 3

class Clientt:
    def __init__(self, command_queue, resolution, q):
        print("init")
        self._lock = threading.Lock()  # Protects _state.
        self._state = ClientState.ENABLED
        self._Logger = ClientLogger(Logger, {'name': "Orange_logger"})
        self._commands = command_queue
        self._tx_q = DroppingQueue(15)
        self.q = q
        self._rx_thread = threading.Thread(target=self._rx_run, args=(False,))
        self._tx_thread = threading.Thread(target=self._tx_run)
        self.start()
        self._resolution = resolution
        print(self._resolution, "existing res")
    class WsPacket:
        def __init__(self):
            self.fin = True
            self.opcode = 2
            self.masked = False
            self.mask = None
            self.length = 0
            self.payload = bytearray()

        def append(self, data):
            if self.masked:
                data = bytes([c ^ k for c, k in zip(data, cycle(self.mask))])
            self.payload.extend(data)

        def serialize(self):
            self.length = len(self.payload)
            buf = bytearray()
            b0 = 0
            b1 = 0
            if self.fin:
                b0 |= 0x80
            b0 |= self.opcode
            buf.append(b0)
            if self.length <= 125:
                b1 |= self.length
                buf.append(b1)
            elif self.length >= 126 and self.length <= 65535:
                b1 |= 126
                buf.append(b1)
                buf.extend(struct.pack('!H', self.length))
            else:
                b1 |= 127
                buf.append(b1)
                buf.extend(struct.pack('!Q', self.length))
            if self.payload:
                buf.extend(self.payload)
            return bytes(buf)


    def start(self):
        self._rx_thread.start()
        self._tx_thread.start()

    def stop(self):
        self._Logger.info('Stopping...')
        self._tx_q.put(None)
        self._tx_thread.join()
        self._rx_thread.join()
        self._Logger.info('Stopped.')

    def _queue_video(self, data):
        
        return self._queue_message(VideoMessage(data))

    
    

    def send_video(self, frame_type, data):
        
        """Only called by camera thread."""
        with self._lock:
            if self._state == ClientState.DISABLED:
                print("disabled")
                pass
            elif self._state == ClientState.ENABLED_NEEDS_SPS:
                if frame_type == NAL.SPS:
                    
                    dropped = self._queue_video(data)
                    if not dropped:
                        self._state = ClientState.ENABLED
            elif self._state == ClientState.ENABLED:
                dropped = self._queue_video(data)
                
                if dropped:
                    self._state = ClientState.ENABLED_NEEDS_SPS
            return self._state

    def _send_command(self, command):
        self._commands.put((self, command))

    def _queue_message(self, message, replace_last=False):
       
        dropped = self._tx_q.put(message, replace_last)
        
        
        if dropped:
            self._Logger.warning('Running behind, dropping messages')
        return dropped

    def _tx_run(self):
        try:
            while True:
                message = self._tx_q.get()
                if message is None:
                    break
                self._send_message(message)
            self._Logger.info('Tx thread finished')
        except Exception as e:
            self._Logger.warning('Tx thread failed: %s', e)

        # Tx thread stops the client in any situation.
        self._send_command(ClientCommand.STOP)

    def _send_message(self, message):
        if isinstance(message, (bytes, bytearray)):
            buf = message
            
        else:

            if isinstance(message, self.WsPacket):
                packet = message
            else:
                packet = self.WsPacket()
                packet.append(message.SerializeToString())
                
            buf = packet.serialize()
            self.q.put(buf)
            

    def _rx_run(self, done):
        print("called rx run")
        if done == False:
            done = True
            self._handle_stream_control()

    def _handle_stream_control(self):
        enabled = True
        self._Logger.info('stream_control %s', enabled)

        with self._lock:
            
         
            self._Logger.info('Enabling client')
            
            print(self._resolution, "existing res in ")
            self._state = ClientState.ENABLED_NEEDS_SPS
            self._queue_message(StartMessage(self._resolution))
            self._send_command(ClientCommand.ENABLE)

