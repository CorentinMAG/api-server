from api.repositories import NotificationServerRepository
from .base import BaseService
from api.models import NotificationServer, Credentials
from dtr_common.schema import ServerUpdate, ServerCreate, Pagination
from werkzeug.datastructures import ImmutableMultiDict


class NotificationServerService(BaseService[NotificationServerRepository]):

    def get_by_name(self, name: str) -> NotificationServer:
        return self.repository.get_by_name(name)

    def get_by_id(self, id: int) -> NotificationServer:
        return self.repository.get_by_id(id)

    def paginate(self, args: ImmutableMultiDict) -> Pagination[NotificationServer]:
        return self.repository.paginate(args)

    def update(self, id: int, schema: ServerUpdate) -> NotificationServer:
        server = self.repository.get_by_id(id)
        return self.repository.update(
            server,
            schema.model_dump(exclude_none=True, context={"include_secrets": True}),
        )

    def create(self, schema: ServerCreate) -> NotificationServer:
        server = NotificationServer(**schema.model_dump(exclude={"credentials"}))

        if schema.credentials:
            credentials = Credentials(
                **schema.credentials.model_dump(context={"include_secrets": True})
            )
            server.credentials = credentials
        return self.repository.create(server)

    def delete(self, id: int):
        print(id)
        server = self.repository.get_by_id(id)
        print(server)
        self.repository.delete(server)