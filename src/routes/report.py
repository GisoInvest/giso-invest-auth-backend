from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from src.models.user import db
from src.models.data.report import Report
from src.routes.user import get_user_from_token
import uuid
from datetime import datetime

report_bp = Blueprint('report', __name__)

@report_bp.route('/reports', methods=['GET'])
@cross_origin()
def get_reports():
    """Get all reports for the current user"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code
        
        reports = Report.query.filter_by(user_id=user.id).all()
        return jsonify({
            'success': True,
            'reports': [report.to_dict() for report in reports]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get reports: {str(e)}'}), 500

@report_bp.route('/reports/<string:report_id>', methods=['GET'])
@cross_origin()
def get_report(report_id):
    """Get a specific report by ID"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code
        
        report = Report.query.filter_by(id=report_id, user_id=user.id).first()
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        return jsonify({
            'success': True,
            'report': report.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get report: {str(e)}'}), 500

@report_bp.route('/reports', methods=['POST'])
@cross_origin()
def create_report():
    """Create a new report"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        title = data.get('title', '').strip()
        report_type = data.get('report_type', 'investment_analysis')
        
        if not title:
            return jsonify({'error': 'Report title is required'}), 400
        
        # Generate unique ID
        report_id = f"report_{uuid.uuid4().hex}"
        
        # Create new report
        report = Report(
            id=report_id,
            user_id=user.id,
            title=title,
            report_type=report_type,
            generated_at=datetime.utcnow()
        )
        
        # Set content if provided
        if 'content' in data:
            report.content = data['content']
        
        # Set properties if provided
        if 'properties' in data:
            report.properties = data['properties']
        
        db.session.add(report)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Report created successfully',
            'report': report.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create report: {str(e)}'}), 500

@report_bp.route('/reports/<string:report_id>', methods=['DELETE'])
@cross_origin()
def delete_report(report_id):
    """Delete a report"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code
        
        report = Report.query.filter_by(id=report_id, user_id=user.id).first()
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        db.session.delete(report)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Report deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete report: {str(e)}'}), 500

@report_bp.route('/reports/migrate', methods=['POST'])
@cross_origin()
def migrate_reports():
    """Migrate reports from localStorage to database"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code
        
        data = request.get_json()
        if not data or 'reports' not in data:
            return jsonify({'error': 'No reports provided'}), 400
        
        reports = data['reports']
        if not isinstance(reports, list):
            return jsonify({'error': 'Reports must be a list'}), 400
        
        imported_count = 0
        skipped_count = 0
        
        for report_data in reports:
            # Skip invalid data
            if 'id' not in report_data or 'title' not in report_data:
                skipped_count += 1
                continue
            
            # Check if report already exists
            existing = Report.query.filter_by(id=report_data['id'], user_id=user.id).first()
            if existing:
                skipped_count += 1
                continue
            
            # Create report from imported data
            report = Report.from_dict(report_data)
            report.user_id = user.id  # Ensure correct user ID
            
            db.session.add(report)
            imported_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Migrated {imported_count} reports, skipped {skipped_count}',
            'imported_count': imported_count,
            'skipped_count': skipped_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to migrate reports: {str(e)}'}), 500

