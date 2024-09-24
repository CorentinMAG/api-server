from typing import cast, Optional, Any
from dtr_common.constantes import State as StateEnum, SubState as SubStateEnum
from dtr_common.types.filter import FilterRequestParams
from flask import current_app as app

from ..db import db
from ..models import Queue, State, TransferPolicy, TransferRequest, TransferPolicyParameters
from api.services.filters import check_policy_params
import datetime
from sqlalchemy import or_, exc
from dtr_common.logs.logger import create_rp_logger
from dtr_common.utils import convert_datetime_regex
from dtr_common.types.requests import CreateRequestCmdJson
import os
import re


log_lvl = os.environ.get("DTR_LOG_LEVEL", "INFO")
version = os.environ["DTR_API_VERSION"]
ssystem_version = os.environ["DTR_VERSION"]


def get_next_request(session, params: FilterRequestParams):
    worker_size_in_gb = 0
    if params.get("worker_storage") is not None:
        worker_size_in_gb = int(re.sub("G", "", params["worker_storage"]))
        worker_size_in_mb = worker_size_in_gb * 1024

    request = (
        session.query(TransferRequest)
        .join(TransferPolicy)
        .join(Queue)
        .join(State)
        .order_by(Queue.priority.asc())
        .order_by(TransferRequest.created_at.asc())
        .filter(TransferRequest.last_state.in_([StateEnum.QUEUED, StateEnum.FAILED]))
        .filter(
            or_(
                TransferRequest.next_retry_min_time.is_(None),
                TransferRequest.next_retry_min_time <= datetime.datetime.utcnow(),
            )
        )
        .filter(or_(TransferRequest.size.is_(None), TransferRequest.size < worker_size_in_mb))
        .with_for_update(skip_locked=True)
        .first()
    )

    return request


def filter_requests(params: FilterRequestParams):
    base = (
        db.session.query(TransferRequest)
        .join(TransferPolicy)
        .join(Queue)
        .join(State)
        .join(TransferPolicyParameters)
        .order_by(Queue.priority.asc())
        .order_by(TransferRequest.created_at.asc())
    )
    if params.get("state") is not None:
        base = base.filter(TransferRequest.last_state == params["state"].upper())
    if params.get("states") is not None:
        states = list(map(lambda x: x.upper(), params["states"].split(",")))
        base = base.filter(TransferRequest.last_state.in_(states))
    if params.get("sub_state") is not None:
        base = base.filter(TransferRequest.last_sub_state == params["sub_state"].upper())
    if params.get("queues") is not None:
        queues = params["queues"].split(",")
        base = base.filter(Queue.name.in_(queues))
    if params.get("id") is not None:
        base = base.filter(TransferRequest.id == params["id"])
    if params.get("ids") is not None:
        transfer_ids = params["ids"].split(",")
        transfer_ids = map(lambda i: int(i), transfer_ids)
        base = base.filter(TransferPolicy.id.in_(transfer_ids))
    if params.get("policy_id") is not None:
        base = base.filter(TransferRequest.policy_id == params["policy_id"])
    if params.get("transfer_policy_name") is not None:
        base = base.filter(TransferPolicy.name == params["transfer_policy_name"])
    if params.get("policy_ids") is not None:
        policy_ids = list(map(lambda x: x.upper(), params["policy_ids"].split(",")))
        base = base.filter(TransferRequest.policy_id.in_(policy_ids))
    return base


def create_request(
    policy_id: Optional[int | None] = None,
    dict_files: Any = None,
    payload: Optional[CreateRequestCmdJson | None] = None,
) -> list[TransferRequest] | None:
    """
    Create transfer request
    """
    if payload is not None and policy_id is None and dict_files is None:
        transfer_policy = payload["transfer_policy"]
        npolicy = check_policy_params(transfer_policy_name=transfer_policy)
        params = {"transfer_policy_name": transfer_policy}
    elif policy_id is not None and dict_files is not None and payload is None:
        npolicy = check_policy_params(policy_id=policy_id)
        params = {"policy_id": policy_id}
    else:
        pass

    requests_to_return = None
    if npolicy:
        queue_limit = npolicy.queue.queue_limit
        queue_threshold = npolicy.queue.queue_threshold
        queue_timeout = npolicy.queue.queue_timeout
        src_path = convert_datetime_regex(npolicy.src.path)
        src_name = npolicy.src.target.name
        host = npolicy.src.target.host
        pattern = npolicy.src.pattern
        dest_path = convert_datetime_regex(npolicy.dest.path)
        dest_name = npolicy.dest.target.name

        transfer_requests = filter_requests(params).all()

        queued_requests = list(filter(lambda x: x.last_state == StateEnum.QUEUED, transfer_requests))
        failed_requests = list(filter(lambda x: x.last_state == StateEnum.FAILED, transfer_requests))
        successful_requests = list(filter(lambda x: x.last_state == StateEnum.SUCCESSFUL, transfer_requests))
        cancelled_requests = list(filter(lambda x: x.last_state == StateEnum.CANCELLED, transfer_requests))
        in_progress_requests = list(
            filter(lambda x: x.last_state == StateEnum.IN_PROGRESS, transfer_requests)
        )

        successful_files = list(map(lambda x: {"file": x.filename, "size": x.size}, successful_requests))
        queued_files = list(map(lambda x: {"file": x.filename, "size": x.size}, queued_requests))
        failed_files = list(map(lambda x: {"file": x.filename, "size": x.size}, failed_requests))
        cancelled_files = list(map(lambda x: {"file": x.filename, "size": x.size}, cancelled_requests))
        in_progress_files = list(map(lambda x: {"file": x.filename, "size": x.size}, in_progress_requests))

        data_to_transfer = []

        # Check if there are transfer requests which reached queue timeout
        tr_in_queue = queued_requests + failed_requests + in_progress_requests

        for tr in tr_in_queue:
            tr_age = datetime.datetime.utcnow() - tr.state_created_at
            tr_age = tr_age.total_seconds()
            if src_path is None:
                src_path = "/"
                src_url = tr.filename
            else:
                src_url = f"{src_path}/{tr.filename}"
            dest_url = f"{dest_path}/{tr.filename}"

            if tr_age > queue_timeout:
                nstate = State(
                    state=StateEnum.CANCELLED.value.upper(),
                    sub_state=SubStateEnum.NOTIFY.value.upper(),
                    failure_reason="Transfer timed-out in queued",
                )
                nrequest = cast(TransferRequest, db.session.query(TransferRequest).get(tr.id))
                nrequest.states.append(nstate)
                try:
                    db.session.commit()
                    app.logger.info(
                        "Cancel of data transfer: uid: %s, source: %s, source_url: %s, destination: %s, destination_url: %s, filename: %s, reason: queue timeout",
                        tr.uid,
                        src_path,
                        src_url,
                        dest_name,
                        dest_url,
                        tr.filename,
                    )
                except exc.SQLAlchemyError:
                    pass

        if dict_files is None and payload is not None:
            file = convert_datetime_regex(os.path.split(payload["path"])[1])
            dict_files = [{"file": file, "size": None}]
            files_already_in_queue = queued_files + failed_files + in_progress_files
        else:
            # Remove data already successfully transferred on option
            files_already_in_queue = queued_files + failed_files + in_progress_files + cancelled_files

        successful_in_dict_files = list(filter(lambda f: f in successful_files, dict_files))
        queued_in_dict_files = list(filter(lambda f: f in files_already_in_queue, dict_files))

        if len(successful_in_dict_files) > 0:
            app.logger.info(
                "Not transferring twice the same data: {}, {}".format(
                    successful_in_dict_files, len(successful_in_dict_files)
                )
            )
        if len(queued_in_dict_files) > 0:
            app.logger.info(
                "Not managing data already in queue: {}, {}".format(
                    queued_in_dict_files, len(queued_in_dict_files)
                )
            )
            requests_to_return = queued_requests + failed_requests + in_progress_requests
        if npolicy.parameters.only_new_data:
            # we transfer data that are not SUCCESSFUL or QUEUED, CANCELLED, FAILED, IN_PROGRESS
            # so we transfer only new data never seen by the database
            data_in_db = successful_in_dict_files + queued_in_dict_files
            data_to_transfer = [i for i in dict_files if i not in data_in_db]
        else:
            # we transfer all data but those in QUEUED,IN_PROGRESS,FAILED,CANCELED in database
            data_to_transfer = [i for i in dict_files if i not in queued_in_dict_files]

        if len(data_to_transfer) > 0:
            app.logger.info("files to transfer: {}, {}".format(data_to_transfer, len(data_to_transfer)))

        # Add nb tr below queue limit
        if queue_limit is not None:
            available_slots = queue_limit - len(tr_in_queue)  # nb slots available in the queue

        # Display a log when reach queue threshold
        if available_slots == queue_threshold:
            app.logger.info("Queue threshold is reached !")

        remaining_data_to_transfer = list(map(lambda x: x["file"], data_to_transfer))

        if available_slots > 0:
            nrequests: list[TransferRequest] = []
            for dict_file in data_to_transfer:
                nstate = State(state=StateEnum.QUEUED)
                if payload is not None:
                    uid = payload.get("uid", None)
                    path = os.path.split(payload["path"])
                    relative_path = None
                    if len(path) > 1:
                        relative_path = convert_datetime_regex(path[0])
                    timestamp = payload["timestamp"]
                    nrequest = TransferRequest(
                        filename=convert_datetime_regex(dict_file["file"]),
                        states=[nstate],
                        uid=uid,
                        created_at=timestamp,
                        source_relative_path=relative_path,
                    )
                else:
                    nrequest = TransferRequest(
                        filename=dict_file["file"], states=[nstate], size=dict_file["size"]
                    )
                if src_path is None:
                    src_url = nrequest.filename
                elif re.search(pattern, src_path):
                    src_url = src_path
                elif src_path.startswith(host):
                    src_url = src_path
                else:
                    src_url = f"{src_path}/{nrequest.filename}"
                dest_url = f"{dest_path}/{nrequest.filename}"

                # Add report logs
                rp_logger = create_rp_logger(
                    "ReportLogs",
                    log_lvl,
                    "DTR",
                    ssystem_version,
                    "Api",
                    version,
                    "TransferRequest",
                    "BEGIN",
                    None,
                    npolicy.name,
                    src_url,
                    nrequest.filename,
                    None,
                    None,
                    src_name,
                    dest_url,
                    dest_name,
                )
                rp_logger.info("Request for Transfer")
                rp_logger.handlers = []  # clean logger

                nrequests.append(nrequest)
                requests_to_return = nrequests

                remaining_data_to_transfer.remove(dict_file["file"])
                available_slots -= 1
                if available_slots == 0:
                    app.logger.info("Queue limit reached")
                    break

            npolicy.transfers.extend(nrequests)
            try:
                db.session.commit()
                for nrequest in nrequests:
                    app.logger.debug("Transfer request has been created with uid: %s ", nrequest.uid)

                    # Add report logs
                    rp_logger = create_rp_logger(
                        "ReportLogs",
                        log_lvl,
                        "DTR",
                        ssystem_version,
                        "Api",
                        version,
                        "TransferRequest",
                        "END",
                        "OK",
                        npolicy.name,
                        src_url,
                        nrequest.filename,
                        nrequest.id,
                        str(nrequest.uid),
                        src_name,
                        dest_url,
                        dest_name,
                    )
                    rp_logger.info("End of request for transfer")
                    rp_logger.handlers = []  # clean logger

                    rp_logger = create_rp_logger(
                        "ReportLogs",
                        log_lvl,
                        "DTR",
                        ssystem_version,
                        "Api",
                        version,
                        "TransferTrigger",
                        "END",
                        "OK",
                        npolicy.name,
                        src_url,
                        nrequest.filename,
                        nrequest.id,
                        str(nrequest.uid),
                    )
                    rp_logger.info("End of TransferTrigger")
                    rp_logger.handlers = []  # clean logger

            except exc.SQLAlchemyError as e:
                for nrequest in nrequests:
                    app.logger.error("Error when creating transfer request with uid: %s", nrequest.uid)

                    # Add report logs TransferTrigger/TransferRequest in case of error
                    rp_logger = create_rp_logger(
                        "ReportLogs",
                        log_lvl,
                        "DTR",
                        ssystem_version,
                        "Api",
                        version,
                        "TransferRequest",
                        "END",
                        "NOK",
                        npolicy.name,
                        src_url,
                        nrequest.filename,
                        None,
                        None,
                        src_name,
                        dest_url,
                        dest_name,
                    )
                    rp_logger.info("Error in creating TransferJob: {}".format(e))
                    rp_logger.handlers = []  # clean logger

                    rp_logger = create_rp_logger(
                        "ReportLogs",
                        log_lvl,
                        "DTR",
                        ssystem_version,
                        "Api",
                        version,
                        "TransferTrigger",
                        "END",
                        "NOK",
                        npolicy.name,
                        src_url,
                        nrequest.filename,
                        nrequest.id,
                        str(nrequest.uid),
                    )
                    rp_logger.info("Error in creating Transfer Request: {}".format(e))
        else:
            app.logger.info("Queue full")
            return []

        if len(remaining_data_to_transfer) > 0:
            app.logger.info(
                "{} data will not be processed in this run".format(len(remaining_data_to_transfer))
            )
            app.logger.debug("Data not processed in this run : {}".format(remaining_data_to_transfer))

    return requests_to_return


def update_request(
    request_id: int,
    status: StateEnum,
    sub_status: Optional[SubStateEnum | None],
    next_retry_min_time: Optional[str | None],
    nb_retry: int,
    failure_reason: Optional[str | None],
    size: Optional[int | None],
    rate: Optional[int | None],
    beginning_time: Optional[str | None],
    end_time: Optional[str | None],
) -> None:
    nstates = []
    nrequest = cast(TransferRequest, db.session.query(TransferRequest).get(request_id))
    max_retry = nrequest.policy.parameters.max_retry
    if max_retry is not None:
        if status == StateEnum.FAILED.value.upper() and nb_retry < max_retry:
            nstate = State(
                state=StateEnum.FAILED.value.upper(), sub_state=sub_status, failure_reason=failure_reason
            )
            nstates.append(nstate)
        elif status == StateEnum.FAILED.value.upper() and nb_retry >= max_retry:
            app.logger.debug("Max retry is reached !")
            nstate = State(
                state=StateEnum.CANCELLED.value.upper(),
                sub_state=SubStateEnum.NOTIFY.value.upper(),
                failure_reason="Transfer failure despite retries.",
            )
            nstates.append(nstate)
        else:
            nstate = State(state=status, sub_state=sub_status, failure_reason=failure_reason)
            nstates.append(nstate)
    nrequest.states.extend(nstates)

    nrequest.nb_retry = nb_retry
    nrequest.size = size
    nrequest.rate = rate
    nrequest.beginning_time = beginning_time
    nrequest.end_time = end_time
    nrequest.next_retry_min_time = next_retry_min_time

    db.session.commit()
    app.logger.debug(
        "[%s] request has been updated to state %s", nrequest.uid, nrequest.last_state.value.upper()
    )
