# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro

"""Structured logging configuration with correlation.

This module provides JSON logging for production environments and
colorized console logging for development, with correlation IDs
for request tracing.
"""

import logging
import uuid
from typing import Any

from flask import Flask, g, has_request_context, request
from pythonjsonlogger.json import JsonFormatter


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output.

    Adds ANSI color codes to log levels for better readability
    in development environments.

    Attributes:
        COLORS: Mapping of log levels to ANSI color codes.
        RESET: ANSI reset code to clear formatting.
    """

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors.

        Args:
            record: Log record to format.

        Returns:
            Formatted log message with ANSI color codes.
        """
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        return super().format(record)


class CorrelationIdFilter(logging.Filter):
    """Logging filter to add correlation ID to log records.

    Extracts correlation ID from Flask request context and adds
    it to log records for distributed tracing.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to log record.

        Args:
            record: Log record to modify.

        Returns:
            True to allow record to be logged.
        """
        if has_request_context():
            record.correlation_id = getattr(g, "correlation_id", "N/A")
        else:
            record.correlation_id = "N/A"
        return True


def setup_logging(app: Flask) -> None:
    """Configure structured logging for the application.

    Sets up JSON logging for production environments and colorized
    console logging for development. Adds correlation ID tracking
    for request tracing.

    Args:
        app: Flask application instance to configure.

    Examples:
        >>> from flask import Flask
        >>> app = Flask(__name__)
        >>> setup_logging(app)
        >>> app.logger.info("Application started")
    """
    # Clear existing handlers to avoid duplicates
    app.logger.handlers.clear()

    # Create handler
    handler = logging.StreamHandler()

    # Set log level from configuration
    log_level = getattr(logging, app.config.get("LOG_LEVEL", "INFO").upper())
    app.logger.setLevel(log_level)
    handler.setLevel(log_level)

    # Add correlation ID filter if enabled
    if app.config.get("ENABLE_CORRELATION_ID"):
        correlation_filter = CorrelationIdFilter()
        handler.addFilter(correlation_filter)

    # Configure formatter based on environment
    log_format = app.config.get("LOG_FORMAT", "json")

    formatter: JsonFormatter | ColoredFormatter
    if log_format == "json":
        # JSON formatter for production
        formatter = JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s %(correlation_id)s",
            rename_fields={"levelname": "level", "name": "logger"},
        )
    else:
        # Colored formatter for development
        formatter = ColoredFormatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s [%(correlation_id)s]",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)
    app.logger.addHandler(handler)

    # Set up correlation ID management
    if app.config.get("ENABLE_CORRELATION_ID"):

        @app.before_request
        def add_correlation_id() -> None:
            """Add a unique correlation ID to each request."""
            g.correlation_id = request.headers.get(
                "X-Correlation-ID", str(uuid.uuid4())
            )

        @app.after_request
        def log_request_info(response: Any) -> Any:
            """Log request information with correlation ID."""
            if app.config.get("ENABLE_REQUEST_LOGGING"):
                app.logger.info(
                    "Request processed",
                    extra={
                        "method": request.method,
                        "path": request.path,
                        "status": response.status_code,
                        "ip": request.remote_addr,
                        "correlation_id": g.get("correlation_id", "N/A"),
                    },
                )
            return response

    app.logger.info(
        "Logging configured",
        extra={
            "log_format": log_format,
            "log_level": app.config.get("LOG_LEVEL"),
            "correlation_id_enabled": app.config.get("ENABLE_CORRELATION_ID"),
        },
    )
