from copy import deepcopy

from dtr_common.types.configuration import ConfigurationJson, TransferPolicyConf
from dtr_common.types.models import QueueJson, TargetJson, NotificationServerJson
from typing import cast
from dtr_common.constantes import Type
from typing import Dict

from ..db import db
from ..models import (
    Credentials,
    DestinationPolicy,
    KafkaTopicParameters,
    NotificationServer,
    PeriodicalParameters,
    Queue,
    SourcePolicy,
    Target,
    TransferPolicyParameters,
    TransferPolicy,
    GlobalParameters,
    TargetParameters,
)


def create_servers(servers: list[NotificationServerJson]) -> list[NotificationServer]:
    nservers: list[NotificationServer] = []
    for server in servers:
        server_copy = deepcopy(server)
        credentials = server_copy.get("credentials", None)
        if credentials is not None:
            server_copy["credentials"] = Credentials(**credentials)
        nserver = NotificationServer(**server_copy)
        nservers.append(nserver)
    db.session.add_all(nservers)
    db.session.commit()
    return nservers


def create_queues(queues: list[QueueJson], global_params: Dict[str, int]) -> list[Queue]:
    nqueues: list[Queue] = []
    for queue in queues:
        if queue.get("queue_timeout", None) is None:
            queue["queue_timeout"] = global_params.get("queue_timeout")
        elif queue.get("queue_limit", None) is None:
            queue["queue_limit"] = global_params.get("queue_limit")
        elif queue.get("queue_threshold", None) is None:
            queue["queue_threshold"] = global_params.get("queue_threshold")
        else:
            pass
        nqueue = Queue(**queue)
        nqueues.append(nqueue)
    db.session.add_all(nqueues)
    db.session.commit()
    return nqueues


def create_targets(targets: list[TargetJson]) -> list[Target]:
    ntargets: list[Target] = []
    for target in targets:
        target_copy = deepcopy(target)
        credentials = target_copy.get("credentials", None)
        parameters = target_copy.get("parameters", None)
        if credentials is not None:
            target_copy["credentials"] = Credentials(**credentials)
        if parameters is not None:
            target_copy["parameters"] = TargetParameters(**parameters)
        else:
            target_copy["parameters"] = TargetParameters()
        ntarget = Target(**target_copy)
        ntargets.append(ntarget)
    db.session.add_all(ntargets)
    db.session.commit()
    return ntargets


def create_policies(
    policies: list[TransferPolicyConf], global_params: Dict[str, int]
) -> list[TransferPolicy]:
    # prerequisities
    nqueues = cast(list[Queue], db.session.query(Queue).all())  # type: ignore
    ntargets = cast(list[Target], db.session.query(Target).all())  # type: ignore
    nservers = cast(list[NotificationServer], db.session.query(NotificationServer).all())  # type: ignore

    npolicies: list[TransferPolicy] = []

    for policy in policies:
        policy_copy = deepcopy(policy)

        period_params = policy_copy.pop("periodical", None)
        notifications = policy_copy.pop("notifications", None)

        src_policy = policy_copy.pop("src")
        dest_policy = policy_copy.pop("dest")
        queue = policy_copy.pop("queue")

        tr_name = policy_copy.pop("name")
        tr_type = Type[policy_copy.pop("type").upper()]
        tr_enabled = policy_copy.pop("enabled", True)

        if period_params is None:
            period_params = {}
            period_params["polling_interval"] = global_params.get("polling_interval")

        if policy_copy.get("retry_delay", None) is None:
            policy_copy["retry_delay"] = global_params.get("retry_delay")
        if policy_copy.get("max_retry", None) is None:
            policy_copy["max_retry"] = global_params.get("max_retry")
        if policy_copy.get("transfer_requests_history", None) is None:
            policy_copy["transfer_requests_history"] = global_params.get("transfer_requests_history")
        if policy_copy.get("compress", None) is None:
            policy_copy["compress"] = global_params.get("compress")
        if policy_copy.get("only_new_data", None) is None:
            policy_copy["only_new_data"] = global_params.get("only_new_data")
        if policy_copy.get("transfer_timeout", None) is None:
            policy_copy["transfer_timeout"] = global_params.get("transfer_timeout")

        ntr_params = TransferPolicyParameters(**policy_copy)

        if period_params is not None and tr_type == Type.PERIODICAL:
            nperiod_params = PeriodicalParameters(**period_params)
            ntr_params.periodical = nperiod_params

        if dest_policy.get("tmp_prefix_dest", None) is None:
            dest_policy["tmp_prefix_dest"] = global_params.get("tmp_prefix_dest")
        elif dest_policy.get("final_prefix_dest", None) is None:
            dest_policy["final_prefix_dest"] = global_params.get("final_prefix_dest")
        else:
            pass

        ntr_queue = next(filter(lambda q: q.name == queue, nqueues))

        src_target = src_policy.pop("target")
        dest_target = dest_policy.pop("target")

        src_policy["target"] = next(filter(lambda t: t.name == src_target, ntargets))
        dest_policy["target"] = next(filter(lambda t: t.name == dest_target, ntargets))

        nsrc_policy = SourcePolicy(**src_policy)
        ndest_policy = DestinationPolicy(**dest_policy)

        npolicy = TransferPolicy(
            name=tr_name,
            type=tr_type,
            enabled=tr_enabled,
            queue=ntr_queue,
            parameters=ntr_params,
            src=nsrc_policy,
            dest=ndest_policy,
        )

        if notifications is not None:
            for notification in notifications:
                notification_copy = deepcopy(notification)
                server_name = notification_copy.pop("server")
                nserver = next(filter(lambda n: n.name == server_name, nservers))

                if nserver.type == "kafka":
                    topics = notification_copy.get("topics", None)
                    if topics is not None:
                        for topic in topics:
                            if isinstance(topic, dict):
                                nparameters = KafkaTopicParameters(**topic)
                            else:
                                nparameters = KafkaTopicParameters(topic=topic)
                            nparameters.server_id = nserver.id
                            npolicy.kafka.append(nparameters)
                else:
                    raise NotImplementedError(f"only 'kafka' server is emplemented (not {nserver.type})")

        npolicies.append(npolicy)

    db.session.add_all(npolicies)
    db.session.commit()

    return npolicies


def create_global_params(global_params: GlobalParameters) -> GlobalParameters:
    """
    Create global params
    """

    nparams = GlobalParameters(**global_params)
    db.session.add(nparams)
    db.session.commit()
    return nparams


def configure(payload: ConfigurationJson):
    global_params = payload.get("global_parameters", None)
    if global_params is not None:
        create_global_params(global_params)

    servers = payload.get("notification_servers", None)
    if servers is not None:
        create_servers(servers)

    queues = payload.get("queues", None)
    if queues is not None:
        create_queues(queues, global_params)

    targets = payload.get("targets", None)
    if targets is not None:
        create_targets(targets)

    policies = payload.get("transfer_policies", None)
    if policies is not None:
        create_policies(policies, global_params)


def unconfigure(keep: list[str] | None = None) -> None:
    tables = db.metadata.sorted_tables
    for table in reversed(tables):
        if keep is not None and table.name in keep:
            continue
        db.session.execute(table.delete())
    db.session.commit()
