from __future__ import annotations
from api.app import DTRApp
from api.config import create_config, Config
from sqlalchemy_utils import create_database, database_exists

def create_app(config: Config | None = None) -> DTRApp:
    """create and configure the flask application"""
    app = DTRApp(__name__)

    if config:
        app.settings = config
    else:
        app.settings = create_config()
    app.initialize()

    if app.settings.CREATE_DB:
        if not database_exists(app.settings.DATABASE_URL):
            create_database(app.settings.DATABASE_URL)
        from api.models.base import Base
        import api.models

        Base.metadata.create_all(app.engine)
    
    @app.route("/", methods=["GET"])
    def index():
        return {"message": "DTR api-server entrypoint"}
    
    @app.route("/healthz", methods=["GET"])
    def healthz():
        return {"status": "healthy"}
    
    from api.routes import v1
    app.register_blueprint(v1, url_prefix="/api/v1")
    return app

