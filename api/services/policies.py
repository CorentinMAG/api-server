from api.repositories import TransferPolicyRepository
from api.models import (
    TransferPolicy,
    SourcePolicy,
    DestinationPolicy,
    TransferPolicyParameters,
    KafkaParameters,
    Notification,
    Queue,
    Trigger,
)
from .base import BaseService
from dtr_common.schema import (
    TransferPolicyCreate,
    SourcePolicyCreate,
    DestinationPolicyCreate,
    TransferPolicyParametersCreate,
    ServerParametersCreate,
    TransferPolicyUpdate,
    Pagination,
)
from werkzeug.datastructures import ImmutableMultiDict
from .targets import TargetService
from api.services import (
    GlobalParametersService,
    QueueService,
    NotificationServerService,
    TriggerService,
)
from sqlalchemy.orm import selectinload


class TransferPolicyService(BaseService[TransferPolicyRepository]):
    target: TargetService
    parameters: GlobalParametersService
    queue: QueueService
    server: NotificationServerService
    trigger: TriggerService

    def get_by_name(self, name: str) -> TransferPolicy:
        return self.repository.get_by_name(name)

    def get_by_id(self, id: int) -> TransferPolicy:
        return self.repository.get_by_id(id)

    def paginate(self, args: ImmutableMultiDict) -> Pagination[TransferPolicy]:
        return self.repository.paginate(args)

    def update(self, id: int, schema: TransferPolicyUpdate) -> TransferPolicy:
        policy = self.repository.get_by_id(
            id,
            eager=[selectinload(TransferPolicy.dests)],
        )
        if schema.src is not None and schema.src.target is not None:
            # WARNING: when updating a policy, we can only update the target in
            # the source policy section, the other fields are ignored
            policy.src.target = self.target.get_by_name(schema.src.target)
        if schema.queue is not None:
            policy.queue = self.queue.get_by_name(schema.queue)
        if schema.dests is not None:
            # WARNING: when updating a transfer policy, we actually
            # delete all related destination policies and recreate them
            for dest in policy.dests:
                self.repository.delete(dest)
            dests_policy = self._build_dests_policy(schema.dests)
            policy.dests = dests_policy
        if schema.trigger is not None:
            policy.trigger = self.trigger.get_by_name(schema.trigger)
        return self.repository.update(
            policy,
            schema.model_dump(
                exclude_none=True, exclude={"src.target", "queue", "dests", "trigger"}
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
        trigger = self._build_trigger_policy(schema.trigger)
        policy = TransferPolicy(
            src=src_policy,
            dests=dests_policy,
            parameters=parameters,
            queue=queue,
            trigger=trigger,
            **schema.model_dump(
                exclude={"src", "dests", "parameters", "queue", "trigger"}
            ),
        )
        return self.repository.create(policy)

    def get_enabled(self, skip: int = 0, limit: int = 100) -> list[TransferPolicy]:
        return self.repository.get_all(
            filters={"enabled": True}, skip=skip, limit=limit
        )

    def _build_src_policy(self, src: SourcePolicyCreate) -> SourcePolicy:
        target_name = src.target
        target = self.target.get_by_name(target_name)
        src_policy = SourcePolicy(target=target, **src.model_dump(exclude={"target"}))
        return src_policy

    def _build_trigger_policy(self, name: str | None) -> Trigger | None:
        if name is None:
            return
        return self.trigger.get_by_name(name)

    def _build_dests_policy(
        self,
        dests: list[DestinationPolicyCreate],
    ) -> list[DestinationPolicy]:
        dest_policies: list[DestinationPolicy] = []
        for dest in dests:
            target_name = dest.target
            target = self.target.get_by_name(target_name)
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
            server = self.server.get_by_name(notification.server)
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
        global_params = self.parameters.get()
        p = {}
        for key, value in params.model_dump().items():
            if value is None:
                p[key] = getattr(global_params, key, None)
            else:
                p[key] = value
        return TransferPolicyParameters(**p)

    def _build_queue_policy(self, queue_name: str) -> Queue:
        return self.queue.get_by_name(queue_name)
