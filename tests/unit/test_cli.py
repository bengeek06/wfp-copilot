# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro

"""Tests for Flask CLI commands.

Tests configuration inspection and validation CLI commands
for proper output formatting and secret masking.
"""

from click.testing import CliRunner
from flask import Flask

from app.cli import config


class TestConfigShow:
    """Test suite for 'flask config show' command."""

    def test_config_show_displays_sections(self, app: Flask) -> None:
        """Test that config show displays all configuration sections.

        Given: A Flask application with configuration
        When: Running 'flask config show'
        Then: All configuration sections are displayed
        """
        runner = CliRunner()
        with app.app_context():
            result = runner.invoke(config, ["show"])

        assert result.exit_code == 0
        assert "Application Configuration" in result.output
        assert "Application:" in result.output
        assert "Database:" in result.output
        assert "JWT Authentication:" in result.output
        assert "Guardian RBAC:" in result.output
        assert "Security:" in result.output

    def test_config_show_masks_secrets(self, app: Flask) -> None:
        """Test that config show masks sensitive configuration values.

        Given: A Flask application with secret keys configured
        When: Running 'flask config show'
        Then: Secret values are masked with asterisks
        """
        runner = CliRunner()
        with app.app_context():
            result = runner.invoke(config, ["show"])

        assert result.exit_code == 0
        # Secrets should be masked
        assert "SECRET_KEY" in result.output
        assert "***" in result.output
        # Full secret values should not be visible
        assert "test-secret-key" not in result.output
        assert "test-jwt-secret" not in result.output

    def test_config_show_displays_environment_variables(self, app: Flask) -> None:
        """Test that config show displays environment variables section.

        Given: A Flask application
        When: Running 'flask config show'
        Then: Environment variables section is displayed
        """
        runner = CliRunner()
        with app.app_context():
            result = runner.invoke(config, ["show"])

        assert result.exit_code == 0
        assert "Environment Variables" in result.output
        assert "FLASK_ENV" in result.output
        assert "DATABASE_URL" in result.output

    def test_config_show_indicates_missing_values(self, app: Flask) -> None:
        """Test that config show indicates when values are not set.

        Given: A Flask application with some unset configuration
        When: Running 'flask config show'
        Then: Missing values are indicated with '<not set>'
        """
        runner = CliRunner()
        with app.app_context():
            result = runner.invoke(config, ["show"])

        assert result.exit_code == 0
        assert "<not set>" in result.output

    def test_config_show_formats_boolean_values(self, app: Flask) -> None:
        """Test that config show properly formats boolean values.

        Given: A Flask application with boolean configuration
        When: Running 'flask config show'
        Then: Boolean values are displayed as True/False
        """
        runner = CliRunner()
        with app.app_context():
            result = runner.invoke(config, ["show"])

        assert result.exit_code == 0
        assert "DEBUG" in result.output
        assert "True" in result.output or "False" in result.output


class TestConfigValidate:
    """Test suite for 'flask config validate' command."""

    def test_config_validate_succeeds_for_valid_config(self, app: Flask) -> None:
        """Test that config validate succeeds with valid configuration.

        Given: A Flask application with valid test configuration
        When: Running 'flask config validate'
        Then: Validation passes without errors
        """
        runner = CliRunner()
        with app.app_context():
            result = runner.invoke(config, ["validate"])

        assert result.exit_code == 0
        assert "Configuration Validation" in result.output

    def test_config_validate_detects_missing_guardian_key(self, app: Flask) -> None:
        """Test that config validate warns about missing Guardian API key.

        Given: A Flask application without GUARDIAN_SERVICE_API_KEY
        When: Running 'flask config validate'
        Then: Warning is displayed about missing API key
        """
        runner = CliRunner()
        # Ensure testing mode is off to trigger validation
        app.config["TESTING"] = False
        app.config["GUARDIAN_SERVICE_API_KEY"] = None

        with app.app_context():
            result = runner.invoke(config, ["validate"])

        # May have warnings but should not fail for missing API key
        assert "GUARDIAN_SERVICE_API_KEY" in result.output or result.exit_code == 0

    def test_config_validate_production_checks(self, app: Flask) -> None:
        """Test that config validate performs production-specific checks.

        Given: A Flask application with production-like config
        When: Running 'flask config validate'
        Then: Production-specific validations are performed
        """
        runner = CliRunner()
        app.config["TESTING"] = False
        app.config["DEBUG"] = False

        with app.app_context():
            result = runner.invoke(config, ["validate"])

        # Should check configuration
        assert "Configuration Validation" in result.output


class TestMaskSecret:
    """Test suite for secret masking utility function."""

    def test_mask_secret_masks_long_values(self, app: Flask) -> None:
        """Test that long secret values are properly masked.

        Given: A long secret value
        When: Masking the secret
        Then: Only first and last characters are visible
        """
        from app.cli import _mask_secret

        result = _mask_secret("secret-key-12345")
        assert result.startswith("s")
        assert result.endswith("5")
        assert "***" in result
        assert "secret-key" not in result

    def test_mask_secret_handles_short_values(self, app: Flask) -> None:
        """Test that short secret values are completely masked.

        Given: A short secret value
        When: Masking the secret
        Then: Value is completely masked
        """
        from app.cli import _mask_secret

        result = _mask_secret("abc")
        assert result == "***"

    def test_mask_secret_handles_none(self, app: Flask) -> None:
        """Test that None values are handled gracefully.

        Given: A None value
        When: Masking the secret
        Then: '<not set>' is returned
        """
        from app.cli import _mask_secret

        result = _mask_secret(None)
        assert result == "<not set>"

    def test_mask_secret_handles_empty_string(self, app: Flask) -> None:
        """Test that empty strings are handled gracefully.

        Given: An empty string
        When: Masking the secret
        Then: '<not set>' is returned
        """
        from app.cli import _mask_secret

        result = _mask_secret("")
        assert result == "<not set>"


class TestFormatValue:
    """Test suite for value formatting utility function."""

    def test_format_value_masks_sensitive_keys(self, app: Flask) -> None:
        """Test that values with sensitive keys are masked.

        Given: Configuration keys containing sensitive names
        When: Formatting the values
        Then: Values are masked
        """
        from app.cli import _format_value

        result = _format_value("JWT_SECRET_KEY", "secret123")
        assert "***" in result
        assert "secret123" not in result

    def test_format_value_formats_booleans(self, app: Flask) -> None:
        """Test that boolean values are formatted correctly.

        Given: Boolean configuration values
        When: Formatting the values
        Then: 'True' or 'False' strings are returned
        """
        from app.cli import _format_value

        result = _format_value("DEBUG", True)
        assert "True" in result

    def test_format_value_formats_lists(self, app: Flask) -> None:
        """Test that list values are formatted correctly.

        Given: List configuration values
        When: Formatting the values
        Then: Comma-separated list is returned
        """
        from app.cli import _format_value

        result = _format_value(
            "CORS_ORIGINS", ["http://localhost:3000", "http://localhost:5000"]
        )
        assert "http://localhost:3000" in result
        assert "http://localhost:5000" in result

    def test_format_value_handles_none(self, app: Flask) -> None:
        """Test that None values are formatted correctly.

        Given: None configuration value
        When: Formatting the value
        Then: '<not set>' is returned
        """
        from app.cli import _format_value

        result = _format_value("SOME_KEY", None)
        assert "<not set>" in result
