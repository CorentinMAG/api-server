from ..models import Target
from .base import BaseRepository
from flask_sqlalchemy import SQLAlchemy
from ..db import db

class TargetRepository(BaseRepository):

    def __init__(self, db: SQLAlchemy) -> None:
        self.db = db

    def get_by_id(self, id: int) -> Target:
        return self.db.session.query(Target).get(id)
    
    def get_by_name(self, name: str) -> Target:
        return self.db.session.query(Target).where(Target.name == name).first()
    
    def get_all(self) -> list[Target]:
        return self.db.session.query(Target).all()

    def add(self, target: Target) -> Target:
        self.db.session.add(target)
        self.db.session.commit()
        return target

    def remove(self, target: Target) -> None:
        self.db.session.delete(target)
        self.db.session.commit()
    
    def flush(self) -> None:
        self.db.session.query(Target).delete()
        self.db.session.commit()

repository = TargetRepository(db)