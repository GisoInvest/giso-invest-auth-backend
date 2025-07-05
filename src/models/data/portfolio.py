from src.models.user import db
from datetime import datetime
import json

class Portfolio(db.Model):
    """Portfolio model for storing user portfolios"""
    id = db.Column(db.String(100), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    total_value = db.Column(db.Float, default=0.0)
    total_properties = db.Column(db.Integer, default=0)
    avg_roi = db.Column(db.Float, default=0.0)
    share_id = db.Column(db.String(100), unique=True, nullable=True)
    is_public = db.Column(db.Boolean, default=False)
    
    # Store deal packages as JSON
    deal_packages_json = db.Column(db.Text, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('portfolios', lazy=True))
    
    @property
    def deal_packages(self):
        """Get deal packages as Python objects"""
        if not self.deal_packages_json:
            return []
        return json.loads(self.deal_packages_json)
    
    @deal_packages.setter
    def deal_packages(self, packages):
        """Set deal packages from Python objects"""
        self.deal_packages_json = json.dumps(packages)
    
    def calculate_stats(self):
        """Calculate portfolio statistics"""
        packages = self.deal_packages
        
        if not packages:
            self.total_value = 0
            self.total_properties = 0
            self.avg_roi = 0
            return
        
        total_value = sum(pkg.get('totalValue', 0) for pkg in packages)
        total_properties = sum(len(pkg.get('properties', [])) for pkg in packages)
        
        # Calculate average ROI
        total_roi = 0
        property_count = 0
        
        for pkg in packages:
            for prop in pkg.get('properties', []):
                if 'roi' in prop and prop['roi'] is not None:
                    total_roi += prop['roi']
                    property_count += 1
        
        avg_roi = total_roi / property_count if property_count > 0 else 0
        
        self.total_value = total_value
        self.total_properties = total_properties
        self.avg_roi = avg_roi
    
    def to_dict(self):
        """Convert portfolio to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'total_value': self.total_value,
            'total_properties': self.total_properties,
            'avg_roi': self.avg_roi,
            'share_id': self.share_id,
            'is_public': self.is_public,
            'deal_packages': self.deal_packages
        }
    
    @staticmethod
    def from_dict(data):
        """Create portfolio from dictionary"""
        portfolio = Portfolio(
            id=data.get('id'),
            user_id=data.get('user_id'),
            name=data.get('name'),
            description=data.get('description'),
            share_id=data.get('share_id'),
            is_public=data.get('is_public', False)
        )
        
        if 'created_at' in data and data['created_at']:
            try:
                portfolio.created_at = datetime.fromisoformat(data['created_at'])
            except (ValueError, TypeError):
                portfolio.created_at = datetime.utcnow()
        
        if 'updated_at' in data and data['updated_at']:
            try:
                portfolio.updated_at = datetime.fromisoformat(data['updated_at'])
            except (ValueError, TypeError):
                portfolio.updated_at = datetime.utcnow()
        
        if 'deal_packages' in data:
            portfolio.deal_packages = data['deal_packages']
        
        portfolio.calculate_stats()
        return portfolio

