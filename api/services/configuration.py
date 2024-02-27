from ..models import (
    NotificationServer, 
    Queue, 
    Target, 
    TransferPolicy, 
    Credentials,
    SourcePolicy,
    DestinationPolicy,
    KafkaParameters,
    PeriodicalParameters,
    TransferParameters
)
from copy import deepcopy
from common.jsontypes import ConfigurationJson, NotificationServerJson, QueueJson, TargetJson, TransferPolicyJson
from ..db import db

def create_servers(servers: list[NotificationServerJson]) -> list[NotificationServer]:
    nservers = []
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

def create_queues(queues: list[QueueJson]) -> list[Queue]:
    nqueues = []
    for queue in queues:
        nqueue = Queue(**queue)
        nqueues.append(nqueue)
    db.session.add_all(nqueues)
    db.session.commit()
    return nqueues

def create_targets(targets: list[TargetJson]) -> list[Target]:
    ntargets = []
    for target in targets:
        target_copy = deepcopy(target)
        credentials = target_copy.get("credentials", None)
        if credentials is not None:
            target_copy["credentials"] = Credentials(**credentials)
        ntarget = Target(**target_copy)
        ntargets.append(ntarget)
    db.session.add_all(ntargets)
    db.session.commit()
    return ntargets

def create_policies(policies: list[TransferPolicyJson]) -> list[TransferPolicy]:

    # prerequisities
    nqueues = db.session.query(Queue).all()
    ntargets = db.session.query(Target).all()
    nservers = db.session.query(NotificationServer).all()

    for policy in policies:
        policy_copy = deepcopy(policy)

        period_params = policy_copy.pop("periodical", None)
        notifications = policy_copy.pop("kafka", None)

        src_policy = policy_copy.pop("src")
        dest_policy = policy_copy.pop("dest")
        queue = policy_copy.pop("queue")

        tr_name = policy_copy.pop("name")
        tr_type = policy_copy.pop("type")
        tr_enabled = policy_copy.pop("enabled", True)

        ntr_params = TransferParameters(**policy_copy)

        if period_params is not None and tr_type == "periodical":
            nperiod_params = PeriodicalParameters(**period_params)
            ntr_params.periodical = nperiod_params

        ntr_queue = next(filter(lambda q: q.name == queue, nqueues))

        src_target = src_policy.pop("target")
        dest_target = dest_policy.pop("target")

        src_policy["target"] = next(filter(lambda t: t.name == src_target, ntargets))
        dest_policy["target"] = next(filter(lambda t: t.name == dest_target, ntargets))

        nsrc_policy = SourcePolicy(**src_policy)
        ndest_policy = DestinationPolicy(**dest_policy)

        ntr_policy = TransferPolicy(
            name = tr_name,
            type = tr_type,
            enabled = tr_enabled,
            queue = ntr_queue, 
            parameters = ntr_params,
            src = nsrc_policy,
            dest = ndest_policy
        )

        db.session.add(ntr_policy)

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
                                nparameters = KafkaParameters(policy_id = ntr_policy.id, **topic)
                            else:
                                nparameters = KafkaParameters(policy_id = ntr_policy.id, topic = topic)
                            nparameters.server_id = nserver.id
                            ntr_policy.kafka.append(nparameters)
                else:
                    raise NotImplementedError(f"only 'kafka' server is emplemented (not {nserver.type})")
                db.session.commit()


def configure(payload: ConfigurationJson):

    servers = payload.get("notification_servers", None)
    if servers is not None:
        create_servers(servers)

    queues = payload.get("queues", None)
    if queues is not None:
        create_queues(queues)

    targets = payload.get("targets", None)
    if targets is not None:
        create_targets(targets)

    policies = payload.get("transfer_policies", None)
    if policies is not None:
        create_policies(policies)

def unconfigure(keep: list[str] | None = None) -> None:
    tables = db.metadata.sorted_tables
    for table in reversed(tables):
        if keep is not None and table.name in keep:
            continue
        db.session.execute(table.delete())
    db.session.commit()