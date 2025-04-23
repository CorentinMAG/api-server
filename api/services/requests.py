import os
import datetime
from urllib.parse import urlparse
from typing import cast, TypedDict
from flask import current_app as app

from api.db import db
from api.models import Queue, State, TransferPolicy, TransferRequest
from sqlalchemy import or_, select, func
from sqlalchemy.exc import SQLAlchemyError
import uuid
from dtr_common.schema import TriggerTransferRequestSchema, CommandedTransferRequestSchema
from dtr_common.constantes import State as StateEnum, SubState as SubStateEnum, Type
from .utils import transactional


class NextTransferRequestParams(TypedDict, total=False):
    state: StateEnum
    size: int
    sub_state: SubStateEnum


def get_next_request(params: NextTransferRequestParams) -> TransferRequest | None:
    state = params.get("state")
    size = params.get("size")
    sub_state = params.get("sub_state")

    base = (
        select(TransferRequest)
        .join(TransferPolicy)
        .join(Queue)
        .order_by(Queue.priority.asc(), TransferRequest.created_at.asc())
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
    if params.get("uid") is not None:
        base = base.filter(TransferRequest.uid == params["uid"])
    if params.get("uids") is not None:
        transfer_uids = params["uids"].split(",")
        transfer_uids = map(lambda i: int(i), transfer_uids)
        base = base.filter(TransferRequest.uid.in_(transfer_uids))
    if params.get("policy_id") is not None:
        base = base.filter(TransferRequest.policy_id == params["policy_id"])
    if params.get("policy_name") is not None:
        base = base.filter(TransferPolicy.name == params["policy_name"])
    if params.get("policy_ids") is not None:
        policy_ids = list(map(lambda x: int(x), params["policy_ids"].split(",")))
        base = base.filter(TransferRequest.policy_id.in_(policy_ids))
    if params.get("filename") is not None:
        base = base.filter(TransferRequest.filename == params["filename"])
    return base


@transactional
def create_periodical_requests(payload: TriggerTransferRequestSchema) -> None:
    policy_id = payload.policy
    triggered_files = payload.files

    # we sort triggered_files by modified_at attribute
    triggered_files = sorted(triggered_files, key=lambda k: k.modified_at, reverse=True)

    npolicy = db.session.scalar(select(TransferPolicy).where(TransferPolicy.id == policy_id))

    if npolicy:
        # if only_new_data is True
        # files already transferred are not transferred twice
        only_new_data = npolicy.parameters.only_new_data
        requests = npolicy.transfers
        queue = npolicy.queue
        dests = npolicy.dests
        nb_dests = len(dests)

        db_files = list(map(lambda r: r.filename, requests))
        db_queued_files = list(filter(lambda r: r.states[0].state == StateEnum.QUEUED, requests))

        available_slots = queue.queue_limit - len(db_queued_files)

        # if queue is already full
        if available_slots <= nb_dests:
            return
        else:
            max_files = available_slots // nb_dests
            triggered_files = triggered_files[:max_files]

        if len(triggered_files) + len(db_queued_files) >= queue.queue_threshold:
            app.logger.warning(
                "queue %s is almost full (%d/%d)",
                queue.name,
                len(db_queued_files),
                queue.queue_limit,
            )

        nrequests: list[TransferRequest] = []
        for file in triggered_files:
            filename = file.filename
            size = file.size
            if filename not in db_files:
                for dest in dests:
                    nrequest = TransferRequest(filename=filename, size=size, dest=dest)
                    nstate = State(state=StateEnum.QUEUED)
                    nrequest.states.append(nstate)
                    nrequests.append(nrequest)
            # if only_new_data is false
            # and the trigerred file is already in database
            # and the state is SUCCESSFUL or CANCELLED
            # we recreate a new transfer request
            elif not only_new_data:
                nrequest = next(filter(lambda r: r.filename == filename, requests))
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
            for dest in npolicy.dests:
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
                            "target_url_string": dest.path,
                            "target_logical_name_string": dest.target.name,
                        },
                    },
                }
            app.logger.info("request for transfer", extra=task)

        for nrequest, uid in zip(nrequests, reports_uid):
            for dest in npolicy.dests:
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
                            "target_url_string": dest.path,
                            "target_logical_name_string": dest.target.name,
                        },
                        "error_code": 0,
                        "output": {"rest_id_string": str(nrequest.uid)},
                    },
                }
            app.logger.info("end of request transfer", extra=task)


@transactional
def create_commanded_request(payload: CommandedTransferRequestSchema) -> tuple[list[str] | None, str | None, int]:
    """
    Create a commanded transfer request.
    Returns a tuple containing:
    - list of request IDs if successful
    - error message if failed
    - HTTP status code
    """
    policy_name = payload.transfer_policy

    npolicy = db.session.scalar(
        select(TransferPolicy).where(
            TransferPolicy.name == policy_name, TransferPolicy.type == Type.COMMANDED
        )
    )

    if not npolicy:
        return None, f"Transfer policy '{policy_name}' not found or is not a commanded policy", 404

    dests = npolicy.dests
    if not dests:
        return None, f"No destinations configured for policy '{policy_name}'", 400

    nrequests = db.session.scalars(
        select(TransferRequest)
        .join(TransferPolicy)
        .where(TransferPolicy.name == policy_name)
        .where(TransferRequest.filename==payload.path.split("/")[-1])
    ).all()

    if nrequests and any(
        req.states[0].state not in [StateEnum.SUCCESSFUL, StateEnum.CANCELLED] for req in nrequests
        ):
        return None, "A transfer request for this file is already in progress", 409

    if payload.path.startswith(("http://", "https://")):
        parsed_url = urlparse(payload.path)
        filename = os.path.basename(parsed_url.path)
        path = os.path.dirname(parsed_url.path)
    else:
        filename = payload.path.split("/")[-1]
        path = payload.path.replace(filename, '')

    try:
        for dest in dests:
            nrequest = TransferRequest(
                filename=filename,
                dest=dest,
                src_relative_path=path,
                follows_from_tasks=payload.uid if payload.uid else None
            )
            nstate = State(state=StateEnum.QUEUED)
            nrequest.states.append(nstate)
            npolicy.transfers.append(nrequest)
        
        db.session.commit()
        
        request_uids = []
        for nrequest in npolicy.transfers[-len(dests):]:
            if nrequest.uid is None:
                app.logger.error("UID is None for a newly created transfer request")
                return None, "Internal error: Failed to create transfer request", 500
            else:
                request_uids.append(str(nrequest.uid))
        
        return request_uids, None, 200
    except SQLAlchemyError as e:
        app.logger.error(
            "Database error while creating commanded requests",
            extra={
                'error_type': 'database_error',
                'error_details': str(e)
            }
        )
        return None, f"Database error: {str(e)}", 500
    except Exception as e:
        app.logger.error(
            "Unexpected error while creating commanded requests",
            extra={
                'error_type': 'unexpected_error',
                'error_details': str(e)
            }
        )
        return None, f"Unexpected error: {str(e)}", 500


@transactional
def update_request(
    request_id: int,
    params: dict,
) -> dict | None:
    nrequest = cast(
        TransferRequest | None,
        db.session.query(TransferRequest).with_for_update().get(request_id)
    )
    state = StateEnum[params["state"].upper()] if params.get("state") else None
    sub_state = SubStateEnum[params["sub_state"].upper()] if params.get("sub_state") else None

    if nrequest and params:
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
                        failure_reason=f"Max retries reached - Last error: {failure_reason}",
                    )
                    nstates.append(nstate)
            else:
                # state is either CANCELLED or SUCCESSFUL
                nrequest.end = datetime.datetime.now(datetime.timezone.utc).isoformat()
                nstate = State(state=state, sub_state=sub_state)
                nstates.append(nstate)
            nrequest.states.extend(nstates)

        nrequest.update(params)
        response = nrequest.to_dict()
        response["Purge"] = can_purge(nrequest)
        return response
    return None


def can_purge(nrequest: TransferRequest | None) -> bool:
    associated_tr = db.session.query(TransferRequest).filter(
        TransferRequest.filename == nrequest.filename,
        TransferRequest.id != nrequest.id,
        TransferPolicy.id == nrequest.policy_id
    ).all()

    app.logger.debug(f"Found {len(associated_tr)} associated transfert requests")

    for tr in associated_tr:
        if not any(state.state == StateEnum.SUCCESSFUL for state in tr.states):
            app.logger.debug(f"Transfert request {tr.id} not successful")
            return False

    app.logger.debug("Authorize worker to purge source")
    return True
