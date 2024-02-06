from . import database
from ..models.notification_servers import NotificationServer

def configure(payload: dict):
    database.flush()

    global_params = payload.get("parameters", None)

    queues = payload.get("queues", None)

    notification_servers = payload.get("notificationServers", None)
    for server in notification_servers:
        nserver = NotificationServer(server)
        nserver.commit()

    data_types = payload.get("dataTypes", None)

    targets = payload.get("targets", None)

    transfer_policies = payload.get("transferPolicies", None)

    # global_params = payload["Parameters"]
    # gp  = GlobalParameters()
    # gp.Set(global_params)
    # gp.DBUpdateAll()

    # queues = payload["Queues"]
    # for it in queues:
    #     q  = Queue()
    #     q.Set(it)
    #     q.DbCreate()
    #     db.Commit()

    # notification_servers = payload["NotificationServers"]
    # for it in notification_servers:
    #     ns  = NotificationServer()
    #     ns.Set(it)
    #     ns.DbCreate()
    #     db.Commit()

    # dataTypes = payload["DataTypes"]
    # for it in dataTypes:
    #     dt  = DataType()
    #     dt.Set(it)
    #     dt.DbCreate()
    #     db.Commit()

    # targets = payload["Targets"]
    # for it in targets:
    #     tg  = Target()
    #     tg.Set(it)
    #     tg.DbCreate()
    #     db.Commit()

    # transferPolicies = payload["TransferPolicies"]
    # for it in transferPolicies:
    #     tp  = TransferPolicy()
    #     tp.Set(it)
    #     tp.DbCreate()
    #     db.Commit()