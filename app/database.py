from __future__ import annotations

from contextvars import ContextVar
from urllib.parse import quote
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from .settings import settings


if settings.sqlite:
    database_url = "sqlite:///./main.db"
    engine = create_engine(database_url, connect_args={"check_same_thread": False})

else:
    database_url = (
        "postgresql+psycopg2://"
        f"{settings.postgres_user}:{quote(settings.postgres_password)}"
        f"@{settings.postgres_host}:{settings.postgres_port}"
        f"/{settings.postgres_name}"
    )
    engine = create_engine(database_url)

SessionLocal: sessionmaker = sessionmaker(  # type: ignore
    autocommit=False, autoflush=False, bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_session: ContextVar[Session] = ContextVar('db_session')
