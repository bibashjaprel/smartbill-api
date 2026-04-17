from datetime import datetime, timezone
from typing import Any, Optional


def success_response(data: Any, request_id: Optional[str] = None, meta: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    payload_meta = {
        "request_id": request_id,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if meta:
        payload_meta.update(meta)

    return {
        "status": "success",
        "data": data,
        "meta": payload_meta,
    }


def paginated_response(
    items: list[Any],
    total: int,
    limit: int,
    skip: int,
    request_id: Optional[str] = None,
) -> dict[str, Any]:
    return success_response(
        data=items,
        request_id=request_id,
        meta={
            "pagination": {
                "total": total,
                "limit": limit,
                "skip": skip,
                "has_more": skip + limit < total,
            }
        },
    )
