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
    tr_repository,
    src_repository,
    dest_repository
)
from ..utils.jsontypes import ConfigurationJson


def configure(payload: ConfigurationJson):

    notification_servers = payload.get("notification_servers", None)
    if notification_servers is not None:
        for server in notification_servers:
            server_copy = deepcopy(server)
            credentials = server_copy.pop("credentials", None)
            nserver = NotificationServer(**server_copy)
            if credentials is not None:
                ncredentials = Credentials(**credentials)
                nserver.credentials = ncredentials
            server_repository.add(nserver)

    queues = payload.get("queues", None)
    if queues is not None:
        for queue in queues:
            nqueue = Queue(**queue)
            queue_repository.add(nqueue)

    targets = payload.get("targets", None)
    if targets is not None:
        for target in targets:
            target_copy = deepcopy(target)
            credentials = target_copy.pop("credentials", None)
            ntarget = Target(**target_copy)
            if credentials is not None:
                ncredentials = Credentials(**credentials)
                ntarget.credentials = ncredentials
            target_repository.add(ntarget)

    transfer_policies = payload.get("transfer_policies", None)
    if transfer_policies is not None:
        for tr_policy in transfer_policies:
            tr_policy_copy = deepcopy(tr_policy)

            notifications = tr_policy_copy.pop("notifications", None)
            if notifications is not None:
                for notification in notifications:
                    notification_copy = deepcopy(notification)
                    server_name = notification_copy.pop("server")
                    nserver = server_repository.get_by_name(server_name)
                    topics = notification_copy.get("topics", None)
                    if topics is not None:
                        for topic in topics:
                            if isinstance(topic, dict):
                                nparameters = KafkaParameters(**topic)
                            else:
                                nparameters = KafkaParameters(topic = topic)
                    nserver.parameters.append(nparameters)
                    server_repository.update(nserver)

            periodical_parameters = tr_policy_copy.pop("periodical", None)
            if periodical_parameters is not None:
                nperiod = PeriodicalParameters(**periodical_parameters)

            src_policy = tr_policy_copy.pop("src")
            src_target = src_policy.pop("target")

            dest_policy = tr_policy_copy.pop("dest")
            dest_target = dest_policy.pop("target")

            nsrc_policy = SourcePolicy(**src_policy)
            ndest_policy = DestinationPolicy(**dest_policy)

            nsrc_policy.src = target_repository.get_by_name(src_target)
            ndest_policy.dest = target_repository.get_by_name(dest_target)

            src_repository.add(nsrc_policy)
            dest_repository.add(ndest_policy)

            ntr_parameters = TransferParameters(**tr_policy_copy)
            ntr_policy = TransferPolicy(
                src = nsrc_policy,
                dest = ndest_policy,
                parameters = ntr_parameters
            )
