"""
Target repository providing specialized database operations.

This repository implements target-specific queries and management operations.
"""

from __future__ import annotations

from typing import List, Optional

from dtr_common.constantes import Protocol
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from api.models import Credentials, Target

from .base import BaseRepository


class TargetRepository(BaseRepository[Target]):
    """Repository for Target operations with specialized queries."""

    def __init__(self, db_session: Session):
        super().__init__(Target, db_session)

    def find_by_criteria(self, **criteria) -> List[Target]:
        """Find targets by basic criteria."""
        query = select(self.model_class)
        for key, value in criteria.items():
            if hasattr(self.model_class, key):
                query = query.where(getattr(self.model_class, key) == value)
        return list(self.db_session.execute(query).scalars().all())

    def find_by_name(self, name: str) -> Optional[Target]:
        """Find target by name."""
        stmt = select(Target).where(Target.name == name)
        return self.db_session.scalar(stmt)

    def find_by_protocol(self, protocol: Protocol) -> List[Target]:
        """Find targets by protocol type."""
        stmt = (
            select(Target)
            .where(Target.protocol == protocol)
            .options(joinedload(Target.credentials), joinedload(Target.parameters))
        )
        return list(self.db_session.execute(stmt).scalars().unique().all())

    def find_by_host(self, host: str) -> List[Target]:
        """Find targets by host."""
        stmt = select(Target).where(Target.host == host).options(joinedload(Target.parameters))
        return list(self.db_session.execute(stmt).scalars().unique().all())

    def find_by_host_and_port(self, host: str, port: int) -> List[Target]:
        """Find targets by host and port combination."""
        stmt = select(Target).where(Target.host == host, Target.port == port)
        return list(self.db_session.execute(stmt).scalars().all())

    def get_with_credentials(self, target_id: int) -> Optional[Target]:
        """Get target with credentials loaded."""
        stmt = select(Target).where(Target.id == target_id).options(joinedload(Target.credentials))
        return self.db_session.scalar(stmt)

    def get_with_full_details(self, target_id: int) -> Optional[Target]:
        """Get target with all relationships loaded."""
        stmt = (
            select(Target)
            .where(Target.id == target_id)
            .options(joinedload(Target.credentials), joinedload(Target.parameters))
        )
        return self.db_session.scalar(stmt)

    def find_targets_with_credentials(self) -> List[Target]:
        """Find all targets that have credentials configured."""
        stmt = select(Target).join(Credentials).options(joinedload(Target.credentials))
        return list(self.db_session.execute(stmt).scalars().unique().all())

    def find_targets_without_credentials(self) -> List[Target]:
        """Find all targets that don't have credentials configured."""
        stmt = select(Target).outerjoin(Credentials).where(Credentials.id.is_(None))
        return list(self.db_session.execute(stmt).scalars().all())

    def get_protocol_summary(self) -> List[dict]:
        """Get summary of targets grouped by protocol."""
        stmt = select(Target.protocol, Target.id).order_by(Target.protocol)
        results = self.db_session.execute(stmt).all()

        # Group by protocol
        protocol_counts = {}
        for protocol, target_id in results:
            if protocol not in protocol_counts:
                protocol_counts[protocol] = 0
            protocol_counts[protocol] += 1

        return [{"protocol": protocol, "count": count} for protocol, count in protocol_counts.items()]

    def validate_target_connectivity(self, target_id: int) -> dict:
        """Validate target configuration for connectivity."""
        target = self.get_with_full_details(target_id)
        if not target:
            return {"valid": False, "error": "Target not found"}

        validation_result = {
            "valid": True,
            "target_id": target_id,
            "name": target.name,
            "protocol": target.protocol,
            "host": target.host,
            "port": target.port,
            "has_credentials": target.credentials is not None,
            "has_parameters": target.parameters is not None,
            "issues": [],
        }

        # Basic validation checks
        if not target.host:
            validation_result["valid"] = False
            validation_result["issues"].append("Host is required")

        if not target.port or target.port <= 0:
            validation_result["valid"] = False
            validation_result["issues"].append("Valid port is required")

        # Protocol-specific validation
        if target.protocol in [Protocol.SFTP, Protocol.FTPS]:
            if not target.credentials:
                validation_result["issues"].append("Credentials required for secure protocols")

        return validation_result
