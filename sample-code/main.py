import time
from threading import Thread

from flask import Flask, jsonify, request
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
# socketio = SocketIO(app)
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow CORS

connected_clients = {}

# Thiết lập thông tin kết nối đến cơ sở dữ liệu MySQL
app.config['MYSQL_HOST'] = '210.86.230.101'
app.config['MYSQL_USER'] = 'Admin01'
app.config['MYSQL_PASSWORD'] = 'admin@abc'
app.config['MYSQL_DB'] = 'msgdb'

mysql = MySQL(app)


def check_new_messages():
    while True:
        new_messages = get_new_messages()
        for message in new_messages:
            user_id = str(message[2])
            message_content = message[1]
            device_id = message[3]
            print(f"--- connected_clients: {connected_clients}")

            if user_id in connected_clients:
                socketio.emit('new_message', {'content': message_content, 'device_id': device_id}, room=connected_clients[user_id])
                print(f"send_mess: đã gửi thông báo tin nhắn mới từ {device_id} đến {user_id}")
                with app.app_context():
                    cursor = mysql.connection.cursor()
                    cursor.execute("UPDATE messages SET state = 'read' WHERE id = %s", (message[0],))
                    mysql.connection.commit()
                    cursor.close()
            else:
                print(f"send_mess: chưa gửi được thông báo cho {user_id}")

        time.sleep(5)


def get_new_messages():
    with app.app_context():
        cursor = mysql.connection.cursor()

        cursor.execute("SELECT * FROM messages WHERE state = 'unread'")
        new_messages = cursor.fetchall()

        if new_messages:
            print(f"new_messages: {new_messages}")
        else:
            print(f"new_messages: chưa có tin nhắn mới")
        cursor.close()

    return new_messages


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    print(username, password)

    # Truy vấn từ cơ sở dữ liệu để kiểm tra thông tin đăng nhập
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    user = cur.fetchone()

    if user:
        return jsonify({'message': 'Login successful', 'user_id': user[0]})
    else:
        return jsonify({'message': 'Invalid username or password'}), 401

# Event handler khi có kết nối mới

@socketio.on('connect')
def handle_connect():
    user_id = request.args.get('user_id')
    if user_id:
        connected_clients[user_id] = request.sid
        print(f"Client connected: {user_id} with SID: {request.sid}")
    else:
        print("Client connected without user_id")

@socketio.on('login_success')
def handle_login_success(data):
    device_id = data.get('device_id')
    user_id = data.get('user_id')
    if device_id:
        join_room(device_id)
        print(f"User {user_id} logged in with device {device_id}")
    else:
        print("No device_id provided")

@socketio.on('disconnect')
def handle_disconnect():
    disconnected_user = None
    for user, sid in connected_clients.items():
        if sid == request.sid:
            disconnected_user = user
            del connected_clients[user]
            print(f"Client disconnected: {user}")
            break
    if not disconnected_user:
        print("Client disconnected without user_id")


@app.route('/messages', methods=['GET', 'POST'])
def messages():
    if request.method == 'POST':
        # Nhận dữ liệu từ request
        data = request.json
        message = data.get('message')
        user_id = data.get('user_id')
        device = data.get('device')
        time = data.get('time')
        direc = data.get('direc')
        state = data.get('state')

        # Thêm dữ liệu vào bảng messages
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO messages (data, user_id, device, time, direc, state) VALUES (%s, %s, %s, %s, %s, %s)",
                    (message, user_id, device, time, direc, state))
        mysql.connection.commit()
        cur.close()

        return jsonify({'message': 'Message added successfully'}), 201

    elif request.method == 'GET':
        # Lấy tất cả dữ liệu từ bảng messages
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM messages")
        data = cur.fetchall()
        cur.close()

        return jsonify(data)

@app.route('/users', methods=['GET', 'POST'])
def users():
    if request.method == 'POST':
        # Nhận dữ liệu từ request
        data = request.json
        user = data.get('username')
        password = data.get('password')

        # Thêm dữ liệu vào bảng users
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (user, password) VALUES (%s, %s)",
                    (user, password))
        mysql.connection.commit()
        cur.close()

        return jsonify({'message': 'User added successfully'}), 201

    elif request.method == 'GET':
        # Lấy tất cả dữ liệu từ bảng users
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users")
        data = cur.fetchall()
        cur.close()

        return jsonify(data)


@app.route('/user/messages', methods=['POST'])
def get_user_messages():
    # Nhận thông tin từ header
    username = request.headers.get('username')
    password = request.headers.get('password')
    print(username,password)
    # Kiểm tra username và password trong cơ sở dữ liệu
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    user = cur.fetchone()

    # Nếu username và password không hợp lệ, trả về lỗi 401
    if not user:
        return jsonify({'message': 'Invalid username or password'}), 401

    # Lấy user_id của người dùng
    user_id = user[0]

    # Nhận thông tin từ body
    data = request.json
    first_time = data.get('first_time')
    last_time = data.get('last_time')

    # Truy vấn tin nhắn của người dùng trong khoảng thời gian first_time và last_time
    cur.execute("SELECT * FROM messages WHERE user = %s AND time BETWEEN %s AND %s",
                (user_id, first_time, last_time))
    messages = cur.fetchall()

    cur.close()

    return jsonify(messages)


@app.route('/send-message', methods=['POST'])
def send_message():
    # Kiểm tra thông tin đăng nhập từ header
    username = request.headers.get('username')
    password = request.headers.get('password')

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    user = cur.fetchone()

    if not user:
        return jsonify({'message': 'Invalid username or password'}), 401

    # Nhận dữ liệu tin nhắn từ body
    data = request.json
    message_data = data.get('data')
    device = data.get('device')
    time = data.get('time')

    # Lưu tin nhắn vào bảng messages
    cur.execute("INSERT INTO messages (data, user, device, time, direc) VALUES (%s, %s, %s, %s, %s)",
                (message_data, user[0], device, time, 0))
    mysql.connection.commit()
    cur.close()

    return jsonify({'message': 'Message sent successfully'}), 201



# Event handler khi có tin nhắn mới từ cơ sở dữ liệu
def handle_new_message(message):
    device_id = message.get('device_id')
    # Gửi tin nhắn đến phòng tương ứng với thiết bị
    emit('new_message', message, room=device_id)
if __name__ == '__main__':
    # Khởi chạy luồng kiểm tra tin nhắn mới
    check_messages_thread = Thread(target=check_new_messages)
    check_messages_thread.daemon = True
    check_messages_thread.start()

    # Chạy Flask server
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)

