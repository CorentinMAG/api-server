from api.app import DTRFlask
from flask import current_app
from typing import cast
from ..errors import NotConfiguredError, OfflineError
from dtr_common.constantes import Mode

def custom_app() -> DTRFlask:
    return cast(DTRFlask, current_app)

def check_gparams_before_request():
    gparams = custom_app().services.params.get()
    if gparams is None:
        raise NotConfiguredError()
    elif gparams.mode == Mode.OFFLINE:
        raise OfflineError()