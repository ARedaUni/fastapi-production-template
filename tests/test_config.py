"""Tests for application configuration."""

import pytest
from app.core.config import get_settings


def test_config_has_basic_settings():
    """Test that config has basic required settings."""
    settings = get_settings()
    
    assert settings.PROJECT_NAME
    assert settings.VERSION
    assert settings.V1_STR == "/api/v1"


def test_config_supports_database_components():
    """Test that config has database connection components."""
    settings = get_settings()
    
    # Should have database connection components
    assert hasattr(settings, 'POSTGRES_HOST')
    assert hasattr(settings, 'POSTGRES_DB') 
    assert hasattr(settings, 'POSTGRES_USER')
    assert hasattr(settings, 'POSTGRES_PASSWORD')


def test_config_builds_database_uri():
    """Test that config builds database URI from components."""
    settings = get_settings()
    
    # Should build database URI
    assert hasattr(settings, 'DATABASE_URL')
    # Should be a string when accessed
    assert isinstance(settings.DATABASE_URL, str)


def test_config_supports_redis_components():
    """Test that config has Redis connection components."""
    settings = get_settings()
    
    # Should have Redis connection components  
    assert hasattr(settings, 'REDIS_HOST')
    assert hasattr(settings, 'REDIS_PORT')


def test_config_has_environment_setting():
    """Test that config has environment setting for production."""
    settings = get_settings()
    
    # Should have environment setting
    assert hasattr(settings, 'ENVIRONMENT')
    assert settings.ENVIRONMENT in ["development", "testing", "production"]


def test_config_has_security_settings():
    """Test that config has security settings with SecretStr."""
    settings = get_settings()
    
    # Should have secret key
    assert hasattr(settings, 'SECRET_KEY')
    # Secret key should be SecretStr type
    assert hasattr(settings.SECRET_KEY, 'get_secret_value')
    # Should have non-empty secret when accessed
    assert len(settings.SECRET_KEY.get_secret_value()) > 0


def test_config_has_oauth2_settings():
    """Test that config has OAuth2 token settings."""
    settings = get_settings()
    
    # Should have OAuth2 token expiry setting
    assert hasattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES')
    assert isinstance(settings.ACCESS_TOKEN_EXPIRE_MINUTES, int)
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0
    
    # Should have algorithm setting for JWT
    assert hasattr(settings, 'ALGORITHM')
    assert isinstance(settings.ALGORITHM, str)


def test_settings_function_is_cached():
    """Test that get_settings returns the same instance (cached)."""
    settings1 = get_settings()
    settings2 = get_settings()
    
    # Should be the same instance due to caching
    assert settings1 is settings2 