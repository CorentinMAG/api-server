
import psycopg
import json
import os
import datetime
from enums import *
import datetime

class database:
    cnx = None

    def Connect(self):

        self.cnx = psycopg.connect(     dbname=os.environ["DTR_DB_NAME"],
					                    user=os.environ["DTR_DB_USER"],
                                         password=os.environ["DTR_DB_PASSWORD"],
                                         host=os.environ["DTR_DB_HOST"],
                                         port=os.environ["DTR_DB_PORT"])


    def Exec(self,stmt,vals):
        cur = self.cnx.cursor()
        cur.execute(stmt,vals,)
        return cur

    def Commit(self):
        self.cnx.commit()

db = database()
db.Connect()


class DbType(Enum):
    def __init__(self):
         Enum.__init__(self, ["text","numeric","date","entity","autoinc"])

class Attribute:
    name = ""
    value = None
    
    isId = False
    fJson = False
    fDB = True

    def __init__(self,name,type ,isId = False):
        self.name = name.lower()
        self.type = DbType()
        if type == None:
            type = "text"
        elif isinstance(type,str):
            self.type.Set(type)
            self.isId = isId
        else:
            self.type.value = type.value

    def SetVal(self,val):
        self.value = val


    def UnSetDB(self):
        self.fDB = False

with open('cfg.json') as jf:
    json_cfg = json.load(jf)

class Entity:
    name = ""
    attributes = dict()

    def __init__(self,name,attributes):
        self.name = name
        self.attributes = dict()
        for k in attributes.keys():
            a = attributes[k]
            cp = Attribute(a.name,a.type)
            cp.SetVal(a.value)
            self.AddAttrib(cp)

        self.cfg = json_cfg[name]
        for k in self.cfg['Fields']:
            item = self.cfg['Fields'][k]
            a = Attribute(k.lower(),item)
            a.fJson = True
            self.AddAttrib(a)

    def GetAttrib(self,name):
        name = name.lower()
        if name in self.attributes.keys():
            res = self.attributes[name]
        else:
            res = Attribute(name,"text",False)
            self.attributes[name] = res
        return res

    def AddAttrib(self,attribute):
        self.attributes[attribute.name] = attribute


    def SetAttrib(self,name,val):
        attrib =  self.GetAttrib(name)
        attrib.SetVal(val)

    
    def UnSetDB(self,name):
        attrib =  self.GetAttrib(name)
        attrib.UnSetDB()

    def DbCreate(self,fNoRet = False):
        s = "INSERT INTO " + self.name + " ( "
        sep = ""
        cols = ""
        vals = list()
        placeHolders = ""
        q = "\""
        for k in self.attributes.keys():
            att = self.attributes[k]
            if att.type.value != "entity" and att.type.value != "autoinc" and att.fDB:
                cols = cols+ sep + att.name 
                placeHolders = placeHolders + sep + "%s"
                vals.append(att.value)
                sep = ","
        s = s + cols + " ) VALUES (" + placeHolders + "); "
        cur = db.Exec(s,vals)
        s = "SELECT lastval();"
        if fNoRet:
            return
        else:
            cur = db.Exec(s,{})
            records = cur.fetchall()
            return records[0][0]


    def DbLoad(self,id):
        self.id = id
        s = "select * from " + self.name + " where " + self.name + "ID = " + str(id) + ";"
        arg = list()
        cur = db.Exec(s,arg)
        records = cur.fetchall()

        if len(records) >0:
            row = records[0]
            i = 0
            for col in cur.description:
                a = self.GetAttrib(col[0])
                a.value = row[i]
                i = i + 1
            return 1
        else:
            return -1
    

    def DbLoadByName(self,name):
        id = self.GetDbId(name)
        self.DbLoad(id)

    def DbGetIds(self):
        s = "select " + self.name + "ID from " + self.name + "  ; "
        arg = list()
        cur = db.Exec(s,arg)
        records = cur.fetchall()
        res = list()
        for r in records:
            res.append(r[0])
        return res

    def GetDbId(self, name ):
        s = "select " + self.name + "ID from " + self.name + "  where logicalname = %s ;"
        arg = list()
        arg.append(name)
        cur = db.Exec(s,arg)
        records = cur.fetchall()
        return records[0][0]

    def GetId(self ):
        return self.id

    def DbDelete(self,name):
        s = "DELETE  from " + self.name + "  where logicalname = %s ;"
        arg = list()
        arg.append(name)
        db.Exec(s,arg)
        db.Commit()

    def DbDeleteAll(self):
        s = "DELETE  from " + self.name + "  ;"
        arg = list()
        db.Exec(s,arg)
        db.Commit()

    def Jsonify(self):
        res = dict()
        for k in self.attributes:
            a = self.attributes[k]
            if a.value :
                if a.fJson:
                    res[a.name] = a.value
        return res

    def Dump(self):
        res = dict()
        for k in self.attributes:
            a = self.attributes[k]
            res[a.name] = a.value

        return res
    

