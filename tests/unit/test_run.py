# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro
"""Unit tests for run.py entry point.

This module tests the development entry point configuration,
environment detection, and Flask development server startup.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch


class TestRunEntryPoint:
    """Tests for run.py entry point."""

    def test_main_function_exists(self) -> None:
        """Test that main function is defined in run module.

        Given: run.py module
        When: Module is imported
        Then: main function exists
        """
        import run

        assert hasattr(run, "main")
        assert callable(run.main)

    def test_main_detects_environment(self) -> None:
        """Test that main function detects environment from FLASK_ENV.

        Given: FLASK_ENV environment variable set
        When: main() is called
        Then: Environment is correctly detected
        """
        with patch("os.environ.get") as mock_env:
            mock_env.side_effect = lambda key, default=None: {
                "FLASK_ENV": "staging",
                "IN_DOCKER_CONTAINER": "1",
            }.get(key, default)

            with patch("run.create_app") as mock_create_app:
                mock_app = MagicMock()
                mock_app.config.get.side_effect = lambda key, default=None: {
                    "DEBUG": False,
                    "SERVICE_PORT": 5000,
                }.get(key, default)
                mock_create_app.return_value = mock_app

                from run import main

                with patch.object(mock_app, "run"):
                    main()

                    # Verify create_app was called with staging config
                    mock_create_app.assert_called_once_with("app.config.StagingConfig")

    def test_main_uses_development_config_by_default(self) -> None:
        """Test that main uses DevelopmentConfig by default.

        Given: No FLASK_ENV environment variable
        When: main() is called
        Then: DevelopmentConfig is used
        """
        with patch("os.environ.get") as mock_env:
            mock_env.side_effect = lambda key, default=None: {
                "FLASK_ENV": None,
                "IN_DOCKER_CONTAINER": "1",
            }.get(key, default)

            with patch("run.create_app") as mock_create_app:
                mock_app = MagicMock()
                mock_app.config.get.side_effect = lambda key, default=None: {
                    "DEBUG": True,
                    "SERVICE_PORT": 5000,
                }.get(key, default)
                mock_create_app.return_value = mock_app

                from run import main

                with patch.object(mock_app, "run"):
                    main()

                    mock_create_app.assert_called_once_with(
                        "app.config.DevelopmentConfig"
                    )

    def test_main_loads_env_development_file(self) -> None:
        """Test that main loads .env.development file when available.

        Given: .env.development file exists and not in Docker
        When: main() is called
        Then: .env.development is loaded
        """
        # Import run module first to ensure dotenv is already imported
        import run

        with patch("os.environ.get") as mock_env:
            mock_env.side_effect = lambda key, default=None: {
                "FLASK_ENV": "development",
                "IN_DOCKER_CONTAINER": None,
                "APP_MODE": None,
            }.get(key, default)

            with (
                patch("pathlib.Path.exists") as mock_exists,
                patch("run.load_dotenv") as mock_load_dotenv,
                patch("run.create_app") as mock_create_app,
            ):
                mock_exists.return_value = True
                mock_app = MagicMock()
                mock_app.config.get.side_effect = lambda key, default=None: {
                    "DEBUG": True,
                    "SERVICE_PORT": 5000,
                }.get(key, default)
                mock_create_app.return_value = mock_app

                with patch.object(mock_app, "run"), patch("builtins.print"):
                    run.main()

                # Should load .env.development
                mock_load_dotenv.assert_called_once()
                call_args = mock_load_dotenv.call_args[0][0]
                assert ".env.development" in str(call_args)

    def test_main_fallback_to_env_file(self) -> None:
        """Test that main falls back to .env if .env.development doesn't exist.

        Given: .env.development doesn't exist but .env does
        When: main() is called
        Then: .env is loaded
        """
        import run

        with patch("os.environ.get") as mock_env:
            mock_env.side_effect = lambda key, default=None: {
                "FLASK_ENV": "development",
                "IN_DOCKER_CONTAINER": None,
                "APP_MODE": None,
            }.get(key, default)

            def exists_side_effect(self):
                """Mock Path.exists to return False for .env.development, True for .env."""
                return ".env.development" not in str(self) and ".env" in str(self)

            with (
                patch.object(Path, "exists", exists_side_effect),
                patch("run.load_dotenv") as mock_load_dotenv,
                patch("run.create_app") as mock_create_app,
            ):
                mock_app = MagicMock()
                mock_app.config.get.side_effect = lambda key, default=None: {
                    "DEBUG": True,
                    "SERVICE_PORT": 5000,
                }.get(key, default)
                mock_create_app.return_value = mock_app

                with patch.object(mock_app, "run"), patch("builtins.print"):
                    run.main()

                # Should load .env
                mock_load_dotenv.assert_called_once()
                call_args = mock_load_dotenv.call_args[0][0]
                assert ".env" in str(call_args)
                assert ".env.development" not in str(call_args)

    def test_main_skips_env_loading_in_docker(self) -> None:
        """Test that main skips .env loading when in Docker.

        Given: IN_DOCKER_CONTAINER environment variable set
        When: main() is called
        Then: dotenv.load_dotenv is not called
        """
        with patch("os.environ.get") as mock_env:
            mock_env.side_effect = lambda key, default=None: {
                "FLASK_ENV": "development",
                "IN_DOCKER_CONTAINER": "1",
            }.get(key, default)

            with (
                patch("dotenv.load_dotenv") as mock_load_dotenv,
                patch("run.create_app") as mock_create_app,
            ):
                mock_app = MagicMock()
                mock_app.config.get.side_effect = lambda key, default=None: {
                    "DEBUG": True,
                    "SERVICE_PORT": 5000,
                }.get(key, default)
                mock_create_app.return_value = mock_app

                from run import main

                with patch.object(mock_app, "run"), patch("builtins.print"):
                    main()

                # load_dotenv should not be called in Docker
                mock_load_dotenv.assert_not_called()

    def test_main_prints_warning_when_no_env_file(self) -> None:
        """Test that main prints warning when no .env file is found.

        Given: Neither .env.development nor .env exists
        When: main() is called
        Then: Warning is printed
        """
        with patch("os.environ.get") as mock_env:
            mock_env.side_effect = lambda key, default=None: {
                "FLASK_ENV": "development",
                "IN_DOCKER_CONTAINER": None,
                "APP_MODE": None,
            }.get(key, default)

            with (
                patch("pathlib.Path.exists", return_value=False),
                patch("run.create_app") as mock_create_app,
                patch("builtins.print") as mock_print,
            ):
                mock_app = MagicMock()
                mock_app.config.get.side_effect = lambda key, default=None: {
                    "DEBUG": True,
                    "SERVICE_PORT": 5000,
                }.get(key, default)
                mock_create_app.return_value = mock_app

                from run import main

                with patch.object(mock_app, "run"):
                    main()

                # Should print warning about missing env file
                warning_printed = any(
                    "Warning" in str(call_args) or "No .env" in str(call_args)
                    for call_args in mock_print.call_args_list
                )
                assert warning_printed

    def test_main_starts_flask_development_server(self) -> None:
        """Test that main starts Flask development server.

        Given: Flask app created
        When: main() is called
        Then: app.run() is called with correct parameters
        """
        with patch("os.environ.get") as mock_env:
            mock_env.side_effect = lambda key, default=None: {
                "FLASK_ENV": "development",
                "IN_DOCKER_CONTAINER": "1",
            }.get(key, default)

            with patch("run.create_app") as mock_create_app:
                mock_app = MagicMock()
                mock_app.config.get.side_effect = lambda key, default=None: {
                    "DEBUG": True,
                    "SERVICE_PORT": 5555,
                }.get(key, default)
                mock_create_app.return_value = mock_app

                from run import main

                with patch("builtins.print"):
                    main()

                # Verify app.run was called with correct parameters
                mock_app.run.assert_called_once_with(
                    host="0.0.0.0",  # nosec B104
                    port=5555,
                    debug=True,
                )

    def test_main_uses_config_debug_setting(self) -> None:
        """Test that main uses DEBUG from config, not environment.

        Given: Flask app with specific DEBUG setting
        When: main() is called
        Then: DEBUG from config is used
        """
        with patch("os.environ.get") as mock_env:
            mock_env.side_effect = lambda key, default=None: {
                "FLASK_ENV": "staging",
                "IN_DOCKER_CONTAINER": "1",
            }.get(key, default)

            with patch("run.create_app") as mock_create_app:
                mock_app = MagicMock()
                mock_app.config.get.side_effect = lambda key, default=None: {
                    "DEBUG": False,
                    "SERVICE_PORT": 5000,
                }.get(key, default)
                mock_create_app.return_value = mock_app

                from run import main

                with patch("builtins.print"):
                    main()

                # Verify debug=False is used from config
                mock_app.run.assert_called_once()
                call_kwargs = mock_app.run.call_args[1]
                assert call_kwargs["debug"] is False

    def test_main_prints_configuration_info(self) -> None:
        """Test that main prints configuration information.

        Given: Flask app created
        When: main() is called
        Then: Configuration info is printed
        """
        with patch("os.environ.get") as mock_env:
            mock_env.side_effect = lambda key, default=None: {
                "FLASK_ENV": "development",
                "IN_DOCKER_CONTAINER": "1",
            }.get(key, default)

            with patch("run.create_app") as mock_create_app:
                mock_app = MagicMock()
                mock_app.config.get.side_effect = lambda key, default=None: {
                    "DEBUG": True,
                    "SERVICE_PORT": 5000,
                }.get(key, default)
                mock_create_app.return_value = mock_app

                from run import main

                with (
                    patch.object(mock_app, "run"),
                    patch("builtins.print") as mock_print,
                ):
                    main()

                # Should print environment and config info
                print_calls = [
                    str(call_args) for call_args in mock_print.call_args_list
                ]
                assert any("Environment" in call for call in print_calls)
                assert any("Config" in call for call in print_calls)
                assert any("Starting Flask" in call for call in print_calls)

    def test_main_config_classes_mapping(self) -> None:
        """Test that main has correct config_classes mapping.

        Given: run module
        When: Accessing config_classes in main
        Then: All environment configurations are mapped
        """
        import run

        # The config_classes dict is defined in main function
        # We can test it by mocking and verifying the correct config is selected
        with patch("os.environ.get") as mock_env:
            mock_env.side_effect = lambda key, default=None: {
                "FLASK_ENV": "integration",
                "IN_DOCKER_CONTAINER": "1",
            }.get(key, default)

            with patch("run.create_app") as mock_create_app:
                mock_app = MagicMock()
                mock_app.config.get.side_effect = lambda key, default=None: {
                    "DEBUG": True,
                    "SERVICE_PORT": 5000,
                }.get(key, default)
                mock_create_app.return_value = mock_app

                with patch.object(mock_app, "run"), patch("builtins.print"):
                    run.main()

                # Verify IntegrationConfig was selected
                mock_create_app.assert_called_once_with("app.config.IntegrationConfig")
