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
from ..repositories import (
    queue_repository, 
    server_repository,
    target_repository,
    tr_repository
)
from ..utils.jsontypes import ConfigurationJson

def configure(payload: ConfigurationJson):

    nservers: list[NotificationServer] = []

    servers = payload.get("notification_servers", None)
    if servers is not None:
        for server in servers:
            server_copy = deepcopy(server)
            credentials = server_copy.get("credentials", None)
            if credentials is not None:
                server_copy["credentials"] = Credentials(**credentials)
            nserver = server_repository.add(NotificationServer(**server_copy))
            nservers.append(nserver)

    nqueues: list[Queue] = []

    queues = payload.get("queues", None)
    if queues is not None:
        for queue in queues:
            nqueue = queue_repository.add(Queue(**queue))
            nqueues.append(nqueue)

    ntargets: list[Target] = []

    targets = payload.get("targets", None)
    if targets is not None:
        for target in targets:
            target_copy = deepcopy(target)
            credentials = target_copy.get("credentials", None)
            if credentials is not None:
                target_copy["credentials"] = Credentials(**credentials)
            ntarget = target_repository.add(Target(**target_copy))
            ntargets.append(ntarget)

    transfer_policies = payload.get("transfer_policies", None)
    if transfer_policies is not None:
        for tr_policy in transfer_policies:
            tr_policy_copy = deepcopy(tr_policy)

            periodical_parameters = tr_policy_copy.pop("periodical", None)
            notifications = tr_policy_copy.pop("notifications", None)

            src_policy = tr_policy_copy.pop("src")
            dest_policy = tr_policy_copy.pop("dest")
            queues = tr_policy_copy.pop("queues")

            tr_name = tr_policy_copy.pop("name")
            tr_type = tr_policy_copy.pop("type")
            tr_enabled = tr_policy_copy.pop("enabled", True)

            ntr_params = TransferParameters(**tr_policy_copy)

            if periodical_parameters is not None and tr_type == "periodical":
                nperiod_params = PeriodicalParameters(**periodical_parameters)
                ntr_params.periodical = nperiod_params

            ntr_queues = [q for q in nqueues if q.name in queues]

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
                queues = ntr_queues, 
                parameters = ntr_params,
                src = nsrc_policy,
                dest = ndest_policy
            )

            ntr_policy = tr_repository.add(ntr_policy)

            if notifications is not None:
                for notification in notifications:
                    notification_copy = deepcopy(notification)
                    server_name = notification_copy.pop("server")
                    nserver = next(filter(lambda n: n.name == server_name, nservers))
                    ntr_policy.servers.append(nserver)
                    tr_repository.update(ntr_policy)
                    if nserver.type == "kafka":
                        topics = notification_copy.get("topics", None)
                        if topics is not None:
                            for topic in topics:
                                if isinstance(topic, dict):
                                    nparameters = KafkaParameters(policy_id = ntr_policy.id, **topic)
                                else:
                                    nparameters = KafkaParameters(policy_id = ntr_policy.id, topic = topic)
                        nserver.parameters.append(nparameters)
                        server_repository.update(nserver)
                    else:
                        raise NotImplementedError(f"only 'kafka' server is emplemented (not {nserver.type})")
