from api.models import Target, Credentials, TargetParameters
from .base import BaseService
from api.repositories import TargetRepository
from dtr_common.schema import TargetCreate, TargetUpdate, Pagination
from werkzeug.datastructures import ImmutableMultiDict


class TargetService(BaseService[TargetRepository]):
    """Service for Target operations"""

    def get_by_name(self, name: str) -> Target:
        return self.repository.get_by_name(name)

    def get_by_id(self, id: int) -> Target:
        return self.repository.get_by_id(id)

    def paginate(self, args: ImmutableMultiDict) -> Pagination[Target]:
        return self.repository.paginate(args)

    def create(self, data: TargetCreate) -> Target:
        """create a new target"""

        target = Target(**data.model_dump(exclude={"credentials", "parameters"}))

        if data.credentials:
            credentials = Credentials(
                **data.credentials.model_dump(context={"include_secrets": True})
            )
            target.credentials = credentials
        target.parameters = TargetParameters(**data.parameters.model_dump())
        return self.repository.create(target)

    def update(self, id: int, data: TargetUpdate) -> Target:
        target = self.repository.get_by_id(id)
        return self.repository.update(
            target,
            data.model_dump(exclude_none=True, context={"include_secrets": True}),
        )

    def delete(self, id: int) -> None:
        target = self.repository.get_by_id(id)
        self.repository.delete(target)