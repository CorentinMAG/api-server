from . import database
from ..models import NotificationServer, Queue, DataType, Target, TransferPolicy, GlobalParameters

def configure(payload: dict):
    database.flush()

    global_params = payload.get("parameters", None)
    nparams = GlobalParameters(**global_params)
    nparams.upsert()

    queues = payload.get("queues", None)
    for queue in queues:
        nqueue = Queue(**queue)
        nqueue.upsert()

    notification_servers = payload.get("notificationServers", None)
    for server in notification_servers:
        nserver = NotificationServer(**server)
        nserver.upsert()

    data_types = payload.get("dataTypes", None)
    for dtype in data_types:
        ndtype = DataType(**dtype)
        ndtype.upsert()

    targets = payload.get("targets", None)
    for target in targets:
        ntarget = Target(**target)
        ntarget.upsert()

    transfer_policies = payload.get("transferPolicies", None)
    for tr_policy in transfer_policies:
        ntr_policy = TransferPolicy(**tr_policy)
        ntr_policy.upsert()