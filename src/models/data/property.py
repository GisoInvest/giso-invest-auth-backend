from src.models.user import db
from datetime import datetime
import json

class Property(db.Model):
    """Property model for storing analyzed properties"""
    id = db.Column(db.String(100), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Basic property details
    price = db.Column(db.Float, nullable=True)
    monthly_rent = db.Column(db.Float, nullable=True)
    bedrooms = db.Column(db.Integer, nullable=True)
    bathrooms = db.Column(db.Integer, nullable=True)
    property_type = db.Column(db.String(50), nullable=True)
    strategy = db.Column(db.String(50), nullable=True)
    roi = db.Column(db.Float, nullable=True)
    
    # Store additional details as JSON
    details_json = db.Column(db.Text, nullable=True)
    analysis_json = db.Column(db.Text, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('properties', lazy=True))
    
    @property
    def details(self):
        """Get property details as Python object"""
        if not self.details_json:
            return {}
        return json.loads(self.details_json)
    
    @details.setter
    def details(self, details_data):
        """Set property details from Python object"""
        self.details_json = json.dumps(details_data)
    
    @property
    def analysis(self):
        """Get property analysis as Python object"""
        if not self.analysis_json:
            return {}
        return json.loads(self.analysis_json)
    
    @analysis.setter
    def analysis(self, analysis_data):
        """Set property analysis from Python object"""
        self.analysis_json = json.dumps(analysis_data)
    
    def to_dict(self):
        """Convert property to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'address': self.address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'price': self.price,
            'monthly_rent': self.monthly_rent,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'property_type': self.property_type,
            'strategy': self.strategy,
            'roi': self.roi,
            'details': self.details,
            'analysis': self.analysis
        }
    
    @staticmethod
    def from_dict(data):
        """Create property from dictionary"""
        property = Property(
            id=data.get('id'),
            user_id=data.get('user_id'),
            address=data.get('address'),
            price=data.get('price'),
            monthly_rent=data.get('monthly_rent'),
            bedrooms=data.get('bedrooms'),
            bathrooms=data.get('bathrooms'),
            property_type=data.get('property_type'),
            strategy=data.get('strategy'),
            roi=data.get('roi')
        )
        
        if 'created_at' in data and data['created_at']:
            try:
                property.created_at = datetime.fromisoformat(data['created_at'])
            except (ValueError, TypeError):
                property.created_at = datetime.utcnow()
        
        if 'updated_at' in data and data['updated_at']:
            try:
                property.updated_at = datetime.fromisoformat(data['updated_at'])
            except (ValueError, TypeError):
                property.updated_at = datetime.utcnow()
        
        if 'details' in data:
            property.details = data['details']
        
        if 'analysis' in data:
            property.analysis = data['analysis']
        
        return property

