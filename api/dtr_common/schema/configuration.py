from __future__ import annotations

from pydantic import model_validator

from .base import StrictBaseModel
from .parameters import GlobalParametersCreate
from .policies import TransferPolicyCreate
from .queue import QueueCreate
from .server import ServerCreate
from .target import TargetCreate
from .trigger import TriggerCreate


class ConfigurationSchema(StrictBaseModel):
    global_parameters: GlobalParametersCreate
    notification_servers: list[ServerCreate]
    triggers: list[TriggerCreate] = []
    workers: list[TriggerCreate] = []
    queues: list[QueueCreate]
    targets: list[TargetCreate]
    transfer_policies: list[TransferPolicyCreate]

    @model_validator(mode="after")
    def validate_policies_targets(self):
        targets_name = [target.name for target in self.targets]

        for policy in self.transfer_policies:
            src_target = policy.src.target
            dest_targets = list(map(lambda d: d.target, policy.dests))

            if src_target not in targets_name:
                raise ValueError(f"Incorrect src target name in policy {policy.name}: {src_target}")

            for dst_target in dest_targets:
                if dst_target not in targets_name:
                    raise ValueError(f"Incorrect dest target name in policy {policy.name}: {dst_target}")
        return self

    @model_validator(mode="after")
    def validate_unique_target_name(self):
        names = [t.name for t in self.targets]
        if len(names) != len(set(names)):
            raise ValueError("Multiple targets have the same name")
        return self

    @model_validator(mode="after")
    def validate_unique_policy_name(self):
        names = [p.name for p in self.transfer_policies]
        if len(names) != len(set(names)):
            raise ValueError("Multiple transfer policies have the same name")
        return self

    @model_validator(mode="after")
    def validate_unique_queue_name(self):
        names = [q.name for q in self.queues]
        if len(names) != len(set(names)):
            raise ValueError("Multiple queues have the same name")
        return self

    @model_validator(mode="after")
    def validate_unique_server_name(self):
        names = [s.name for s in self.notification_servers]
        if len(names) != len(set(names)):
            raise ValueError("Multiple notification servers have the same name")
        return self

    @model_validator(mode="after")
    def validate_notifications(self):
        server_names = [s.name for s in self.notification_servers]
        for policy in self.transfer_policies:
            dests = policy.dests
            dest_notif = list(filter(lambda d: d.notifications is not None, dests))
            for d in dest_notif:
                for notif in d.notifications:
                    server_name = notif.server
                    if server_name not in server_names:
                        raise ValueError(
                            f"notification server: {server_name} doesn't exist (policy: {policy.name})"
                        )

    @model_validator(mode="after")
    def validate_unique_worker_name(self):
        names = [w.name for w in self.workers]
        if len(names) != len(set(names)):
            raise ValueError("Multiple workers have the same name")
        return self

    @model_validator(mode="after")
    def validate_unique_trigger_name(self):
        names = [w.name for w in self.triggers]
        if len(names) != len(set(names)):
            raise ValueError("Multiple triggers have the same name")
        return self

    @model_validator(mode="after")
    def validate_worker_queues(self):
        queue_names = [q.name for q in self.queues]
        for worker in self.workers:
            if not set(worker.queues).issubset(queue_names):
                raise ValueError(f"Worker {worker.name} is linked to unknown queues")
        return self

    @model_validator(mode="after")
    def validate_policy_trigger(self):
        trigger_names = [t.name for t in self.triggers]
        for policy in self.transfer_policies:
            trigger_name = policy.trigger
            if trigger_name is not None and trigger_name not in trigger_names:
                raise ValueError(f"Policy {policy.name} is linked to the unknown trigger {trigger_name}")
