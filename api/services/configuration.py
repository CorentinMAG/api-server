# from __future__ import annotations

# import copy
# from typing import cast
# from dtr_common.constantes import Type
# from dtr_common.schema import (
#     ConfigurationSchema,
#     GlobalParametersSchema,
#     QueueSchema,
#     ServerSchema,
#     TargetSchema,
#     TransferPolicySchema,
#     TriggerSchema,
#     WorkerSchema
# )
# from sqlalchemy import select
# from api.models import db
# from api.models import (
#     Credentials,
#     DestinationPolicy,
#     GlobalParameters,
#     KafkaTopicParameters,
#     NotificationServer,
#     Trigger,
#     Queue,
#     ServerParameters,
#     SourcePolicy,
#     Target,
#     TargetParameters,
#     TransferPolicy,
#     TransferPolicyParameters,
#     Worker
# )
# from .utils import transactional


# def create_servers(servers: list[ServerSchema]) -> list[NotificationServer]:
#     db_servers = db.session.scalars(select(NotificationServer)).all()
#     db_servers = {server.name: server for server in db_servers}
#     config_servers = {server.name: server for server in servers}
#     nservers: list[NotificationServer] = []
#     for name, sserver in config_servers.items():
#         model = sserver.model_dump()
#         # update
#         if name in db_servers.keys():
#             nserver = db_servers.get(name)
#             nserver.update(model)
#         # create
#         else:
#             credentials = sserver.credentials
#             if credentials is not None:
#                 cred = {"login": credentials.login, "password": credentials.password.get_secret_value()}
#                 ncred = Credentials(**cred)
#                 model["credentials"] = ncred
#             nserver = NotificationServer(**model)
#         nservers.append(nserver) 
#     # delete
#     servers_to_delete = [nserver for nserver in db_servers.values() if nserver.name not in config_servers.keys()]
#     for s in servers_to_delete:
#         db.session.delete(s)

#     return nservers

# def create_workers(workers: list[WorkerSchema], nqueues: list[Queue]) -> list[Worker]:
#     db_workers = db.session.scalars(select(Worker)).all()
#     db_workers = {w.name: w for w in db_workers}
#     config_workers = {w.name: w for w in workers}
#     nworkers: list[Worker] = []
#     for name, sworker in config_workers.items():
#         model = sworker.model_dump()
#         # update
#         if name in db_workers.keys():
#             nworker = db_workers.get(name)
#             nworker.update(model)
#             nworker.queues = list(filter(lambda q: q.name in sworker.queues, nqueues))
#         # create
#         else:
#             nworker = Worker(name = sworker.name)
#             nworker.queues = list(filter(lambda q: q.name in sworker.queues, nqueues))
#         nworkers.append(nworker)
#     return nworkers


# def create_queues(queues: list[QueueSchema], gparams: GlobalParameters) -> list[Queue]:
#     db_queues = db.session.scalars(select(Queue)).all()
#     db_queues = {queue.name: queue for queue in  db_queues}
#     config_queues = {queue.name: queue for queue in queues}
#     nqueues: list[Queue] = []
#     for name, squeue in config_queues.items():
#         model = squeue.model_dump()
#         model["queue_timeout"] = model.get("queue_timeout") or gparams.queue_timeout
#         model["queue_limit"] = model.get("queue_limit") or gparams.queue_limit
#         model["queue_threshold"] = model.get("queue_threshold") or gparams.queue_threshold

#         # update
#         if name in db_queues.keys():
#             nqueue = db_queues.get(name)
#             nqueue.update(model)
#         #create
#         else:
#             nqueue = Queue(**model)
#         nqueues.append(nqueue)
#     # delete
#     queues_to_delete = [nqueue for nqueue in db_queues.values() if nqueue.name not in config_queues.keys()]
#     for q in queues_to_delete:
#         db.session.delete(q)
#     return nqueues


# def create_targets(targets: list[TargetSchema]) -> list[Target]:
#     db_targets = db.session.scalars(select(Target)).all()
#     db_targets = {target.name: target for target in db_targets}
#     config_targets = {target.name: target for target in targets}
#     ntargets: list[Target] = []
#     for name, starget in config_targets.items():
#         model = starget.model_dump()
#         if model.get("credentials"):
#             model["credentials"]["password"] = model["credentials"]["password"].get_secret_value()
#         # update
#         if name in db_targets.keys():
#             ntarget = db_targets.get(name)
#             if not ntarget.credentials and model.get("credentials"):
#                 ntarget.credentials = Credentials(**model.pop("credentials"))
#             ntarget.update(model)
#         # create
#         else:
#             if model.get("credentials"):
#                 ncred = Credentials(**model.pop("credentials"))
#                 model["credentials"] = ncred
#             model["parameters"] = TargetParameters(**model.pop("parameters"))
#             ntarget = Target(**model)
#         ntargets.append(ntarget)
#     # delete
#     targets_to_delete = [ntarget for ntarget in db_targets.values() if ntarget.name not in config_targets.keys()]
#     for t in targets_to_delete:
#         db.session.delete(t)
#     return ntargets


# def create_triggers(triggers: list[TriggerSchema], params: GlobalParameters) -> list[Trigger]:
#     db_triggers = db.session.scalars(select(Trigger)).all()
#     db_triggers = {trigger.name: trigger for trigger in db_triggers}
#     config_triggers = {trigger.name: trigger for trigger in triggers}
#     ntriggers: list[Trigger] = []
#     for name, strigger in config_triggers.items():
#         model = strigger.model_dump()
#         # update
#         if name in db_triggers.keys():
#             ntrigger = db_triggers.get(name)
#             ntrigger.update(model)
#         # create
#         else:
#             ntrigger = Trigger(**model)
#         ntriggers.append(ntrigger)
#     # delete
#     triggers_to_delete = [ntrigger for ntrigger in db_triggers.values() if ntrigger.name not in config_triggers.keys()]
#     for t in triggers_to_delete:
#         db.session.delete(t)
#     return ntriggers

# def create_policies(
#     policies: list[TransferPolicySchema],
#     ngparams: GlobalParameters,
#     nservers: list[NotificationServer],
#     nqueues: list[Queue],
#     ntargets: list[Target],
#     ntriggers: list[Trigger]
# ) -> list[TransferPolicy]:
#     npolicies: list[TransferPolicy] = []

#     db_policies = db.session.scalars(select(TransferPolicy)).unique().all()
#     db_policies = {p.name: p for p in db_policies}
#     config_policies = {p.name: p for p in policies}

#     for policy in policies:
#         name = policy.name
#         enabled = policy.enabled
#         tr_type = policy.type

#         # to create SourcePolicy and DestinationPolicy objects
#         # we need the target object and not only the name
#         src = policy.src.model_dump()
#         src["target"] = next(filter(lambda t: t.name == policy.src.target, ntargets))

#         dests = []
#         for dest in policy.dests:
#             dest_json = dest.model_dump()
#             try:
#                 dest_json["target"] = next(filter(lambda t: t.name == dest.target, ntargets))
#             except StopIteration:
#                 # no target, it is a notification request
#                 dest_json["target"] = None

#             # if some params are set to None, we take the default one in GlobalParameters
#             dparams = {k: v for k, v in dest_json.items() if k in ngparams.to_dict()}
#             for k, v in dparams.items():
#                 if v is None:
#                     dparams[k] = getattr(ngparams, k)
#             dest_json.update(dparams)
#             dests.append(dest_json)

#         queue = policy.queue
#         nqueue = next(filter(lambda q: q.name == queue, nqueues))

#         # if some params are set to None, we take the default one in GlobalParameter
#         if policy.parameters:
#             params = {k: v for k, v in policy.parameters.model_dump().items() if k in ngparams.to_dict()}
#             for k, v in params.items():
#                 if v is None:
#                     params[k] = getattr(ngparams, k)
#         else:
#             params = {k: v for k, v in ngparams.to_dict().items() if k in TransferPolicyParameters.__table__.columns}
#         nparams = TransferPolicyParameters(**params)

#         nsrc = SourcePolicy(**src)

#         for dest in dests:
#             if dest.get("notifications") is not None:
#                 nnotifications: list[ServerParameters] = []
#                 for notification in dest["notifications"]:
#                     notif = copy.deepcopy(notification)
#                     server_name = notif.pop("server")
#                     nserver = next(filter(lambda n: n.name == server_name, nservers))

#                     if nserver.type == "kafka":
#                         topics = cast(list, notif["topics"])
#                         for topic in topics:
#                             if isinstance(topic, dict):
#                                 nparameters = KafkaTopicParameters(server=nserver, **topic)
#                             else:
#                                 nparameters = KafkaTopicParameters(server=nserver, topic=topic)
#                             nnotifications.append(nparameters)
#                     else:
#                         raise NotImplementedError(f"only 'kafka' server is emplemented (not {nserver.type})")
#                 dest["notifications"] = nnotifications
#             else:
#                 dest["notifications"] = []
#         ndests = list(map(lambda dest: DestinationPolicy(**dest), dests))
#         npolicy = db_policies.get(name)
#         if npolicy:
#             p = {
#                 "type": tr_type,
#                 "enabled": enabled,
#                 "parameters": nparams.to_dict()
#             }
#             npolicy.update(p)
#         else:
#             npolicy = TransferPolicy(
#                 name=name, type=tr_type, enabled=enabled, queue=nqueue, parameters=nparams, src=nsrc, dests=ndests
#             )
#         if tr_type == Type.PERIODICAL:
#             if policy.trigger is not None:
#               npolicy.trigger = next(filter(lambda t: t.name == policy.trigger, ntriggers))
#         npolicies.append(npolicy)
#     # delete
#     policies_to_delete = [npolicy for npolicy in db_policies.values() if npolicy.name not in config_policies.keys()]
#     for p in policies_to_delete:
#         db.session.delete(p)
#     return npolicies


# def create_global_params(gparams: GlobalParametersSchema) -> GlobalParameters:
#     """
#     Create global params
#     """
#     db_params = db.session.execute(select(GlobalParameters)).scalar()
#     if db_params:
#         db.session.delete(db_params)
#     model = gparams.model_dump()
#     nparams = GlobalParameters(**model)
#     return nparams


# @transactional
# def configure(payload: ConfigurationSchema):
#     gparams = payload.global_parameters
#     ngparams = create_global_params(gparams)

#     servers = payload.notification_servers
#     nservers = create_servers(servers)

#     triggers = payload.triggers
#     ntriggers = create_triggers(triggers, ngparams)

#     queues = payload.queues
#     nqueues = create_queues(queues, ngparams)

#     workers = payload.workers
#     nworkers = create_workers(workers, nqueues)

#     targets = payload.targets
#     ntargets = create_targets(targets)

#     policies = payload.transfer_policies
#     npolicies = create_policies(policies, ngparams, nservers, nqueues, ntargets, ntriggers)
#     data = [ngparams] + nservers + nqueues + ntargets + npolicies + ntriggers + nworkers
#     db.session.add_all(data)

# @transactional
# def unconfigure(keep: list[str] | None = None) -> None:
#     tables = db.metadata.sorted_tables
#     for table in reversed(tables):
#         if keep is not None and table.name in keep:
#             continue
#         db.session.execute(table.delete())
