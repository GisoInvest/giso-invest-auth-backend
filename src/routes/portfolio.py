from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from src.models.user import db
from src.models.data.portfolio import Portfolio
from src.routes.user import get_user_from_token
import uuid
from datetime import datetime

portfolio_bp = Blueprint('portfolio', __name__)

@portfolio_bp.route('/portfolios', methods=['GET'])
@cross_origin()
def get_portfolios():
    """Get all portfolios for the current user"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code
        
        portfolios = Portfolio.query.filter_by(user_id=user.id).all()
        return jsonify({
            'success': True,
            'portfolios': [portfolio.to_dict() for portfolio in portfolios]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get portfolios: {str(e)}'}), 500

@portfolio_bp.route('/portfolios/<string:portfolio_id>', methods=['GET'])
@cross_origin()
def get_portfolio(portfolio_id):
    """Get a specific portfolio by ID"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code
        
        portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=user.id).first()
        if not portfolio:
            return jsonify({'error': 'Portfolio not found'}), 404
        
        return jsonify({
            'success': True,
            'portfolio': portfolio.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get portfolio: {str(e)}'}), 500

@portfolio_bp.route('/portfolios', methods=['POST'])
@cross_origin()
def create_portfolio():
    """Create a new portfolio"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        
        if not name:
            return jsonify({'error': 'Portfolio name is required'}), 400
        
        # Generate unique IDs
        portfolio_id = f"portfolio_{uuid.uuid4().hex}"
        share_id = f"share_{uuid.uuid4().hex}"
        
        # Create new portfolio
        portfolio = Portfolio(
            id=portfolio_id,
            user_id=user.id,
            name=name,
            description=description,
            share_id=share_id,
            is_public=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Set deal packages if provided
        if 'deal_packages' in data:
            portfolio.deal_packages = data['deal_packages']
            portfolio.calculate_stats()
        
        db.session.add(portfolio)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Portfolio created successfully',
            'portfolio': portfolio.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create portfolio: {str(e)}'}), 500

@portfolio_bp.route('/portfolios/<string:portfolio_id>', methods=['PUT'])
@cross_origin()
def update_portfolio(portfolio_id):
    """Update an existing portfolio"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code
        
        portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=user.id).first()
        if not portfolio:
            return jsonify({'error': 'Portfolio not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update basic fields
        if 'name' in data:
            portfolio.name = data['name'].strip()
        
        if 'description' in data:
            portfolio.description = data['description'].strip()
        
        if 'is_public' in data:
            portfolio.is_public = data['is_public']
            
            # Generate new share ID when making public
            if portfolio.is_public and not portfolio.share_id:
                portfolio.share_id = f"share_{uuid.uuid4().hex}"
        
        # Update deal packages if provided
        if 'deal_packages' in data:
            portfolio.deal_packages = data['deal_packages']
            portfolio.calculate_stats()
        
        portfolio.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Portfolio updated successfully',
            'portfolio': portfolio.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update portfolio: {str(e)}'}), 500

@portfolio_bp.route('/portfolios/<string:portfolio_id>', methods=['DELETE'])
@cross_origin()
def delete_portfolio(portfolio_id):
    """Delete a portfolio"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code
        
        portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=user.id).first()
        if not portfolio:
            return jsonify({'error': 'Portfolio not found'}), 404
        
        db.session.delete(portfolio)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Portfolio deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete portfolio: {str(e)}'}), 500

@portfolio_bp.route('/portfolios/share/<string:share_id>', methods=['GET'])
@cross_origin()
def get_shared_portfolio(share_id):
    """Get a shared portfolio by share ID"""
    try:
        portfolio = Portfolio.query.filter_by(share_id=share_id, is_public=True).first()
        if not portfolio:
            return jsonify({'error': 'Shared portfolio not found'}), 404
        
        return jsonify({
            'success': True,
            'portfolio': portfolio.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get shared portfolio: {str(e)}'}), 500

@portfolio_bp.route('/portfolios/import', methods=['POST'])
@cross_origin()
def import_portfolio():
    """Import a portfolio from localStorage data"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate portfolio data
        if 'id' not in data or 'name' not in data:
            return jsonify({'error': 'Invalid portfolio data'}), 400
        
        # Check if portfolio already exists
        existing = Portfolio.query.filter_by(id=data['id'], user_id=user.id).first()
        if existing:
            return jsonify({'error': 'Portfolio already exists', 'portfolio': existing.to_dict()}), 409
        
        # Create portfolio from imported data
        portfolio = Portfolio.from_dict(data)
        portfolio.user_id = user.id  # Ensure correct user ID
        
        db.session.add(portfolio)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Portfolio imported successfully',
            'portfolio': portfolio.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to import portfolio: {str(e)}'}), 500

@portfolio_bp.route('/portfolios/migrate', methods=['POST'])
@cross_origin()
def migrate_portfolios():
    """Migrate portfolios from localStorage to database"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code
        
        data = request.get_json()
        if not data or 'portfolios' not in data:
            return jsonify({'error': 'No portfolios provided'}), 400
        
        portfolios = data['portfolios']
        if not isinstance(portfolios, list):
            return jsonify({'error': 'Portfolios must be a list'}), 400
        
        imported_count = 0
        skipped_count = 0
        
        for portfolio_data in portfolios:
            # Skip invalid data
            if 'id' not in portfolio_data or 'name' not in portfolio_data:
                skipped_count += 1
                continue
            
            # Check if portfolio already exists
            existing = Portfolio.query.filter_by(id=portfolio_data['id'], user_id=user.id).first()
            if existing:
                skipped_count += 1
                continue
            
            # Create portfolio from imported data
            portfolio = Portfolio.from_dict(portfolio_data)
            portfolio.user_id = user.id  # Ensure correct user ID
            
            db.session.add(portfolio)
            imported_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Migrated {imported_count} portfolios, skipped {skipped_count}',
            'imported_count': imported_count,
            'skipped_count': skipped_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to migrate portfolios: {str(e)}'}), 500

