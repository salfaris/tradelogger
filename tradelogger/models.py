# Built-in imports
from datetime import datetime

# Third-party imports
from flask_login import UserMixin

# Local imports
from tradelogger import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# Users table for database
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    logs = db.relationship('Trades', backref='author', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

# Trades table for database
class Trades(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    stock_name = db.Column(db.String(20), nullable=False)
    buy_price = db.Column(db.Integer, nullable=False)
    sell_price = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    profit_loss = db.Column(db.Integer, nullable=False)
    sell_type = db.Column(db.String(200), nullable=False, default="-")
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f"Log('{self.created_at}', '{self.stock_name}')"