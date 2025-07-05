from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from src.models.user import db
from src.models.data.portfolio import Portfolio
from src.models.data.property import Property
from src.models.data.report import Report
from src.routes.user import get_user_from_token
from datetime import datetime

data_bp = Blueprint('data', __name__)

@data_bp.route('/data/migrate', methods=['POST'])
@cross_origin()
def migrate_all_data():
    """Migrate all user data from localStorage to database"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        results = {
            'properties': {'imported': 0, 'skipped': 0},
            'portfolios': {'imported': 0, 'skipped': 0},
            'reports': {'imported': 0, 'skipped': 0}
        }
        
        # Migrate properties
        if 'properties' in data and isinstance(data['properties'], list):
            for property_data in data['properties']:
                # Skip invalid data
                if 'id' not in property_data or 'address' not in property_data:
                    results['properties']['skipped'] += 1
                    continue
                
                # Check if property already exists
                existing = Property.query.filter_by(id=property_data['id'], user_id=user.id).first()
                if existing:
                    results['properties']['skipped'] += 1
                    continue
                
                # Create property from imported data
                property = Property.from_dict(property_data)
                property.user_id = user.id  # Ensure correct user ID
                
                db.session.add(property)
                results['properties']['imported'] += 1
        
        # Migrate portfolios
        if 'portfolios' in data and isinstance(data['portfolios'], list):
            for portfolio_data in data['portfolios']:
                # Skip invalid data
                if 'id' not in portfolio_data or 'name' not in portfolio_data:
                    results['portfolios']['skipped'] += 1
                    continue
                
                # Check if portfolio already exists
                existing = Portfolio.query.filter_by(id=portfolio_data['id'], user_id=user.id).first()
                if existing:
                    results['portfolios']['skipped'] += 1
                    continue
                
                # Create portfolio from imported data
                portfolio = Portfolio.from_dict(portfolio_data)
                portfolio.user_id = user.id  # Ensure correct user ID
                
                db.session.add(portfolio)
                results['portfolios']['imported'] += 1
        
        # Migrate reports
        if 'reports' in data and isinstance(data['reports'], list):
            for report_data in data['reports']:
                # Skip invalid data
                if 'id' not in report_data or 'title' not in report_data:
                    results['reports']['skipped'] += 1
                    continue
                
                # Check if report already exists
                existing = Report.query.filter_by(id=report_data['id'], user_id=user.id).first()
                if existing:
                    results['reports']['skipped'] += 1
                    continue
                
                # Create report from imported data
                report = Report.from_dict(report_data)
                report.user_id = user.id  # Ensure correct user ID
                
                db.session.add(report)
                results['reports']['imported'] += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Data migration completed successfully',
            'results': results
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to migrate data: {str(e)}'}), 500

@data_bp.route('/data/stats', methods=['GET'])
@cross_origin()
def get_user_stats():
    """Get user data statistics"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code
        
        # Count properties
        property_count = Property.query.filter_by(user_id=user.id).count()
        
        # Count portfolios
        portfolio_count = Portfolio.query.filter_by(user_id=user.id).count()
        
        # Count reports
        report_count = Report.query.filter_by(user_id=user.id).count()
        
        # Calculate total value and average ROI
        total_value = 0
        total_roi = 0
        roi_count = 0
        
        properties = Property.query.filter_by(user_id=user.id).all()
        for prop in properties:
            if prop.price:
                total_value += prop.price
            
            if prop.roi is not None:
                total_roi += prop.roi
                roi_count += 1
        
        avg_roi = total_roi / roi_count if roi_count > 0 else 0
        
        # Count deal packages
        deal_package_count = 0
        portfolios = Portfolio.query.filter_by(user_id=user.id).all()
        for portfolio in portfolios:
            deal_package_count += len(portfolio.deal_packages)
        
        return jsonify({
            'success': True,
            'stats': {
                'property_count': property_count,
                'portfolio_count': portfolio_count,
                'report_count': report_count,
                'deal_package_count': deal_package_count,
                'total_value': total_value,
                'avg_roi': avg_roi
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get user stats: {str(e)}'}), 500

