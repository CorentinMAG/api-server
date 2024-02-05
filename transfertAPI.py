from flask import Flask, request, jsonify
import json
import uuid
from business_rules import *
from log import JsonFormatter
from datetime import datetime
import logging

DTR_OFFLINE = False

app = Flask(__name__)

logger = logging.getLogger("api")
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
formatter = JsonFormatter("DTR", "api", "1.1.0")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

@app.route('/dtr/transfer-request', methods=['POST'])
def TransferCmd():
    LOG.print_log("DEBUG","TransferCmd start")
    record = json.loads(request.data)
    tp_name = record['transfer-policy']
    file = record['path']
    if 'uid' in record:
        uid =  record['uid']
    else:
         uid = uuid.uuid4()

    timestamp = record['timestamp']
    queue = Queue()
    trsf_id = queue.QueueRequestCmd(tp_name,file, uid,timestamp)
    if trsf_id > 0:
        LOG.print_log(f"INFO","TransferCmd {trsf_id} ")
    res = dict()
    res["transfer_id"] = trsf_id
    return res


@app.route('/api/SetOffLine', methods=['PUT'])
def SetOffLine():
    global DTR_OFFLINE
    payload = json.loads(request.data)
    DTR_OFFLINE = payload["OffLine"]

    logger.info("set DTR in offline mode")

    return ""


@app.route('/api/GetOffLine', methods=['GET'])
def GetOffLine():
    global DTR_OFFLINE
    res = dict()
    res["OffLine"] =  DTR_OFFLINE 
    return res


@app.route('/api/Target', methods=['GET'])
def GetTarget():
    ln = request.args.get('logicalname')
    if ln:
        tg  = Target()
        tg.DbLoadByName(ln)

        logger.info("get target %s", ln)
        return tg.Jsonify()
    else:    
        tg  = Target()
        ids = tg.DbGetIds()
        tgs = list()
        for id in ids:
            tg  = Target()
            tg.DbLoad(id)
            tgs.append(tg.Jsonify())
        return tgs

@app.route('/api/GetNextTransferPolicy', methods=['GET'])
def GetNextTransferPolicy():

    global DTR_OFFLINE

    res = dict()
    tp  = TransferPolicy()
    tps = list()
    id = tp.GetNextTransferPolicy()
    if id and not DTR_OFFLINE:
        tp.DbLoad(id)
        tps.append(tp.Jsonify())
        res["TransferPolicies"]=tps

        sf = ScannedFile()
        transferPolicyName = tp.GetAttrib("LogicalName").value
        res["ScannedFiles"] = sf.GetScannedFiles(transferPolicyName)
        logger.info("GetNextTransferPolicy")
        return res
    else :
        res["TransferPolicies"]=dict()
        return res

@app.route('/configuration/notification', methods=['GET'])
def GetNotificationConfiguration():
    res = dict()
    ns = NotificationServer()
    ids = ns.DbGetIds()
    nss = list()
    for id in ids:
        ns  = NotificationServer()
        ns.DbLoad(id)
        nss.append(ns.Jsonify())
    res["notification_servers"] = nss
    gp  = GlobalParameters()
    res["polling_interval"] =  gp.DBGet("NotificationPollingInterval")
    logger.info("get notification servers configuration")
    return res


 
@app.route('/notification', methods=['GET'])
def GetTransferToNotify():
    res = dict()
    q = Queue()
    id = q.GetQueueNextNotify()
    if id:
        tr = TransferRequest()
        tr.DbLoad(id)
        res["transfer-policy"] = tr.GetAttrib("TransferPolicyID").value
        res["filename"] = tr.GetAttrib("Filename").value
        res["transfer_id"] = tr.GetAttrib("TransferrequestID").value
        res["status"] = "Completed"
        res["reason"] = tr.GetAttrib("RequestState").value
        res["timestamp"] = tr.GetAttrib("Updated").value

        if tr.transferPolicy.Notifications:
            topics = list()
            for n in tr.transferPolicy.Notifications:
                topics.append(n.GetAttrib("topic").value)

            res["topics"] = topics
            res["notifier"] = tr.transferPolicy.Notifications[0].topic.NotificationServer

            logger.info("notifier get a notification")
        else:
            logger.info(f"transfer request: {tr.id} associated to transfer policy: {tr.transferPolicy.logicalname} has no notifications")
            return {}
    return res


 
@app.route('/notification', methods=['POST'])
def UpdateTransferNotifyStatus():
    payload = json.loads(request.data)
    id = payload["transfer_id"]
    status = payload["status"]
    req = TransferRequest()
    req.DbLoad(id)
    if status == "FAILED" :
        status = "Failed"
    elif status == "SENT":
        status = "Completed"
    logger.info("the transfer request %d notify with status: %s", id, status)
    req.UpdateState(id,status)
    return {}


@app.route('/api/TransferRequest', methods=['GET'])
def GetTransferRequests():
    res = dict()
    trs = list()
    tr  = TransferRequest()
    if request.args.get('transferrequestid'):
        id = request.args.get('transferrequestid')

        if  tr.DbPartialLoad(id):
            trs.append(tr.Dump())

    else:
        ids = tr.DbGetIds()
        for id in ids:
            tr  = TransferRequest()
            tr.DbPartialLoad(id)
            trs.append(tr.Dump())
    
    res["TransferRequests"]=trs

    logger.ingo("GetTransferRequests")
    return res


@app.route('/api/QueueRequests', methods=['POST'])
def QueueTransfers():
    record = json.loads(request.data)
    tp_name = record['TransferPolicyName']
    files = record['Files']
    uid = record['uid']
    queue = Queue()
    dt = datetime.now()
    queue.QueueTransfersRequest(tp_name,files,uid,dt)

    return jsonify("Recorded")


@app.route('/api/GetQueueNextRequest', methods=['GET'])
def GetQueueNextRequest():  
    logger.info("get next transfer request")

    global DTR_OFFLINE

    res = dict()
    q = Queue()
    id = q.GetQueueNextRequest()
    if id and not DTR_OFFLINE:
        tr = TransferRequest()
        tr.DbLoad(id)
        tr.HouseKeeping()
        res["TransferRequest"] = tr.Jsonify()
        logger.info("next transfer id: %d", id)    
    else:
        res["TransferRequest"] = dict()

    return res

@app.route('/api/RequestUpdate', methods=['POST'])
def RequestUpdate():  


    payload = json.loads(request.data)
    id = payload["transferrequestid"]
    state = payload["requeststate"]
    failed_step= payload["failedstep"]
    # Check if notification is reqired 
    req = TransferRequest()
    req.DbLoad(id)

    if state == "Completed" and req.transferPolicy.Notifications is not None:
        state = "Notify"
    req.UpdateState(id,state,failed_step)

    logger.info(f"RequestUpdate {id} {state} {failed_step}")
    return "Ok"

@app.route('/api', methods=['GET'])
def GetConfig():
    res = dict()

    gp  = GlobalParameters()
    gp.DbLoad()
    res["Parameters"] = gp.Jsonify()

    q  = Queue()
    ids = q.DbGetIds()
    qs = list()
    for id in ids:
        q  = Queue()
        q.DbLoad(id)
        qs.append(q.Jsonify())
    res["Queues"]=qs

    ns  = NotificationServer()
    ids = ns.DbGetIds()
    nss = list()
    for id in ids:
        ns  = NotificationServer()
        ns.DbLoad(id)
        nss.append(ns.Jsonify())
    res["NotificationServers"] = nss

    tg  = Target()
    ids = tg.DbGetIds()
    tgs = list()
    for id in ids:
        tg  = Target()
        tg.DbLoad(id)
        tgs.append(tg.Jsonify())
    res["Targets"]=tgs

    dt  = DataType()
    ids = dt.DbGetIds()
    dts = list()
    for id in ids:
        dt  = DataType()
        dt.DbLoad(id)
        dts.append(dt.Jsonify())
    res["DataTypes"]=dts

    tp  = TransferPolicy()
    ids = tp.DbGetIds()
    tps = list()
    for id in ids:
        tp  = TransferPolicy()
        tp.DbLoad(id)
        tps.append(tp.Jsonify())
    res["TransferPolicies"]=tps

    return res

@app.route('/api', methods=['PUT'])
def CreateCfg():
    logger.info("set DTR configuration")
    payload = json.loads(request.data)

    DeleteRecords()

    global_params = payload["Parameters"]
    gp  = GlobalParameters()
    gp.Set(global_params)
    gp.DBUpdateAll()

    queues = payload["Queues"]
    for it in queues:
        q  = Queue()
        q.Set(it)
        q.DbCreate()
        db.Commit()

    notification_servers = payload["NotificationServers"]
    for it in notification_servers:
        ns  = NotificationServer()
        ns.Set(it)
        ns.DbCreate()
        db.Commit()

    dataTypes = payload["DataTypes"]
    for it in dataTypes:
        dt  = DataType()
        dt.Set(it)
        dt.DbCreate()
        db.Commit()

    targets = payload["Targets"]
    for it in targets:
        tg  = Target()
        tg.Set(it)
        tg.DbCreate()
        db.Commit()
        
    transferPolicies = payload["TransferPolicies"]
    for it in transferPolicies:
        tp  = TransferPolicy()
        tp.Set(it)
        tp.DbCreate()
        db.Commit()

    return request.data


@app.route('/api', methods=['DELETE'])
def DeleteRecords():
    logger.info("delete all records")
    tr = TransferRequest()
    #tr.BreakWithConf()
    tr.DbDeleteAll()

    p = Periodical()
    p.DbDeleteAll()

    tp = TransferPolicy()
    tp.DbDeleteAll()

    dt = DataType()
    dt.DbDeleteAll()

    sp = SourcePolicy()
    sp.DbDeleteAll()

    dp = DestinationPolicy()
    dp.DbDeleteAll()

    dp = DataPolicy()
    dp.DbDeleteAll()


    tg = Target()
    tg.DbDeleteAll()
    
    c = Credential()
    c.DbDeleteAll()

    l = Login()
    l.DbDeleteAll()

    s = Secret()
    s.DbDeleteAll()

    t = Token()
    t.DbDeleteAll()

    q = Queue()
    q.DbDeleteAll()

    ns =NotificationServer()
    ns.DbDeleteAll()

    return ""

@app.route('/api/DbAgeDays', methods=['PUT'])
def PutDbAgeDays():
    res = dict()

    if request.args.get('days'):
        days = int(request.args.get('days'))
        es  = ExecutionSlot()
        es.DbAgeDays(days)

        ess = list()
        es  = ExecutionSlot()

        ids = es.DbGetIds()
        for id in ids:
            es  = ExecutionSlot()
            es.DbLoad(id)
            ess.append(es.Jsonify())
        res["ExecutionSlots"] = ess
        return res

@app.route('/api/ExecutionSlot', methods=['Get'])
def GetExecutionSlot():
    res = dict()
    ess = list()
    es  = ExecutionSlot()
    if request.args.get('id'):
        id = request.args.get('id')
        es.DbLoad(id)
        ess.append(es.Jsonify())
    else:
        ids = es.DbGetIds()
        for id in ids:
            es  = ExecutionSlot()
            es.DbLoad(id)
            ess.append(es.Jsonify())

        
    res["ExecutionSlots"] = ess

    return res
