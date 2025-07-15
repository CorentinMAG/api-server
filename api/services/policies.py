from __future__ import annotations

import datetime
from typing import TypedDict, cast

from dtr_common.constantes import Type
from sqlalchemy import or_

from api.db import db
from api.models import (
    DestinationPolicy,
    PeriodicalParameters,
    Queue,
    SourcePolicy,
    Target,
    TransferPolicy,
    TransferPolicyParameters,
)

from .utils import db_retry, transactional
from sqlalchemy.orm import exc as orm_exc


class FilterPolicyParams(TypedDict, total=False):
    enabled: bool
    type: Type | str
    src: str
    dests: str
    queues: str
    id: int
    ids: str
    next_polling_min_time: bool


@db_retry(total=3, initial_delay=1, max_delay=5)
def filter_policies(params: FilterPolicyParams):
    """Return a SQLAlchemy query filtered according to *params*."""

    try:
        base = db.session.query(TransferPolicy)

        if params.get("enabled") is not None:
            base = base.filter(TransferPolicy.enabled == params["enabled"])
        if params.get("type") is not None:
            type = params["type"] if isinstance(params["type"], Type) else Type[params["type"].upper()]
            base = base.filter(TransferPolicy.type == type)
        if params.get("src") is not None:
            base = base.join(SourcePolicy).join(Target).filter(Target.name == params["src"])
        if params.get("dests") is not None:
            base = base.join(DestinationPolicy).join(Target).filter(Target.name == params["dests"])
        if params.get("queues") is not None:
            queues = params["queues"].split(",")
            base = base.join(TransferPolicy.queue).filter(Queue.name.in_(queues))
        if params.get("id") is not None:
            base = base.filter(TransferPolicy.id == params["id"])
        if params.get("ids") is not None:
            policies_id = params["ids"].split(",")
            policies_id = map(lambda i: int(i), policies_id)
            base = base.filter(TransferPolicy.id.in_(policies_id))
        if params.get("next_polling_min_time") is not None and params.get("next_polling_min_time") is True:
            base = (
                base.join(TransferPolicyParameters)
                .join(PeriodicalParameters)
                .filter(
                    or_(
                        PeriodicalParameters.next_polling_min_time.is_(None),
                        PeriodicalParameters.next_polling_min_time
                        <= datetime.datetime.now(datetime.timezone.utc),
                    )
                )
            )
        base = base.order_by(TransferPolicy.created_at)

        return base
    except Exception as exc:  # pragma: no cover – defensive fallback
        from flask import current_app

        current_app.logger.error("Error in filter_policies: %s", exc, exc_info=True)

        # Return empty query that won't crash pagination
        return db.session.query(TransferPolicy).filter(TransferPolicy.id == -1)


@transactional
def update_policy(policy_id: int, payload: dict):
    npolicy = cast(TransferPolicy | None, db.session.query(TransferPolicy).get(policy_id))
    if not npolicy:
        from flask import current_app
        current_app.logger.warning("TransferPolicy %s not found for update", policy_id)
        return

    # Guarantee parameters structure exists for safe updates from trigger
    if npolicy.parameters is None:
        npolicy.parameters = TransferPolicyParameters()
    if npolicy.type == Type.PERIODICAL:
        if npolicy.parameters.periodical is None:
            # on crée toujours la sous-entrée periodical
            npolicy.parameters.periodical = PeriodicalParameters(
                polling_interval = payload
                    .get("parameters", {})
                    .get("periodical", {})
                    .get("polling_interval", 10)   # défaut
            )

    try:
        npolicy.update(payload)
    except orm_exc.StaleDataError:
        # The underlying PeriodicalParameters row may have been deleted/expired.
        # Issue a merge on the detached objects and retry the update once.
        db.session.merge(npolicy)
        db.session.flush()
        npolicy.update(payload)