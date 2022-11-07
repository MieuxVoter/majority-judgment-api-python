from pydantic import BaseSettings


class Settings(BaseSettings):
    postgres_password: str
    postgres_db: str = "mj"
    postgres_name: str = "mj"
    postgres_host: str = "mj_db"
    postgres_port: int = 5432


settings = Settings()
