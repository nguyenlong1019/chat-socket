from flask import request, jsonify, make_response 
from . import app, db 
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
        return jsonify({'message': 'Login failed'})
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

        }), 404)
    elif not check_password_hash(user.password, data['password']):
        return make_response(jsonify({
            'message': 'Password does not match!',
            'access_token': None,

        }), 401)
    else:
        access_token = create_access_token(identity=user.id)
        return make_response(jsonify({
            'message': 'Login successfully!',
            'access_token': access_token,

        }), 200) # Ok


@app.route('/send-message', methods=['POST'])
def send_message():
    data = request.get_json()
    new_message = Message(sender_id=data['sender_id'], receiver_id=data['receiver_id'], message=data['message'])
    db.session.add(new_message)
    db.session.commit()
    return jsonify({'message': 'Message sent successfully!'})


@app.route('/get-message/<int:user_id>', methods=['GET'])
def get_message(user_id):
    messages = Message.query.filter_by(receiver_id=user_id).all()
    return jsonify([{'sender_id': msg.sender_id, 'message': msg.message, 'timestamp': msg.timestamp} for msg in messages])
