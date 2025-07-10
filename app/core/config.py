from typing import Any, Dict, Optional, Literal
from functools import lru_cache

from pydantic import EmailStr, SecretStr, field_validator, computed_field, BeforeValidator
from pydantic_settings import BaseSettings
from typing_extensions import Annotated


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


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
    DATABASE_URL: str = None
    TEST_DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    
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
    
    # CORS settings
    BACKEND_CORS_ORIGINS: Annotated[
        list[str] | str, BeforeValidator(parse_cors)
    ] = []
    
    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        """
        Get all CORS origins with environment-specific defaults.
        
        For development: allows localhost variants
        For testing: restrictive (empty by default)
        For production: only explicitly configured origins
        """
        base_origins = []
        
        # Convert BACKEND_CORS_ORIGINS to list if it's a string
        if isinstance(self.BACKEND_CORS_ORIGINS, str):
            if self.BACKEND_CORS_ORIGINS:
                base_origins = [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]
        else:
            base_origins = [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS]
        
        # Add environment-specific defaults
        if self.ENVIRONMENT == "development":
            default_dev_origins = [
                "http://localhost:3000",  # React default
                "http://localhost:8080",  # Vue default
                "http://localhost:5173",  # Vite default
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8080",
                "http://127.0.0.1:5173"
            ]
            # Add defaults if no origins configured
            if not base_origins:
                base_origins = default_dev_origins
            else:
                # Merge with configured origins, avoiding duplicates
                all_origins = base_origins + [origin for origin in default_dev_origins if origin not in base_origins]
                base_origins = all_origins
        elif self.ENVIRONMENT == "testing":
            # For testing, only use explicitly configured origins (usually none)
            pass
        elif self.ENVIRONMENT == "production":
            # For production, only use explicitly configured origins
            if not base_origins:
                raise ValueError("BACKEND_CORS_ORIGINS must be configured for production environment")
        
        return base_origins
    
    # Security
    SECRET_KEY: SecretStr = SecretStr("your-secret-key-change-in-production")
    
    # OAuth2 / JWT settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Create settings instance once at module level
settings = get_settings()




