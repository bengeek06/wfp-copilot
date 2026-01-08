# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro
"""Unit tests for application configuration.

This module tests all configuration classes and ensures proper
environment variable loading, default values, and security validations.
"""

import os
from datetime import timedelta

import pytest

from app.config import (
    Config,
    DevelopmentConfig,
    IntegrationConfig,
    ProductionConfig,
    StagingConfig,
    TestingConfig,
    config_by_name,
)


class TestBaseConfig:
    """Tests for base Config class."""

    def test_base_config_has_required_attributes(self) -> None:
        """Test that base config contains all required attributes.

        Given: Base Config class
        When: Accessing configuration attributes
        Then: All required attributes are present
        """
        config = Config()

        # Flask configuration
        assert hasattr(config, "SECRET_KEY")
        assert hasattr(config, "DEBUG")
        assert hasattr(config, "TESTING")

        # Database configuration
        assert hasattr(config, "SQLALCHEMY_DATABASE_URI")
        assert hasattr(config, "SQLALCHEMY_TRACK_MODIFICATIONS")

        # JWT configuration
        assert hasattr(config, "JWT_SECRET_KEY")
        assert hasattr(config, "JWT_ALGORITHM")
        assert hasattr(config, "JWT_ACCESS_TOKEN_EXPIRES")

        # Service configuration
        assert hasattr(config, "GUARDIAN_SERVICE_URL")
        assert hasattr(config, "IDENTITY_SERVICE_URL")
        assert hasattr(config, "SERVICE_NAME")

    def test_jwt_access_token_expires_is_timedelta(self) -> None:
        """Test that JWT_ACCESS_TOKEN_EXPIRES is a timedelta.

        Given: Base Config class
        When: Accessing JWT_ACCESS_TOKEN_EXPIRES
        Then: Value is a timedelta instance
        """
        config = Config()

        assert isinstance(config.JWT_ACCESS_TOKEN_EXPIRES, timedelta)

    def test_security_headers_configuration(self) -> None:
        """Test that security headers are properly configured.

        Given: Base Config class
        When: Accessing SECURITY_HEADERS
        Then: All required security headers are present
        """
        config = Config()

        assert "X-Content-Type-Options" in config.SECURITY_HEADERS
        assert "X-Frame-Options" in config.SECURITY_HEADERS
        assert "X-XSS-Protection" in config.SECURITY_HEADERS
        assert "Strict-Transport-Security" in config.SECURITY_HEADERS
        assert "Content-Security-Policy" in config.SECURITY_HEADERS

    def test_cors_origins_is_list(self) -> None:
        """Test that CORS_ORIGINS is properly parsed as list.

        Given: Base Config class with CORS_ORIGINS environment variable
        When: Accessing CORS_ORIGINS
        Then: Value is a list of origins
        """
        config = Config()

        assert isinstance(config.CORS_ORIGINS, list)
        assert len(config.CORS_ORIGINS) > 0


class TestDevelopmentConfig:
    """Tests for DevelopmentConfig class."""

    def test_development_debug_enabled(self) -> None:
        """Test that DEBUG is enabled in development.

        Given: DevelopmentConfig instance
        When: Accessing DEBUG setting
        Then: DEBUG is True
        """
        config = DevelopmentConfig()

        assert config.DEBUG is True

    def test_development_sqlalchemy_echo_enabled(self) -> None:
        """Test that SQL query logging is enabled in development.

        Given: DevelopmentConfig instance
        When: Accessing SQLALCHEMY_ECHO setting
        Then: SQLALCHEMY_ECHO is True
        """
        config = DevelopmentConfig()

        assert config.SQLALCHEMY_ECHO is True

    def test_development_log_level_is_debug(self) -> None:
        """Test that log level is DEBUG in development.

        Given: DevelopmentConfig instance
        When: Accessing LOG_LEVEL setting
        Then: LOG_LEVEL is DEBUG
        """
        config = DevelopmentConfig()

        assert config.LOG_LEVEL == "DEBUG"

    def test_development_jwt_cookie_not_secure(self) -> None:
        """Test that JWT cookies are not secure in development.

        Given: DevelopmentConfig instance (local HTTP development)
        When: Accessing JWT_COOKIE_SECURE setting
        Then: JWT_COOKIE_SECURE is False
        """
        config = DevelopmentConfig()

        assert config.JWT_COOKIE_SECURE is False


class TestTestingConfig:
    """Tests for TestingConfig class."""

    def test_testing_flag_enabled(self) -> None:
        """Test that TESTING flag is enabled.

        Given: TestingConfig instance
        When: Accessing TESTING setting
        Then: TESTING is True
        """
        config = TestingConfig()

        assert config.TESTING is True

    def test_testing_uses_in_memory_database(self) -> None:
        """Test that testing uses in-memory SQLite database.

        Given: TestingConfig instance
        When: Accessing SQLALCHEMY_DATABASE_URI setting
        Then: Database URI points to in-memory SQLite
        """
        config = TestingConfig()

        assert ":memory:" in config.SQLALCHEMY_DATABASE_URI

    def test_testing_rate_limit_disabled(self) -> None:
        """Test that rate limiting is disabled in testing.

        Given: TestingConfig instance
        When: Accessing RATE_LIMIT_ENABLED setting
        Then: RATE_LIMIT_ENABLED is False
        """
        config = TestingConfig()

        assert config.RATE_LIMIT_ENABLED is False

    def test_testing_request_logging_disabled(self) -> None:
        """Test that request logging is disabled in testing.

        Given: TestingConfig instance
        When: Accessing ENABLE_REQUEST_LOGGING setting
        Then: ENABLE_REQUEST_LOGGING is False
        """
        config = TestingConfig()

        assert config.ENABLE_REQUEST_LOGGING is False


class TestIntegrationConfig:
    """Tests for IntegrationConfig class."""

    def test_integration_debug_enabled(self) -> None:
        """Test that DEBUG is enabled in integration tests.

        Given: IntegrationConfig instance
        When: Accessing DEBUG setting
        Then: DEBUG is True
        """
        config = IntegrationConfig()

        assert config.DEBUG is True

    def test_integration_testing_enabled(self) -> None:
        """Test that TESTING flag is enabled in integration tests.

        Given: IntegrationConfig instance
        When: Accessing TESTING setting
        Then: TESTING is True
        """
        config = IntegrationConfig()

        assert config.TESTING is True


class TestStagingConfig:
    """Tests for StagingConfig class."""

    def test_staging_debug_disabled(self) -> None:
        """Test that DEBUG is disabled in staging.

        Given: StagingConfig instance
        When: Accessing DEBUG setting
        Then: DEBUG is False
        """
        config = StagingConfig()

        assert config.DEBUG is False

    def test_staging_jwt_cookie_secure_enabled(self) -> None:
        """Test that JWT cookies are secure in staging.

        Given: StagingConfig instance (HTTPS environment)
        When: Accessing JWT_COOKIE_SECURE setting
        Then: JWT_COOKIE_SECURE is True
        """
        config = StagingConfig()

        assert config.JWT_COOKIE_SECURE is True

    def test_staging_swagger_ui_enabled(self) -> None:
        """Test that Swagger UI is enabled in staging.

        Given: StagingConfig instance
        When: Accessing ENABLE_SWAGGER_UI setting
        Then: ENABLE_SWAGGER_UI is True
        """
        config = StagingConfig()

        assert config.ENABLE_SWAGGER_UI is True


class TestProductionConfig:
    """Tests for ProductionConfig class."""

    def test_production_debug_disabled(self) -> None:
        """Test that DEBUG is disabled in production.

        Given: ProductionConfig instance
        When: Accessing DEBUG setting
        Then: DEBUG is False
        """
        # Set required environment variables for production
        required_vars = {
            "SECRET_KEY": "prod-secret-key",
            "JWT_SECRET_KEY": "prod-jwt-secret",
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
            "GUARDIAN_SERVICE_URL": "http://guardian:5001",
            "GUARDIAN_SERVICE_API_KEY": "guardian-key",
            "IDENTITY_SERVICE_URL": "http://identity:5002",
            "IDENTITY_SERVICE_API_KEY": "identity-key",
            "METRICS_API_KEY": "metrics-key",
        }

        for key, value in required_vars.items():
            os.environ[key] = value

        try:
            config = ProductionConfig()
            assert config.DEBUG is False
        finally:
            # Cleanup environment variables
            for key in required_vars:
                os.environ.pop(key, None)

    def test_production_swagger_ui_disabled(self) -> None:
        """Test that Swagger UI is disabled in production.

        Given: ProductionConfig instance
        When: Accessing ENABLE_SWAGGER_UI setting
        Then: ENABLE_SWAGGER_UI is False
        """
        required_vars = {
            "SECRET_KEY": "prod-secret-key",
            "JWT_SECRET_KEY": "prod-jwt-secret",
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
            "GUARDIAN_SERVICE_URL": "http://guardian:5001",
            "GUARDIAN_SERVICE_API_KEY": "guardian-key",
            "IDENTITY_SERVICE_URL": "http://identity:5002",
            "IDENTITY_SERVICE_API_KEY": "identity-key",
            "METRICS_API_KEY": "metrics-key",
        }

        for key, value in required_vars.items():
            os.environ[key] = value

        try:
            config = ProductionConfig()
            assert config.ENABLE_SWAGGER_UI is False
        finally:
            for key in required_vars:
                os.environ.pop(key, None)

    def test_production_requires_environment_variables(self) -> None:
        """Test that ProductionConfig validates required environment variables.

        Given: ProductionConfig instantiation without required variables
        When: Creating ProductionConfig instance
        Then: ValueError is raised with missing variable names
        """
        # Clear environment variables
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

        original_values = {}
        for key in required_vars:
            original_values[key] = os.environ.pop(key, None)

        try:
            with pytest.raises(
                ValueError, match="Missing required environment variables"
            ):
                ProductionConfig()
        finally:
            # Restore environment variables
            for key, value in original_values.items():
                if value is not None:
                    os.environ[key] = value

    def test_production_rejects_default_secret_key(self) -> None:
        """Test that ProductionConfig rejects default SECRET_KEY.

        Given: ProductionConfig with default SECRET_KEY value
        When: Creating ProductionConfig instance
        Then: ValueError is raised
        """
        os.environ["SECRET_KEY"] = "dev-secret-change-in-production"  # nosec B105
        os.environ["JWT_SECRET_KEY"] = "prod-jwt-secret"  # nosec B105
        os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost/db"
        os.environ["GUARDIAN_SERVICE_URL"] = "http://guardian:5001"
        os.environ["GUARDIAN_SERVICE_API_KEY"] = "guardian-key"
        os.environ["IDENTITY_SERVICE_URL"] = "http://identity:5002"
        os.environ["IDENTITY_SERVICE_API_KEY"] = "identity-key"
        os.environ["METRICS_API_KEY"] = "metrics-key"

        try:
            with pytest.raises(ValueError, match="SECRET_KEY must be changed"):
                ProductionConfig()
        finally:
            for key in [
                "SECRET_KEY",
                "JWT_SECRET_KEY",
                "DATABASE_URL",
                "GUARDIAN_SERVICE_URL",
                "GUARDIAN_SERVICE_API_KEY",
                "IDENTITY_SERVICE_URL",
                "IDENTITY_SERVICE_API_KEY",
                "METRICS_API_KEY",
            ]:
                os.environ.pop(key, None)

    def test_production_rejects_default_jwt_secret_key(self) -> None:
        """Test that ProductionConfig rejects default JWT_SECRET_KEY.

        Given: ProductionConfig with default JWT_SECRET_KEY value
        When: Creating ProductionConfig instance
        Then: ValueError is raised
        """
        os.environ["SECRET_KEY"] = "prod-secret-key"  # nosec B105
        os.environ["JWT_SECRET_KEY"] = "jwt-secret-change-in-production"  # nosec B105
        os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost/db"
        os.environ["GUARDIAN_SERVICE_URL"] = "http://guardian:5001"
        os.environ["GUARDIAN_SERVICE_API_KEY"] = "guardian-key"
        os.environ["IDENTITY_SERVICE_URL"] = "http://identity:5002"
        os.environ["IDENTITY_SERVICE_API_KEY"] = "identity-key"
        os.environ["METRICS_API_KEY"] = "metrics-key"

        try:
            with pytest.raises(ValueError, match="JWT_SECRET_KEY must be changed"):
                ProductionConfig()
        finally:
            for key in [
                "SECRET_KEY",
                "JWT_SECRET_KEY",
                "DATABASE_URL",
                "GUARDIAN_SERVICE_URL",
                "GUARDIAN_SERVICE_API_KEY",
                "IDENTITY_SERVICE_URL",
                "IDENTITY_SERVICE_API_KEY",
                "METRICS_API_KEY",
            ]:
                os.environ.pop(key, None)


class TestConfigMapping:
    """Tests for config_by_name mapping."""

    def test_config_by_name_contains_all_environments(self) -> None:
        """Test that config_by_name contains all environment configurations.

        Given: config_by_name dictionary
        When: Checking available configurations
        Then: All environment configs are present
        """
        assert "development" in config_by_name
        assert "testing" in config_by_name
        assert "integration" in config_by_name
        assert "staging" in config_by_name
        assert "production" in config_by_name

    def test_config_by_name_returns_correct_classes(self) -> None:
        """Test that config_by_name maps to correct configuration classes.

        Given: config_by_name dictionary
        When: Accessing configurations by name
        Then: Correct configuration classes are returned
        """
        assert config_by_name["development"] == DevelopmentConfig
        assert config_by_name["testing"] == TestingConfig
        assert config_by_name["integration"] == IntegrationConfig
        assert config_by_name["staging"] == StagingConfig
        assert config_by_name["production"] == ProductionConfig
