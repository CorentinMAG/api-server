from __future__ import annotations
from flask import Flask
from .error_handlers import register_error_handlers
from .db import init_app as init_db_app
from .config import logger

def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.logger = logger

    @app.route("/", methods=["GET"])
    def index():
        return {"message": "DTR api-server entrypoint"}

    @app.route("/healthz", methods=["GET"])
    def healthz():
        """
        Basic health check endpoint for Kubernetes readiness probes
        """
        return {"status": "healthy", "service": "api-server"}
    
    from api.routes import v1

    # Initialize extensions
    init_db_app(app)
    register_error_handlers(app)
    app.register_blueprint(v1, url_prefix="/dtr/v1")
    return app
