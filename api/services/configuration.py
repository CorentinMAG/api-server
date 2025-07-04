from __future__ import annotations

import copy
from typing import cast

from dtr_common.constantes import Type
from dtr_common.schema import (
    ConfigurationSchema,
    GlobalParametersSchema,
    QueueSchema,
    ServerSchema,
    TargetSchema,
    TransferPolicySchema,
)

from api.db import db
from api.models import (
    Credentials,
    DestinationPolicy,
    GlobalParameters,
    KafkaTopicParameters,
    NotificationServer,
    PeriodicalParameters,
    Queue,
    ServerParameters,
    SourcePolicy,
    Target,
    TargetParameters,
    TransferPolicy,
    TransferPolicyParameters,
)

from .utils import transactional


def create_servers(servers: list[ServerSchema]) -> list[NotificationServer]:
    nservers: list[NotificationServer] = []
    for server in servers:
        model = server.model_dump()
        credentials = server.credentials
        if credentials is not None:
            cred = {"login": credentials.login, "password": credentials.password.get_secret_value()}
            ncred = Credentials(**cred)
            model["credentials"] = ncred
        nserver = NotificationServer(**model)
        nservers.append(nserver)
    return nservers


def create_queues(queues: list[QueueSchema], gparams: GlobalParameters) -> list[Queue]:
    nqueues: list[Queue] = []
    for queue in queues:
        queue.queue_timeout = (
            queue.queue_timeout if queue.queue_timeout is not None else gparams.queue_timeout
        )
        queue.queue_limit = queue.queue_limit if queue.queue_limit is not None else gparams.queue_limit
        queue.queue_threshold = (
            queue.queue_threshold if queue.queue_threshold is not None else gparams.queue_threshold
        )
        nqueue = Queue(**queue.model_dump())
        nqueues.append(nqueue)
    return nqueues


def create_targets(targets: list[TargetSchema]) -> list[Target]:
    ntargets: list[Target] = []
    for target in targets:
        model = target.model_dump()
        credentials = target.credentials
        parameters = target.parameters
        if credentials is not None:
            cred = {"login": credentials.login, "password": credentials.password.get_secret_value()}
            ncred = Credentials(**cred)
            model["credentials"] = ncred
        model["parameters"] = TargetParameters(**parameters.model_dump())
        ntarget = Target(**model)
        ntargets.append(ntarget)
    return ntargets


def create_policies(
    policies: list[TransferPolicySchema],
    ngparams: GlobalParameters,
    nservers: list[NotificationServer],
    nqueues: list[Queue],
    ntargets: list[Target],
) -> list[TransferPolicy]:
    npolicies: list[TransferPolicy] = []

    for policy in policies:
        name = policy.name
        enabled = policy.enabled
        tr_type = policy.type

        # to create SourcePolicy and DestinationPolicy objects
        # we need the target object and not only the name
        src = policy.src.model_dump()
        src["target"] = next(filter(lambda t: t.name == policy.src.target, ntargets))

        dests = []
        for dest in policy.dests:
            dest_json = dest.model_dump()
            dest_json["target"] = next(filter(lambda t: t.name == dest.target, ntargets))

            # if some params are set to None, we take the default one in GlobalParameters
            dparams = {k: v for k, v in dest_json.items() if k in ngparams.to_dict()}
            for k, v in dparams.items():
                if v is None:
                    dparams[k] = getattr(ngparams, k)
            dest_json.update(dparams)
            dests.append(dest_json)

        queue = policy.queue
        nqueue = next(filter(lambda q: q.name == queue, nqueues))

        # if some params are set to None, we take the default one in GlobalParameter
        if policy.parameters:
            params = {k: v for k, v in policy.parameters.model_dump().items() if k in ngparams.to_dict()}
            for k, v in params.items():
                if v is None:
                    params[k] = getattr(ngparams, k)
        else:
            params = {
                k: v
                for k, v in ngparams.to_dict().items()
                if k in TransferPolicyParameters.__mapper__.columns
            }
        nparams = TransferPolicyParameters(**params)

        if tr_type == Type.PERIODICAL:
            if policy.parameters is None or policy.parameters.periodical is None:
                pparams = {"polling_interval": ngparams.polling_interval}
            else:
                pparams = policy.parameters.periodical.model_dump()
            npparams = PeriodicalParameters(**pparams)
            nparams.periodical = npparams

        nsrc = SourcePolicy(**src)

        for dest in dests:
            if dest.get("notifications") is not None:
                nnotifications: list[ServerParameters] = []
                for notification in dest["notifications"]:
                    notif = copy.deepcopy(notification)
                    server_name = notif.pop("server")
                    nserver = next(filter(lambda n: n.name == server_name, nservers))

                    if nserver.type == "kafka":
                        topics = cast(list, notif["topics"])
                        for topic in topics:
                            if isinstance(topic, dict):
                                nparameters = KafkaTopicParameters(server=nserver, **topic)
                            else:
                                nparameters = KafkaTopicParameters(server=nserver, topic=topic)
                            nnotifications.append(nparameters)
                    else:
                        raise NotImplementedError(f"only 'kafka' server is emplemented (not {nserver.type})")
                dest["notifications"] = nnotifications
            else:
                dest["notifications"] = []
        ndests = list(map(lambda dest: DestinationPolicy(**dest), dests))

        npolicy = TransferPolicy(
            name=name, type=tr_type, enabled=enabled, queue=nqueue, parameters=nparams, src=nsrc, dests=ndests
        )

        npolicies.append(npolicy)

    return npolicies


def create_global_params(gparams: GlobalParametersSchema) -> GlobalParameters:
    """
    Create global params
    """
    model = gparams.model_dump()
    nparams = GlobalParameters(**model)
    return nparams


@transactional
def configure(payload: ConfigurationSchema):
    gparams = payload.global_parameters
    ngparams = create_global_params(gparams)

    servers = payload.notification_servers
    nservers = create_servers(servers)

    queues = payload.queues
    nqueues = create_queues(queues, ngparams)

    targets = payload.targets
    ntargets = create_targets(targets)

    policies = payload.transfer_policies
    npolicies = create_policies(policies, ngparams, nservers, nqueues, ntargets)

    data = [ngparams] + nservers + nqueues + ntargets + npolicies
    db.session.add_all(data)


@transactional
def unconfigure(keep: list[str] | None = None) -> None:
    tables = db.metadata.sorted_tables
    for table in reversed(tables):
        if keep is not None and table.name in keep:
            continue
        db.session.execute(table.delete())
