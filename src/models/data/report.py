from src.models.user import db
from datetime import datetime
import json

class Report(db.Model):
    """Report model for storing user generated reports"""
    id = db.Column(db.String(100), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    generated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    report_type = db.Column(db.String(50), nullable=False, default='investment_analysis')
    
    # Store report content and metadata as JSON
    content_json = db.Column(db.Text, nullable=True)
    properties_json = db.Column(db.Text, nullable=True)
    
    # Statistics
    property_count = db.Column(db.Integer, default=0)
    avg_roi = db.Column(db.Float, default=0.0)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('reports', lazy=True))
    
    @property
    def content(self):
        """Get report content as Python object"""
        if not self.content_json:
            return {}
        return json.loads(self.content_json)
    
    @content.setter
    def content(self, content_data):
        """Set report content from Python object"""
        self.content_json = json.dumps(content_data)
    
    @property
    def properties(self):
        """Get report properties as Python objects"""
        if not self.properties_json:
            return []
        return json.loads(self.properties_json)
    
    @properties.setter
    def properties(self, properties_data):
        """Set report properties from Python objects"""
        self.properties_json = json.dumps(properties_data)
        self.property_count = len(properties_data)
        
        # Calculate average ROI
        total_roi = 0
        property_count = 0
        
        for prop in properties_data:
            if 'roi' in prop and prop['roi'] is not None:
                total_roi += prop['roi']
                property_count += 1
        
        self.avg_roi = total_roi / property_count if property_count > 0 else 0
    
    def to_dict(self):
        """Convert report to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'report_type': self.report_type,
            'property_count': self.property_count,
            'avg_roi': self.avg_roi,
            'content': self.content,
            'properties': self.properties
        }
    
    @staticmethod
    def from_dict(data):
        """Create report from dictionary"""
        report = Report(
            id=data.get('id'),
            user_id=data.get('user_id'),
            title=data.get('title'),
            report_type=data.get('report_type', 'investment_analysis')
        )
        
        if 'generated_at' in data and data['generated_at']:
            try:
                report.generated_at = datetime.fromisoformat(data['generated_at'])
            except (ValueError, TypeError):
                report.generated_at = datetime.utcnow()
        
        if 'content' in data:
            report.content = data['content']
        
        if 'properties' in data:
            report.properties = data['properties']
        
        return report

