from flask import Blueprint
from . import configure
from . import mode
from . import policies
from . import requests
from . import notifications
from . import trigger
from . import parameters
from . import worker

v1 = Blueprint("api_v1", __name__)

v1.register_blueprint(configure.bp)
v1.register_blueprint(mode.bp)
v1.register_blueprint(policies.bp)
v1.register_blueprint(requests.bp)
v1.register_blueprint(notifications.bp)
v1.register_blueprint(trigger.bp)
v1.register_blueprint(parameters.bp)
v1.register_blueprint(worker.bp)
