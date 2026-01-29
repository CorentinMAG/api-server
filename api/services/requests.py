from api.models.request import TransferRequest
from .base import BaseService
from api.models import TransferRequest, Worker, State
from api.repositories import TransferRequestRepository
from dtr_common.constantes import State as StateEnum, SubState as SubStateEnum
import datetime

class TransferRequestService(BaseService[TransferRequestRepository]):
    pass

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



