from sqlalchemy.orm import selectinload
from sqlalchemy import select
from .base import BaseRepository
from api.models import Queue
from api.exception import NotFoundException


class QueueRepository(BaseRepository[Queue]):
    """repository for queue operations"""

    pass
