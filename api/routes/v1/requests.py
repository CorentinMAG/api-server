from flask import Blueprint, request
from api.services.filters import get_params
from api.services.requests import (
    filter_requests,
    create_periodical_requests,
    update_request,
    create_commanded_request,
)
from dtr_common.utils import parse_params
from dtr_common.constantes import Mode
from dtr_common.schema import TriggerTransferRequestSchema, CommandedTransferRequestSchema

from api.db import db

bp = Blueprint("requests", __name__)


@bp.route("/get-status", methods=["GET"])
def get_transfer_status():
    """
    For a given transfer-id, list the transfer request detailed informations
    """
    nglobal_parameters = get_params()
    if nglobal_parameters is None or nglobal_parameters.mode == Mode.OFFLINE:
        return {"error": "No configuration found"}, 404
    else:
        parsed_params = parse_params(request.args.to_dict())
        if not parsed_params:
            return {"error": "No transfer-id provided"}, 400
        result = filter_requests(parsed_params)
        req = db.session.scalar(result)
        
        # Check if the request was found
        if req is None:
            return {"error": "Transfer request not found"}, 404
        
        # Get the latest state
        latest_state = req.states[0] if req.states else None
        
        # Calculate transfer rate if both start and end times are available
        transfer_rate = None
        if req.start and req.end and req.size:
            try:
                start_time = req.start
                end_time = req.end
                duration_seconds = (end_time - start_time).total_seconds()
                if duration_seconds > 0:
                    transfer_rate = req.size / duration_seconds  # MB/s
            except (TypeError, ValueError):
                pass
        
        # Get failure information
        failure_count = req.nb_retry
        failure_reason = None
        if latest_state and latest_state.failure_reason:
            failure_reason = latest_state.failure_reason
        
        # Get source and destination information
        source = None
        destination = None
        if req.policy and req.policy.src:
            source = {
                "name": req.policy.src.target.name if req.policy.src.target else None,
                "path": req.policy.src.path,
                "protocol": req.policy.src.target.protocol.value if req.policy.src.target else None
            }
        
        if req.dest:
            destination = {
                "name": req.dest.target.name if req.dest.target else None,
                "path": req.dest.path,
                "protocol": req.dest.target.protocol.value if req.dest.target else None
            }
        
        # Create detailed request object with grouped information
        detailed_request = {
            "follows_from_task": req.follows_from_task,
            "transfer_id": str(req.uid),
            "transfer_status": {
                "status": latest_state.state.value if latest_state else "UNKNOWN",
                "sub_status": latest_state.sub_state.value if latest_state and latest_state.sub_state else None,
                "failure_count": failure_count,
                "failure_reason": failure_reason
            },
            "transfer_info": {
                "data_identifier": req.filename,
                "data_size_mb": req.size,
                "data_type": "file",  # All transfers are files
                "policy_name": req.policy.name if req.policy else None,
                "created_at": req.created_at.isoformat() if req.created_at else None,
                "transfer_begin_time": req.start.isoformat() if req.start else None,
                "transfer_end_time": req.end.isoformat() if req.end else None,
                "transfer_rate_mb_s": round(transfer_rate, 2) if transfer_rate else None
            },
            "download": {
                "source": source,
                "download_rate_mb_s": req.download_rate,
                "download_time_s": req.download_time
            },
            "upload": {
                "destination": destination,
                "upload_rate_mb_s": req.upload_rate,
                "upload_time_s": req.upload_time
            }
        }
        
        return detailed_request, 200


@bp.route("/request", methods=["POST"])
def new_requests():
    payload = request.json

    schema = TriggerTransferRequestSchema(**payload)

    create_periodical_requests(schema)
    return "", 200


@bp.route("/transfer-request", methods=["POST"])
def new_commanded_request():
    payload = request.json
    if not payload:
        return {
            "error": "No payload provided"
                    }, 400

    schema = CommandedTransferRequestSchema(**payload)

    request_uids, error_message, status_code = create_commanded_request(schema)
    if request_uids:
        return {"transfer_id": request_uids}, 200
    return {
            "error": error_message or "Failed to create transfer request"
                }, status_code or 500


@bp.route("/request/<int:id>", methods=["PUT"])
def update_requests(id: int):
    payload = request.json

    response = update_request(id, payload)

    if response:
        return response, 200
    return "", 200