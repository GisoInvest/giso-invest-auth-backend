from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets
import jwt
import os

db = SQLAlchemy()

class User(db.Model):
    """
    Backward Compatible User Model
    Works with existing database schema while providing new functionality
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Session management (existing)
    session_token = db.Column(db.String(255), unique=True, nullable=True)
    token_expires_at = db.Column(db.DateTime, nullable=True)
    
    # Trial information (existing)
    trial_start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    trial_end_date = db.Column(db.DateTime, nullable=False)
    trial_days_used = db.Column(db.Integer, default=0)
    trial_status = db.Column(db.String(20), default='active')
    
    # Timestamps (existing)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.set_password(password)
        self.initialize_trial()

    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)

    def initialize_trial(self):
        """Initialize trial period for new user"""
        if not self.trial_start_date:
            self.trial_start_date = datetime.utcnow()
        if not self.trial_end_date:
            self.trial_end_date = self.trial_start_date + timedelta(days=7)

    def generate_session_token(self):
        """Generate a new session token"""
        self.session_token = secrets.token_urlsafe(32)
        self.token_expires_at = datetime.utcnow() + timedelta(days=30)
        return self.session_token

    def is_token_valid(self):
        """Check if current session token is valid"""
        if not self.session_token or not self.token_expires_at:
            return False
        return datetime.utcnow() < self.token_expires_at

    def generate_jwt_token(self):
        """Generate JWT token for authentication"""
        payload = {
            'user_id': self.id,
            'username': self.username,
            'email': self.email,
            'exp': datetime.utcnow() + timedelta(days=30),
            'iat': datetime.utcnow()
        }
        
        secret_key = os.environ.get('JWT_SECRET_KEY', 'giso-invest-secret-key-2024')
        return jwt.encode(payload, secret_key, algorithm='HS256')

    @staticmethod
    def verify_jwt_token(token):
        """Verify JWT token and return user"""
        try:
            secret_key = os.environ.get('JWT_SECRET_KEY', 'giso-invest-secret-key-2024')
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            return User.query.get(payload['user_id'])
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, KeyError):
            return None

    def calculate_trial_status(self):
        """Calculate current trial status - compatible with existing schema"""
        now = datetime.utcnow()
        
        if not self.trial_start_date or not self.trial_end_date:
            return {
                'is_active': False,
                'is_expired': True,
                'days_remaining': 0,
                'days_used': 0,
                'status': 'expired'
            }
        
        days_used = (now - self.trial_start_date).days
        days_remaining = max(0, (self.trial_end_date - now).days)
        is_active = now <= self.trial_end_date
        
        return {
            'is_active': is_active,
            'is_expired': not is_active,
            'days_remaining': days_remaining,
            'days_used': days_used,
            'status': 'active' if is_active else 'expired'
        }

    # Subscription-related properties (computed from existing data)
    @property
    def trial_active(self):
        """Check if trial is currently active"""
        return self.calculate_trial_status()['is_active']
    
    @property
    def subscription_plan(self):
        """Get current subscription plan"""
        return 'trial' if self.trial_active else 'expired'
    
    @property
    def subscription_status(self):
        """Get current subscription status"""
        return 'trial_active' if self.trial_active else 'trial_expired'
    
    @property
    def plan(self):
        """Alias for subscription_plan"""
        return self.subscription_plan
    
    @property
    def payment_required(self):
        """Check if payment is required"""
        return not self.trial_active
    
    @property
    def stripe_customer_id(self):
        """Stripe customer ID (placeholder for compatibility)"""
        return None
    
    @property
    def stripe_payment_intent_id(self):
        """Stripe payment intent ID (placeholder for compatibility)"""
        return None
    
    @property
    def subscription_start_date(self):
        """Subscription start date (placeholder for compatibility)"""
        return None
    
    @property
    def last_payment_date(self):
        """Last payment date (placeholder for compatibility)"""
        return None
    
    @property
    def next_billing_date(self):
        """Next billing date (placeholder for compatibility)"""
        return None

    def to_dict(self):
        """Convert user to dictionary"""
        trial_status = self.calculate_trial_status()
        
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'trial_start_date': self.trial_start_date.isoformat() if self.trial_start_date else None,
            'trial_end_date': self.trial_end_date.isoformat() if self.trial_end_date else None,
            'trial_days_used': trial_status['days_used'],
            'trial_status': trial_status['status'],
            'trial_active': trial_status['is_active'],
            'subscription_plan': self.subscription_plan,
            'subscription_status': self.subscription_status,
            'payment_required': self.payment_required,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

