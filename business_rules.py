import datetime
from enums import *

from dbms import *



class GlobalParameters(Entity):
    def __init__(self):
        dic = {}
        super().__init__("GlobalParameter", dic)

    def Set(self, values ):
        for k, val in values.items():
            super().SetAttrib(k,val)

    def DbLoad(self):
        s = "select ParameterName,ParameterValue from GlobalParameter;" 
        arg = list()
        cur = db.Exec(s,arg)
        records = cur.fetchall()

        row = records[0]
        for row in records:
            a = self.GetAttrib(row[0])
            a.value = row[1]


    def DBGet(self,parameterName):
        s = "select ParameterValue from GlobalParameter where ParameterName =%s ;" 
        arg = list()
        arg.append(parameterName)
        cur = db.Exec(s,arg)
        records = cur.fetchall()
        return records[0][0]


    def DBUpdate(self,parameterName,value):
        s = "update GlobalParameter set ParameterValue = %s  where ParameterName =%s ;" 
        arg = list()
        arg.append(value)
        arg.append(parameterName)
        db.Exec(s,arg)
        db.Commit()


    def DBUpdateAll(self):
        for k in self.attributes:
            a = self.attributes[k]
            self.DBUpdate(a.name,a.value)

class ScannedFile(Entity):

    def __init__(self):
        self.logicalname = ""
        dic = {}
        super().__init__("Scanned_file", dic)
    
    def DbCreate(self,transferRequestId,transferPolicyName,FileName):

        super().SetAttrib("Filename",FileName)
        super().SetAttrib("Trsfpolicyname",transferPolicyName)
        super().SetAttrib("PeriodicalID",transferRequestId)
        id = super().DbCreate()

        return id

    def GetScannedFiles(self,transferPolicyName):
        s = "select Filename from Scanned_file where Trsfpolicyname = %s ;"
        arg = list()
        arg.append(transferPolicyName)
        cur = db.Exec(s,arg)
        records = cur.fetchall()   
        res = list()
        for r in records:
            res.append(r[0])

        return res
           

class Topic(Entity):
    def __init__(self):
        self.logicalname = ""
        dic = {}
        super().__init__("Topic", dic)
        super().UnSetDB("notificationserver")

    def Set(self, values ):
        for k, val in values.items():
            if k == "Topic":
                super().SetAttrib(k,val)
            elif k == "NotificationServer" :
                self.NotificationServer = val
                super().SetAttrib(k,val)

 
                
    def Jsonify(self):
        res = super().Jsonify()
        return res

    def GetDbId(self, topic ):
        s = "select TopicID from Topic  where Topic = %s  ;"
        arg = list()
        arg.append(topic)
        cur = db.Exec(s,arg)
        records = cur.fetchall()
        if records:
            return records[0][0]  
        else:
            return None

    def GetCreateDbId(self, topic ):
        id = self.GetDbId(topic)
        if id :  # record exists
            return id
        else :   # create Topic
            ns = NotificationServer()
            ns_id = ns.GetDbId(self.NotificationServer)
            super().SetAttrib("NotificationServerid",ns_id)

            return super().DbCreate()

    def DbLoad(self, id):
        self.id = id
        super().DbLoad(id)
        s = "select  name from NotificationServer  where NotificationServerID = %s ;"
        arg = list()
        ns_id = super().GetAttrib("NotificationServerid").value
        arg.append(ns_id)
        cur = db.Exec(s,arg)
        records = cur.fetchall()
        self.NotificationServer =  records[0][0]
        super().SetAttrib("NotificationServer",self.NotificationServer)


class Notification(Entity):
    def __init__(self):
        self.logicalname = ""
        dic = {}
        self.topic = Topic()
        super().__init__("Notification", dic)
        super().UnSetDB("notificationserver")
        super().UnSetDB("topic")
        super().SetAttrib("TdsOn",True)

    def Set(self, values ):
        topic_vals ={}
        for k, val in values.items():
            if k == "TdsOn" :
                super().SetAttrib(k,val)
            elif k == "Topic" :
                topic_vals[k] = val 
                self.topic_val = val
            else:
                topic_vals[k] = val 
                
        self.topic.Set(topic_vals)

    def DbCreate(self):
        topic_id = self.topic.GetCreateDbId(self.topic_val)
        super().SetAttrib("topicid",topic_id)
        return super().DbCreate()
                
    def Jsonify(self):
        res = super().Jsonify()
        return res

    def DbGetTransferPolicyNotifications(self,tp_id):        
        s = "select NotificationID from Notification where transferpolicyid = %s ; "
        arg = list()
        arg.append(tp_id)
        cur = db.Exec(s,arg)
        records = cur.fetchall()
        res = list()
        for r in records:
            res.append(r[0])
        return res

    def DbLoad(self, id):
        self.id = id
        super().DbLoad(id)
        topic_id = super().GetAttrib("topicid").value
        self.topic.DbLoad(topic_id)
        super().SetAttrib("topic",  self.topic.GetAttrib("topic").value)


class NotificationServer(Entity):
    def __init__(self):
        self.logicalname = ""
        dic = {}
        super().__init__("NotificationServer", dic)

    def Set(self, values ):
        for k, val in values.items():
            super().SetAttrib(k,val)

    def DbCreate(self):
        return super().DbCreate(True)
                
    def Jsonify(self):
        res = super().Jsonify()
        return res

    def GetDbId(self, name ):
        s = "select NotificationServerID from NotificationServer  where name = %s ;"
        arg = list()
        arg.append(name)
        cur = db.Exec(s,arg)
        records = cur.fetchall()
        return records[0][0]        
  
class Queue(Entity):
    def __init__(self):
        self.logicalname = ""
        dic = {}
        super().__init__("Queue", dic)

    def Set(self, values ):
        for k, val in values.items():
            super().SetAttrib(k,val)
            if k == "Id":
                super().SetAttrib("queueid",val)

    def QueueRequestCmd(self,tp_name,file, uid,timestamp):
        tp = TransferPolicy()
        tp.DbLoadByName(tp_name)
        self.id = tp.GetAttrib('QueueID').value
        super().DbLoad(self.id)
        queuedNb = self.DbQueuedNb()
        maxQueue = super().GetAttrib('MaxQueuedItems').value
        queueThreshold = super().GetAttrib('QueueThreshold').value
        if  queuedNb < maxQueue:
            tr = TransferRequest()
            i = tr.DbCreate(self.id,tp.GetId(),file,uid,timestamp,True)
            if i > 0:
                queuedNb = queuedNb + 1
                es = ExecutionSlot()
                es.DbCreate(i)
        else:
            i = -1
        return i


    def QueueTransfersRequest(self,transferPolicyName,f,uid,timestamp):
        tp = TransferPolicy()
        tp.DbLoadByName(transferPolicyName)
        self.id = tp.GetAttrib('QueueID').value
        super().DbLoad(self.id)
        queuedNb = self.DbQueuedNb()
        maxQueue = super().GetAttrib('MaxQueuedItems').value
        queueThreshold = super().GetAttrib('QueueThreshold').value

        if  queuedNb < maxQueue:
            tr = TransferRequest()
            i = tr.DbCreate(self.id,tp.GetId(),f,uid,timestamp,False)
            if i > 0:
                es = ExecutionSlot()
                es.DbCreate(i)
                queuedNb = queuedNb + 1
                sf = ScannedFile()
                sf.DbCreate(i,transferPolicyName,f)

        tp.periodical.DbUpdateTimeStamp(tp.GetId())
        queueLastTransferPolicyID = tp.id
    
    def GetQueueNextRequest(self):
        s = "select TransferRequestID from TransferRequest inner join Queue on (Queue.QueueID = TransferRequest.QueueID) where TransferRequest.RequestState = 'Queued' order by priorityorder,TransferRequestID LIMIT 1 ;"
        arg = list()
        cur = db.Exec(s,arg)
        records = cur.fetchall()   
        if records: 

            id = records[0][0]     
            s = "update TransferRequest set requeststate = 'In Progress' where  TransferRequestID = %s ;"
            arg.append(id)
            db.Exec(s,arg)
            es = ExecutionSlot()
            es.GetRequestLastSlot(id)
            es.Start()
            db.Commit()
        else:
            id = 0
        return id
       
    def GetQueueNextNotify(self):
        s = "select TransferRequestID from TransferRequest inner join Queue on (Queue.QueueID = TransferRequest.QueueID) where  TransferRequest.RequestState = 'Notify' order by priorityorder,TransferRequestID LIMIT 1 ;"
        arg = list()
        cur = db.Exec(s,arg)
        records = cur.fetchall()   
        if records: 
            id = records[0][0]     
            s = "update TransferRequest set requeststate = 'In Progress' where  TransferRequestID = %s ;"
            arg.append(id)
            db.Exec(s,arg)
            db.Commit()
        else:
            id = 0
        return id       
    def DbCreate(self):
        return super().DbCreate(True)


    def DbQueuedNb(self):
        s = "select count(*) from TransferRequest where RequestState not in ('Failed','Completed','Cancelled') and QueueID = %s ;"
        arg = list()
        arg.append(self.id)
        cur = db.Exec(s,arg)
        records = cur.fetchall()
        return records[0][0]
                

          
class DataType(Entity):
    def __init__(self):
        self.logicalname = ""
        dic = {}
        super().__init__("DataType", dic)


    def Set(self, values ):
        # check mandatory attributes
        for k, val in values.items():
            super().SetAttrib(k,val)




class Login(Entity):
    def __init__(self):
        # record mandatory attributes
        dic = {}
        dic["logicalname"]=Attribute("logicalname","text",True)
        super().__init__("Login", dic)



class Secret(Entity):
    def __init__(self):
       # record mandatory attributes
        dic = {}
        super().__init__("Secret", dic)


class Token(Entity):
    def __init__(self):
       # record mandatory attributes
        dic = {}
        super().__init__("Token", dic)


class Credential(Entity):
    def __init__(self):
       # record mandatory attributes
        dic = {}
        dic["logicalname"]=Attribute("logicalname","text",True)
        super().__init__("Credential", dic)

        self.type = CredentialType()
        self.login = Login()
        self.secret = Secret()
        self.token = Token()

    def Set(self, values, logicalname ):
        super().SetAttrib("logicalname",logicalname)
        # check mandatory attributes
        for k, val in values.items():
            if k == "Login":
                self.type.Set("login")
                self.login.SetAttrib("logicalname",logicalname)
                self.login.SetAttrib(k,val)
            elif k == "Password":
                self.type.Set("login")
                self.login.SetAttrib("logicalname",logicalname )
                self.login.SetAttrib(k,val)
            elif k == "Secret":
                self.type.Set("secret")
                self.Secret.SetAttrib("logicalname",logicalname)
                self.Secret.SetAttrib(k,val)
            elif k == "Token":
                self.type.Set("token")
                self.token.SetAttrib("logicalname",logicalname)
                self.token.SetAttrib(k,val)
            else:
                self.type.Set("login")
                
        super().SetAttrib("CredentialType",self.type.Get())
              

    def DbCreate(self):
        if self.type.Get() == "login":
            id = self.login.DbCreate()
            super().SetAttrib("loginid",id)
        elif self.type.Get() == "secret":
            id = self.Secret.DbCreate()
            super().SetAttrib("secretid",id)
        elif self.type.Get() == "login":
            id = self.token.DbCreate()
            super().SetAttrib("tokenid",id)
        return super().DbCreate()

    def DbLoad(self, id):
        super().DbLoad(id)
        if super().GetAttrib("loginid").value:
            self.type.Set("login")
        elif super().GetAttrib("secretid").value:
            self.type.Set("secret")
        elif super().GetAttrib("tokenid").value:
            self.type.Set("token")

        if self.type.Get() == "login":
            id = super().GetAttrib("loginid").value
            self.login.DbLoad(id)
        elif self.type.Get() == "secret":
            id = super().GetAttrib("secretid").value
            self.secret.DbLoad(id)
        elif self.type.Get() == "token":
            id = super().GetAttrib("tokenid").value
            self.token.DbLoad(id)

    def Jsonify(self):
        res = None
        if self.type.Get() == "login":
            res = self.login.Jsonify()
        elif self.type.Get() == "secret":
            res = self.Secret.Jsonify()
        elif self.type.Get() == "token":
            res = self.token.Jsonify()
        return res
        
class Target(Entity):
    def __init__(self):
        self.credential = Credential()
        super().SetAttrib("credentialid",-1)
        dic = {}
        dic["logicalname"]=Attribute("logicalname","text",True)
        super().__init__("Target", dic)

    def Set(self, values ):
        for k, val in values.items():
            if k == "LogicalName":
                self.logicalname = val
                super().SetAttrib(k,val)

            elif k == "Credential":
                self.credential.Set(val,self.logicalname)
            else :
                super().SetAttrib(k,val)


    def DbCreate(self):
        id = self.credential.DbCreate()
        super().SetAttrib("credentialid",id)
        return super().DbCreate()

    def DbLoad(self, id):
        super().DbLoad(id)
        credentialID = super().GetAttrib("credentialid").value
        self.credential.DbLoad(credentialID)

    def Jsonify(self):
        res = super().Jsonify()
        res["Credential"] = self.credential.Jsonify()
        return res

class DestinationPolicy(Entity):

    def __init__(self):
        self.target = Target()
        dic = {}
        dic["logicalname"]=Attribute("logicalname","text",True)
        super().__init__("DestinationPolicy", dic)

    def Set(self, values, logicalname ):
        self.target = Target()
        super().SetAttrib("logicalname",logicalname)
        for k, val in values.items():
                               
            if k == "Destination":
                id = self.target.GetDbId(val)
                super().SetAttrib("targetid",id)
                super().UnSetDB("Destination")
            else:
                super().SetAttrib(k,val)

    def DbCreate(self):
        return super().DbCreate()

    def Jsonify(self):
        res = super().Jsonify()
        res["Destination"] = self.target.Jsonify()
        return res

    def DbLoad(self, id):
        super().DbLoad(id)
        tgid = super().GetAttrib("targetid").value
        self.target.DbLoad(tgid)     

class SourcePolicy(Entity):

    def __init__(self):
        self.target = Target()
        dic = {}
        dic["logicalname"]=Attribute("logicalname","text",True)
        super().__init__("SourcePolicy", dic)

    def Set(self, values, logicalname ):
        self.target = Target()
        super().SetAttrib("logicalname",logicalname)
        # check mandatory attributes
        for k, val in values.items():
                               
            if k == "Source":
                id = self.target.GetDbId(val)
                super().SetAttrib("targetid",id)
                super().UnSetDB("Source")
            else:
                super().SetAttrib(k,val)


    def Jsonify(self):
        res = super().Jsonify()
        res["Source"] = self.target.Jsonify()
        return res

    def DbLoad(self, id):
        super().DbLoad(id)
        tgid = super().GetAttrib("targetid").value
        self.target.DbLoad(tgid)       

class DataPolicy(Entity):

    def __init__(self):
        self.itemType = ItemType()
        dic = {}
        dic["logicalname"]=Attribute("logicalname","text",True)
        super().__init__("DataPolicy", dic)

    def Set(self, values, logicalname ):
        super().SetAttrib("logicalname",logicalname)
        for k, val in values.items():
            super().SetAttrib(k,val)



class Periodical(Entity):
    def __init__(self):
        dic = {}
        dic["logicalname"]=Attribute("logicalname","text",True)
        super().__init__("Periodical", dic)

    def Set(self, values, logicalname ):
        super().SetAttrib("logicalname",logicalname)
        for k, val in values.items():
            super().SetAttrib(k,val)

    def DbUpdateTimeStamp(self, id):
        arg = list()
        arg.append(id)
        s = "SELECT PollingInterval,NOW() FROM Periodical WHERE PeriodicalID = %s ;"
        cur = db.Exec(s,arg)
        records = cur.fetchall()
        nextscan = records[0][1] + datetime.timedelta(seconds=records[0][0])
        s = "UPDATE Periodical set lastscan = %s where PeriodicalID = %s ;"
        arg = list()
        arg.append(nextscan)
        arg.append(id)
        cur = db.Exec(s,arg)
        db.Commit()

            
    def DbLoad(self, id):
        self.id = id
        super().DbLoad(id)



queueLastTransferPolicyID = 0

class TransferPolicy(Entity):

    def __init__(self):
        self.logicalname = ""
        self.transferRequestType = TransferRequestType()
        self.dataType = DataType()
        self.periodical = Periodical()
        self.fDataPolicy = False
        self.dataPolicy = DataPolicy()
        self.sourcePolicy = SourcePolicy()
        self.destinationPolicy = DestinationPolicy()
        self.target = Target()
        self.fNotification = False
        self.Notifications = []
        dic = {}
        dic["logicalname"]=Attribute("logicalname","text",True)
        super().__init__("TransferPolicy", dic)


    def Set(self, values ):
        # check mandatory attributes
        fPeriodical = False
        for k, val in values.items():
            if k == "LogicalName":
                self.logicalname = val
                super().SetAttrib(k,val)

            elif k == "DataType":
                id = self.dataType.GetDbId(val)
                super().SetAttrib("datatypeid",id)
  
            elif k == "DataPolicy":
                self.fDataPolicy = True
                self.dataPolicy.Set(val,self.logicalname)
            
            elif k == "DestinationPolicy":
                self.destinationPolicy.Set(val,self.logicalname)
                   
            elif k == "SourcePolicy":
                self.sourcePolicy.Set(val,self.logicalname)
               
            elif k == "Periodical":
                fPeriodical = True
                self.periodical.Set(val,self.logicalname)

            elif k == "TransferRequestType":
                self.transferRequestType.Set(val)

            elif k == "Notifications":
                for notif in val:
                    n = Notification()
                    n.Set(notif)
                    self.Notifications.append(n)
                    self.fNotification = True

            else :
                super().SetAttrib(k,val)
        

        super().SetAttrib("transferrequesttype",self.transferRequestType.Get())  
  

    def GetNextTransferPolicy(self):
        global queueLastTransferPolicyID
        arg = list()
        arg.append(queueLastTransferPolicyID)
        s = "select min(TransferPolicyID) from TransferPolicy  inner join periodical on (periodicalID = TransferPolicyID) where  lastscan  < NOW() and TransferPolicyID > %s;"    

        cur = db.Exec(s,arg)
        records = cur.fetchall()
        if records[0][0] :
            id = records[0][0]
            self.periodical.DbUpdateTimeStamp(id)
            return id 
        else :
            db.Commit()
            queueLastTransferPolicyID = 0    # If no next policy found starting from last Policy, restart search   starting from the list beginning
            arg = list()
            s = "select min(TransferPolicyID) from TransferPolicy  inner join periodical on (periodicalID = TransferPolicyID) where  lastscan  < NOW() ;"    

            cur = db.Exec(s,arg)
            records = cur.fetchall()
            if records[0][0] :
                self.periodical.DbUpdateTimeStamp(records[0][0])
                return records[0][0] 
            else:
                pass


    def DbCreate(self):
        #self.Dump()
        if self.fDataPolicy:
            id = self.dataPolicy.DbCreate()
            super().SetAttrib("datapolicyid",id)

        id = self.destinationPolicy.DbCreate()
        super().SetAttrib("destinationpolicyid",id)

        id = self.sourcePolicy.DbCreate()
        super().SetAttrib("sourcepolicyid",id)

        id = super().DbCreate()
        if self.transferRequestType.Get() == "periodical":
            self.periodical.SetAttrib("periodicalid",id)
            self.periodical.DbCreate()
        
        if self.fNotification :
            for n in self.Notifications:   
                n.SetAttrib("TransferPolicyId",id) 
                n.DbCreate()

        return id
    
    def DbLoad(self, id):
        super().DbLoad(id)
        self.periodical.DbLoad(id)
        dpid = super().GetAttrib("datapolicyid").value
        if dpid:
            self.dataPolicy.DbLoad(dpid)

        dtid = super().GetAttrib("datatypeid").value
        if dtid:
            self.dataType.DbLoad(dtid)
            
        dpid = super().GetAttrib("destinationpolicyid").value
        self.destinationPolicy.DbLoad(dpid)

        spid = super().GetAttrib("sourcepolicyid").value
        self.sourcePolicy.DbLoad(spid)
        n = Notification()
        ids = n.DbGetTransferPolicyNotifications(id)
        self.TdsOn = False
        for id in ids:
            n = Notification()
            self.fNotification = True
            n.DbLoad(id)
            if n.GetAttrib("TdsOn").value:
                self.TdsOn = False

            self.Notifications.append(n)

    def Jsonify(self):
        res = super().Jsonify()
        res["Periodical"] = self.periodical.Jsonify()
        res["DataType"] = self.dataType.Jsonify()
        res["DataPolicy"] = self.dataPolicy.Jsonify()
        res["SourcePolicy"] = self.sourcePolicy.Jsonify()
        res["DestinationPolicy"] = self.destinationPolicy.Jsonify()
        if self.fNotification:
            notifs = []
            for n in self.Notifications :
                notifs.append(n.Jsonify())

            res["Notifications"] = notifs 

        return res

 

class ExecutionSlot(Entity):
    def __init__(self):
        dic = {}
        super().__init__("ExecutionSlot", dic)

    def Set(self, values ):
        for k, val in values.items():
            super().SetAttrib(k,val)

    def DbCreate(self,transferRequestId):
        arg = list()
        arg.append(transferRequestId)
        s = "INSERT INTO ExecutionSlot (TransferRequestId,QueueCreation) VALUES(%s,NOW());"
        db.Exec(s,arg)
        s = "SELECT lastval();"
        cur = db.Exec(s,{})
        records = cur.fetchall()
        self.dbid = records[0][0]
        db.Commit()


    def Start(self):
        arg = list()
        arg.append(self.dbid)
        s = "UPDATE ExecutionSlot SET ExecutionStart=NOW() WHERE ExecutionSlotID = %s ;"
        db.Exec(s,arg)
        db.Commit()

    def End(self):
        arg = list()
        arg.append(self.dbid)
        s = "UPDATE ExecutionSlot SET ExecutionEnd=NOW() WHERE ExecutionSlotID = %s ;"
        db.Exec(s,arg)
        db.Commit()

        s = "SELECT abs(extract (second from ExecutionEnd - ExecutionStart)) FROM ExecutionSlot  WHERE ExecutionSlotID = %s ;" 
        cur = db.Exec(s,arg)
        records = cur.fetchall()
        return records[0][0] 

    def GetRequestLastSlot(self,transferRequestId):  
        arg = list()
        arg.append(transferRequestId)
        s = "SELECT MAX(ExecutionSlotID) FROM ExecutionSlot WHERE TransferRequestId = %s;"
        cur = db.Exec(s,arg)
        records = cur.fetchall()
        self.dbid = records[0][0] 
        return  self.dbid

    def DbLoad(self, id):
        self.id = id
        super().DbLoad(id)
        super().Dump()   

    def DbAgeDays(self,days):
 
        arg = list()
        days = - abs(days)
        s = f"UPDATE ExecutionSlot SET ExecutionEnd = ExecutionEnd + interval '{days} days' , ExecutionStart = ExecutionStart + interval '{days} days' ,QueueCreation = QueueCreation + interval '{days} days'  ;"
        db.Exec(s,arg)
        db.Commit()

class TransferRequest(Entity):

    def __init__(self):
        self.logicalname = ""
        self.transferPolicy = TransferPolicy()
        dic = {}
        super().__init__("TransferRequest", dic)


    def Set(self, values ):
        # check mandatory attributes
        for k, val in values.items():
            if k == "LogicalName":
                self.logicalname = val
                super().SetAttrib(k,val)
            else :
                super().SetAttrib(k,val)
        
        super().SetAttrib("transferrequesttype",self.transferRequestType.Get())     


    def DbCreate(self,queueDbId,transferPolicyDbId,FileName,uid,timestamp,isCmd):
        if ( self.DbQueuedFileNb(transferPolicyDbId,FileName,isCmd) == 0):
            super().SetAttrib("Filename",FileName)
            super().SetAttrib("QueueID",queueDbId)
            super().SetAttrib("TransferPolicyID",transferPolicyDbId)
            super().SetAttrib("Uid",uid)
            super().SetAttrib("CmdTimestamp",timestamp)
            super().SetAttrib("RequestState",'Queued')
            id = super().DbCreate()
            s = "insert into TransferIsNotified (TransferRequestId,NotificationId) select %s, NotificationId from Notification where TransferPolicyId = %s ;"
            arg = list()
            arg.append(id)
            arg.append(transferPolicyDbId)
            cur = db.Exec(s,arg)
        else:
            id = -1
        return id

    def DbQueuedFileNb(self,transferPolicyDbId,filename,isCmd):
        if isCmd :
            s = "select count(*) from TransferRequest where TransferPolicyID = %s and Filename = %s and RequestState in ('Queued','In Progress','Paused','Notify');"
        else:
            s = "select count(*) from TransferRequest where TransferPolicyID = %s and Filename = %s;"
        arg = list()
        arg.append(transferPolicyDbId)
        arg.append(filename)
        cur = db.Exec(s,arg)
        records = cur.fetchall()
        return records[0][0] 

    def DbLoad(self, id):
        super().DbLoad(id)
        tpid = super().GetAttrib("transferpolicyid").value
        if tpid:
            self.transferPolicy.DbLoad(tpid)

    def DbPartialLoad(self, id):
        if super().DbLoad(id):
            return 1
        else:
            return -1

    def UpdateState(self,id,state,failed_step = None):
        if not failed_step:
            failed_step = None

        es = ExecutionSlot()
        es.GetRequestLastSlot(id)
        duration = es.End()
        arg = list()
        s = "update TransferRequest set requeststate = %s, FailedStep = %s , TransferDuration = %s where  TransferRequestID = %s ;"
        arg.append(state)
        arg.append(failed_step)
        arg.append(duration)
        arg.append(id)
        db.Exec(s,arg)

        db.Commit()
 

    def Jsonify(self):
        res = super().Jsonify()
        res["TransferPolicy"] = self.transferPolicy.Jsonify()
        return res

    def BreakWithConf(self):
        arg = list()
        s = "update TransferRequest set TransferPolicyID = NULL,QueueID = NULL ;"
        db.Exec(s,arg)
        db.Commit()

    def DbRetentionDays(self):

        if self.transferPolicy.GetAttrib("DatabaseRetentionDays").value:
            retentionDays = self.transferPolicy.GetAttrib("DatabaseRetentionDays").value
        else :
            gp  = GlobalParameters()
            retentionDays =  gp.DBGet("DatabaseRetentionDays")

        return retentionDays


    def HouseKeeping(self):
        tpid = self.transferPolicy.GetAttrib("transferpolicyid").value
        retentionDays = self.DbRetentionDays()
        minDate = datetime.datetime.today() + datetime.timedelta(days = - retentionDays)

        arg = list()
        arg.append(minDate)
        arg.append(tpid)

        s = "DELETE  FROM TransferRequest USING ExecutionSlot  where ExecutionSlot.TransferRequestID = TransferRequest.TransferRequestID and ExecutionSlot.ExecutionEnd < %s  and TransferRequest.transferpolicyid = %s;"
        db.Exec(s,arg)
        db.Commit()

    

