from flask import Flask, request
from werkzeug.exceptions import HTTPException
import logging
from .common.logs.formatter import JsonFormatter
from flask.logging import default_handler

def create_app():

    app = Flask(__name__, instance_relative_config=False)

    app.logger.setLevel(logging.INFO)
    formatter = JsonFormatter("DTR", "api", "1.1.0")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    app.logger.addHandler(stream_handler)
    app.logger.removeHandler(default_handler)

    @app.route("/", methods = ["GET"])
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
        app.logger.debug("headers: %s, body: %s", request.headers, request.json)

    from . import routing
    app.register_blueprint(routing.bp)

    from . import db
    db.init_app(app)

    return app