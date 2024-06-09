from flask import Flask 
from flask_sqlalchemy import SQLAlchemy 
from flask_jwt_extended import JWTManager 
from flask_socketio import SocketIO


db = SQLAlchemy()
jwt = JWTManager() 
socketio = SocketIO()



def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app)

    with app.app_context():
        from . import routes 
        db.create_all()
    
    return app 
