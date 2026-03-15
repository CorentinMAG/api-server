from api.models.request import TransferRequest
from .base import BaseService
from api.models import TransferRequest, Worker, State
from api.repositories import TransferRequestRepository
from dtr_common.constantes import State as StateEnum, SubState as SubStateEnum, Type
import datetime
from api.services import TransferPolicyService
from dtr_common.schema import (
    TransferRequestCreate,
    CommandedTransferRequestCreate,
    PeriodicalTransferRequestCreate,
)
from typing import cast
import logging
from urllib.parse import urlparse
import uuid

logger = logging.getLogger(__name__)


class TransferRequestService(BaseService[TransferRequestRepository]):

    policy: TransferPolicyService

    def create(self, schema: TransferRequestCreate) -> list[TransferRequest]:
        type = schema.item.type
        requests = getattr(self, f"_create_{type}_request")(schema)
        return sorted(requests, key=lambda r: r.created_at)

    def _create_commanded_request(self, schema: TransferRequestCreate):
        payload = cast(CommandedTransferRequestCreate, schema.item)

        policy_name = payload.transfer_policy
        policy = self.policy.get_by_name(policy_name)

        if policy.type != Type.COMMANDED:
            raise ValueError(
                f"policy {policy_name} has type {policy.type} (not commanded)"
            )
        dests = policy.dests

        # the path key of the payload ca be:
        # - a relative path
        # - the full path
        # - scheme + origin + full path
        # - scheme + origin + port + full path
        path = urlparse(payload.path)
        relative_path = path.path.lstrip("/")

        # the filename may not be included in the URL
        filename = (
            relative_path.split("/")[-1]
            if "." in relative_path.split("/")[-1]
            else None
        )

        requests: list[TransferRequest] = []
        multi_uid = uuid.uuid4() if len(dests) > 1 else None
        filters = {
            "src_relative_path": relative_path,
            "policy.name": policy_name,
            "follow_from_task": payload.uid,
            "multi_dest_uid": multi_uid,
            "filename": filename,
        }
        for dest in dests:
            request = self.repository.fetch(filters)
            # check if there are already IN_PROGRESS transfers for this file
            if request is not None:
                logger.warning(
                    "Transfer request is alreay in progress. (Policy: %s, destination: %s)",
                    policy_name,
                    dest.target.name,
                )
                requests.append(request)
            else:
                tr = TransferRequest(
                    filename=filename,
                    dest=dest,
                    src_relative_path=relative_path,
                    follow_from_task=payload.uid,
                    multi_dest_uid=multi_uid,
                )
                request = self.repository.create(tr)
                requests.append(request)
        return requests

    def _create_periodical_request(
        self, schema: TransferRequestCreate
    ) -> list[TransferRequest]:
        payload = cast(PeriodicalTransferRequestCreate, schema.item)
        policy = self.policy.get_by_id(payload.policy)

        only_new_data = policy.parameters.only_new_data
        nrequests = policy.transfers

    # def get_next_worker_request(
    #         self,
    #         size: int,
    #         worker: Worker | None
    #     ) -> TransferRequest | None:
    #     # a worker can only process files whose size is
    #     # <= 5% of the worker maximal capacity
    #     size = int(size * (1 - (5/100)))

    #     # we format the size in bytes
    #     size = size * 1024 *1024

    #     queues = [q.name for q in worker.queues] if worker else []
    #     return self.repository.get_next_request(size = size, queues = queues)

    # def get_next_notifier_request(self) -> TransferRequest | None:
    #     return self.repository.get_next_request(sub_state = SubStateEnum.NOTIFY)

    # def start_processing(self, request_id: int) -> TransferRequest:
    #     request = self.repository.get_by_id(request_id)

    #     now = datetime.datetime.now(datetime.timezone.utc)
    #     data = {
    #         "start": now
    #     }
    #     request.update(data)
    #     request.states.append(
    #         State(state = StateEnum.IN_PROGRESS)
    #     )
    #     self.repository.session.commit()
    #     return request
