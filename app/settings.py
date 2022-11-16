from pydantic import BaseSettings


class Settings(BaseSettings):
    sqlite: bool = False

    postgres_password: str = ""
    postgres_user: str = "mj"
    postgres_name: str = "mj"
    postgres_host: str = "mj_db"
    postgres_port: int = 5432

    max_grades: int = 100
    max_candidates: int = 1000
    max_voters: int = 1_000_000

    class Config:
        env_file = ".env"


settings = Settings()
