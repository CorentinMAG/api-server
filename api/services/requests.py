from api.models.request import TransferRequest
from .base import BaseService
from api.models import TransferRequest, Worker, State
from api.repositories import TransferRequestRepository
from dtr_common.constantes import State as StateEnum, SubState as SubStateEnum, Type
import datetime
from dtr_common.schema import TransferRequestCreate, CommandedTransferRequestCreate, PeriodicalTransferRequestCreate
from typing import cast
import logging

logger = logging.getLogger(__name__)

class TransferRequestService(BaseService[TransferRequestRepository]):

    def __init__(self):
        super().__init__()
        self.transfer_policy_repository = self._get_or_create_repository("TransferPolicyRepository")
    
    def create(self, schema: TransferRequestCreate) -> TransferRequest:
        type = schema.item.type
        request = getattr(self, f"_create_{type}_request")(schema)
        return request
    
    def _create_commanded_request(self, schema: TransferRequestCreate):
        payload = cast(CommandedTransferRequestCreate, schema.item)

        policy_name = payload.transfer_policy
        policy = self.transfer_policy_repository.get_by_name(policy_name)

        if policy.type != Type.COMMANDED:
            logger.warning("User wants to create commanded transfer but a %s")

    def _create_periodical_request(self, schema: TransferRequestCreate) -> TransferRequest:
        payload = cast(PeriodicalTransferRequestCreate, schema.item)
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



