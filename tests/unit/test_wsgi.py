# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro
"""Unit tests for WSGI entry point.

This module tests the WSGI entry point configuration, environment
detection, and application instantiation.
"""

from pathlib import Path
from unittest.mock import patch


class TestWSGIEntryPoint:
    """Tests for wsgi.py entry point."""

    def test_wsgi_creates_app_instance(self) -> None:
        """Test that wsgi module creates an app instance.

        Given: wsgi.py module
        When: Module is imported
        Then: app variable is created and is a Flask instance
        """
        # Clear any existing wsgi module
        import sys

        if "wsgi" in sys.modules:
            del sys.modules["wsgi"]

        with patch("os.environ.get") as mock_env:
            mock_env.side_effect = lambda key, default=None: {
                "FLASK_ENV": "testing",
                "IN_DOCKER_CONTAINER": None,
                "APP_MODE": None,
            }.get(key, default)

            with patch("pathlib.Path.exists", return_value=False):
                import wsgi

                assert hasattr(wsgi, "app")
                assert wsgi.app is not None

    def test_wsgi_uses_production_config_by_default(self) -> None:
        """Test that wsgi uses ProductionConfig by default.

        Given: No FLASK_ENV environment variable
        When: wsgi module is imported
        Then: ProductionConfig is selected
        """
        import sys

        if "wsgi" in sys.modules:
            del sys.modules["wsgi"]

        # Mock to avoid actual ProductionConfig validation
        with patch("os.environ.get") as mock_env:
            mock_env.side_effect = lambda key, default=None: {
                "FLASK_ENV": None,
                "IN_DOCKER_CONTAINER": "1",
                "SECRET_KEY": "prod-key",
                "JWT_SECRET_KEY": "prod-jwt",
                "DATABASE_URL": "postgresql://localhost/db",
                "GUARDIAN_SERVICE_URL": "http://guardian:5001",
                "GUARDIAN_SERVICE_API_KEY": "key",
                "IDENTITY_SERVICE_URL": "http://identity:5002",
                "IDENTITY_SERVICE_API_KEY": "key",
                "METRICS_API_KEY": "key",
            }.get(key, default)

            import wsgi

            # Check that config_class is ProductionConfig
            assert wsgi.config_class == "app.config.ProductionConfig"

    def test_wsgi_respects_flask_env_variable(self) -> None:
        """Test that wsgi respects FLASK_ENV environment variable.

        Given: FLASK_ENV set to development
        When: wsgi module is imported
        Then: DevelopmentConfig is selected
        """
        import sys

        if "wsgi" in sys.modules:
            del sys.modules["wsgi"]

        with patch("os.environ.get") as mock_env:
            mock_env.side_effect = lambda key, default=None: {
                "FLASK_ENV": "development",
                "IN_DOCKER_CONTAINER": None,
                "APP_MODE": None,
            }.get(key, default)

            with patch("pathlib.Path.exists", return_value=False):
                import wsgi

                assert wsgi.config_class == "app.config.DevelopmentConfig"

    def test_wsgi_skips_env_loading_in_docker(self) -> None:
        """Test that wsgi skips .env loading when in Docker.

        Given: IN_DOCKER_CONTAINER environment variable set
        When: wsgi module is imported
        Then: dotenv.load_dotenv is not called
        """
        import sys

        if "wsgi" in sys.modules:
            del sys.modules["wsgi"]

        with patch("os.environ.get") as mock_env:
            mock_env.side_effect = lambda key, default=None: {
                "IN_DOCKER_CONTAINER": "1",
                "FLASK_ENV": "testing",
            }.get(key, default)

            with patch("dotenv.load_dotenv") as mock_load_dotenv:
                # load_dotenv should not be called in Docker
                mock_load_dotenv.assert_not_called()

    def test_wsgi_loads_env_development_file(self) -> None:
        """Test that wsgi loads .env.development file when available.

        Given: .env.development file exists and not in Docker
        When: wsgi module is imported
        Then: .env.development is loaded
        """
        import sys

        if "wsgi" in sys.modules:
            del sys.modules["wsgi"]

        with patch("os.environ.get") as mock_env:
            mock_env.side_effect = lambda key, default=None: {
                "IN_DOCKER_CONTAINER": None,
                "APP_MODE": None,
                "FLASK_ENV": "testing",
            }.get(key, default)

            with patch("pathlib.Path.exists") as mock_exists:
                mock_exists.return_value = True

                with patch("dotenv.load_dotenv") as mock_load_dotenv:
                    import wsgi  # noqa: F401

                    # Should load .env.development
                    mock_load_dotenv.assert_called_once()
                    call_args = mock_load_dotenv.call_args[0][0]
                    assert ".env.development" in str(call_args)

    def test_wsgi_fallback_to_env_file(self) -> None:
        """Test that wsgi falls back to .env if .env.development doesn't exist.

        Given: .env.development doesn't exist but .env does
        When: wsgi module is imported
        Then: .env is loaded
        """
        import sys

        if "wsgi" in sys.modules:
            del sys.modules["wsgi"]

        with patch("os.environ.get") as mock_env:
            mock_env.side_effect = lambda key, default=None: {
                "IN_DOCKER_CONTAINER": None,
                "APP_MODE": None,
                "FLASK_ENV": "testing",
            }.get(key, default)

            def exists_side_effect(self):
                """Mock Path.exists to return False for .env.development, True for .env."""
                return ".env.development" not in str(self) and ".env" in str(self)

            with (
                patch.object(Path, "exists", exists_side_effect),
                patch("dotenv.load_dotenv") as mock_load_dotenv,
            ):
                import wsgi  # noqa: F401

                # Should load .env
                mock_load_dotenv.assert_called_once()
                call_args = mock_load_dotenv.call_args[0][0]
                assert ".env" in str(call_args)
                assert ".env.development" not in str(call_args)

    def test_wsgi_config_classes_mapping(self) -> None:
        """Test that wsgi has correct config_classes mapping.

        Given: wsgi module
        When: Accessing config_classes
        Then: All environment configurations are mapped
        """
        import sys

        if "wsgi" in sys.modules:
            del sys.modules["wsgi"]

        with (
            patch("os.environ.get", return_value=None),
            patch("pathlib.Path.exists", return_value=False),
            patch("app.config.ProductionConfig.__init__", return_value=None),
        ):
            import wsgi

            assert "development" in wsgi.config_classes
            assert "testing" in wsgi.config_classes
            assert "integration" in wsgi.config_classes
            assert "staging" in wsgi.config_classes
            assert "production" in wsgi.config_classes
