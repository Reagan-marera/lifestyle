from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

from db import db

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    nationality_number = db.Column(db.String(50), unique=True, nullable=False)
    branch = db.Column(db.String(50), nullable=False)
    amount_paid = db.Column(db.Float, default=0.0)
    top_up = db.Column(db.Float, default=0.0)
    balance = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(50), default='active')
    phone_number = db.Column(db.String(20), nullable=True)  # New field
    date_amount_paid_updated = db.Column(db.Date, nullable=True)  # New field
    date_top_up_updated = db.Column(db.Date, nullable=True)  # New field
    date_balance_updated = db.Column(db.Date, nullable=True)  # New field
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Updated field

class CEO(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
