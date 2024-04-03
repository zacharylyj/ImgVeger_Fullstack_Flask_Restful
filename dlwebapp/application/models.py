from application import db, login_manager
from datetime import datetime, timedelta
from flask_login import UserMixin


class User(db.Model, UserMixin):
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    creation_time = db.Column(
        db.DateTime, default=lambda: datetime.utcnow() + timedelta(hours=8)
    )

    def get_id(self):
        return str(self.user_id)


class History(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(120), db.ForeignKey("user.user_id"), nullable=False)
    prediction = db.Column(db.Float)
    image_path = db.Column(db.String(255), nullable=False)
    model_used = db.Column(db.String(10), nullable=False) 
    creation_time = db.Column(
        db.DateTime, default=lambda: datetime.utcnow() + timedelta(hours=8)
    )
    

