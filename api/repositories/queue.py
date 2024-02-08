from ..utils import Singleton
from ..db import db
from ..models import Queue

class QueueRepository(Singleton):

    def getById(self, id: int):
        queues = db.session.execute(db.select(Queue)).all()
        print(queues[1][0].queueid)

repository = QueueRepository()