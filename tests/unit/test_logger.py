# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro

"""Tests for logging configuration module.

Tests structured logging setup with JSON and colored formatters,
correlation ID tracking, and request logging.
"""

import logging
from unittest.mock import patch

import pytest
from flask import Flask

from app.utils.logger import ColoredFormatter, CorrelationIdFilter, setup_logging


class TestColoredFormatter:
    """Tests for ColoredFormatter."""

    def test_colored_formatter_adds_colors_to_log_levels(self) -> None:
        """Test that formatter adds ANSI colors to log levels.

        Given: A log record with INFO level
        When: ColoredFormatter formats the record
        Then: Log level contains ANSI color codes
        """
        formatter = ColoredFormatter(
            fmt="%(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        assert "\033[32m" in formatted  # Green for INFO
        assert "\033[0m" in formatted  # Reset code

    def test_colored_formatter_handles_all_log_levels(self) -> None:
        """Test that formatter handles all standard log levels.

        Given: Log records with different levels
        When: ColoredFormatter formats the records
        Then: Each level has appropriate color code
        """
        formatter = ColoredFormatter(fmt="%(levelname)s")

        levels_and_colors = [
            (logging.DEBUG, "\033[36m"),  # Cyan
            (logging.INFO, "\033[32m"),  # Green
            (logging.WARNING, "\033[33m"),  # Yellow
            (logging.ERROR, "\033[31m"),  # Red
            (logging.CRITICAL, "\033[35m"),  # Magenta
        ]

        for level, color in levels_and_colors:
            record = logging.LogRecord(
                name="test",
                level=level,
                pathname="",
                lineno=0,
                msg="Test",
                args=(),
                exc_info=None,
            )
            formatted = formatter.format(record)
            assert color in formatted


class TestCorrelationIdFilter:
    """Tests for CorrelationIdFilter."""

    def test_correlation_id_filter_adds_id_from_context(self) -> None:
        """Test that filter adds correlation ID from Flask context.

        Given: A request context with correlation ID
        When: Filter processes a log record
        Then: Record has correlation_id attribute
        """
        app = Flask(__name__)
        correlation_filter = CorrelationIdFilter()

        with app.test_request_context():
            from flask import g

            g.correlation_id = "test-id-123"

            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg="Test",
                args=(),
                exc_info=None,
            )

            result = correlation_filter.filter(record)

            assert result is True
        assert record.correlation_id == "test-id-123"  # type: ignore[attr-defined]

    def test_correlation_id_filter_handles_missing_context(self) -> None:
        """Test that filter handles missing request context gracefully.

        Given: No request context
        When: Filter processes a log record
        Then: Record has correlation_id set to N/A
        """
        correlation_filter = CorrelationIdFilter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test",
            args=(),
            exc_info=None,
        )

        result = correlation_filter.filter(record)

        assert result is True
        assert record.correlation_id == "N/A"  # type: ignore[attr-defined]


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_configures_json_format_for_production(
        self, production_app: Flask
    ) -> None:
        """Test that production uses JSON logging format.

        Given: Production configuration
        When: setup_logging is called
        Then: Logger uses JSON formatter
        """
        setup_logging(production_app)

        assert len(production_app.logger.handlers) > 0
        handler = production_app.logger.handlers[0]
        assert handler.formatter is not None
        # Check that it's using JsonFormatter by inspecting class name
        assert "JsonFormatter" in handler.formatter.__class__.__name__

    def test_setup_logging_configures_colored_format_for_development(
        self, development_app: Flask
    ) -> None:
        """Test that development uses colored logging format.

        Given: Development configuration
        When: setup_logging is called
        Then: Logger uses ColoredFormatter
        """
        setup_logging(development_app)

        assert len(development_app.logger.handlers) > 0
        handler = development_app.logger.handlers[0]
        assert isinstance(handler.formatter, ColoredFormatter)

    def test_setup_logging_sets_log_level_from_config(
        self, development_app: Flask
    ) -> None:
        """Test that log level is set from configuration.

        Given: Configuration with DEBUG log level
        When: setup_logging is called
        Then: Logger level is set to DEBUG
        """
        development_app.config["LOG_LEVEL"] = "DEBUG"
        setup_logging(development_app)

        assert development_app.logger.level == logging.DEBUG

    def test_setup_logging_adds_correlation_id_filter(
        self, development_app: Flask
    ) -> None:
        """Test that correlation ID filter is added when enabled.

        Given: Configuration with correlation ID enabled
        When: setup_logging is called
        Then: Handler has CorrelationIdFilter
        """
        development_app.config["ENABLE_CORRELATION_ID"] = True
        setup_logging(development_app)

        handler = development_app.logger.handlers[0]
        has_correlation_filter = any(
            isinstance(f, CorrelationIdFilter) for f in handler.filters
        )
        assert has_correlation_filter

    def test_setup_logging_registers_before_request_hook(
        self, development_app: Flask
    ) -> None:
        """Test that before_request hook is registered for correlation ID.

        Given: Configuration with correlation ID enabled
        When: setup_logging is called and request is made
        Then: Correlation ID is set in context
        """
        development_app.config["ENABLE_CORRELATION_ID"] = True
        setup_logging(development_app)

        with development_app.test_request_context(
            headers={"X-Correlation-ID": "custom-id"}
        ):
            # Trigger before_request hooks
            development_app.preprocess_request()
            from flask import g

            assert g.correlation_id == "custom-id"

    def test_setup_logging_generates_correlation_id_when_not_provided(
        self, development_app: Flask
    ) -> None:
        """Test that correlation ID is generated when not in headers.

        Given: Request without X-Correlation-ID header
        When: Request is processed
        Then: Correlation ID is auto-generated
        """
        development_app.config["ENABLE_CORRELATION_ID"] = True
        setup_logging(development_app)

        with development_app.test_request_context():
            development_app.preprocess_request()
            from flask import g

            assert hasattr(g, "correlation_id")
            assert g.correlation_id != "N/A"
            # Should be a UUID format
            assert len(g.correlation_id) == 36

    def test_setup_logging_logs_request_info_when_enabled(
        self, development_app: Flask
    ) -> None:
        """Test that request logging works when enabled.

        Given: Configuration with request logging enabled
        When: Request is processed
        Then: Request info is logged
        """
        development_app.config["ENABLE_REQUEST_LOGGING"] = True
        development_app.config["ENABLE_CORRELATION_ID"] = True
        setup_logging(development_app)

        with (
            development_app.test_client() as client,
            patch.object(development_app.logger, "info") as mock_log,
        ):
            # Make a request (will fail 404 but that's ok for test)
            client.get("/test-endpoint")

            # Check that request was logged
            assert mock_log.called

    def test_setup_logging_clears_existing_handlers(
        self, development_app: Flask
    ) -> None:
        """Test that existing handlers are cleared before setup.

        Given: Logger with existing handlers
        When: setup_logging is called
        Then: Old handlers are removed
        """
        # Add a dummy handler
        old_handler = logging.StreamHandler()
        development_app.logger.addHandler(old_handler)
        assert len(development_app.logger.handlers) >= 1

        setup_logging(development_app)

        # Should only have the new handler
        assert old_handler not in development_app.logger.handlers

    def test_setup_logging_logs_configuration_info(
        self, development_app: Flask
    ) -> None:
        """Test that setup logs its own configuration.

        Given: Fresh Flask app
        When: setup_logging is called
        Then: Configuration info is logged
        """
        with patch.object(development_app.logger, "info") as mock_log:
            setup_logging(development_app)

            # Check that "Logging configured" message was logged
            calls = [str(call) for call in mock_log.call_args_list]
            assert any("Logging configured" in call for call in calls)


@pytest.fixture
def production_app() -> Flask:
    """Fixture providing a production Flask app.

    Returns:
        Flask app with ProductionConfig-like settings.
    """
    app = Flask(__name__)
    app.config.update(
        {
            "LOG_LEVEL": "WARNING",
            "LOG_FORMAT": "json",
            "ENABLE_CORRELATION_ID": True,
            "ENABLE_REQUEST_LOGGING": True,
        }
    )
    return app


@pytest.fixture
def development_app() -> Flask:
    """Fixture providing a development Flask app.

    Returns:
        Flask app with DevelopmentConfig-like settings.
    """
    app = Flask(__name__)
    app.config.update(
        {
            "LOG_LEVEL": "DEBUG",
            "LOG_FORMAT": "text",
            "ENABLE_CORRELATION_ID": True,
            "ENABLE_REQUEST_LOGGING": True,
        }
    )
    return app
