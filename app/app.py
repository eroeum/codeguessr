"""Factory for creating the Flask application."""
import logging
import os

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_cors import CORS
from flask_smorest import Api

from app.config import DefaultConfig
from app.views import blp as view_blueprint
from app.api.code import blp as api_code_blueprint

bootstrap = Bootstrap()

def create_app(path: str = os.path.abspath(__file__)) -> Flask:
    """Factory to create the application."""
    app = Flask(__name__)
    app.logger.setLevel(logging.INFO)
    app.config.from_object(DefaultConfig)

    app.config["CODE_PATH"] = path
    app.logger.info("Using Path: %s", path)
    if not os.path.exists(path):
        raise ValueError(f"Invalid path: {path}")

    Bootstrap(app)
    api = Api(app)
    CORS(app)

    # Register APIs
    api.register_blueprint(api_code_blueprint)

    # Register views
    app.register_blueprint(view_blueprint)
    return app
