from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from src.models.user import User, db
import datetime
import uuid

subscription_bp = Blueprint('subscription', __name__)

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

@subscription_bp.route('/subscription/status', methods=['GET'])
@cross_origin()
def get_subscription_status():
    """Get current user's subscription status"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code

        # Calculate trial status
        trial_status = user.calculate_trial_status()
        
        return jsonify({
            'user_id': user.id,
            'subscription_plan': user.subscription_plan,
            'subscription_status': user.subscription_status,
            'trial_start_date': user.trial_start_date.isoformat() if user.trial_start_date else None,
            'trial_end_date': user.trial_end_date.isoformat() if user.trial_end_date else None,
            'subscription_start_date': user.subscription_start_date.isoformat() if user.subscription_start_date else None,
            'subscription_end_date': user.subscription_end_date.isoformat() if user.subscription_end_date else None,
            'trial_status': trial_status,
            'is_trial_active': trial_status['is_active'],
            'is_trial_expired': trial_status['is_expired'],
            'days_remaining': trial_status['days_remaining']
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get subscription status: {str(e)}'}), 500

@subscription_bp.route('/subscription/create', methods=['POST'])
@cross_origin()
def create_subscription():
    """Create a new subscription for the user"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code

        data = request.get_json()
        plan = data.get('plan')
        payment_method_id = data.get('payment_method_id')
        
        if not plan or not payment_method_id:
            return jsonify({'error': 'Plan and payment method are required'}), 400
        
        # Validate plan
        valid_plans = ['starter', 'professional', 'enterprise']
        if plan not in valid_plans:
            return jsonify({'error': 'Invalid plan selected'}), 400
        
        # Here you would integrate with Stripe to process payment
        # For now, we'll simulate successful payment
        
        # Update user subscription
        user.subscription_plan = plan
        user.subscription_status = 'active'
        user.subscription_start_date = datetime.datetime.utcnow()
        user.subscription_end_date = datetime.datetime.utcnow() + datetime.timedelta(days=30)
        user.stripe_customer_id = f"cus_{uuid.uuid4().hex[:24]}"  # Simulate Stripe customer ID
        user.stripe_subscription_id = f"sub_{uuid.uuid4().hex[:24]}"  # Simulate Stripe subscription ID
        
        db.session.commit()
        
        return jsonify({
            'message': 'Subscription created successfully',
            'subscription': {
                'plan': user.subscription_plan,
                'status': user.subscription_status,
                'start_date': user.subscription_start_date.isoformat(),
                'end_date': user.subscription_end_date.isoformat()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create subscription: {str(e)}'}), 500

@subscription_bp.route('/subscription/cancel', methods=['POST'])
@cross_origin()
def cancel_subscription():
    """Cancel user's subscription"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code

        if user.subscription_status != 'active':
            return jsonify({'error': 'No active subscription to cancel'}), 400
        
        # Here you would integrate with Stripe to cancel subscription
        
        # Update user subscription status
        user.subscription_status = 'cancelled'
        user.subscription_end_date = datetime.datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Subscription cancelled successfully',
            'subscription': {
                'plan': user.subscription_plan,
                'status': user.subscription_status,
                'end_date': user.subscription_end_date.isoformat()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to cancel subscription: {str(e)}'}), 500

@subscription_bp.route('/subscription/upgrade', methods=['POST'])
@cross_origin()
def upgrade_subscription():
    """Upgrade user's subscription plan"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code

        data = request.get_json()
        new_plan = data.get('plan')
        
        if not new_plan:
            return jsonify({'error': 'New plan is required'}), 400
        
        # Validate plan
        valid_plans = ['starter', 'professional', 'enterprise']
        if new_plan not in valid_plans:
            return jsonify({'error': 'Invalid plan selected'}), 400
        
        # Check if it's actually an upgrade
        plan_hierarchy = {'starter': 1, 'professional': 2, 'enterprise': 3}
        current_level = plan_hierarchy.get(user.subscription_plan, 0)
        new_level = plan_hierarchy.get(new_plan, 0)
        
        if new_level <= current_level:
            return jsonify({'error': 'Can only upgrade to a higher plan'}), 400
        
        # Here you would integrate with Stripe to update subscription
        
        # Update user subscription
        user.subscription_plan = new_plan
        
        db.session.commit()
        
        return jsonify({
            'message': 'Subscription upgraded successfully',
            'subscription': {
                'plan': user.subscription_plan,
                'status': user.subscription_status,
                'start_date': user.subscription_start_date.isoformat() if user.subscription_start_date else None,
                'end_date': user.subscription_end_date.isoformat() if user.subscription_end_date else None
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to upgrade subscription: {str(e)}'}), 500

@subscription_bp.route('/subscription/billing-history', methods=['GET'])
@cross_origin()
def get_billing_history():
    """Get user's billing history"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code

        # Here you would integrate with Stripe to get billing history
        # For now, return mock data
        
        billing_history = [
            {
                'id': 'inv_' + uuid.uuid4().hex[:16],
                'date': user.subscription_start_date.isoformat() if user.subscription_start_date else None,
                'amount': 99.00 if user.subscription_plan == 'professional' else 49.00,
                'status': 'paid',
                'plan': user.subscription_plan
            }
        ] if user.subscription_plan and user.subscription_plan != 'free' else []
        
        return jsonify({
            'billing_history': billing_history
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get billing history: {str(e)}'}), 500



@subscription_bp.route('/create-checkout-session', methods=['POST'])
@cross_origin()
def create_checkout_session():
    """Create Stripe checkout session for subscription"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code

        data = request.get_json()
        price_id = data.get('priceId')
        plan_type = data.get('planType')
        
        if not price_id or not plan_type:
            return jsonify({'error': 'Price ID and plan type are required'}), 400
        
        # Here you would integrate with Stripe to create checkout session
        # For now, we'll simulate successful checkout session creation
        
        checkout_session_id = f"cs_{uuid.uuid4().hex[:24]}"
        checkout_url = f"https://checkout.stripe.com/pay/{checkout_session_id}"
        
        return jsonify({
            'success': True,
            'checkout_url': checkout_url,
            'session_id': checkout_session_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to create checkout session: {str(e)}'}), 500

@subscription_bp.route('/verify-payment', methods=['POST'])
@cross_origin()
def verify_payment():
    """Verify payment after Stripe checkout completion"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code

        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'Session ID is required'}), 400
        
        # Here you would verify the payment with Stripe
        # For now, we'll simulate successful payment verification
        
        # Update user subscription (assuming professional plan for demo)
        user.subscription_plan = 'professional'
        user.subscription_status = 'active'
        user.subscription_start_date = datetime.datetime.utcnow()
        user.subscription_end_date = datetime.datetime.utcnow() + datetime.timedelta(days=30)
        user.stripe_customer_id = f"cus_{uuid.uuid4().hex[:24]}"
        user.stripe_subscription_id = f"sub_{uuid.uuid4().hex[:24]}"
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'subscription': {
                'plan': user.subscription_plan,
                'status': user.subscription_status,
                'start_date': user.subscription_start_date.isoformat(),
                'end_date': user.subscription_end_date.isoformat()
            },
            'user': {
                'id': user.id,
                'subscription_plan': user.subscription_plan,
                'subscription_status': user.subscription_status
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to verify payment: {str(e)}'}), 500

