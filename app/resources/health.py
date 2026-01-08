# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro

"""Health, readiness and version endpoints.

This module provides standardized observability endpoints for Kubernetes
probes and monitoring systems. These endpoints do not require authentication
and must be available at the root path (no version prefix).
"""

import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from flask import current_app
from flask_restful import Resource
from sqlalchemy import text

from app import db


def _check_database() -> dict[str, Any]:
    """Check database connectivity with a lightweight query.

    Executes a simple SELECT 1 query to verify database connectivity
    and measures response time. Uses existing connection pool.

    Returns:
        Dictionary containing check results with status, response time,
        and optional error message.

    Examples:
        >>> _check_database()
        {'status': 'ok', 'response_time_ms': 15}
        >>> _check_database()  # When DB is down
        {'status': 'error', 'response_time_ms': 3000, 'error': 'Connection refused'}
    """
    start = time.time()
    try:
        db.session.execute(text("SELECT 1"))
        duration_ms = int((time.time() - start) * 1000)
        return {"status": "ok", "response_time_ms": duration_ms}
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        error_msg = str(e)
        current_app.logger.warning(f"Database health check failed: {error_msg}")
        return {
            "status": "error",
            "response_time_ms": duration_ms,
            "error": error_msg,
        }


def _get_version_info() -> dict[str, Any]:
    """Read version information from VERSION file.

    Reads the VERSION file from repository root and extracts version number.
    Also retrieves build metadata from environment variables if available.

    Returns:
        Dictionary containing version, commit, build_date, and environment.

    Raises:
        FileNotFoundError: If VERSION file does not exist.
        ValueError: If VERSION file content is invalid.

    Examples:
        >>> _get_version_info()
        {
            'version': '1.0.0',
            'commit': 'abc123',
            'build_date': '2026-01-07T08:00:00Z',
            'environment': 'production'
        }
    """
    # VERSION file is at repository root
    version_file = Path(__file__).parent.parent.parent / "VERSION"

    if not version_file.exists():
        raise FileNotFoundError("VERSION file not found at repository root")

    version = version_file.read_text().strip()
    if not version:
        raise ValueError("VERSION file is empty")

    # Build metadata from environment variables (set by CI/CD)
    return {
        "version": version,
        "commit": os.getenv("GIT_COMMIT", "unknown"),
        "build_date": os.getenv("BUILD_DATE", "unknown"),
        "environment": os.getenv("FLASK_ENV", "development"),
    }


class HealthResource(Resource):
    """Liveness probe endpoint.

    Checks if the application is alive and functioning. Used by Kubernetes
    liveness probes to detect if the container needs restart. Returns 200 OK
    even if dependencies are degraded (only fails if application itself is broken).

    This endpoint performs lightweight health checks on critical dependencies
    (primarily database) but does not fail if dependencies are temporarily
    unavailable. The "degraded" status allows monitoring to alert while
    avoiding unnecessary pod restarts.
    """

    def get(self) -> tuple[dict[str, Any], int]:
        """Perform liveness health check.

        Returns:
            Tuple of (response dictionary, HTTP status code).
            Status is always 200 unless application itself is broken.

        Examples:
            >>> resource = HealthResource()
            >>> response, status = resource.get()
            >>> status
            200
            >>> response['status']
            'ok'
        """
        try:
            timestamp = datetime.now(UTC).isoformat()

            # Check database connectivity
            db_check = _check_database()

            # Determine overall status
            status = "ok" if db_check["status"] == "ok" else "degraded"

            response = {
                "status": status,
                "timestamp": timestamp,
                "checks": {"database": db_check},
            }

            return response, 200

        except Exception as e:
            # Only return 500 if the application itself is broken
            current_app.logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "error",
                "timestamp": datetime.now(UTC).isoformat(),
                "error": str(e),
            }, 500


class ReadyResource(Resource):
    """Readiness probe endpoint.

    Checks if the application is ready to accept traffic. Used by Kubernetes
    readiness probes to control load balancer routing. Returns 503 if any
    critical dependency is unavailable.

    This endpoint verifies all critical dependencies are operational before
    allowing traffic to reach the service. Unlike liveness checks, readiness
    checks fail fast when dependencies are down.
    """

    def get(self) -> tuple[dict[str, Any], int]:
        """Perform readiness check on all critical dependencies.

        Returns:
            Tuple of (response dictionary, HTTP status code).
            Status is 200 if ready, 503 if not ready.

        Examples:
            >>> resource = ReadyResource()
            >>> response, status = resource.get()
            >>> status
            200
            >>> response['status']
            'ready'
        """
        timestamp = datetime.now(UTC).isoformat()

        # Check all critical dependencies
        checks: dict[str, dict[str, Any]] = {}

        # Database is always critical
        checks["database"] = _check_database()

        # Optional: Add Redis, Guardian, Identity checks based on configuration
        # For now, only database is checked as critical dependency

        # Determine if service is ready
        all_ok = all(check["status"] == "ok" for check in checks.values())

        if all_ok:
            response = {
                "status": "ready",
                "timestamp": timestamp,
                "checks": checks,
            }
            return response, 200
        else:
            response = {
                "status": "not_ready",
                "timestamp": timestamp,
                "checks": checks,
            }
            return response, 503


class VersionResource(Resource):
    """Version information endpoint.

    Returns version information about the deployed service for debugging
    and tracking. Reads version from VERSION file at repository root and
    includes build metadata from environment variables.

    Version information is useful for:
    - Verifying correct version is deployed
    - Debugging version-specific issues
    - Tracking deployments across environments
    """

    def get(self) -> tuple[dict[str, Any], int]:
        """Retrieve service version information.

        Returns:
            Tuple of (response dictionary, HTTP status code).
            Status is 200 on success, 500 if VERSION file is missing.

        Examples:
            >>> resource = VersionResource()
            >>> response, status = resource.get()
            >>> status
            200
            >>> 'version' in response
            True
        """
        try:
            version_info = _get_version_info()
            return version_info, 200
        except (FileNotFoundError, ValueError) as e:
            current_app.logger.error(f"Failed to read version: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.now(UTC).isoformat(),
            }, 500
