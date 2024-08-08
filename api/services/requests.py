from typing import cast
from dtr_common.constantes import State as StateEnum, SubState as SubStateEnum
from dtr_common.types.filter import FilterRequestParams
from flask import current_app as app

from ..db import db
from ..models import Queue, State, TransferPolicy, TransferRequest, TransferPolicyParameters
from api.services.filters import set_transfer_policy_params
import datetime
from sqlalchemy import or_, exc
from dtr_common.logs.logger import create_rp_logger

def get_next_request(session):
    request = (session
               .query(TransferRequest)
               .join(TransferPolicy)
               .join(Queue)
               .join(State)
               .order_by(Queue.priority.asc())
               .order_by(TransferRequest.created_at.asc())
               .filter(TransferRequest.last_state.in_([StateEnum.QUEUED, StateEnum.FAILED]))
               .filter(or_(
                TransferRequest.next_retry_min_time.is_(None),
                TransferRequest.next_retry_min_time <= datetime.datetime.utcnow(),
            ))
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
    if params.get("policy_id") is not None:
        base = base.filter(TransferRequest.policy_id == params["policy_id"])
    if params.get("policy_ids") is not None:
        policy_ids = list(map(lambda x: x.upper(), params["policy_ids"].split(",")))
        base = base.filter(TransferRequest.policy_id.in_(policy_ids))
    return base


def create_request(policy_id: int, dict_files: list[dict]) -> None:
    """
    Create transfer request
    """
    npolicy = set_transfer_policy_params(policy_id)

    if npolicy:
        queue_limit = npolicy.queue.queue_limit
        queue_threshold = npolicy.queue.queue_threshold
        queue_timeout = npolicy.queue.queue_timeout
        src_path = npolicy.src.path
        dest_path = npolicy.dest.path
        dest_name = npolicy.dest.target.name

        params = {"policy_id": policy_id}
        transfer_requests = filter_requests(params).all()

        queued_requests = list(filter(lambda x: x.last_state == StateEnum.QUEUED, transfer_requests))
        failed_requests = list(filter(lambda x: x.last_state == StateEnum.FAILED, transfer_requests))
        successful_requests = list(filter(lambda x: x.last_state == StateEnum.SUCCESSFUL, transfer_requests))
        cancelled_requests = list(filter(lambda x: x.last_state == StateEnum.CANCELLED, transfer_requests))
        in_progress_requests = list(filter(lambda x: x.last_state == StateEnum.IN_PROGRESS, transfer_requests))

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
                nstate = State(state=StateEnum.CANCELLED.value.upper(), sub_state=SubStateEnum.NOTIFY.value.upper(), 
                        failure_reason="Transfer timed-out in queued")
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

        # Remove data already successfully transferred on option
        files_already_in_queue = queued_files + failed_files + in_progress_files + cancelled_files
        successful_in_dict_files = list(filter(lambda f: f in successful_files , dict_files))
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

        if npolicy.parameters.only_new_data:
            # we transfer data that are not SUCCESSFUL or QUEUED, CANCELLED, FAILED, IN_PROGRESS
            # so we transfer only new data never seen by the database
            data_to_transfer = [i for i in dict_files if i not in successful_in_dict_files + queued_in_dict_files]
        else:
            # we transfer all data but those in QUEUED,IN_PROGRESS,FAILED,CANCELED in database
            data_to_transfer = [i for i in dict_files if i not in queued_in_dict_files]
        
        if len(data_to_transfer) > 0:
            app.logger.info("files to transfer: {}, {}".format(data_to_transfer, len(data_to_transfer)))
    

        # Add nb tr below queue limit
        available_slots = queue_limit - len(tr_in_queue)  # nb slots available in the queue
        # Send log when reach queue threshold
        if available_slots == queue_threshold:
            app.logger.info("Queue threshold is reached !")
        remaining_data_to_transfer = list(map(lambda x: x["file"], data_to_transfer))
    
        if available_slots > 0:
            nrequests: list[TransferRequest] = []
            for dict_file in data_to_transfer:
                nstate = State(state=StateEnum.QUEUED)
                nrequest = TransferRequest(filename=dict_file["file"], states=[nstate], size=dict_file["size"])
                nrequests.append(nrequest)

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

                    # Add report logs for End of Transfer Trigger
                    if nrequest.policy.src.path is None:
                        src_url =  nrequest.filename
                    else:
                        src_url =  f"{nrequest.policy.src.path}/{nrequest.filename}"
                    rp_logger = create_rp_logger("ReportLogs", "TransferTrigger", "END", "OK",
                                                nrequest.policy.name, src_url, nrequest.filename, 
                                                str(nrequest.uid))
                    rp_logger.info("End of TransferTrigger")
                    rp_logger.handlers = []  #clean logger
            except exc.SQLAlchemyError as e:
                for nrequest in nrequests:
                    app.logger.error("Error when creating transfer request with uid: %s ", nrequest.uid)

                    # Add report logs for End of Transfer Trigger
                    if nrequest.policy.src.path is None:
                        src_url =  nrequest.filename
                    else:
                        src_url =  f"{nrequest.policy.src.path}/{nrequest.filename}"
                    rp_logger = create_rp_logger("ReportLogs", "TransferTrigger", "END", "NOK",
                                                nrequest.policy.name, src_url, nrequest.filename, 
                                                str(nrequest.uid))
                    rp_logger.info("Error in creating Transfer Request: {}".format(e)) 
        else:
            app.logger.info("Queue full")

        if len(remaining_data_to_transfer) > 0:
            app.logger.info("{} data will not be processed in this run".format(len(remaining_data_to_transfer)))
            app.logger.debug("Data not processed in this run : {}".format(remaining_data_to_transfer))

        

def update_request(
    request_id: int,
    status: StateEnum,
    sub_status: SubStateEnum | None,
    next_retry_min_time: str | None,
    nb_retry: int,
    failure_reason: str | None,
) -> None:
    nstates = []
    nrequest = cast(TransferRequest, db.session.query(TransferRequest).get(request_id))
    max_retry = nrequest.policy.parameters.max_retry
    if status == StateEnum.FAILED.value.upper() and nb_retry < max_retry:
        nstate = State(state=StateEnum.FAILED.value.upper(), sub_state=sub_status, 
                       failure_reason=failure_reason)
        nstates.append(nstate)
    elif status == StateEnum.FAILED.value.upper() and nb_retry >= max_retry:
        app.logger.debug("Max retry is reached !")
        nstate = State(state=StateEnum.CANCELLED.value.upper(), sub_state=SubStateEnum.NOTIFY.value.upper(), 
                       failure_reason= "Transfer failure despite retries.")
        nstates.append(nstate)
    else:
        nstate = State(state=status, sub_state=sub_status, failure_reason=failure_reason)
        nstates.append(nstate)
    nrequest.states.extend(nstates)
    nrequest.nb_retry = nb_retry
    nrequest.next_retry_min_time = next_retry_min_time
    db.session.commit()
    app.logger.debug(
        "[%s] request has been updated to state %s", nrequest.uid, nrequest.last_state.value.upper()
    )
