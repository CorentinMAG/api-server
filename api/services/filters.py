from flask import current_app as app
from typing import cast, Optional

from ..db import db
from ..models import GlobalParameters, TransferPolicy


def switch_mode(mode: str) -> None:
    params = db.session.query(GlobalParameters).first()
    if params is None:
        app.logger.error("no global parameters, the DTR doesn't know how to switch mode")
    else:
        params.mode = mode
        db.session.commit()


def get_params() -> GlobalParameters | None:
    params = db.session.query(GlobalParameters).first()
    return params


def check_policy_params(
    policy_id: Optional[int | None] = None, transfer_policy_name: Optional[str | None] = None
) -> Optional[TransferPolicy | None]:
    if policy_id is not None:
        tr_policy = cast(TransferPolicy | None, db.session.query(TransferPolicy).get(policy_id))
        if tr_policy is None:
            app.logger.error("Transfer policy do not exists for policy_id {}".format(policy_id))
            return None
    elif transfer_policy_name is not None:
        tr_policy = cast(
            TransferPolicy,
            db.session.query(TransferPolicy).filter(TransferPolicy.name == transfer_policy_name).first(),
        )
        if tr_policy is None:
            app.logger.error(
                "Tranfer policy do not exists for  transfer_policy_name {}".format(transfer_policy_name)
            )
            return None
    else:
        pass

    return tr_policy

