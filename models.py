from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    user_id     = db.Column(db.Integer, primary_key=True)
    username    = db.Column(db.String(80), unique=True, nullable=False)
    email       = db.Column(db.String(120), unique=True, nullable=False)
    password    = db.Column(db.String(256), nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def get_id(self):
        return str(self.user_id)

class MoctaleRating(db.Model):
    __tablename__ = 'moctale_meter'
    rating_id   = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    movie_id    = db.Column(db.Integer, nullable=False)
    meter_value = db.Column(db.String(20), nullable=False)
    rated_on    = db.Column(db.DateTime, default=datetime.utcnow)

class VibeChart(db.Model):
    __tablename__ = 'vibe_chart'
    vibe_id     = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    movie_id    = db.Column(db.Integer, nullable=False)
    action      = db.Column(db.Float, default=0)
    romance     = db.Column(db.Float, default=0)
    comedy      = db.Column(db.Float, default=0)
    thriller    = db.Column(db.Float, default=0)
    drama       = db.Column(db.Float, default=0)

class Comment(db.Model):
    __tablename__ = 'comments'
    comment_id  = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    movie_id    = db.Column(db.Integer, nullable=False)
    content     = db.Column(db.Text, nullable=False)
    likes       = db.Column(db.Integer, default=0)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

class Dashboard(db.Model):
    __tablename__ = 'dashboard'
    dash_id     = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.user_id'), unique=True)
    fav_genre   = db.Column(db.String(50))
    total_votes = db.Column(db.Integer, default=0)