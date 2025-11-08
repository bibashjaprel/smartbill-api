from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

# Create engine with updated configuration for SQLAlchemy 2.0
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID
import uuid

class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            if isinstance(value, uuid.UUID):
                return value
            else:
                return uuid.UUID(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value

engine = create_engine(
    settings.DATABASE_URL,
    # Connection pool settings
    pool_pre_ping=True,
    pool_recycle=300
)

# Create session factory
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False
)

# New style declarative base for SQLAlchemy 2.0
Base = declarative_base()

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create database tables from SQLAlchemy models.

    This imports the models package to ensure all model classes are registered
    on the declarative `Base` metadata, then runs `create_all` on the engine.
    """
    # Import models so they register on Base.metadata
    try:
        # Importing the package will import submodules which define models
        import app.models  # noqa: F401
    except Exception:
        # If import fails, still attempt create_all (models may already be imported)
        pass

    Base.metadata.create_all(bind=engine)
