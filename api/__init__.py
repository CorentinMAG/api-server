from __future__ import annotations
from .handlers import register_handlers
from .config import get_config, Config
from flask import g
from .app import DTRFlask
import uuid

def create_app(config: Config | None = None) -> DTRFlask:
    """create and configure the flask application"""
    app = DTRFlask(__name__)

    if config:
        app.settings = config
    else:
        app.settings = get_config()

    from api.routes import v1

    # Initialize extensions
    app.init_logger()
    app.init_database()
    register_handlers(app)
    app.register_blueprint(v1, url_prefix="/dtr/v1")

    @app.route("/healthz", methods=["GET"])
    def healthz():
        """health check endpoint"""
        return {
            "status": "healthy"
            }, 200
    
    @app.before_request
    def assign_request_id():
        # g is a special object that is unique
        # for each request
        g.request_id = str(uuid.uuid4())

    return app
