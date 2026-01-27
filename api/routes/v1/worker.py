from __future__ import annotations
from flask import request

from api.routes import BaseAPI
from api.services import WorkerService
from api.dtr_common.schema import WorkerCreate, WorkerUpdate


class WorkerAPI(BaseAPI[WorkerService]):

    def get(self, id: int | None = None):
        if id is None:
            paginated = self.service.paginate()
            items = [worker.to_dict() for worker in paginated.items]
            return {"pagination": paginated.pagination.model_dump(), "items": items}
        worker = self.service.get_by_id(id)
        return worker.to_dict()

    def put(self, id: int):
        data = request.json
        schema = WorkerUpdate(**data)
        worker = self.service.update(id, schema)
        self.service.commit()
        return worker.to_dict()

    def post(self):
        data = request.json
        schema = WorkerCreate(**data)
        worker = self.service.create(schema)
        self.service.commit()
        return worker.to_dict()

    def delete(self, id: int):
        self.service.delete(id)
        self.service.commit()


WorkerAPI.register(
    "workers",
    url_prefix="workers",
    rules=[
        {"route": "/", "defaults": {"id": None}, "methods": ["GET", "POST"]},
        {"route": "/<int:id>", "methods": ["GET", "PUT", "DELETE"]},
    ],
)


# @bp.route("/configuration/worker", methods=["GET"])
# def worker():
#     """
#     Get next available transfer request for worker processing.
#     This endpoint ensures atomicity by using a transaction with row-level locking
#     (SELECT ... FOR UPDATE) to prevent the same task from being assigned to
#     multiple workers simultaneously.
#     """
#     logger = current_app.logger
#     ngparams = get_params()
#     if ngparams is None or ngparams.mode == Mode.OFFLINE:
#         logger.info("API in OFFLINE mode, no request assigned.")
#         return {"request": {}}

#     worker_storage = request.args.get("size", type=float)
#     if worker_storage is None or worker_storage <= 0:
#         raise ValueError("Worker size not specified in query parameters or invalid")

#     # The transaction is implicitly managed by Flask-SQLAlchemy per request.
#     # We perform all operations within this single request context.
#     params = {"size": worker_storage, "state": StateEnum.QUEUED}
#     next_request = get_next_request(params, db_session=db.session)

#     if next_request:
#         # This all happens before the transaction is committed.
#         # The row remains locked until the commit.
#         nstate = State(state=StateEnum.IN_PROGRESS)
#         next_request.states.append(nstate)
#         next_request.start = datetime.datetime.now(datetime.timezone.utc)

#         db.session.flush()

#         # The request object is still bound to the session, so we can serialize it.
#         response_data = next_request.to_dict()

#         # Commit the transaction to finalize the state change and release the lock.
#         db.session.commit()

#         logger.info(f"Assigned transfer request {next_request.uid} to worker")
#         return {"request": response_data}

#     # No request was found. No need to commit anything.
#     logger.debug("No available transfer requests for worker")
#     return {"request": {}}
