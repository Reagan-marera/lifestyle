from datetime import datetime
from db import db

class Branch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    branch_name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    branch_ceos = db.relationship('BranchCEO', backref='branch', lazy=True)
    students = db.relationship('Student', backref='branch', lazy=True)

    def __repr__(self):
        return f'<Branch {self.branch_name}>'

class BranchCEO(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    branch_name = db.Column(db.String(100), db.ForeignKey('branch.branch_name'), nullable=False)  # Changed to branch_name
    phone_number = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<BranchCEO {self.name} - {self.branch.branch_name}>'

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    nationality_number = db.Column(db.String(50), unique=True, nullable=False)
    branch_name = db.Column(db.String(100), db.ForeignKey('branch.branch_name'), nullable=False)  # Changed to branch_name
    amount_paid = db.Column(db.Float, default=0.0)
    top_up = db.Column(db.Float, default=0.0)
    balance = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(50), default='active')
    phone_number = db.Column(db.String(20), nullable=True)
    date_amount_paid_updated = db.Column(db.Date, nullable=True)
    date_top_up_updated = db.Column(db.Date, nullable=True)
    date_balance_updated = db.Column(db.Date, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Student {self.name} - {self.branch.branch_name}>'

class CEO(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<CEO {self.name}>'
