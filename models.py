from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# a single shared db object, imported by app.py and every model file
db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    avatar_path = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    images = db.relationship("Image", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Image(db.Model):
    __tablename__ = "images"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    original_filename = db.Column(db.String(255), nullable=False)
    original_path = db.Column(db.String(500), nullable=False)
    thumbnail_path = db.Column(db.String(500), nullable=False)

    # stored so the gallery can show how the thumbnail differs from the original
    original_width = db.Column(db.Integer)
    original_height = db.Column(db.Integer)
    original_bytes = db.Column(db.Integer)
    thumbnail_width = db.Column(db.Integer)
    thumbnail_height = db.Column(db.Integer)
    thumbnail_bytes = db.Column(db.Integer)

    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class RateLimitLog(db.Model):
    __tablename__ = "rate_limit_logs"

    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    endpoint = db.Column(db.String(120), nullable=False)
    limit_type = db.Column(db.String(20), nullable=False)  # "ip" or "user"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
