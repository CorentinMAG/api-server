from ..models import GlobalParameters
from .base import BaseRepository
from sqlalchemy import select
from flask_sqlalchemy import SQLAlchemy

class GlobalParametersRepository(BaseRepository[GlobalParameters]):
    def __init__(self, db: SQLAlchemy):
        super().__init__(GlobalParameters, db)

    def get_params(self) -> GlobalParameters | None:
        query = select(GlobalParameters).limit(1)
        obj = self.session.scalar(query)
        return obj