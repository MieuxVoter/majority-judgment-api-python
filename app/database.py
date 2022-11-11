from urllib.parse import quote
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .settings import settings


# database_url = (
#     "postgresql+psycopg2://"
#     f"{settings.postgres_name}:{quote(settings.postgres_password)}"
#     f"@{settings.postgres_host}:{settings.postgres_port}"
#     f"/{settings.postgres_db}"
# )
# engine = create_engine(database_url)

database_url = "sqlite:///./main.db"
engine = create_engine(
    database_url, connect_args={"check_same_thread": False}
)

SessionLocal: sessionmaker = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
