# """
# Notifications API routes with dependency injection and error handling.
# """

# from __future__ import annotations
# from flask import Blueprint

# from api.utils.utils import check_gparams_before_request, custom_app

# bp = Blueprint("notification", __name__)

# @bp.before_request
# def handler():
#     check_gparams_before_request()

# @bp.route("/notifications", methods=["GET"])
# def notification():
#     """
#     Get next transfer request requiring notification.
#     """

#     app = custom_app()

#     nrequest = app.services.requests.get_next_notifier_request()

#     if nrequest is not None:
#         return {"request": nrequest.to_dict(rules=("dest.notifications", "-dest.target", "current_state.state", "current_state.failure_reason", "policy.name", "-multi_dest_uid"))}

#     return {"request": {}}
