import os

from flask import Flask, request
from werkzeug.exceptions import HTTPException

from .common.logs.logger import create_logger


def create_app():
    app = Flask(__name__, instance_relative_config=False)

    log_lvl = os.environ.get("DTR_LOG_LEVEL", "INFO")
    version = os.environ["DTR_API_VERSION"]

    app.logger = create_logger("api", log_lvl, "DTR", version)

    @app.route("/", methods=["GET"])
    def index():
        return {"message": "DTR api-server entrypoint"}

    @app.route("/healthz", methods=["GET"])
    def healthz():
        return {"message": "healthy"}

    @app.errorhandler(HTTPException)
    def handle_exception(e: HTTPException):
        response = e.get_response()
        app.logger.error(e.description)
        return response

    @app.before_request
    def log_request():
        body = request.json if request.is_json else "NO BODY"
        app.logger.debug("headers: %s body: %s", dict(request.headers), body)

    from api.routes import v1

    app.register_blueprint(v1, url_prefix="/api/v1")

    from . import db

    db.init_app(app)

    return app
