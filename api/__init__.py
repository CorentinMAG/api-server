from __future__ import annotations

from logging import getLogger

from sqlalchemy_utils import create_database, database_exists

from api.app import DTRApp
from api.config import Config, create_config

logger = getLogger(__name__)


def create_app(config: Config | None = None) -> DTRApp:
    app = DTRApp(__name__)

    if config:
        app.settings = config
    else:
        app.settings = create_config()
    app.initialize()

    if app.settings.CREATE_DB:
        if database_exists(app.settings.DATABASE_URL):
            logger.info("Database already exists. Skipping creation.")
        else:
            logger.info("Creating database...")
            create_database(app.settings.DATABASE_URL)
            logger.info("Database created successfully.")
        import api.models
        from api.models.base import Base

        Base.metadata.create_all(app.engine)

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
    app.register_blueprint(v1, url_prefix="/api/v1")
    return app
