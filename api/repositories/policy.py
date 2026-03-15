from .base import BaseRepository
from api.models import TransferPolicy, DestinationPolicy
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from api.exception import NotFoundException
from typing import overload


class TransferPolicyRepository(BaseRepository[TransferPolicy]):
    """Repository for TransferPolicy operations"""

    pass
