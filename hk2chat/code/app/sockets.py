from flask_socketio import join_room, leave_room 
from flask_jwt_extended import jwt_required, get_jwt_identity 
from . import socketio 


@socketio.on('connect')
@jwt_required()
def handle_connect():
    current_user_id = get_jwt_identity()
    join_room(str(current_user_id))
    emit('message', {'data': 'Connected', 'user_id': current_user_id})


@socketio.on('disconnect')
@jwt_required()
def handle_disconnect():
    current_user_id = get_jwt_identity()
    leave_room(str(current_user_id))
    emit('message', {'data': 'Disconnected', 'user_id': current_user_id})

