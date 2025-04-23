import random
import sys
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    sqlite: bool = False

    secret: str = ""
    aes_key: bytes = b""

    postgres_password: str = ""
    postgres_user: str = "mj"
    postgres_name: str = "mj"
    postgres_host: str = "mj_db"
    postgres_port: int = 5432

    max_grades: int = 100
    max_candidates: int = 1000
    max_voters: int = 1_000_000

    allowed_origins: list[str] = ["http://localhost"]

    class Config:
        env_file = ".env"
        extra="ignore"


def get_random_key(length: int, rng: random.Random) -> bytes:
    """
    Inspired from https://stackoverflow.com/a/37357035/4986615
    """
    if length == 0:
        return b""
    integer = rng.getrandbits(length * 8)
    result = integer.to_bytes(length, sys.byteorder)
    return result


settings = Settings()

if settings.secret == "":
    raise RuntimeError("Please generate a secret key")

rng = random.Random(settings.secret)
settings.aes_key = get_random_key(16, rng)
