import os
from flask import Flask
from dotenv import load_dotenv

# Load environment variables from .env if present (but do not commit .env)
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-in-production')
    ENV = os.environ.get('FLASK_ENV', 'production')

def create_app(config_class=Config):
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(config_class)

    # Register blueprints
    from .home import bp as home_bp
    from .health import bp as health_bp
    app.register_blueprint(home_bp)
    app.register_blueprint(health_bp)

    # Error handlers
    from flask import render_template, jsonify
    @app.errorhandler(404)
    def not_found(e):
        if app.config.get('ENV') == 'development':
            return render_template('404.html'), 404
        return jsonify(error='not found'), 404

    @app.errorhandler(500)
    def server_error(e):
        if app.config.get('ENV') == 'development':
            return render_template('500.html'), 500
        return jsonify(error='server error'), 500

    return app
