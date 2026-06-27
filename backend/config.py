from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "logisense"
    postgres_user: str = "logisense"
    postgres_password: str = "logisense_secure_2024"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = "redis_secure_2024"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "logisense_minio"
    minio_secret_key: str = "minio_secure_2024"

    jwt_secret_key: str = "change_this_to_a_long_random_secret_at_least_32_chars"
    jwt_algorithm: str = "HS256"
    jwt_access_expire_minutes: int = 480
    jwt_refresh_expire_days: int = 7

    anthropic_api_key: str = ""
    demo_mode: bool = True

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sync_database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/0"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
