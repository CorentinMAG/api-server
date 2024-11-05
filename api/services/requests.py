from typing import cast
from dtr_common.constantes import State as StateEnum, SubState as SubStateEnum
from flask import current_app as app

from api.db import db
from api.models import Queue, State, TransferPolicy, TransferRequest
import datetime
from sqlalchemy import or_, select, func
import uuid
from typing import cast, TypedDict
from dtr_common.schema import TriggerTransferRequestSchema, CommandedTransferRequestSchema
from dtr_common.constantes import State as StateEnum, SubState
import datetime


class NextTransferRequestParams(TypedDict, total=False):
    state: StateEnum
    size: int
    sub_state: SubState


def get_next_request(params: NextTransferRequestParams) -> TransferRequest | None:
    state = params.get("state")
    size = params.get("size")
    sub_state = params.get("sub_state")

    base = (
        select(TransferRequest)
        .join(TransferPolicy)
        .join(Queue)
        .order_by(Queue.priority.asc())
        .order_by(TransferRequest.created_at.asc())
    )

    if state or sub_state:
        # select the last state for each TransferRequest
        # state id is always incremented. We sort by id
        # because it is more reliable than created_at date
        # Indeed, multiple records can have the same created_at date
        # if they are added to the TransferRequest in the same transaction
        substmt = (
            select(State.id)
            .where(State.request_id == TransferRequest.id)
            .order_by(State.id.desc())
            .limit(1)
            .correlate(TransferRequest)
        )
        statestmt = State.sub_state == sub_state if sub_state else State.state == state
        base = base.join(State, State.id == substmt.scalar_subquery()).where(statestmt)

    if size:
        now = datetime.datetime.now(datetime.timezone.utc)
        base = base.where(
            or_(TransferRequest.size < size, TransferRequest.size.is_(None)),
            or_(TransferRequest.next_retry_min_time.is_(None), TransferRequest.next_retry_min_time <= now),
        )

    base = base.with_for_update(skip_locked=True)
    nrequest = db.session.scalar(base)
    return nrequest


def filter_requests(params):
    base = select(TransferRequest).order_by(TransferRequest.created_at.asc())

    if params.get("state") is not None:
        state = StateEnum[params.get("state").upper()]
        subquery = (
            select(State.request_id, func.max(State.created_at).label("latest_created_at"))
            .group_by(State.request_id)
            .subquery()
        )
        base = (
            base.join(State)
            .join(
                subquery,
                (subquery.c.request_id == State.request_id)
                & (subquery.c.latest_created_at == State.created_at),
            )
            .filter(State.state == state)
        )
    if params.get("states") is not None:
        states = list(map(lambda x: StateEnum[x.upper()], params["states"].split(",")))
        subquery = (
            select(State.request_id, func.max(State.created_at).label("latest_created_at"))
            .group_by(State.request_id)
            .subquery()
        )
        base = (
            base.join(State)
            .join(
                subquery,
                (subquery.c.request_id == State.request_id)
                & (subquery.c.latest_created_at == State.created_at),
            )
            .filter(State.state.in_(states))
        )
    if params.get("queues") is not None:
        queues = params["queues"].split(",")
        base = base.select_from(TransferPolicy).join(Queue).filter(Queue.name.in_(queues))
    if params.get("id") is not None:
        base = base.filter(TransferRequest.id == params["id"])
    if params.get("ids") is not None:
        transfer_ids = params["ids"].split(",")
        transfer_ids = map(lambda i: int(i), transfer_ids)
        base = base.filter(TransferRequest.id.in_(transfer_ids))
    if params.get("policy_id") is not None:
        base = base.filter(TransferRequest.policy_id == params["policy_id"])
    if params.get("policy_name") is not None:
        base = base.filter(TransferPolicy.name == params["policy_name"])
    if params.get("policy_ids") is not None:
        policy_ids = list(map(lambda x: int(x), params["policy_ids"].split(",")))
        base = base.filter(TransferRequest.policy_id.in_(policy_ids))
    return base


def create_periodical_requests(payload: TriggerTransferRequestSchema) -> None:
    # TODO: with Aniel,
    # when the trigger sent data to the api,
    # we used to check if a transfer was in the QUEUED state
    # longer than expected
    # if this was the case, then the transfer state was passed to CANCELED
    # Moreover, there was a WARNING log if the queue is almost full
    # with also have to handle the case where the queue is full (not accepting new requests)
    policy_id = payload.policy
    triggered_files = payload.files

    # we sort triggered_files by modified_at attribute
    triggered_files = sorted(triggered_files, key=lambda k: k["modified_at"], reverse=True)

    npolicy = db.session.scalar(select(TransferPolicy).where(TransferPolicy.id == policy_id))

    if npolicy:
        # if only_new_data is True
        # files already transferred are not transferred twice
        only_new_data = npolicy.parameters.only_new_data
        requests = npolicy.transfers
        queue = npolicy.queue

        db_files = list(map(lambda r: r.filename, requests))
        db_queued_files = list(filter(lambda r: r.states[0].state == StateEnum.QUEUED, requests))
        l = queue.queue_limit - len(db_queued_files)

        if l <= 0:
            # queue is already full
            return
        else:
            triggered_files = triggered_files[:l]

        if len(triggered_files) + len(db_queued_files) >= queue.queue_threshold:
            app.logger.warning(
                "queue %s is almost full (%d/%d)",
                queue.name,
                len(triggered_files) + len(db_queued_files),
                queue.queue_limit,
            )

        nrequests: list[TransferRequest] = []
        for file in triggered_files:
            filename = file.filename
            size = file.size
            if filename not in db_files:
                nrequest = TransferRequest(filename=filename, size=size)
                nstate = State(state=StateEnum.QUEUED)
                nrequest.states.append(nstate)
                nrequests.append(nrequest)
            # if only_new_data is false
            # and the trigerred file is already in database
            # and the state is SUCCESSFUL or CANCELLED
            # we recreate a new transfer request
            elif not only_new_data:
                nrequest = cast(TransferRequest, next(filter(lambda r: r.filename == filename, requests)))
                latest_state = nrequest.states[0]
                if latest_state.state == StateEnum.CANCELLED or latest_state.state == StateEnum.SUCCESSFUL:
                    nrequest = nrequest.clone()
                    nstate = State(state=StateEnum.QUEUED)
                    nrequest.states.append(nstate)
                    nrequests.append(nrequest)
        npolicy.transfers.extend(nrequests)
        db.session.add(npolicy)

        ## for each new request we create a report log
        reports_uid = []
        for nrequest in nrequests:
            uid = uuid.uuid4()
            reports_uid.append(uid)
            task = {
                "type": "REPORT",
                "task": {
                    "uid": str(uid),
                    "name": "dtr_api_transfer_request",
                    "event": "BEGIN",
                    "input": {
                        "tpln_string": npolicy.name,
                        "source_url_string": npolicy.src.path,
                        "filename_string": nrequest.filename,
                        "target_url_string": npolicy.dest.path,
                        "target_logical_name_string": npolicy.dest.target.name,
                    },
                },
            }
            app.logger.info("request for transfer", extra=task)
        db.session.commit()

        for nrequest, uid in zip(nrequests, reports_uid):
            task = {
                "type": "REPORT",
                "task": {
                    "uid": str(uid),
                    "name": "dtr_api_transfer_request",
                    "event": "END",
                    "status": "OK",
                    "input": {
                        "tpln_string": npolicy.name,
                        "source_url_string": npolicy.src.path,
                        "filename_string": nrequest.filename,
                        "target_url_string": npolicy.dest.path,
                        "target_logical_name_string": npolicy.dest.target.name,
                    },
                    "error_code": 0,
                    "output": {"rest_id_string": str(nrequest.uid)},
                },
            }
            app.logger.info("end of request transfer", extra=task)


def create_commanded_request(payload: CommandedTransferRequestSchema) -> None:
    policy_name = payload.transfer_policy

    npolicy = db.session.scalar(select(TransferPolicy).where(TransferPolicy.name == policy_name))

    if npolicy:
        if payload.uid:
            nrequest = db.session.scalar(
                select(TransferRequest)
                .where(TransferPolicy.name == policy_name)
                .where(TransferRequest.uid == payload.uid)
            )
            if nrequest and nrequest.states[0].state == StateEnum.QUEUED:
                return nrequest.uid
        filename = payload.path.split("/")[-1]
        nrequest = TransferRequest(filename=filename)
        nstate = State(state=StateEnum.QUEUED)
        nrequest.states.append(nstate)
        npolicy.transfers.append(nrequest)
        db.session.commit()


def update_request(
    request_id: int,
    params: dict,
) -> TransferRequest | None:
    nrequest = cast(TransferRequest | None, db.session.query(TransferRequest).get(request_id))
    state = StateEnum[params["state"].upper()] if params.get("state") else None
    sub_state = SubState[params["sub_state"].upper()] if params.get("sub_state") else None

    if nrequest:
        npolicy = nrequest.policy
        # if we are updating the request status,
        # we need to check if it is a FAILED or not
        if state:
            nstates = []
            max_retries = npolicy.parameters.max_retry
            if state == StateEnum.FAILED:
                failure_reason = params.get("failure_reason")
                if not max_retries or nrequest.nb_retry + 1 < max_retries:
                    failed = State(state=StateEnum.FAILED, failure_reason=failure_reason)
                    queued = State(state=StateEnum.QUEUED)
                    nstates.extend([failed, queued])
                    nrequest.nb_retry += 1
                elif nrequest.nb_retry + 1 >= max_retries:
                    nstate = State(
                        state=StateEnum.CANCELLED.value.upper(),
                        sub_state=SubStateEnum.NOTIFY.value.upper(),
                        failure_reason="Max retries reached",
                    )
                    nstates.append(nstate)
            else:
                # state is either CANCELLED or SUCCESSFUL
                nrequest.end = datetime.datetime.now(datetime.timezone.utc)
                nstate = State(state=state, sub_state=sub_state)
                nstates.append(nstate)
            nrequest.states.extend(nstates)

        nrequest.update(params)
        db.session.commit()
        return nrequest
