from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets
import jwt
import os

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
    trial_active = db.Column(db.Boolean, default=True)
    
    # Subscription information
    subscription_plan = db.Column(db.String(20), default='trial')
    subscription_status = db.Column(db.String(50), default='trial_active')
    plan = db.Column(db.String(50), default='trial')
    subscription_start_date = db.Column(db.DateTime)
    last_payment_date = db.Column(db.DateTime)
    next_billing_date = db.Column(db.DateTime)
    
    # Payment information
    payment_required = db.Column(db.Boolean, default=False)
    stripe_customer_id = db.Column(db.String(255))
    stripe_payment_intent_id = db.Column(db.String(255))
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    last_trial_check = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.set_password(password)
        self.initialize_trial()

    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the user's password"""
        return check_password_hash(self.password_hash, password)

    def initialize_trial(self):
        """Initialize trial period for new user"""
        self.trial_start_date = datetime.utcnow()
        self.trial_end_date = datetime.utcnow() + timedelta(days=7)
        self.trial_days_used = 0
        self.trial_status = 'active'
        self.trial_active = True
        self.subscription_plan = 'trial'
        self.subscription_status = 'trial_active'
        self.plan = 'trial'
        self.payment_required = False

    def calculate_trial_status(self):
        """Calculate current trial status"""
        if not self.trial_start_date:
            return {
                'is_on_trial': False,
                'is_expired': True,
                'days_remaining': 0,
                'hours_remaining': 0,
                'trial_end_date': None,
                'can_access': False,
                'payment_required': True,
                'has_paid_subscription': False
            }

        now = datetime.utcnow()
        trial_end = self.trial_end_date or (self.trial_start_date + timedelta(days=7))
        
        time_remaining = trial_end - now
        days_remaining = max(0, time_remaining.days)
        hours_remaining = max(0, int(time_remaining.total_seconds() / 3600))
        
        is_expired = time_remaining.total_seconds() <= 0
        
        # Check if user has paid subscription
        has_paid_subscription = (
            self.subscription_status == 'active' and 
            self.subscription_plan not in ['trial', 'free']
        )
        
        is_on_trial = not is_expired and self.trial_active
        can_access = is_on_trial or has_paid_subscription
        payment_required = is_expired and not has_paid_subscription

        return {
            'is_on_trial': is_on_trial,
            'is_expired': is_expired,
            'days_remaining': days_remaining,
            'hours_remaining': hours_remaining,
            'trial_end_date': trial_end.isoformat(),
            'can_access': can_access,
            'payment_required': payment_required,
            'has_paid_subscription': has_paid_subscription
        }

    def update_trial_status(self):
        """Update trial status and related fields"""
        trial_status = self.calculate_trial_status()
        
        self.trial_days_used = 7 - trial_status['days_remaining']
        self.payment_required = trial_status['payment_required']
        self.last_trial_check = datetime.utcnow()
        
        # Update subscription status based on trial
        if trial_status['is_expired'] and not trial_status['has_paid_subscription']:
            self.subscription_status = 'trial_expired'
            self.trial_active = False
            self.trial_status = 'expired'
        elif trial_status['is_on_trial']:
            self.subscription_status = 'trial_active'
            self.trial_status = 'active'
        
        return trial_status

    def can_access_app(self):
        """Check if user can access the application"""
        trial_status = self.calculate_trial_status()
        return trial_status['can_access']

    def start_subscription(self, plan_id, payment_data=None):
        """Start a paid subscription"""
        self.subscription_status = 'active'
        self.subscription_plan = plan_id
        self.plan = plan_id
        self.trial_active = False
        self.payment_required = False
        self.subscription_start_date = datetime.utcnow()
        self.last_payment_date = datetime.utcnow()
        self.next_billing_date = datetime.utcnow() + timedelta(days=30)
        
        if payment_data:
            self.stripe_customer_id = payment_data.get('customer_id')
            self.stripe_payment_intent_id = payment_data.get('payment_intent_id')

    def cancel_subscription(self):
        """Cancel current subscription"""
        self.subscription_status = 'cancelled'
        self.subscription_plan = 'free'
        self.plan = 'free'
        self.payment_required = False
        self.trial_active = False

    def generate_jwt_token(self):
        """Generate a JWT token for the user"""
        secret_key = os.environ.get('SECRET_KEY', 'giso-invest-auth-secret-key-2024')
        
        payload = {
            'user_id': self.id,
            'username': self.username,
            'email': self.email,
            'exp': datetime.utcnow() + timedelta(days=30),  # Token expires in 30 days
            'iat': datetime.utcnow(),  # Issued at
            'sub': str(self.id)  # Subject (user ID)
        }
        
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        return token

    def generate_session_token(self):
        """Generate a new session token (legacy support)"""
        self.session_token = secrets.token_urlsafe(32)
        self.token_expires_at = datetime.utcnow() + timedelta(days=30)
        return self.session_token

    @staticmethod
    def verify_jwt_token(token):
        """Verify and decode a JWT token"""
        try:
            secret_key = os.environ.get('SECRET_KEY', 'giso-invest-auth-secret-key-2024')
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            
            user_id = payload.get('user_id')
            if not user_id:
                return None
            
            user = User.query.get(user_id)
            return user
        except jwt.ExpiredSignatureError:
            return None  # Token has expired
        except jwt.InvalidTokenError:
            return None  # Invalid token

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
        trial_status = self.calculate_trial_status()
        return trial_status['days_remaining']

    def is_trial_expired(self):
        """Check if the trial has expired"""
        trial_status = self.calculate_trial_status()
        return trial_status['is_expired']

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary"""
        trial_status = self.calculate_trial_status()
        
        user_dict = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'trial_status': self.trial_status,
            'trial_active': self.trial_active,
            'trial_start_date': self.trial_start_date.isoformat() if self.trial_start_date else None,
            'trial_end_date': self.trial_end_date.isoformat() if self.trial_end_date else None,
            'trial_days_used': self.trial_days_used,
            'trial_days_remaining': trial_status['days_remaining'],
            'subscription_plan': self.subscription_plan,
            'subscription_status': self.subscription_status,
            'plan': self.plan,
            'subscription_start_date': self.subscription_start_date.isoformat() if self.subscription_start_date else None,
            'next_billing_date': self.next_billing_date.isoformat() if self.next_billing_date else None,
            'payment_required': trial_status['payment_required'],
            'can_access_app': trial_status['can_access'],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'trial_calculation': trial_status
        }
        
        if include_sensitive:
            user_dict.update({
                'session_token': self.session_token,
                'token_expires_at': self.token_expires_at.isoformat() if self.token_expires_at else None
            })
        
        return user_dict

    @staticmethod
    def find_by_session_token(token):
        """Find user by session token (legacy support)"""
        return User.query.filter_by(session_token=token).first()

    @staticmethod
    def find_by_username_or_email(identifier):
        """Find user by username or email"""
        return User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

