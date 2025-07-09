from typing import Any, Dict, Optional, Literal
from functools import lru_cache

from pydantic import EmailStr, SecretStr, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
    
    # API settings
    PROJECT_NAME: str = "FastAPI Template"
    VERSION: str = "0.1.0"
    V1_STR: str = "/api/v1"
    
    # Database components 
    POSTGRES_HOST: str = "localhost"
    POSTGRES_DB: str = "fastapi_db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: SecretStr = SecretStr("postgres")
    DATABASE_URL: Optional[str] = None
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v: Optional[str], info) -> str:
        if isinstance(v, str):
            return v
        values = info.data if hasattr(info, 'data') else {}
        password: SecretStr = values.get("POSTGRES_PASSWORD", SecretStr(""))
        return "postgresql+asyncpg://{user}:{password}@{host}/{db}".format(
            user=values.get("POSTGRES_USER"),
            password=password.get_secret_value(),
            host=values.get("POSTGRES_HOST"),
            db=values.get("POSTGRES_DB"),
        )
    
    # Redis components
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # Environment
    ENVIRONMENT: Literal["development", "testing", "production"] = "development"
    
    # Security
    SECRET_KEY: SecretStr = SecretStr("your-secret-key-change-in-production")
    
    # OAuth2 / JWT settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Create settings instance once at module level
settings = get_settings()




