from ..models import TransferPolicy, SourcePolicy, DestinationPolicy
from .base import BaseRepository
from flask_sqlalchemy import SQLAlchemy
from ..db import db

class TransferPolicyRepository(BaseRepository):

    def __init__(self, db: SQLAlchemy) -> None:
        self.db = db

    def get_by_id(self, id: int) -> TransferPolicy:
        return self.db.session.query(TransferPolicy).get(id)
    
    def get_all(self) -> list[TransferPolicy]:
        return self.db.session.query(TransferPolicy).all()

    def add(self, policy: TransferPolicy) -> int:
        self.db.session.add(policy)
        self.db.session.commit()
        return policy

    def remove(self, policy: TransferPolicy) -> None:
        self.db.session.delete(policy)
        self.db.session.commit()
    
    def flush(self) -> None:
        self.db.session.query(TransferPolicy).delete()
        self.db.session.commit()

class SourcePolicyRepository(BaseRepository):

    def __init__(self, db: SQLAlchemy) -> None:
        self.db = db

    def get_by_id(self, id: int) -> SourcePolicy:
        return self.db.session.query(SourcePolicy).get(id)
    
    def get_all(self) -> list[SourcePolicy]:
        return self.db.session.query(SourcePolicy).all()

    def add(self, queue: SourcePolicy) -> int:
        self.db.session.add(queue)
        self.db.session.commit()
        return queue

    def remove(self, queue: SourcePolicy) -> None:
        self.db.session.delete(queue)
        self.db.session.commit()
    
    def flush(self) -> None:
        self.db.session.query(TransferPolicy).delete()
        self.db.session.commit()

class DestinationPolicyRepository(BaseRepository):

    def __init__(self, db: SQLAlchemy) -> None:
        self.db = db

    def get_by_id(self, id: int) -> DestinationPolicy:
        return self.db.session.query(DestinationPolicy).get(id)
    
    def get_all(self) -> list[DestinationPolicy]:
        return self.db.session.query(DestinationPolicy).all()

    def add(self, queue: DestinationPolicy) -> int:
        self.db.session.add(queue)
        self.db.session.commit()
        return queue

    def remove(self, queue: DestinationPolicy) -> None:
        self.db.session.delete(queue)
        self.db.session.commit()
    
    def flush(self) -> None:
        self.db.session.query(DestinationPolicy).delete()
        self.db.session.commit()

tr_repository = TransferPolicyRepository(db)
src_repository = SourcePolicyRepository(db)
dest_repository = DestinationPolicyRepository(db)