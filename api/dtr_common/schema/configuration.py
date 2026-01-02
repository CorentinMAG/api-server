# from __future__ import annotations
# from pydantic import model_validator
# from .base import StrictBaseModel
# from .parameters import GlobalParametersSchema
# from .server import ServerSchema
# from .queue import QueueSchema
# from .target import TargetSchema
# from .policies import TransferPolicySchema


# class ConfigurationSchema(StrictBaseModel):
#     global_parameters: GlobalParametersSchema
#     notification_servers: list[ServerSchema]
#     queues: list[QueueSchema]
#     targets: list[TargetSchema]
#     transfer_policies: list[TransferPolicySchema]

#     @model_validator(mode="after")
#     def validate_policies_targets(self):
#         targets_name = [target.name for target in self.targets]

#         for policy in self.transfer_policies:
#             src_target = policy.src.target
#             dst_targets = list(map(lambda d: d.target, policy.dests))

#             if src_target not in targets_name:
#                 raise ValueError(f"Incorrect src target name in policy {policy.name}: {src_target}")

#             for dst_target in dst_targets:
#                 if dst_target not in targets_name:
#                     raise ValueError(f"Incorrect dest target name in policy {policy.name}: {dst_target}")
#         return self

#     @model_validator(mode="after")
#     def validate_unique_target_name(self):
#         names = [t.name for t in self.targets]
#         if len(names) != len(set(names)):
#             raise ValueError("Multiple targets have the same name")
#         return self

#     @model_validator(mode="after")
#     def validate_unique_policy_name(self):
#         names = [p.name for p in self.transfer_policies]
#         if len(names) != len(set(names)):
#             raise ValueError("Multiple transfer policies have the same name")
#         return self

# @model_validator(mode="after")
# def validate_unique_queue_name(self):
#     names = [q.name for q in self.queues]
#     if len(names) != len(set(names)):
#         raise ValueError("Multiple queues have the same name")
#     return self

# @model_validator(mode="after")
# def validate_unique_server_name(self):
#     names = [s.name for s in self.notification_servers]
#     if len(names) != len(set(names)):
#         raise ValueError("Multiple notification servers have the same name")
#     return self

# @model_validator(mode="after")
# def validate_notifications(self):
#     server_names = [s.name for s in self.notification_servers]
#     for policy in self.transfer_policies:
#         dests = policy.dests
#         dest_notif = list(filter(lambda d: d.notifications is not None, dests))
#         for d in dest_notif:
#             for notif in d.notifications:
#                 server_name = notif.server
#                 if server_name not in server_names:
#                     raise ValueError(f"notification server: {server_name} doesn't exist")
