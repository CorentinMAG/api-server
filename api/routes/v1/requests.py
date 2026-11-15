from __future__ import annotations

from flask import request

from api.routes import BaseAPI
from api.services import TransferRequestService
from api.utils import check_offline_mode


class TransferRequestAPI(BaseAPI[TransferRequestService]):

    decorators = [check_offline_mode]
    prefix = "requests"

    def get(self, id: int | None = None):
        pass

    def put(self, id: int):
        pass

    def delete(self, id: int):
        pass

    def post(self):
        data = request.json
        schema = TransferRequestCreate(**data)
        request = self.service.create(schema)
        self.service.commit()
        return request.to_dict()


# @bp.route("/get-status", methods=["GET"])
# def get_transfer_status():
#     """
#     get status about a transfer in database
#     """
#     params = get_params()
#     if params.mode == Mode.OFFLINE:
#         return {}
#     parsed_params = parse_params(request.args.to_dict())
#     if not parsed_params and not parsed_params.get("id"):
#         raise ValueError("Cannot fetch transfer request as no id has been provided")
#     id = uuid.UUID(parsed_params["id"])
#     nrequest = get_request(id)
#     if nrequest is None:
#         raise ValueError("transfer request not found: %s", id.hex)
#     last_state = nrequest.states[0]
#     return {
#         "download": {
#             "download_rate_mb_s": nrequest.download_rate,
#             "download_time_s": nrequest.download_time,
#             "source": nrequest.policy.src.to_dict(
#                 only=(
#                     "target.name",
#                     "path",
#                     "target.protocol",
#                 )
#             ),
#         },
#         "upload": {
#             "upload_rate_mb_s": nrequest.upload_rate,
#             "upload_time_s": nrequest.upload_time,
#             "destination": nrequest.dest.to_dict(
#                 only=("target.name", "path", "target.protocol")
#             ),
#         },
#         "follows_from_task": nrequest.follows_from_task,
#         "transfer_id": id.hex,
#         "transfer_info": {
#             "created_at": nrequest.created_at,
#             "data_identifier": nrequest.filename,
#             "data_size_mb": nrequest.size,
#             "data_type": "file",
#             "policy_name": nrequest.policy.name,
#             "transfer_begin_time": nrequest.start,
#             "transfer_end_time": nrequest.end,
#             "transfer_rate_mb_s": nrequest.avg_data_rate,
#         },
#         "transfer_status": {
#             "failure_count": nrequest.nb_retry,
#             "failure_reason": last_state.failure_reason,
#             "status": (
#                 "failed"
#                 if nrequest.nb_retry >= 1
#                 and nrequest.nb_retry < nrequest.policy.parameters.max_retry
#                 else last_state.state.value
#             ),
#             "sub_status": last_state.sub_state.value if last_state.sub_state else None,
#         },
#     }


# @bp.route("/request", methods=["POST"])
# def new_requests():
#     """
#     Create new periodical transfer requests.
#     """
#     payload = request.json
#     if not payload:
#         raise ValueError("no payload has been provided")
#     srequest = TriggerTransferRequestSchema(**payload)

#     create_periodical_requests(srequest)
#     return {}, 200


# @bp.route("/transfer-request", methods=["POST"])
# def new_commanded_request():
#     """
#     Create new commanded transfer request.
#     """
#     payload = request.json
#     if not payload:
#         raise ValueError("no payload provided cannot create transfer request")

#     srequest = CommandedTransferRequestSchema(**payload)

#     uuids = create_commanded_request(srequest)

#     return {"transfer_id": uuids}


# @bp.route("/request/<int:id>", methods=["PUT"])
# def update_requests(id: int):
#     """
#     Update transfer request.
#     """
#     payload = request.json
#     response = update_request(id, payload)
#     if response:
#         return response, 200
#     return {"error": "Request not found"}, 404
