import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.subscription import subscription_bp
from src.routes.portfolio import portfolio_bp
from src.routes.property import property_bp
from src.routes.report import report_bp
from src.routes.data import data_bp

app = Flask(__name__)

# Use environment variable for secret key in production
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'giso-invest-auth-secret-key-2024')

# Enable CORS for all routes
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"])

app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(subscription_bp, url_prefix='/api')
app.register_blueprint(portfolio_bp, url_prefix='/api')
app.register_blueprint(property_bp, url_prefix='/api')
app.register_blueprint(report_bp, url_prefix='/api')
app.register_blueprint(data_bp, url_prefix='/api')

# Database configuration - use environment variable for production
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Production database (PostgreSQL)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Development database (SQLite)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    """Home endpoint"""
    return "GISO Invest Authentication Service is running", 200

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "GISO Invest Authentication Service"}, 200

if __name__ == '__main__':
    # Use environment variables for port and host in production
    port = int(os.environ.get('PORT', 5001))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    app.run(host=host, port=port, debug=debug)

