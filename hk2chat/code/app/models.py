from . import db 
from datetime import datetime 
import uuid 


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    role = db.Column(db.String(10), nullable=False) # owner or family or admin
    api_key = db.Column(db.String(32), default=lambda: str(uuid.uuid4()))


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(32), default=lambda: str(uuid.uuid4()))
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_rooms')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_rooms')


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(10), nullable=False) # owner or family 
    message = db.Column(db.Text, nullable=False) 
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    room = db.relationship('Room', backref='messages')

