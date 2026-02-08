from api.repositories import TransferPolicyRepository, TargetRepository, GlobalParametersRepository, NotificationServerRepository, QueueRepository
from api.models import (
    TransferPolicy,
    SourcePolicy,
    DestinationPolicy,
    TransferPolicyParameters,
    KafkaParameters,
    Notification,
    Queue,
)
from .base import BaseService
from api.dtr_common.schema import (
    TransferPolicyCreate,
    SourcePolicyCreate,
    DestinationPolicyCreate,
    TransferPolicyParametersCreate,
    ServerParametersCreate,
    TransferPolicyUpdate,
)
from werkzeug.datastructures import ImmutableMultiDict
from api.dtr_common.schema import Pagination


class TransferPolicyService(BaseService[TransferPolicyRepository]):

    def __init__(self):
        super().__init__()
        self.target_repository = self._get_or_create_repository(TargetRepository)
        self.parameters_repository = self._get_or_create_repository(
            GlobalParametersRepository
        )
        self.server_repository = self._get_or_create_repository(
            NotificationServerRepository
        )
        self.queue_repository = self._get_or_create_repository(QueueRepository)

    def get_by_name(self, name: str) -> TransferPolicy:
        return self.repository.get_by_name(name)

    def get_by_id(self, id: int) -> TransferPolicy:
        return self.repository.get_by_id(id)

    def paginate(self, args: ImmutableMultiDict) -> Pagination[TransferPolicy]:
        return self.repository.paginate(args)

    def get_with_relations(self, id: int) -> TransferPolicy:
        return self.repository.get_with_relations(id)

    def count(self, filters: dict[str, any] | None = None) -> int:
        return self.repository.count(filters)

    def get(
        self, skip: int = 0, limit: int = 100, filters: dict[str, any] | None = None
    ) -> list[TransferPolicy]:
        return self.repository.get(skip, limit, filters)

    def update(self, id: int, schema: TransferPolicyUpdate) -> TransferPolicy:
        policy = self.repository.get_with_relations(id)
        if schema.src is not None and schema.src.target is not None:
            policy.src.target = self.target_repository.get_by_name(schema.src.target)
        if schema.queue is not None:
            policy.queue = self.queue_repository.get_by_name(schema.queue)
        if schema.dests is not None:
            for dest in policy.dests:
                self.repository.delete(dest)
            dests_policy = self._build_dests_policy(schema.dests)
            policy.dests = dests_policy
        return self.repository.update(
            policy,
            schema.model_dump(
                exclude_none=True, exclude={"src.target", "queue", "dests"}
            ),
        )

    def delete(self, id: int) -> None:
        policy = self.repository.get_by_id(id)
        self.repository.delete(policy)

    def create(self, schema: TransferPolicyCreate) -> TransferPolicy:
        src_policy = self._build_src_policy(schema.src)
        dests_policy = self._build_dests_policy(schema.dests)
        queue = self._build_queue_policy(schema.queue)
        parameters = self._build_parameters_policy(schema.parameters)
        policy = TransferPolicy(
            src=src_policy,
            dests=dests_policy,
            parameters=parameters,
            queue=queue,
            **schema.model_dump(exclude={"src", "dests", "parameters", "queue"}),
        )
        return self.repository.create(policy)

    def get_enabled(self, skip: int = 0, limit: int = 100) -> list[TransferPolicy]:
        return self.repository.get_all(
            filters={"enabled": True}, skip=skip, limit=limit
        )

    def _build_src_policy(self, src: SourcePolicyCreate) -> SourcePolicy:
        target_name = src.target
        target = self.target_repository.get_by_name(target_name)
        src_policy = SourcePolicy(target=target, **src.model_dump(exclude={"target"}))
        return src_policy

    def _build_dests_policy(
        self,
        dests: list[DestinationPolicyCreate],
    ) -> list[DestinationPolicy]:
        dest_policies: list[DestinationPolicy] = []
        for dest in dests:
            target_name = dest.target
            target = self.target_repository.get_by_name(target_name)
            notifications = self._build_notifications(dest.notifications)
            dest_policies.append(
                DestinationPolicy(
                    target=target,
                    notifications=notifications,
                    **dest.model_dump(exclude={"target", "notifications"}),
                )
            )
        return dest_policies

    def _build_notifications(
        self,
        notifications: list[ServerParametersCreate] | None,
    ) -> list[Notification]:
        nnotifications: list[Notification] = []
        if notifications is None:
            return nnotifications
        for notification in notifications:
            server = self.server_repository.get_by_name(notification.server)
            n = Notification(server=server)
            server_type = server.type.value
            param_class = globals().get(f"{server_type.capitalize()}Parameters")

            for parameter in notification.parameters:
                p = param_class(**parameter.model_dump())
                n.parameters.append(p)
            nnotifications.append(n)
        return nnotifications

    def _build_parameters_policy(
        self,
        params: TransferPolicyParametersCreate,
    ) -> TransferPolicyParameters:
        global_params = self.parameters_repository.get()
        p = {}
        for key, value in params.model_dump().items():
            if value is None:
                p[key] = getattr(global_params, key, None)
            else:
                p[key] = value
        return TransferPolicyParameters(**p)

    def _build_queue_policy(self, queue_name: str) -> Queue:
        return self.queue_repository.get_by_name(queue_name)
