from flask import current_app as app
from typing import cast

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


def set_transfer_policy_params(policy_id: int) -> TransferPolicy:
    global_params = db.session.query(GlobalParameters).first()

    tr_policy = cast(TransferPolicy | None, db.session.query(TransferPolicy).get(policy_id))

    if tr_policy is None:
        app.logger.error("Policy id: %d doesn't exist", policy_id)
        raise Exception("Policy does not exists")  # create class to format exception

    if not tr_policy.parameters.only_new_data:
        tr_policy.parameters.only_new_data = global_params.only_new_data
    elif tr_policy.dest.tmp_prefix_dest is None:
        tr_policy.dest.tmp_prefix_dest = global_params.tmp_prefix_dest
    elif tr_policy.dest.final_prefix_dest is None:
        tr_policy.dest.final_prefix_dest = global_params.final_prefix_dest
    elif tr_policy.parameters.max_retry is None:
        tr_policy.parameters.max_retry = global_params.max_retry
    elif tr_policy.parameters.retry_delay is None:
        tr_policy.parameters.retry_delay = global_params.retry_delay
    elif tr_policy.parameters.transfer_requests_history is None:
        tr_policy.parameters.transfer_requests_history = global_params.transfer_requests_history
    elif not tr_policy.parameters.compress:
        tr_policy.parameters.compress = global_params.compress
    elif tr_policy.parameters.transfer_timeout is None:
        tr_policy.parameters.transfer_timeout = global_params.transfer_timeout
    elif tr_policy.queue.queue_timeout is None:
        tr_policy.queue.queue_timeout = global_params.queue_timeout
    else:
        pass

    return tr_policy
