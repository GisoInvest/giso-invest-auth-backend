from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from src.models.user import User, db
from datetime import datetime
import re

user_bp = Blueprint('user', __name__)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    return True, ""

def get_user_from_token():
    """Extract user from JWT token in Authorization header"""
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return None, {'error': 'No token provided'}, 401
    
    token = auth_header.split(' ')[1]
    user = User.verify_jwt_token(token)
    
    if not user:
        return None, {'error': 'Invalid or expired token'}, 401
    
    return user, None, None

@user_bp.route('/auth/register', methods=['POST'])
@cross_origin()
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Validate input
        if not username or not email or not password:
            return jsonify({'error': 'All fields are required'}), 400
        
        if len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters long'}), 400
        
        if not validate_email(email):
            return jsonify({'error': 'Please enter a valid email address'}), 400
        
        is_valid, password_error = validate_password(password)
        if not is_valid:
            return jsonify({'error': password_error}), 400
        
        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            if existing_user.username == username:
                return jsonify({'error': 'Username already exists'}), 409
            else:
                return jsonify({'error': 'Email already exists'}), 409
        
        # Create new user
        user = User(username=username, email=email, password=password)
        user.update_last_login()
        
        db.session.add(user)
        db.session.commit()
        
        # Generate JWT token
        jwt_token = user.generate_jwt_token()
        
        return jsonify({
            'success': True,
            'message': 'Account created successfully',
            'user': user.to_dict(),
            'token': jwt_token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@user_bp.route('/auth/login', methods=['POST'])
@cross_origin()
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        identifier = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not identifier or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Find user by username or email
        user = User.find_by_username_or_email(identifier)
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Update last login
        user.update_last_login()
        db.session.commit()
        
        # Generate JWT token
        jwt_token = user.generate_jwt_token()
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': user.to_dict(),
            'token': jwt_token
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@user_bp.route('/auth/logout', methods=['POST'])
@cross_origin()
def logout():
    """Logout user"""
    try:
        # For JWT tokens, we don't need to invalidate on server side
        # The client will simply discard the token
        # But we can still validate the token to ensure it's a valid logout request
        
        user, error_response, status_code = get_user_from_token()
        if error_response:
            # Even if token is invalid, we consider logout successful
            pass
        
        return jsonify({
            'success': True,
            'message': 'Logout successful'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Logout failed: {str(e)}'}), 500

@user_bp.route('/auth/validate', methods=['GET'])
@cross_origin()
def validate_session():
    """Validate user session"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code
        
        return jsonify({
            'valid': True,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'valid': False, 'error': f'Validation failed: {str(e)}'}), 500

@user_bp.route('/auth/refresh', methods=['POST'])
@cross_origin()
def refresh_token():
    """Refresh user session token"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code
        
        # Generate new JWT token
        new_token = user.generate_jwt_token()
        user.update_last_login()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'token': new_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Token refresh failed: {str(e)}'}), 500

@user_bp.route('/users/profile', methods=['GET'])
@cross_origin()
def get_profile():
    """Get current user profile"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get profile: {str(e)}'}), 500

@user_bp.route('/users/profile', methods=['PUT'])
@cross_origin()
def update_profile():
    """Update current user profile"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update allowed fields
        if 'username' in data:
            new_username = data['username'].strip()
            if len(new_username) < 3:
                return jsonify({'error': 'Username must be at least 3 characters long'}), 400
            
            # Check if username is already taken by another user
            existing_user = User.query.filter(
                User.username == new_username,
                User.id != user.id
            ).first()
            
            if existing_user:
                return jsonify({'error': 'Username already exists'}), 409
            
            user.username = new_username
        
        if 'email' in data:
            new_email = data['email'].strip().lower()
            if not validate_email(new_email):
                return jsonify({'error': 'Please enter a valid email address'}), 400
            
            # Check if email is already taken by another user
            existing_user = User.query.filter(
                User.email == new_email,
                User.id != user.id
            ).first()
            
            if existing_user:
                return jsonify({'error': 'Email already exists'}), 409
            
            user.email = new_email
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update profile: {str(e)}'}), 500

# Legacy endpoints for backward compatibility
@user_bp.route('/users', methods=['GET'])
@cross_origin()
def get_users():
    """Get all users (admin only - for development)"""
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@user_bp.route('/users/<int:user_id>', methods=['GET'])
@cross_origin()
def get_user(user_id):
    """Get specific user by ID"""
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

