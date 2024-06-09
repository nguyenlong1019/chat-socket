from flask import Flask, render_template 
from flask_socketio import SocketIO, send 


app = Flask(__name__)
app.config['SECRET'] = 'hk21019DcPu101920021752Hacker02LITlItgNoL'
socketio = SocketIO(app, cors_allowed_origins="*")


@socketio.on('message')
def handle_message(message):
    print("Received message: " + message)
    if message != "User connected!":
        send(message, broadcast=True)


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    socketio.run(app, host="192.168.1.206", port=5000)
