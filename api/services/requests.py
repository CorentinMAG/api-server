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
        # Use a window function to find the latest state for each request.
        # This is much more efficient than a correlated subquery.
        latest_state_cte = (
            select(
                State.id.label("state_id"),
                State.request_id,
                State.state,
                State.sub_state,
                func.row_number()
                .over(partition_by=State.request_id, order_by=State.id.desc())
                .label("rn"),
            )
            .cte("latest_state")
        )

        base = base.join(
            latest_state_cte,
            latest_state_cte.c.request_id == TransferRequest.id,
        ).where(latest_state_cte.c.rn == 1)

        if sub_state:
            base = base.where(latest_state_cte.c.sub_state == sub_state)
        else:
            base = base.where(latest_state_cte.c.state == state)


    if size:
        now = datetime.datetime.now(datetime.timezone.utc)
        base = base.where(
            or_(TransferRequest.size < size, TransferRequest.size.is_(None)),
            or_(TransferRequest.next_retry_min_time.is_(None), TransferRequest.next_retry_min_time <= now),
        )

    base = base.with_for_update(skip_locked=True).limit(1)
    nrequest = db.session.scalar(base)
    return nrequest


def filter_requests(params):
    base = select(TransferRequest).order_by(TransferRequest.created_at.asc())
    return base.filter(TransferRequest.uid == params["id"])


@transactional
def create_periodical_requests(payload: TriggerTransferRequestSchema) -> None:
    policy_id = payload.policy
    triggered_files = payload.files

    # we sort triggered_files by modified_at attribute
    triggered_files = sorted(triggered_files, key=lambda k: k.modified_at, reverse=True)

    npolicy = db.session.get(TransferPolicy, policy_id)
    if not npolicy:
        return

    only_new_data = npolicy.parameters.only_new_data
    queue = npolicy.queue
    dests = npolicy.dests
    nb_dests = len(dests)

    # Optimized: Count queued files directly in the DB
    # We build a subquery to find the latest state ID for each request
    latest_state_subquery = (
        select(func.max(State.id))
        .group_by(State.request_id)
        .where(State.request_id == TransferRequest.id)
        .correlate(TransferRequest)
        .scalar_subquery()
    )

    # Now we count how many of those latest states are 'QUEUED'
    queued_count_stmt = (
        select(func.count(TransferRequest.id))
        .join(State, TransferRequest.id == State.request_id)
        .where(
            TransferRequest.policy_id == policy_id,
            State.id == latest_state_subquery,
            State.state == StateEnum.QUEUED,
        )
    )
    db_queued_files_count = db.session.execute(queued_count_stmt).scalar_one_or_none() or 0


    available_slots = queue.queue_limit - db_queued_files_count

    # if queue is already full
    if available_slots <= nb_dests:
        return
    else:
        max_files = available_slots // nb_dests

    if db_queued_files_count + len(triggered_files) >= queue.queue_threshold:
        app.logger.warning(
            "queue %s is almost full (%d/%d)",
            queue.name,
            db_queued_files_count,
            queue.queue_limit,
        )

    nrequests: list[TransferRequest] = []
    files_to_create = []

    # Fast check for existing filenames
    filenames_in_triggered_files = {f.filename for f in triggered_files}
    if filenames_in_triggered_files:
        existing_files_stmt = select(TransferRequest.filename).where(
            TransferRequest.policy_id == policy_id,
            TransferRequest.filename.in_(filenames_in_triggered_files),
        )
        db_files = set(db.session.execute(existing_files_stmt).scalars().all())
    else:
        db_files = set()


    for file in triggered_files:
        if len(files_to_create) >= max_files:
            break

        if file.filename not in db_files:
            files_to_create.append(file)
        elif not only_new_data:
            # Check if all previous requests for this file are finished.
            # This is more efficient than loading all requests.
            unfinished_count_stmt = (
                select(func.count(TransferRequest.id))
                .join(State, TransferRequest.id == State.request_id)
                .where(
                    TransferRequest.policy_id == policy_id,
                    TransferRequest.filename == file.filename,
                    State.id == latest_state_subquery,
                    State.state.not_in([StateEnum.SUCCESSFUL, StateEnum.CANCELLED]),
                )
            )
            unfinished_count = db.session.execute(unfinished_count_stmt).scalar_one()

            if unfinished_count == 0:
                files_to_create.append(file)

    for file in files_to_create:
        for dest in dests:
            nrequest = TransferRequest(filename=file.filename, size=file.size, dest=dest)
            nstate = State(state=StateEnum.QUEUED)
            nrequest.states.append(nstate)
            nrequests.append(nrequest)

    if nrequests:
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

    filename = payload.path.split("/")[-1]
    if payload.path.startswith(("http://", "https://")):
        parsed_url = urlparse(payload.path)
        filename = os.path.basename(parsed_url.path)
        path = os.path.dirname(parsed_url.path)
    else:
        path = payload.path.replace(filename, '')

    try:
        request_uids = []
        for dest in dests:
            # Check if there's already a transfer in progress for this file to this specific destination
            existing_request = db.session.scalar(
                select(TransferRequest)
                .join(TransferPolicy)
                .where(TransferPolicy.name == policy_name)
                .where(TransferRequest.filename == filename)
                .where(TransferRequest.dest_id == dest.id)
                .where(TransferRequest.states.any(State.state.not_in([StateEnum.SUCCESSFUL, StateEnum.CANCELLED])))
            )

            if existing_request:
                app.logger.warning(
                    f"Transfer already in progress: {filename}"
                )
                continue

            nrequest = TransferRequest(
                filename=filename,
                dest=dest,
                src_relative_path=path,
                follows_from_task=payload.uid if payload.uid else None
            )
            nstate = State(state=StateEnum.QUEUED)
            nrequest.states.append(nstate)
            npolicy.transfers.append(nrequest)
        
        if not npolicy.transfers:
            return None, "No new transfers could be created - all destinations have transfers in progress", 409
        
        db.session.commit()
        
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
    state_param = params.get("state")
    sub_state_param = params.get("sub_state")

    # Convert string params to Enum types if they exist, otherwise they remain None
    state_enum = StateEnum[state_param.upper()] if state_param else None
    sub_state_enum = SubStateEnum[sub_state_param.upper()] if sub_state_param else None

    if nrequest and params:
        npolicy = nrequest.policy
        new_states_to_append: list[State] = []

        if state_enum:  # A main state update is requested
            max_retries = npolicy.parameters.max_retry
            if state_enum == StateEnum.FAILED:
                failure_reason = params.get("failure_reason")
                if not max_retries or nrequest.nb_retry + 1 < max_retries:
                    failed_s = State(state=StateEnum.FAILED, failure_reason=failure_reason)
                    queued_s = State(state=StateEnum.QUEUED)
                    new_states_to_append.extend([failed_s, queued_s])
                    nrequest.nb_retry += 1
                elif nrequest.nb_retry + 1 >= max_retries:
                    # Request becomes CANCELLED after max retries
                    nrequest.end = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    
                    # Determine sub_state based on whether notifications are configured for the destination
                    current_sub_state = None
                    if nrequest.dest and nrequest.dest.notifications:
                        current_sub_state = SubStateEnum.NOTIFY
                    # else: current_sub_state remains None, or could be set to another default if needed

                    cancelled_s = State(
                        state=StateEnum.CANCELLED,
                        sub_state=current_sub_state, # Use determined sub_state
                        failure_reason=f"Max retries reached - Last error: {failure_reason}",
                    )
                    new_states_to_append.append(cancelled_s)
            elif state_enum in [StateEnum.SUCCESSFUL, StateEnum.CANCELLED]:
                # Handles direct SUCCESSFUL or CANCELLED updates (not from max_retry logic)
                nrequest.end = datetime.datetime.now(datetime.timezone.utc).isoformat()
                # sub_state_enum here is the one parsed from params, could be None
                final_s = State(state=state_enum, sub_state=sub_state_enum)
                new_states_to_append.append(final_s)

        elif sub_state_enum:  # No main 'state' in params, only 'sub_state' (state_enum is None)
            if nrequest.states:  # Ensure there are existing states to get the current main state
                latest_main_state = nrequest.states[0].state # Assuming states are ordered, states[0] is the latest
                sub_state_update_s = State(state=latest_main_state, sub_state=sub_state_enum)
                new_states_to_append.append(sub_state_update_s)
            else:
                app.logger.warning(
                    f"Request {request_id} has no prior states. Cannot update sub_state only."
                )
        
        if new_states_to_append:
            nrequest.states.extend(new_states_to_append)

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