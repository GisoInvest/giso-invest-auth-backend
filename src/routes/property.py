from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from src.models.user import db
from src.models.data.property import Property
from src.routes.user import get_user_from_token
import uuid
from datetime import datetime

property_bp = Blueprint('property', __name__)

@property_bp.route('/properties', methods=['GET'])
@cross_origin()
def get_properties():
    """Get all properties for the current user"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code
        
        properties = Property.query.filter_by(user_id=user.id).all()
        return jsonify({
            'success': True,
            'properties': [prop.to_dict() for prop in properties]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get properties: {str(e)}'}), 500

@property_bp.route('/properties/<string:property_id>', methods=['GET'])
@cross_origin()
def get_property(property_id):
    """Get a specific property by ID"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code
        
        property = Property.query.filter_by(id=property_id, user_id=user.id).first()
        if not property:
            return jsonify({'error': 'Property not found'}), 404
        
        return jsonify({
            'success': True,
            'property': property.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get property: {str(e)}'}), 500

@property_bp.route('/properties', methods=['POST'])
@cross_origin()
def create_property():
    """Create a new property"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        address = data.get('address', '').strip()
        
        if not address:
            return jsonify({'error': 'Property address is required'}), 400
        
        # Generate unique ID
        property_id = f"property_{uuid.uuid4().hex}"
        
        # Create new property
        property = Property(
            id=property_id,
            user_id=user.id,
            address=address,
            price=data.get('price'),
            monthly_rent=data.get('monthly_rent'),
            bedrooms=data.get('bedrooms'),
            bathrooms=data.get('bathrooms'),
            property_type=data.get('property_type'),
            strategy=data.get('strategy'),
            roi=data.get('roi'),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Set details if provided
        if 'details' in data:
            property.details = data['details']
        
        # Set analysis if provided
        if 'analysis' in data:
            property.analysis = data['analysis']
        
        db.session.add(property)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Property created successfully',
            'property': property.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create property: {str(e)}'}), 500

@property_bp.route('/properties/<string:property_id>', methods=['PUT'])
@cross_origin()
def update_property(property_id):
    """Update an existing property"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code
        
        property = Property.query.filter_by(id=property_id, user_id=user.id).first()
        if not property:
            return jsonify({'error': 'Property not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update basic fields
        if 'address' in data:
            property.address = data['address'].strip()
        
        if 'price' in data:
            property.price = data['price']
        
        if 'monthly_rent' in data:
            property.monthly_rent = data['monthly_rent']
        
        if 'bedrooms' in data:
            property.bedrooms = data['bedrooms']
        
        if 'bathrooms' in data:
            property.bathrooms = data['bathrooms']
        
        if 'property_type' in data:
            property.property_type = data['property_type']
        
        if 'strategy' in data:
            property.strategy = data['strategy']
        
        if 'roi' in data:
            property.roi = data['roi']
        
        # Update details if provided
        if 'details' in data:
            property.details = data['details']
        
        # Update analysis if provided
        if 'analysis' in data:
            property.analysis = data['analysis']
        
        property.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Property updated successfully',
            'property': property.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update property: {str(e)}'}), 500

@property_bp.route('/properties/<string:property_id>', methods=['DELETE'])
@cross_origin()
def delete_property(property_id):
    """Delete a property"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code
        
        property = Property.query.filter_by(id=property_id, user_id=user.id).first()
        if not property:
            return jsonify({'error': 'Property not found'}), 404
        
        db.session.delete(property)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Property deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete property: {str(e)}'}), 500

@property_bp.route('/properties/migrate', methods=['POST'])
@cross_origin()
def migrate_properties():
    """Migrate properties from localStorage to database"""
    try:
        user, error_response, status_code = get_user_from_token()
        if error_response:
            return jsonify(error_response), status_code
        
        data = request.get_json()
        if not data or 'properties' not in data:
            return jsonify({'error': 'No properties provided'}), 400
        
        properties = data['properties']
        if not isinstance(properties, list):
            return jsonify({'error': 'Properties must be a list'}), 400
        
        imported_count = 0
        skipped_count = 0
        
        for property_data in properties:
            # Skip invalid data
            if 'id' not in property_data or 'address' not in property_data:
                skipped_count += 1
                continue
            
            # Check if property already exists
            existing = Property.query.filter_by(id=property_data['id'], user_id=user.id).first()
            if existing:
                skipped_count += 1
                continue
            
            # Create property from imported data
            property = Property.from_dict(property_data)
            property.user_id = user.id  # Ensure correct user ID
            
            db.session.add(property)
            imported_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Migrated {imported_count} properties, skipped {skipped_count}',
            'imported_count': imported_count,
            'skipped_count': skipped_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to migrate properties: {str(e)}'}), 500

