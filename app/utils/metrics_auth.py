# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro

"""Metrics endpoint authentication utilities.

This module provides API key authentication for the Prometheus metrics endpoint
to prevent unauthorized access to application metrics and system information.
"""

from __future__ import annotations

import logging
import secrets
from datetime import UTC, datetime
from functools import wraps
from typing import TYPE_CHECKING, Any

from flask import current_app, request

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


def _sanitize_for_log(value: Any) -> str | None:
    """Sanitize potentially untrusted values before logging.

    Removes newline and carriage-return characters to reduce log injection risk.
    """
    if value is None:
        return None
    text = str(value)
    # Strip CRLF and LF characters that could break log lines
    return text.replace("\r\n", "").replace("\r", "").replace("\n", "")


def require_metrics_api_key(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to enforce API key authentication for metrics endpoint.

    Validates the Authorization header contains a valid Bearer token matching
    the METRICS_API_KEY environment variable. Returns 401 for missing or
    invalid API keys and logs authentication failures.

    Args:
        f: Function to decorate (typically a Flask route handler).

    Returns:
        Decorated function with API key validation.

    Raises:
        None: Returns JSON error responses instead of raising exceptions.

    Examples:
        >>> @require_metrics_api_key
        ... def metrics():
        ...     return "metrics data"
    """

    @wraps(f)
    def decorated_function(
        *args: Any, **kwargs: Any
    ) -> tuple[dict[str, Any], int] | Any:
        """Validate API key before executing function.

        Returns:
            Tuple of (response dictionary, HTTP status code) or function result.
        """
        api_key = current_app.config.get("METRICS_API_KEY")

        # Check if API key is configured
        if not api_key:
            logger.error("METRICS_API_KEY not configured in application")
            return (
                {
                    "message": "Metrics API key not configured",
                    "timestamp": datetime.now(UTC).isoformat(),
                },
                500,
            )

        # Get Authorization header
        auth_header = request.headers.get("Authorization", "")

        # Check if header exists and has correct format
        if not auth_header:
            logger.warning(
                "Metrics access attempt without Authorization header",
                extra={
                    "ip": _sanitize_for_log(request.remote_addr),
                    "path": _sanitize_for_log(request.path),
                },
            )
            return (
                {
                    "message": "Missing Authorization header",
                    "timestamp": datetime.now(UTC).isoformat(),
                },
                401,
            )

        if not auth_header.startswith("Bearer "):
            logger.warning(
                "Metrics access attempt with invalid Authorization format",
                extra={
                    "ip": request.remote_addr,
                    "path": request.path,
                    "auth_format": auth_header[:20] if auth_header else "",
                },
            )
            return (
                {
                    "message": "Invalid Authorization format. Expected: Bearer <key>",
                    "timestamp": datetime.now(UTC).isoformat(),
                },
                401,
            )

        # Extract and validate API key
        provided_key = auth_header[7:]  # Remove 'Bearer ' prefix

        # Use constant-time comparison to prevent timing attacks
        if not secrets.compare_digest(provided_key, api_key):
            logger.warning(
                "Invalid metrics API key attempt",
                extra={
                    "ip": _sanitize_for_log(request.remote_addr),
                    "path": _sanitize_for_log(request.path),
                    "key_length": len(provided_key),
                },
            )
            return (
                {
                    "message": "Invalid API key",
                    "timestamp": datetime.now(UTC).isoformat(),
                },
                401,
            )

        # API key valid, proceed with request
        return f(*args, **kwargs)

    return decorated_function
