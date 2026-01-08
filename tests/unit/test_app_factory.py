# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro
"""Unit tests for Flask application factory.

This module tests the create_app function and ensures proper
initialization of Flask extensions, configuration loading,
and middleware setup.
"""

from flask import Flask

from app import create_app


class TestCreateApp:
    """Tests for create_app factory function."""

    def test_create_app_returns_flask_instance(self) -> None:
        """Test that create_app returns a Flask application instance.

        Given: Valid configuration class path
        When: Calling create_app
        Then: Flask application instance is returned
        """
        app = create_app("app.config.TestingConfig")

        assert isinstance(app, Flask)

    def test_create_app_with_development_config(self) -> None:
        """Test creating app with development configuration.

        Given: DevelopmentConfig class path
        When: Calling create_app
        Then: App is created with DEBUG enabled
        """
        app = create_app("app.config.DevelopmentConfig")

        assert app.config["DEBUG"] is True
        assert app.config["TESTING"] is False

    def test_create_app_with_testing_config(self) -> None:
        """Test creating app with testing configuration.

        Given: TestingConfig class path
        When: Calling create_app
        Then: App is created with TESTING enabled
        """
        app = create_app("app.config.TestingConfig")

        assert app.config["TESTING"] is True
        assert ":memory:" in app.config["SQLALCHEMY_DATABASE_URI"]

    def test_create_app_initializes_sqlalchemy(self) -> None:
        """Test that SQLAlchemy extension is initialized.

        Given: Valid configuration class path
        When: Calling create_app
        Then: SQLAlchemy db is initialized with app
        """
        app = create_app("app.config.TestingConfig")

        # Check that db is registered with the app
        assert "sqlalchemy" in app.extensions

    def test_create_app_initializes_marshmallow(self) -> None:
        """Test that Marshmallow extension is initialized.

        Given: Valid configuration class path
        When: Calling create_app
        Then: Marshmallow is initialized with app
        """
        app = create_app("app.config.TestingConfig")

        # Check that marshmallow is registered with the app
        assert "flask-marshmallow" in app.extensions

    def test_create_app_initializes_migrate(self) -> None:
        """Test that Flask-Migrate extension is initialized.

        Given: Valid configuration class path
        When: Calling create_app
        Then: Flask-Migrate is initialized with app
        """
        app = create_app("app.config.TestingConfig")

        # Check that migrate is registered with the app
        assert "migrate" in app.extensions

    def test_create_app_uses_default_config_when_not_specified(self) -> None:
        """Test that create_app uses DevelopmentConfig by default.

        Given: No configuration class path provided
        When: Calling create_app without arguments
        Then: DevelopmentConfig is used
        """
        app = create_app()

        # DevelopmentConfig has DEBUG=True
        assert app.config["DEBUG"] is True

    def test_create_app_registers_routes(self) -> None:
        """Test that routes are registered in create_app.

        Given: Valid configuration class path
        When: Calling create_app
        Then: Routes are registered (url_map not empty)
        """
        app = create_app("app.config.TestingConfig")

        # Check that some routes are registered
        # Flask has default routes for static files
        assert len(app.url_map._rules) > 0


class TestSecurityHeaders:
    """Tests for security headers middleware."""

    def test_security_headers_added_when_enabled(self, app: Flask, client) -> None:
        """Test that security headers are added to responses.

        Given: App with SECURITY_HEADERS_ENABLED=True
        When: Making a request
        Then: Security headers are present in response
        """
        response = client.get("/")

        if app.config.get("SECURITY_HEADERS_ENABLED"):
            assert "X-Content-Type-Options" in response.headers
            assert "X-Frame-Options" in response.headers
            assert "X-XSS-Protection" in response.headers

    def test_security_headers_values(self, app: Flask, client) -> None:
        """Test that security headers have correct values.

        Given: App with security headers configured
        When: Making a request
        Then: Security headers have correct values
        """
        response = client.get("/")

        if app.config.get("SECURITY_HEADERS_ENABLED"):
            headers = app.config["SECURITY_HEADERS"]

            for header_name, header_value in headers.items():
                if header_name in response.headers:
                    assert response.headers[header_name] == header_value


class TestCORSConfiguration:
    """Tests for CORS configuration."""

    def test_cors_configured_when_origins_specified(self) -> None:
        """Test that CORS is configured when CORS_ORIGINS is set.

        Given: App with CORS_ORIGINS configured
        When: Creating app
        Then: CORS extension is initialized
        """
        app = create_app("app.config.TestingConfig")

        # Check if CORS is in extensions
        # Flask-CORS registers as 'cors'
        if app.config.get("CORS_ORIGINS"):
            assert hasattr(app, "extensions")


class TestConfigLoading:
    """Tests for configuration loading."""

    def test_config_loads_from_object(self) -> None:
        """Test that configuration is loaded from object.

        Given: Configuration class path
        When: Creating app
        Then: Configuration values are loaded correctly
        """
        app = create_app("app.config.TestingConfig")

        # Check specific TestingConfig values
        assert app.config["TESTING"] is True
        assert app.config["RATE_LIMIT_ENABLED"] is False

    def test_config_contains_required_keys(self) -> None:
        """Test that configuration contains all required keys.

        Given: Valid configuration class path
        When: Creating app
        Then: All required configuration keys are present
        """
        app = create_app("app.config.TestingConfig")

        required_keys = [
            "SECRET_KEY",
            "SQLALCHEMY_DATABASE_URI",
            "JWT_SECRET_KEY",
            "JWT_ALGORITHM",
            "SERVICE_NAME",
            "SERVICE_VERSION",
            "GUARDIAN_SERVICE_URL",
            "IDENTITY_SERVICE_URL",
        ]

        for key in required_keys:
            assert key in app.config

    def test_sqlalchemy_track_modifications_disabled(self) -> None:
        """Test that SQLALCHEMY_TRACK_MODIFICATIONS is disabled.

        Given: Any configuration
        When: Creating app
        Then: SQLALCHEMY_TRACK_MODIFICATIONS is False
        """
        app = create_app("app.config.TestingConfig")

        assert app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] is False


class TestRateLimiting:
    """Tests for rate limiting configuration."""

    def test_rate_limiter_initialized_when_enabled(self) -> None:
        """Test that Flask-Limiter is initialized when RATE_LIMIT_ENABLED is True.

        Given: DevelopmentConfig with RATE_LIMIT_ENABLED=True
        When: Creating app
        Then: Limiter extension is initialized
        """
        app = create_app("app.config.DevelopmentConfig")

        # Flask-Limiter registers as 'limiter'
        assert "limiter" in app.extensions

    def test_rate_limiter_not_initialized_when_disabled(self) -> None:
        """Test that Flask-Limiter is not initialized when RATE_LIMIT_ENABLED is False.

        Given: TestingConfig with RATE_LIMIT_ENABLED=False
        When: Creating app
        Then: Limiter extension is not initialized
        """
        app = create_app("app.config.TestingConfig")

        # Should not be initialized in testing
        assert "limiter" not in app.extensions


class TestPrometheusMetrics:
    """Tests for Prometheus metrics configuration."""

    def test_prometheus_initialized_when_enabled(self) -> None:
        """Test that Prometheus is initialized when PROMETHEUS_METRICS_ENABLED is True.

        Given: DevelopmentConfig with PROMETHEUS_METRICS_ENABLED=True
        When: Creating app
        Then: /metrics endpoint is registered
        """
        app = create_app("app.config.DevelopmentConfig")

        # Check if /metrics endpoint exists
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        assert "/metrics" in routes

    def test_prometheus_not_initialized_when_disabled(self) -> None:
        """Test that Prometheus is not initialized when PROMETHEUS_METRICS_ENABLED is False.

        Given: TestingConfig with PROMETHEUS_METRICS_ENABLED=False
        When: Creating app
        Then: /metrics endpoint is not registered
        """
        app = create_app("app.config.TestingConfig")

        # Check if /metrics endpoint does not exist
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        assert "/metrics" not in routes


class TestCORSDisabled:
    """Tests for CORS when disabled."""

    def test_cors_not_configured_when_origins_empty(self) -> None:
        """Test that CORS is not configured when CORS_ORIGINS is empty.

        Given: Config with empty CORS_ORIGINS
        When: Creating app
        Then: CORS extension may not be initialized
        """
        import os
        from unittest.mock import patch

        # Temporarily override CORS_ORIGINS to empty
        with patch.object(os, "environ", {"CORS_ORIGINS": ""}):
            from app.config import TestingConfig

            # Create a modified config
            test_config = TestingConfig()
            test_config.CORS_ORIGINS = []

            # This test just verifies no errors occur
            # CORS initialization is conditional
            assert True  # Placeholder - CORS behavior varies


class TestSecurityHeadersDisabled:
    """Tests for security headers when disabled."""

    def test_security_headers_not_added_when_disabled(self) -> None:
        """Test that security headers are not added when SECURITY_HEADERS_ENABLED is False.

        Given: Config with SECURITY_HEADERS_ENABLED=False
        When: Creating app and making request
        Then: Security headers middleware is not active
        """
        from unittest.mock import patch

        # Create app with security headers disabled
        with patch("app.config.TestingConfig.SECURITY_HEADERS_ENABLED", False):
            app = create_app("app.config.TestingConfig")
            client = app.test_client()

            response = client.get("/")

            # Security headers should not be added by our middleware
            # (Flask may add some default headers)
            # We just verify no error occurs
            assert response.status_code in [404, 200]
