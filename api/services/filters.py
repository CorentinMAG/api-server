# from __future__ import annotations

# from typing import Optional, cast

# from flask import current_app as app

# from ..db import db
# from ..models import GlobalParameters, TransferPolicy
# from .utils import transactional


# @transactional
# def switch_mode(mode: str) -> None:
#     params = db.session.query(GlobalParameters).first()
#     if params is None:
#         app.logger.error("no global parameters, the dtr doesn't know how to switch mode")
#     else:
#         params.mode = mode
#         app.logger.info("dtr has switched to %s mode", mode.value.upper())


# def get_params() -> GlobalParameters | None:
#     try:
#         params = db.session.query(GlobalParameters).first()
#         return params
#     except Exception as e:
#         app.logger.warning(f"Could not retrieve global parameters: {str(e)}")
#         return None


# def check_policy_params(
#     policy_id: Optional[int | None] = None, transfer_policy_name: Optional[str | None] = None
# ) -> Optional[TransferPolicy | None]:
#     if policy_id is not None:
#         tr_policy = cast(TransferPolicy | None, db.session.query(TransferPolicy).get(policy_id))
#         if tr_policy is None:
#             app.logger.error("Transfer policy do not exists for policy_id {}".format(policy_id))
#             return None
#     elif transfer_policy_name is not None:
#         tr_policy = cast(
#             TransferPolicy,
#             db.session.query(TransferPolicy).filter(TransferPolicy.name == transfer_policy_name).first(),
#         )
#         if tr_policy is None:
#             app.logger.error(
#                 "Tranfer policy do not exists for  transfer_policy_name {}".format(transfer_policy_name)
#             )
#             return None
#     else:
#         pass

#     return tr_policy
