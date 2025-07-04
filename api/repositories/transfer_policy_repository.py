"""
TransferPolicy repository providing specialized database operations.

This repository implements complex queries specific to transfer policy
management, including policy filtering and validation operations.
"""
from __future__ import annotations

from typing import List, Optional

from dtr_common.constantes import Type
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from api.models import DestinationPolicy, SourcePolicy, TransferPolicy

from .base import BaseRepository


class TransferPolicyRepository(BaseRepository[TransferPolicy]):
    """Repository for TransferPolicy operations with specialized queries."""

    def __init__(self, db_session: Session):
        super().__init__(TransferPolicy, db_session)

    def find_by_criteria(self, **criteria) -> List[TransferPolicy]:
        """Find transfer policies by basic criteria."""
        query = select(self.model_class)
        for key, value in criteria.items():
            if hasattr(self.model_class, key):
                query = query.where(getattr(self.model_class, key) == value)
        return list(self.db_session.execute(query).scalars().all())

    def find_by_name(self, name: str) -> Optional[TransferPolicy]:
        """Find transfer policy by name."""
        stmt = select(TransferPolicy).where(TransferPolicy.name == name)
        return self.db_session.scalar(stmt)

    def find_by_name_and_type(self, name: str, policy_type: Type) -> Optional[TransferPolicy]:
        """Find transfer policy by name and type."""
        stmt = select(TransferPolicy).where(TransferPolicy.name == name, TransferPolicy.type == policy_type)
        return self.db_session.scalar(stmt)

    def find_enabled_policies(self) -> List[TransferPolicy]:
        """Find all enabled transfer policies."""
        stmt = (
            select(TransferPolicy)
            .where(TransferPolicy.enabled.is_(True))
            .options(
                joinedload(TransferPolicy.queue),
                joinedload(TransferPolicy.parameters),
                joinedload(TransferPolicy.src),
                joinedload(TransferPolicy.dests),
            )
        )
        return list(self.db_session.execute(stmt).scalars().unique().all())

    def find_by_type(self, policy_type: Type) -> List[TransferPolicy]:
        """Find transfer policies by type."""
        stmt = (
            select(TransferPolicy)
            .where(TransferPolicy.type == policy_type)
            .options(joinedload(TransferPolicy.dests))
        )
        return list(self.db_session.execute(stmt).scalars().unique().all())

    def find_periodical_policies(self) -> List[TransferPolicy]:
        """Find all periodical transfer policies."""
        return self.find_by_type(Type.PERIODICAL)

    def find_commanded_policies(self) -> List[TransferPolicy]:
        """Find all commanded transfer policies."""
        return self.find_by_type(Type.COMMANDED)

    def get_with_relationships(self, policy_id: int) -> Optional[TransferPolicy]:
        """Get transfer policy with all relationships loaded."""
        stmt = (
            select(TransferPolicy)
            .where(TransferPolicy.id == policy_id)
            .options(
                joinedload(TransferPolicy.queue),
                joinedload(TransferPolicy.parameters),
                joinedload(TransferPolicy.src).joinedload(SourcePolicy.target),
                joinedload(TransferPolicy.dests).joinedload(DestinationPolicy.target),
                joinedload(TransferPolicy.transfers),
            )
        )
        return self.db_session.scalar(stmt)

    def count_by_status(self, enabled: bool) -> int:
        """Count transfer policies by enabled status."""
        stmt = select(self.model_class.id).where(self.model_class.enabled == enabled)
        return len(list(self.db_session.execute(stmt).scalars().all()))

    def find_policies_with_queue(self, queue_name: str) -> List[TransferPolicy]:
        """Find all policies using a specific queue."""
        stmt = (
            select(TransferPolicy).join(TransferPolicy.queue).where(TransferPolicy.queue.has(name=queue_name))
        )
        return list(self.db_session.execute(stmt).scalars().all())

    def delete_policy_cascade(self, policy_id: int) -> bool:
        """Delete policy and handle cascading relationships."""
        policy = self.get_by_id(policy_id)
        if not policy:
            return False

        try:
            # Delete the policy (cascading should handle relationships)
            self.db_session.delete(policy)
            return True
        except Exception:
            return False
