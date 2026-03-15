from unittest.mock import Mock


def make_pagination(items: list, total: int, page: int = 1, page_size: int = 10):
    pagination = Mock()

    pagination.model_dump.return_value = {
        "page": page,
        "page_size": page_size,
        "total": total,
    }

    paginated = Mock()

    paginated.pagination = pagination
    paginated.items = items
    return paginated
