from __future__ import annotations

from api.repositories import TransferRequestRepository

from .base import BaseService


class TransferRequestService(BaseService[TransferRequestRepository]):
    pass


# from dtr_common.constantes import State as StateEnum, SubState as SubStateEnum, Type
# from dtr_common.schema import CommandedTransferRequestSchema, TriggerTransferRequestSchema, PeriodicalTransferRequestSchema
# from flask import current_app as app
# from sqlalchemy import func, or_, select
# from sqlalchemy.orm import Session

# from api.db import db
# from api.models import Queue, State, TransferPolicy, TransferRequest
# from .utils import db_retry, transactional


# class NextTransferRequestParams(TypedDict, total=False):
#     state: StateEnum
#     size: int
#     sub_state: SubStateEnum


# def get_request(uuid: uuid.UUID) -> TransferRequest | None:
#     stmt = select(TransferRequest).join(TransferPolicy).join(Queue).where(TransferRequest.uid == uuid)
#     request = db.session.execute(stmt).scalar()
#     return request


# def get_next_request(
#     params: NextTransferRequestParams, db_session: Optional[Session] = None
# ) -> TransferRequest | None:
#     """Get the next transfer request. Supports dependency injection for testing."""
#     if db_session is None:
#         db_session = db.session

#     state = params.get("state")
#     size = params.get("size")
#     sub_state = params.get("sub_state")

#     base = (
#         select(TransferRequest)
#         .join(TransferPolicy)
#         .join(Queue)
#         .order_by(Queue.priority.asc(), TransferRequest.created_at.asc())
#     )

#     if state or sub_state:
#         # Use a window function to find the latest state for each request.
#         # This is much more efficient than a correlated subquery.
#         latest_state_cte = select(
#             State.id.label("state_id"),
#             State.request_id,
#             State.state,
#             State.sub_state,
#             func.row_number().over(partition_by=State.request_id, order_by=State.id.desc()).label("rn"),
#         ).cte("latest_state")

#         base = base.join(
#             latest_state_cte,
#             latest_state_cte.c.request_id == TransferRequest.id,
#         ).where(latest_state_cte.c.rn == 1)

#         if sub_state:
#             base = base.where(latest_state_cte.c.sub_state == sub_state)
#         else:
#             base = base.where(latest_state_cte.c.state == state)

#     if size:
#         now = datetime.datetime.now(datetime.timezone.utc)
#         base = base.where(
#             or_(TransferRequest.size < size, TransferRequest.size.is_(None)),
#             or_(TransferRequest.next_retry_min_time.is_(None), TransferRequest.next_retry_min_time <= now),
#         )

#     base = base.with_for_update(of=TransferRequest, skip_locked=True).limit(1)
#     nrequest = db_session.scalar(base)
#     return nrequest


# @transactional
# def create_periodical_requests(
#     payload: TriggerTransferRequestSchema
# ) -> list[TransferRequest]:
#     """
#     Create periodical transfer requests

#     Args:
#         payload: Transfer request payload
#     Returns:
#         list[TransferRequest]: list of transfer requests created
#     """
#     logger = app.logger
#     policy_id = payload.policy
#     triggered_files = payload.files

#     npolicy = cast(TransferPolicy | None, db.session.get(TransferPolicy, policy_id))
#     if not npolicy:
#         return []

#     only_new_data = npolicy.parameters.only_new_data
#     nrequests = npolicy.transfers
#     queue = npolicy.queue
#     dests = npolicy.dests
#     nb_dests = len(dests)

#     db_files = list(map(lambda r: r.filename, nrequests))
#     db_queued_files = list(filter(lambda r: r.states[0].state == StateEnum.QUEUED, nrequests))
#     available_slots = queue.queue_limit - len(db_queued_files)

#     if available_slots < nb_dests:
#         # the queue is already full or about to be full
#         # but none requests can be created
#         return []

#     if only_new_data:
#         # we don't re-transfer files that are already in database
#         files_to_transfer = list(filter(lambda f: f.filename not in db_files, triggered_files))
#     else:
#         # we re-transfer files that are in database in SUCCESSFUL/CANCELED states
#         db_retransfer_files = filter(lambda r: r.states[0].state in (StateEnum.SUCCESSFUL, StateEnum.CANCELLED), nrequests)
#         db_retransfer_files = list(map(lambda r: r.filename, db_retransfer_files))
#         files_to_transfer = list(filter(lambda f: f.filename in db_retransfer_files or f.filename not in db_files, triggered_files))

#     # Sort triggered files by modified_at attribute
#     # WARNING: if only_new_data is false, we will always have
#     # files in SUCCESSFUL/CANCELLED states at the begining of the list (if purge is not enabled)
#     # that mean that if the queue limit is not big enough, new files won't be discovered
#     files_to_transfer = sorted(files_to_transfer, key=lambda k: k.modified_at, reverse=True)

#     # a new transfer request is created by destination
#     nb_files = available_slots // nb_dests
#     files_to_transfer = files_to_transfer[:nb_files]

#     available_slots = available_slots - (nb_files * nb_dests)

#     if available_slots <= queue.queue_limit - queue.queue_threshold:
#         logger.warning("queue %s is almost full (%d/%d) slots are available", queue.name, available_slots, queue.queue_limit)

#     # Create transfer requests
#     nrequests_created = _create_periodical_transfer_requests(triggered_files, npolicy)

#     _generate_transfer_reports(nrequests_created, npolicy, logger)

#     return nrequests_created

# @transactional
# def _create_periodical_transfer_requests(files: list[PeriodicalTransferRequestSchema], npolicy: TransferPolicy) -> list[TransferRequest]:
#     nrequests = list[TransferRequest] = []
#     dests = npolicy.dests
#     for file in files:
#         for dest in dests:
#             nrequest = TransferRequest(filename = file.filename, size = file.size, dest = dest)
#             nstate = State(state = StateEnum.QUEUED)
#             nrequest.states.append(nstate)
#             nrequests.append(nrequest)
#     npolicy.transfers.extend(nrequests)
#     db.session.add(npolicy)
#     return nrequests


# def _generate_transfer_reports(requests: list[TransferRequest], npolicy: TransferPolicy, logger: logging.Logger) -> None:
#     """Helper function to generate transfer reports."""
#     # Generate report logs for each new request
#     for nrequest in requests:
#         for dest in npolicy.dests:
#             uid = uuid.uuid4()

#             # BEGIN report
#             begin_task = {
#                 "type": "REPORT",
#                 "task": {
#                     "uid": uid.hex,
#                     "name": "dtr_api_transfer_request",
#                     "event": "BEGIN",
#                     "input": {
#                         "tpln_string": npolicy.name,
#                         "source_url_string": npolicy.src.path,
#                         "filename_string": nrequest.filename,
#                         "target_url_string": dest.path,
#                         "target_logical_name_string": dest.target.name,
#                     },
#                 },
#             }
#             logger.info("request for transfer", extra=begin_task)

#             # END report
#             end_task = {
#                 "type": "REPORT",
#                 "task": {
#                     "uid": uid.hex,
#                     "name": "dtr_api_transfer_request",
#                     "event": "END",
#                     "status": "OK",
#                     "input": {
#                         "tpln_string": npolicy.name,
#                         "source_url_string": npolicy.src.path,
#                         "filename_string": nrequest.filename,
#                         "target_url_string": dest.path,
#                         "target_logical_name_string": dest.target.name,
#                     },
#                     "error_code": 0,
#                     "output": {"rest_id_string": nrequest.uid.hex},
#                 },
#             }
#             logger.info("end of request transfer", extra=end_task)


# def create_commanded_request(
#     payload: CommandedTransferRequestSchema
# ) -> list[uuid.UUID]:
#     """
#     Create a commanded transfer request.
#     Returns a tuple containing:
#     - list of request IDs if successful
#     - error message if failed
#     - HTTP status code
#     """
#     # Initialize logger with default if not provided (backward compatibility)
#     logger = app.logger

#     policy_name = payload.transfer_policy

#     npolicy = db.session.scalar(
#         select(TransferPolicy).where(
#             TransferPolicy.name == policy_name, TransferPolicy.type == Type.COMMANDED
#         )
#     )

#     if not npolicy:
#         raise ValueError(f"transfer policy: {policy_name} not found or is not a commanded policy")

#     dests = npolicy.dests

#     # in path, we can have a subpath
#     # or a complete http url so we need a bit of logic
#     path = urlparse(payload.path)
#     filename = path.path.split("/")[-1]
#     relative_path = path.path.replace(filename, "").rstrip("/")
#     nrequests: list[TransferRequest] = []
#     for dest in dests:
#         # Check if there's already a transfer in progress for this file to this specific destination
#         nrequest = db.session.scalar(
#             select(TransferRequest)
#             .join(TransferPolicy)
#             .where(TransferPolicy.name == policy_name)
#             .where(TransferRequest.filename == filename)
#             .where(TransferRequest.dest == dest)
#             .where(
#                 TransferRequest.states.any(
#                     State.state.not_in([StateEnum.SUCCESSFUL, StateEnum.CANCELLED])
#                 )
#             )
#         )

#         if nrequest:
#             logger.warning("Transfer already in progress policy: %s filename: %s destination: %s", policy_name, filename, dest.target.name)
#         else:
#             # create a new transfer request
#             nrequest = TransferRequest(
#                 filename=filename,
#                 dest=dest,
#                 src_relative_path=relative_path,
#                 follows_from_task=payload.uid if payload.uid else None,
#             )
#             nstate = State(state=StateEnum.QUEUED)
#             nrequest.states.append(nstate)
#             npolicy.transfers.append(nrequest)
#             nrequests.append(nrequest)

#     db.session.commit()

#     uuids = [r.uid for r in nrequests[::-1]]
#     return uuids


# @transactional
# def update_request(
#     request_id: int,
#     params: dict,
# ) -> dict | None:
#     nrequest = cast(
#         TransferRequest | None, db.session.query(TransferRequest).with_for_update().get(request_id)
#     )
#     # state and sub_state parameters are mutually exclusive
#     state = StateEnum[params["state"].upper()] if params.get("state") else None
#     sub_state = SubStateEnum[params["sub_state"].upper()] if params.get("sub_state") else None

#     if state is not None and sub_state is not None:
#         raise ValueError("state and sub_state parameters are mutually exclusive")

#     if nrequest and params:
#         npolicy = nrequest.policy
#         # if we are updating the request status,
#         # we need to check if it is a FAILED or not
#         if state:
#             nstates: list[State] = []
#             max_retries = npolicy.parameters.max_retry
#             if state == StateEnum.FAILED:
#                 failure_reason = params.get("failure_reason")
#                 if nrequest.nb_retry + 1 < max_retries:
#                     failed = State(state=StateEnum.FAILED, failure_reason=failure_reason)
#                     queued = State(state=StateEnum.QUEUED)
#                     nstates.extend([failed, queued])
#                     nrequest.nb_retry += 1
#                 elif nrequest.nb_retry + 1 >= max_retries:
#                     # Request becomes CANCELLED after max retries
#                     nrequest.end = datetime.datetime.now(datetime.timezone.utc).isoformat()
#                     # Determine sub_state based on whether notifications are configured for the destination
#                     cancelled = State(
#                         state=StateEnum.CANCELLED,
#                         sub_state=SubStateEnum.NOTIFY if nrequest.dest.notifications else None,
#                         failure_reason=f"Max retries reached - Last error: {failure_reason}",
#                     )
#                     nstates.append(cancelled)
#             elif state in [StateEnum.SUCCESSFUL, StateEnum.CANCELLED]:
#                 # Handles direct SUCCESSFUL or CANCELLED updates (not from max_retry logic)
#                 nrequest.end = datetime.datetime.now(datetime.timezone.utc).isoformat()
#                 # sub_state_enum here is the one parsed from params, could be None
#                 final_s = State(state=state, sub_state=SubStateEnum.NOTIFY if nrequest.dest.notifications else None)
#                 nstates.append(final_s)
#             nrequest.states.extend(nstates)
#         elif sub_state:
#             if nrequest.states:
#                 last_state = nrequest.states[0]
#                 new_state = State(state = last_state.state, sub_state=sub_state)
#                 nrequest.states.append(new_state)
#         nrequest.update(params)
#         response = nrequest.to_dict()
#         response["Purge"] = can_purge(nrequest)
#         return response
#     return None


# @db_retry(total=3, backoff=5)
# def can_purge(
#     nrequest: TransferRequest,
# ) -> bool:
#     """Check if a request can be purged. Supports dependency injection for testing."""
#     requests = db.session.query(TransferRequest).filter(
#         TransferRequest.id != nrequest.id,
#         TransferRequest.filename == nrequest.filename,
#         TransferPolicy.id == nrequest.policy_id
#     ).all()
#     app.logger.debug("Found %d associated requests", len(requests))
#     for r in requests:
#         if not any(state.state == StateEnum.SUCCESSFUL for state in r.states):
#             return False
#     return True
