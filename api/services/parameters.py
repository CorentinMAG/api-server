from flask import current_app as app
from typing import cast
from ..db import db
from ..models import PeriodicalParameters


def update_params(param_id: int, next_polling_min_time: str) -> None:
    """
    Update periodical parameters
    """
    periodical_params = cast(PeriodicalParameters, db.session.query(PeriodicalParameters).first())
    periodical_params.next_polling_min_time = next_polling_min_time
    db.session.commit()
    app.logger.debug(
        "Update periodical parameter id {} with next polling min time {}".format(
            param_id, next_polling_min_time
        )
    )
