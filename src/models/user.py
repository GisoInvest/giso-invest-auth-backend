from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Session management
    session_token = db.Column(db.String(255), unique=True, nullable=True)
    token_expires_at = db.Column(db.DateTime, nullable=True)
    
    # Trial information
    trial_start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    trial_end_date = db.Column(db.DateTime, nullable=False)
    trial_days_used = db.Column(db.Integer, default=0)
    trial_status = db.Column(db.String(20), default='active')
    subscription_plan = db.Column(db.String(20), default='trial')
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.set_password(password)
        self.trial_start_date = datetime.utcnow()
        self.trial_end_date = datetime.utcnow() + timedelta(days=7)
        self.trial_days_used = 0
        self.trial_status = 'active'
        self.subscription_plan = 'trial'

    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the user's password"""
        return check_password_hash(self.password_hash, password)

    def generate_session_token(self):
        """Generate a new session token"""
        self.session_token = secrets.token_urlsafe(32)
        self.token_expires_at = datetime.utcnow() + timedelta(days=30)
        return self.session_token

    def is_session_valid(self):
        """Check if the current session token is valid"""
        if not self.session_token or not self.token_expires_at:
            return False
        return datetime.utcnow() < self.token_expires_at

    def invalidate_session(self):
        """Invalidate the current session"""
        self.session_token = None
        self.token_expires_at = None

    def update_last_login(self):
        """Update the last login timestamp"""
        self.last_login = datetime.utcnow()

    def get_trial_days_remaining(self):
        """Get the number of trial days remaining"""
        if self.trial_status != 'active':
            return 0
        
        now = datetime.utcnow()
        if now > self.trial_end_date:
            return 0
        
        days_remaining = (self.trial_end_date - now).days
        return max(0, days_remaining)

    def is_trial_expired(self):
        """Check if the trial has expired"""
        return datetime.utcnow() > self.trial_end_date

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary"""
        user_dict = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'trial_status': self.trial_status,
            'trial_days_used': self.trial_days_used,
            'trial_days_remaining': self.get_trial_days_remaining(),
            'subscription_plan': self.subscription_plan,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        
        if include_sensitive:
            user_dict.update({
                'session_token': self.session_token,
                'token_expires_at': self.token_expires_at.isoformat() if self.token_expires_at else None
            })
        
        return user_dict

    @staticmethod
    def find_by_session_token(token):
        """Find user by session token"""
        return User.query.filter_by(session_token=token).first()

    @staticmethod
    def find_by_username_or_email(identifier):
        """Find user by username or email"""
        return User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

