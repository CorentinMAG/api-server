# Enum class with string values
class Enum:



    def __init__(self,values):
        self.values = values
        self.value = self.values[0]

    def Set(self,value):
        f = False
        for it in self.values:
            if it == value:
                f = True
                break
        if f == False:
            msg = "unknown value " + value + " for enum"
            raise Exception(msg)
        else:
            self.value = value

    def Get(self):
        return self.value


class Protocol(Enum):
    def __init__(self):
         Enum.__init__(self, ["SFTP","FTPS","HTTPS","MOUNTED FS","S3"])


class CredentialType(Enum):
    def __init__(self):
         Enum.__init__(self, ["login","secret","token"])
         

class ItemType(Enum):
    def __init__(self):
         Enum.__init__(self, ["dir","file"])


class TransferRequestType(Enum):
    def __init__(self):
         Enum.__init__(self, ["on demand","periodical"])



class RequestState(Enum):
    def __init__(self):
         Enum.__init__(self, ["Queued","In Progress","Failed","Completed","Cancelled","Paused","Notify"])

class FailedStep(Enum):
    def __init__(self):
         Enum.__init__(self, ["SourceCnxException","SourceDirDidNotExist","SourceFileCopyException","UnTarException","CheckFailed","CheckException","ValidationFailed","ValidationException","TarException","DestinationCnxException","DestinationCopyException","SourceAuthentException","DestinationAuthentException","DestinationDirDidNotException"])


         


