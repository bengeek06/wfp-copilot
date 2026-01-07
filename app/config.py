# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro
"""Application configuration module.

This module provides configuration classes for different environments
(development, testing, integration, staging, production) with proper
secret management and environment variable loading.
"""

import os
from datetime import timedelta
from typing import Final


class Config:
    """Base configuration class.

    Contains common configuration shared across all environments.
    Loads sensitive values from environment variables.

    Attributes:
        SECRET_KEY: Secret key for Flask sessions.
        SQLALCHEMY_DATABASE_URI: Database connection string.
        SQLALCHEMY_TRACK_MODIFICATIONS: Disable modification tracking.
        SQLALCHEMY_ECHO: Enable SQL query logging.
        JWT_SECRET_KEY: Secret key for JWT token encryption.
        JWT_ALGORITHM: Algorithm for JWT encoding/decoding.
        JWT_ACCESS_TOKEN_EXPIRES: Token validity duration.
        JWT_COOKIE_NAME: Name of the cookie storing JWT token.
        JWT_COOKIE_SECURE: Whether to use secure cookies (HTTPS only).
        JWT_COOKIE_HTTPONLY: Prevent JavaScript access to cookies.
        JWT_COOKIE_SAMESITE: SameSite cookie attribute.
        GUARDIAN_SERVICE_URL: URL of the Guardian service for RBAC.
        GUARDIAN_SERVICE_TIMEOUT: Timeout for Guardian API calls.
        GUARDIAN_SERVICE_API_KEY: API key for Guardian service.
        IDENTITY_SERVICE_URL: URL of the Identity service.
        IDENTITY_SERVICE_TIMEOUT: Timeout for Identity API calls.
        IDENTITY_SERVICE_API_KEY: API key for Identity service.
        METRICS_API_KEY: API key for metrics endpoint.
        PROMETHEUS_METRICS_ENABLED: Enable Prometheus metrics collection.
        SERVICE_NAME: Name of the service.
        SERVICE_VERSION: Version of the service.
        SERVICE_PORT: Port on which the service runs.
        LOG_LEVEL: Logging level.
        LOG_FORMAT: Logging format (json or text).
        ENABLE_REQUEST_LOGGING: Enable request/response logging.
        ENABLE_CORRELATION_ID: Enable correlation ID tracking.
        CORS_ORIGINS: Allowed CORS origins.
        CORS_ALLOW_CREDENTIALS: Allow credentials in CORS requests.
        RATE_LIMIT_ENABLED: Enable rate limiting.
        RATE_LIMIT_STORAGE_URL: Storage backend for rate limiting.
        SECURITY_HEADERS_ENABLED: Enable security headers.
        SECURITY_HEADERS: Security headers to add to responses.
    """

    # Flask Configuration
    SECRET_KEY: Final[str] = os.environ.get(
        "SECRET_KEY", "dev-secret-change-in-production"
    )
    DEBUG: bool = False
    TESTING: bool = False

    # Database Configuration
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        "DATABASE_URL", "sqlite:///data/app.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: Final[bool] = False
    SQLALCHEMY_ECHO: bool = False
    SQLALCHEMY_POOL_SIZE: int = int(os.environ.get("SQLALCHEMY_POOL_SIZE", "5"))
    SQLALCHEMY_MAX_OVERFLOW: int = int(os.environ.get("SQLALCHEMY_MAX_OVERFLOW", "10"))
    SQLALCHEMY_POOL_TIMEOUT: int = int(os.environ.get("SQLALCHEMY_POOL_TIMEOUT", "30"))
    SQLALCHEMY_POOL_RECYCLE: int = int(
        os.environ.get("SQLALCHEMY_POOL_RECYCLE", "3600")
    )

    # JWT Configuration
    JWT_SECRET_KEY: str = os.environ.get(
        "JWT_SECRET_KEY", "jwt-secret-change-in-production"
    )
    JWT_ALGORITHM: Final[str] = os.environ.get("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(
        seconds=int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES", "3600"))
    )

    # JWT Cookie Configuration
    JWT_COOKIE_NAME: Final[str] = os.environ.get("JWT_COOKIE_NAME", "access_token")
    JWT_COOKIE_SECURE: bool = (
        os.environ.get("JWT_COOKIE_SECURE", "false").lower() == "true"
    )
    JWT_COOKIE_HTTPONLY: Final[bool] = True
    JWT_COOKIE_SAMESITE: Final[str] = os.environ.get("JWT_COOKIE_SAMESITE", "Lax")

    # Guardian Service Configuration (RBAC)
    GUARDIAN_SERVICE_URL: str = os.environ.get(
        "GUARDIAN_SERVICE_URL", "http://localhost:5001"
    )
    GUARDIAN_SERVICE_TIMEOUT: int = int(os.environ.get("GUARDIAN_SERVICE_TIMEOUT", "5"))
    GUARDIAN_SERVICE_API_KEY: str = os.environ.get("GUARDIAN_SERVICE_API_KEY", "")

    # Identity Service Configuration
    IDENTITY_SERVICE_URL: str = os.environ.get(
        "IDENTITY_SERVICE_URL", "http://localhost:5002"
    )
    IDENTITY_SERVICE_TIMEOUT: int = int(os.environ.get("IDENTITY_SERVICE_TIMEOUT", "5"))
    IDENTITY_SERVICE_API_KEY: str = os.environ.get("IDENTITY_SERVICE_API_KEY", "")

    # Metrics Configuration
    METRICS_API_KEY: str = os.environ.get("METRICS_API_KEY", "")
    PROMETHEUS_METRICS_ENABLED: bool = (
        os.environ.get("PROMETHEUS_METRICS_ENABLED", "true").lower() == "true"
    )

    # Service Configuration
    SERVICE_NAME: Final[str] = os.environ.get("SERVICE_NAME", "wfp-flask-template")
    SERVICE_VERSION: Final[str] = os.environ.get("SERVICE_VERSION", "1.0.0")
    SERVICE_PORT: int = int(os.environ.get("SERVICE_PORT", "5000"))

    # Logging Configuration
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.environ.get("LOG_FORMAT", "json")
    LOG_FILE: str = os.environ.get("LOG_FILE", "logs/app.log")
    ENABLE_REQUEST_LOGGING: bool = (
        os.environ.get("ENABLE_REQUEST_LOGGING", "true").lower() == "true"
    )
    ENABLE_CORRELATION_ID: bool = (
        os.environ.get("ENABLE_CORRELATION_ID", "true").lower() == "true"
    )

    # CORS Configuration
    CORS_ORIGINS: list[str] = os.environ.get(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:5000"
    ).split(",")
    CORS_ALLOW_CREDENTIALS: Final[bool] = (
        os.environ.get("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
    )

    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED: bool = (
        os.environ.get("RATE_LIMIT_ENABLED", "true").lower() == "true"
    )
    RATE_LIMIT_STORAGE_URL: str = os.environ.get("RATE_LIMIT_STORAGE_URL", "memory://")

    # Security Headers
    SECURITY_HEADERS_ENABLED: bool = (
        os.environ.get("SECURITY_HEADERS_ENABLED", "true").lower() == "true"
    )
    SECURITY_HEADERS: Final[dict[str, str]] = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
    }

    # Feature Flags
    ENABLE_SWAGGER_UI: bool = (
        os.environ.get("ENABLE_SWAGGER_UI", "true").lower() == "true"
    )
    ENABLE_HEALTH_CHECK: Final[bool] = True
    ENABLE_METRICS_ENDPOINT: Final[bool] = True


class DevelopmentConfig(Config):
    """Development environment configuration.

    Enables debugging, SQL query logging, and uses SQLite database.
    Suitable for local development with hot-reload enabled.
    """

    DEBUG: bool = True
    SQLALCHEMY_ECHO: bool = True
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "DEBUG")
    LOG_FORMAT: str = "text"
    JWT_COOKIE_SECURE: bool = False


class TestingConfig(Config):
    """Testing environment configuration.

    Uses in-memory SQLite database for fast test execution.
    Disables CSRF protection and external service calls.
    """

    TESTING: bool = True
    DEBUG: bool = True
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        "TEST_DATABASE_URL", "sqlite:///:memory:"
    )
    SQLALCHEMY_ECHO: bool = False
    LOG_LEVEL: str = "WARNING"
    LOG_FORMAT: str = "text"
    JWT_COOKIE_SECURE: bool = False
    RATE_LIMIT_ENABLED: bool = False
    PROMETHEUS_METRICS_ENABLED: bool = False
    ENABLE_REQUEST_LOGGING: bool = False
    WTF_CSRF_ENABLED: bool = False


class IntegrationConfig(Config):
    """Integration testing environment configuration.

    Uses PostgreSQL database for realistic integration tests.
    Mirrors staging configuration but with test-specific settings.
    """

    DEBUG: bool = True
    TESTING: bool = True
    SQLALCHEMY_ECHO: bool = True
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "DEBUG")
    LOG_FORMAT: str = "text"
    JWT_COOKIE_SECURE: bool = False


class StagingConfig(Config):
    """Staging environment configuration.

    Pre-production environment with production-like settings
    but with additional debugging capabilities enabled.
    """

    DEBUG: bool = False
    SQLALCHEMY_ECHO: bool = False
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "json"
    JWT_COOKIE_SECURE: bool = True
    ENABLE_SWAGGER_UI: bool = True


class ProductionConfig(Config):
    """Production environment configuration.

    Secure configuration for production deployment with all
    debugging features disabled and strict security settings.
    """

    DEBUG: bool = False
    TESTING: bool = False
    SQLALCHEMY_ECHO: bool = False
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "WARNING")
    LOG_FORMAT: str = "json"
    JWT_COOKIE_SECURE: bool = True
    ENABLE_SWAGGER_UI: bool = False

    # Enforce environment variables in production
    def __init__(self) -> None:
        """Validate that critical environment variables are set in production."""
        required_vars = [
            "SECRET_KEY",
            "JWT_SECRET_KEY",
            "DATABASE_URL",
            "GUARDIAN_SERVICE_URL",
            "GUARDIAN_SERVICE_API_KEY",
            "IDENTITY_SERVICE_URL",
            "IDENTITY_SERVICE_API_KEY",
            "METRICS_API_KEY",
        ]

        missing_vars = [var for var in required_vars if not os.environ.get(var)]

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables in production: {', '.join(missing_vars)}"
            )

        # Validate that default secrets are not used in production
        secret_key = os.environ.get("SECRET_KEY", "")
        jwt_secret_key = os.environ.get("JWT_SECRET_KEY", "")

        if secret_key == "dev-secret-change-in-production":
            raise ValueError("SECRET_KEY must be changed in production")

        if jwt_secret_key == "jwt-secret-change-in-production":
            raise ValueError("JWT_SECRET_KEY must be changed in production")

        super().__init__()


# Configuration mapping for easy access
config_by_name: Final[dict[str, type[Config]]] = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "integration": IntegrationConfig,
    "staging": StagingConfig,
    "production": ProductionConfig,
}
