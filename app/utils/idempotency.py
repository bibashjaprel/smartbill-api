from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from ..models.idempotency_key import IdempotencyKey


def build_request_hash(payload: Any) -> str:
    return sha256(payload.model_dump_json().encode("utf-8")).hexdigest()


def get_active_idempotency_record(
    db: Session,
    *,
    key: str,
    endpoint: str,
    user_id: UUID,
    shop_id: UUID,
) -> IdempotencyKey | None:
    return (
        db.query(IdempotencyKey)
        .filter(
            IdempotencyKey.key == key,
            IdempotencyKey.endpoint == endpoint,
            IdempotencyKey.user_id == user_id,
            IdempotencyKey.shop_id == shop_id,
            IdempotencyKey.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )
