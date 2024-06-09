from flask import request, jsonify, make_response 
from . import app, db, socketio 
from .models import User, Message, Room 
from werkzeug.security import generate_password_hash, check_password_hash 
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'], method='sha256')
    new_user = User(username=data['username'], password=hashed_password, role=data['role'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'})


# login for admin 
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if not user or not check_password_hash(user.password, data['password']):
        return make_response(jsonify({'message': 'Login failed'}), 401)
    return jsonify({'message': 'Login successful', 'user_id': user.id, 'role': user.role})

# login for owner
@app.route('/login-owner', methods=['POST'])
def login_owner():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if not user:
        return make_response(jsonify({
            'message': 'Email does not exist!',
            'user_id': None,
            'username': user.username,
            'api_key': None,
            'success': False,
        }), 404) # Not Found
    elif not check_password_hash(user.password, data['password']):
        return make_response(jsonify({
            'message': 'Password does not match!',
            'user_id': None,
            'username': user.username,
            'api_key': None, 
            'success': False,
        }), 401) # Unauthorized
    else:
        return make_response(jsonify({
            'message': 'Login successfully!', 
            'user_id': user.id,
            'username': user.username, 
            'api_key': user.api_key,
            'success': True,
        }), 200) # Ok


# login for family
@app.route('/login-family', methods=['POST'])
def login_family():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if not user:
        return make_response(jsonify({
            'message': 'Email does not exist!',
            'access_token': None,
            'username': None,
        }), 404)
    elif not check_password_hash(user.password, data['password']):
        return make_response(jsonify({
            'message': 'Password does not match!',
            'access_token': None,
            'username': None,
        }), 401)
    else:
        access_token = create_access_token(identity=user.id)
        return make_response(jsonify({
            'message': 'Login successfully!',
            'access_token': access_token,
            'username': user.username,
        }), 200) # Ok


# Cần sửa lại từ dòng này 
@app.route('/send-message-family', methods=['POST'])
@jwt_required()
def send_message_by_family():
    data = request.json()
    current_user_id = get_jwt_identity()
    room = Room.query.filter_by(sender_id=current_user_id, receiver_id=data['receiver_id']).first()
    if not room:
        room = Room(sender_id=current_user_id, receiver_id=data['receiver_id'])
        db.session.add(room)
        db.session.commit()
    new_message = Message(room_id=room.id, type='family', message=data['message'])
    db.session.add(new_message)
    db.session.commit()
    # Notify the receiver through socket (if connected)
    socketio.emit('new_message', {'message': data['message'], 'sender_id': current_user_id}, room=str(data['receiver_id']))
    return jsonify({'message': 'Message sent successfully!'})


@app.route('/send-message-owner', methods=['POST'])
def send_message_by_owner():
    data = request.get_json()
    api_key = request.headers.get('x-api-key')
    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return make_response(jsonify({'message': 'Invalid API key!'}), 401)
    room = Room.query.filter_by(sender_id=user.id, receiver_id=data['receiver_id']).first()
    if not room:
        room = Room(sender_id=user.id, receiver_id=data['receiver_id'])
        db.session.add(room)
        db.session.commit()
    new_message = Message(room_id=room.id, type='owner', message=data['message'])
    db.session.add(new_message)
    db.session.commit()
    # Notify the receiver through socket (if connected)
    socketio.emit('new_message', {'message': data['message'], 'sender_id': user.id}, room=str(data['receiver_id']))
    return jsonify({'message': 'Message sent successfully!'})


@app.route('/get-messages/<int:room_id>', methods=['GET'])
@jwt_required()
def get_messages(room_id):
    current_user_id = get_jwt_identity()
    room = Room.query.filter_by(id=room_id).first()
    if not room or (room.sender_id != current_user_id and room.receiver_id != current_user_id):
        return make_response(jsonify({'message': 'No access to this room!'}), 403)
    messages = Message.query.filter_by(room_id=room_id).order_by(Message.timestamp).all()
    return jsonify([{'type': msg.type, 'message': msg.message, 'timestamp': msg.timestamp} for msg in messages])
