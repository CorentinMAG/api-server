from ..models import NotificationServer
from .base import BaseRepository
from flask_sqlalchemy import SQLAlchemy
from ..db import db

class ServerRepository(BaseRepository):

    def __init__(self, db: SQLAlchemy) -> None:
        self.db = db

    def get_by_id(self, id: int) -> NotificationServer:
        return self.db.session.query(NotificationServer).get(id)
    
    def get_by_name(self, name: str) -> NotificationServer:
        return self.db.session.query(NotificationServer).where(NotificationServer.name == name).first()
    
    def get_all(self) -> list[NotificationServer]:
        return self.db.session.query(NotificationServer).all()

    def add(self, server: NotificationServer) -> int:
        self.db.session.add(server)
        self.db.session.commit()
        return server

    def remove(self, server: NotificationServer) -> None:
        self.db.session.delete(server)
        self.db.session.commit()

    def update(self, server: NotificationServer) -> int:
        self.db.session.commit()
    
    def flush(self) -> None:
        self.db.session.query(NotificationServer).delete()
        self.db.session.commit()

repository = ServerRepository(db)