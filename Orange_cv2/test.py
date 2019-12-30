#!/usr/bin/env python
from threading import Lock
from flask import Flask, render_template, session, request, \
    copy_current_request_context
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()




@app.route('/')
def index():
    return render_template('test.html', async_mode=socketio.async_mode)


@socketio.on('my_event')
def test_message(message):
    print(message, "emit test")
    message = "hello"
    for i in range(100):

        socketio.emit('my_response', i, broadcast=True)


if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", debug=True)
