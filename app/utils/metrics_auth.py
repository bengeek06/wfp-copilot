# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro

"""Authentication for Prometheus metrics endpoint.

This module provides API key authentication for the /metrics endpoint
used by Prometheus scraping. Validates Bearer token from Authorization header.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from flask import current_app, g, jsonify, request

if TYPE_CHECKING:
    from flask import Response


def _get_timestamp() -> str:
    """Get current UTC timestamp in ISO format.

    Returns:
        ISO 8601 formatted timestamp string.
    """
    return datetime.now(UTC).isoformat()


def _sanitize_for_log(value: str) -> str:
    r"""Sanitize string for safe logging.

    Removes newlines and carriage returns to prevent log injection attacks.

    Args:
        value: String to sanitize.

    Returns:
        Sanitized string safe for logging.

    Examples:
        >>> _sanitize_for_log("test\\ninjection")
        'test injection'
    """
    return value.replace("\n", " ").replace("\r", " ")


def require_metrics_api_key() -> tuple[Response, int] | None:
    """Validate API key for metrics endpoint access.

    Checks Authorization header for valid Bearer token matching METRICS_API_KEY.
    Logs authentication failures at WARNING level with sanitized input.

    Returns:
        Tuple of (error_dict, status_code) if authentication fails.
        None if authentication succeeds.

    Raises:
        None - returns error responses instead of raising exceptions.

    Examples:
        >>> # In view function:
        >>> auth_error = require_metrics_api_key()
        >>> if auth_error:
        >>>     return auth_error
    """
    auth_header = request.headers.get("Authorization")

    # Missing Authorization header (AC-002)
    if not auth_header:
        current_app.logger.warning(
            "Metrics authentication failed: missing Authorization header",
            extra={
                "correlation_id": getattr(g, "correlation_id", "N/A"),
                "remote_addr": _sanitize_for_log(request.remote_addr or "unknown"),
            },
        )
        return (
            jsonify(
                {
                    "message": "Missing Authorization header",
                    "timestamp": _get_timestamp(),
                }
            ),
            401,
        )

    # Parse Bearer token
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        auth_format = _sanitize_for_log(auth_header[:50])  # Limit length
        current_app.logger.warning(
            "Metrics authentication failed: invalid Authorization format",
            extra={
                "correlation_id": getattr(g, "correlation_id", "N/A"),
                "auth_format": auth_format,
                "remote_addr": _sanitize_for_log(request.remote_addr or "unknown"),
            },
        )
        return (
            jsonify(
                {
                    "message": "Invalid Authorization format. Expected: Bearer <token>",
                    "timestamp": _get_timestamp(),
                }
            ),
            401,
        )

    provided_key = parts[1]
    expected_key = current_app.config["METRICS_API_KEY"]

    # Invalid API key (AC-003)
    # Use timing-safe comparison to prevent timing attacks
    import hmac

    if not hmac.compare_digest(provided_key, expected_key):
        # Only log first 8 chars of invalid key
        key_prefix = _sanitize_for_log(provided_key[:8])
        current_app.logger.warning(
            "Metrics authentication failed: invalid API key",
            extra={
                "correlation_id": getattr(g, "correlation_id", "N/A"),
                "key_prefix": f"{key_prefix}...",
                "remote_addr": _sanitize_for_log(request.remote_addr or "unknown"),
            },
        )
        return (
            jsonify(
                {
                    "message": "Invalid API key",
                    "timestamp": _get_timestamp(),
                }
            ),
            401,
        )

    # Authentication successful
    return None
