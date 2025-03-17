"""
Database Table Comparison Tool - A web application to compare tables between databases.
"""
import os
import secrets
from flask import Flask
from flask_cors import CORS

def create_app(test_config=None):
    """Create and configure the Flask application"""
    app = Flask(__name__, 
                static_folder='../static',
                template_folder='templates')
    
    # Set up configuration
    app.config['SECRET_KEY'] = secrets.token_hex(16)
    
    # Configure CORS
    CORS(app, resources={
        r"/comparison/api/*": {
            "origins": ["http://localhost:5000", "http://localhost:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.connections import connections_bp
    from app.routes.comparison import comparison_bp
    from app.routes.errors import errors_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(connections_bp)
    app.register_blueprint(comparison_bp)
    app.register_blueprint(errors_bp)
    
    return app
