from flask import Blueprint, request, jsonify
from src.models.user import User
from src.database import db
from src.utils.auth import token_required
import datetime
import uuid

subscription_bp = Blueprint('subscription', __name__)

@subscription_bp.route('/subscription/status', methods=['GET'])
@token_required
def get_subscription_status(current_user):
    """Get current user's subscription status"""
    try:
        user = User.query.get(current_user.id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Calculate trial status
        trial_status = user.calculate_trial_status()
        
        subscription_data = {
            'user_id': user.id,
            'subscription_status': user.subscription_status,
            'subscription_plan': user.subscription_plan,
            'trial_active': user.trial_active,
            'trial_start_date': user.trial_start_date.isoformat() if user.trial_start_date else None,
            'trial_end_date': user.trial_end_date.isoformat() if user.trial_end_date else None,
            'subscription_start_date': user.subscription_start_date.isoformat() if user.subscription_start_date else None,
            'next_billing_date': user.next_billing_date.isoformat() if user.next_billing_date else None,
            'trial_status': trial_status,
            'can_access_app': trial_status['can_access'],
            'payment_required': trial_status['payment_required']
        }
        
        return jsonify(subscription_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@subscription_bp.route('/subscription/create', methods=['POST'])
@token_required
def create_subscription(current_user):
    """Create a new subscription for the user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['plan_id', 'payment_intent_id', 'customer_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        user = User.query.get(current_user.id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Update user subscription
        user.subscription_status = 'active'
        user.subscription_plan = data['plan_id']
        user.plan = data['plan_id']
        user.trial_active = False
        user.payment_required = False
        user.subscription_start_date = datetime.datetime.utcnow()
        user.last_payment_date = datetime.datetime.utcnow()
        user.next_billing_date = datetime.datetime.utcnow() + datetime.timedelta(days=30)
        user.stripe_customer_id = data['customer_id']
        user.stripe_payment_intent_id = data['payment_intent_id']
        
        # Save to database
        db.session.commit()
        
        return jsonify({
            'message': 'Subscription created successfully',
            'subscription_status': user.subscription_status,
            'subscription_plan': user.subscription_plan,
            'next_billing_date': user.next_billing_date.isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@subscription_bp.route('/subscription/update', methods=['PUT'])
@token_required
def update_subscription(current_user):
    """Update user's subscription plan"""
    try:
        data = request.get_json()
        
        if 'plan_id' not in data:
            return jsonify({'error': 'Missing plan_id'}), 400
        
        user = User.query.get(current_user.id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Update subscription plan
        old_plan = user.subscription_plan
        user.subscription_plan = data['plan_id']
        user.plan = data['plan_id']
        
        # If upgrading, update billing date
        if data.get('immediate_billing', False):
            user.last_payment_date = datetime.datetime.utcnow()
            user.next_billing_date = datetime.datetime.utcnow() + datetime.timedelta(days=30)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Subscription updated from {old_plan} to {data["plan_id"]}',
            'subscription_plan': user.subscription_plan,
            'next_billing_date': user.next_billing_date.isoformat() if user.next_billing_date else None
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@subscription_bp.route('/subscription/cancel', methods=['POST'])
@token_required
def cancel_subscription(current_user):
    """Cancel user's subscription"""
    try:
        user = User.query.get(current_user.id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Update subscription status
        user.subscription_status = 'cancelled'
        user.subscription_plan = 'free'
        user.plan = 'free'
        user.payment_required = False
        user.trial_active = False
        
        db.session.commit()
        
        return jsonify({
            'message': 'Subscription cancelled successfully',
            'subscription_status': user.subscription_status,
            'subscription_plan': user.subscription_plan
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@subscription_bp.route('/subscription/reactivate', methods=['POST'])
@token_required
def reactivate_subscription(current_user):
    """Reactivate a cancelled subscription"""
    try:
        data = request.get_json()
        
        user = User.query.get(current_user.id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.subscription_status != 'cancelled':
            return jsonify({'error': 'Subscription is not cancelled'}), 400
        
        # Reactivate subscription
        user.subscription_status = 'active'
        user.subscription_plan = data.get('plan_id', 'professional')
        user.plan = user.subscription_plan
        user.subscription_start_date = datetime.datetime.utcnow()
        user.last_payment_date = datetime.datetime.utcnow()
        user.next_billing_date = datetime.datetime.utcnow() + datetime.timedelta(days=30)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Subscription reactivated successfully',
            'subscription_status': user.subscription_status,
            'subscription_plan': user.subscription_plan,
            'next_billing_date': user.next_billing_date.isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@subscription_bp.route('/subscription/billing-history', methods=['GET'])
@token_required
def get_billing_history(current_user):
    """Get user's billing history"""
    try:
        user = User.query.get(current_user.id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # For now, return basic billing info
        # In a real app, this would query a billing/payments table
        billing_history = []
        
        if user.last_payment_date:
            billing_history.append({
                'date': user.last_payment_date.isoformat(),
                'amount': get_plan_price(user.subscription_plan),
                'plan': user.subscription_plan,
                'status': 'paid',
                'payment_method': 'card'
            })
        
        return jsonify({
            'billing_history': billing_history,
            'next_billing_date': user.next_billing_date.isoformat() if user.next_billing_date else None,
            'current_plan': user.subscription_plan
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_plan_price(plan_id):
    """Get the price for a given plan"""
    plan_prices = {
        'free': 0,
        'starter': 49,
        'professional': 99,
        'enterprise': 199
    }
    return plan_prices.get(plan_id, 0)

@subscription_bp.route('/subscription/plans', methods=['GET'])
def get_available_plans():
    """Get all available subscription plans"""
    try:
        plans = [
            {
                'id': 'free',
                'name': 'Free',
                'price': 0,
                'currency': 'GBP',
                'interval': 'forever',
                'features': [
                    '1 Investment Strategy',
                    'Basic property analysis',
                    '5 property analyses per month',
                    'Email support'
                ]
            },
            {
                'id': 'starter',
                'name': 'Starter',
                'price': 49,
                'currency': 'GBP',
                'interval': 'month',
                'features': [
                    '5 Investment Strategies',
                    'Advanced property analysis',
                    'Basic deal packaging',
                    '50 property analyses per month',
                    'Priority email support'
                ]
            },
            {
                'id': 'professional',
                'name': 'Professional',
                'price': 99,
                'currency': 'GBP',
                'interval': 'month',
                'features': [
                    'All 10 Investment Strategies',
                    'Comprehensive property analysis',
                    'Advanced deal packaging',
                    'Unlimited property analyses',
                    'Priority support (24/7)',
                    'Portfolio tracking'
                ],
                'popular': True
            },
            {
                'id': 'enterprise',
                'name': 'Enterprise',
                'price': 199,
                'currency': 'GBP',
                'interval': 'month',
                'features': [
                    'All Professional features',
                    'Team collaboration tools',
                    'Custom branding',
                    'Dedicated account manager',
                    'API access',
                    'Advanced analytics'
                ]
            }
        ]
        
        return jsonify({'plans': plans}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

