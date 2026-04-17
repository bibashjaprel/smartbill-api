from contextlib import contextmanager
from typing import Generator

from sqlalchemy.orm import Session


@contextmanager
def write_transaction(db: Session) -> Generator[None, None, None]:
    try:
        yield
        db.commit()
    except Exception:
        db.rollback()
        raise
