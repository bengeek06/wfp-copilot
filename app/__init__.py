# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro

"""Flask application factory and initialization.

This module provides the application factory pattern for creating
Flask application instances with proper configuration and extension
initialization.
"""

from contextlib import suppress
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Optional, cast

from flask import Flask, g, request

if TYPE_CHECKING:
    from flask import Response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from prometheus_client import Gauge
from prometheus_flask_exporter import PrometheusMetrics

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
ma = Marshmallow()
limiter = Limiter(key_func=get_remote_address)
metrics: PrometheusMetrics | None = None  # Initialized in create_app


def create_app(config_class: str = "app.config.DevelopmentConfig") -> Flask:
    """Create and configure Flask application instance.

    Factory function that creates a Flask application with proper
    configuration, extension initialization, and route registration.

    Args:
        config_class: Fully qualified class name for configuration.
                     Example: "app.config.DevelopmentConfig"

    Returns:
        Configured Flask application instance.

    Examples:
        >>> app = create_app("app.config.ProductionConfig")
        >>> app.run()
    """
    app = Flask(__name__)

    # Load configuration from class path
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)

    # Import models for migrations autogenerate
    with app.app_context():
        from app.models import Dummy  # noqa: F401

    # Configure rate limiting
    if app.config.get("RATE_LIMIT_ENABLED"):
        limiter.init_app(app)

    # Configure Prometheus metrics
    if app.config.get("PROMETHEUS_METRICS_ENABLED"):
        global metrics
        # Exclude health endpoints from metrics (AC-007, GUD-005)
        metrics = PrometheusMetrics(
            app,
            defaults_prefix="flask",
            excluded_paths=["/health", "/ready", "/version"],
        )
        # Don't register app_info gauge if already exists (for tests)
        with suppress(ValueError):
            metrics.info(
                "app_info",
                "Application info",
                version=app.config.get("SERVICE_VERSION", "1.0.0"),
            )

        # Instrument SQLAlchemy connection pool metrics (AC-006, REQ-005)
        # Wrap in try/except to avoid duplicate registration in tests
        try:
            sqlalchemy_pool_size = Gauge(
                "sqlalchemy_pool_size",
                "Current size of the connection pool",
                ["pool_name"],
            )
            sqlalchemy_pool_checked_in = Gauge(
                "sqlalchemy_pool_checked_in_connections",
                "Number of connections currently checked in to the pool",
                ["pool_name"],
            )
            sqlalchemy_pool_checked_out = Gauge(
                "sqlalchemy_pool_checked_out_connections",
                "Number of connections currently checked out of the pool",
                ["pool_name"],
            )
            sqlalchemy_pool_overflow = Gauge(
                "sqlalchemy_pool_overflow",
                "Number of connections in overflow",
                ["pool_name"],
            )
        except ValueError:
            # Metrics already registered (happens when create_app called multiple times)
            from prometheus_client import REGISTRY

            sqlalchemy_pool_size = cast(
                "Gauge", REGISTRY._names_to_collectors["sqlalchemy_pool_size"]
            )
            sqlalchemy_pool_checked_in = cast(
                "Gauge",
                REGISTRY._names_to_collectors["sqlalchemy_pool_checked_in_connections"],
            )
            sqlalchemy_pool_checked_out = cast(
                "Gauge",
                REGISTRY._names_to_collectors[
                    "sqlalchemy_pool_checked_out_connections"
                ],
            )
            sqlalchemy_pool_overflow = cast(
                "Gauge", REGISTRY._names_to_collectors["sqlalchemy_pool_overflow"]
            )

        @app.before_request
        def update_sqlalchemy_pool_metrics() -> None:
            """Update SQLAlchemy pool metrics before each request."""
            from sqlalchemy.pool import QueuePool

            if hasattr(db.engine, "pool"):
                pool = db.engine.pool
                pool_name = str(db.engine.url.database or "default")
                # Only QueuePool has size(), checkedin(), checkedout(), overflow()
                if isinstance(pool, QueuePool):
                    sqlalchemy_pool_size.labels(pool_name=pool_name).set(pool.size())
                    sqlalchemy_pool_checked_in.labels(pool_name=pool_name).set(
                        pool.checkedin()
                    )
                    sqlalchemy_pool_checked_out.labels(pool_name=pool_name).set(
                        pool.checkedout()
                    )
                    sqlalchemy_pool_overflow.labels(pool_name=pool_name).set(
                        pool.overflow()
                    )

        # Define authentication functions outside the request handler for efficiency
        from app.utils.metrics_auth import require_metrics_api_key

        # Rate limit function wrapped with limiter
        if app.config.get("RATE_LIMIT_ENABLED"):
            rate_limit_default = app.config.get("RATE_LIMIT_DEFAULT", "10 per minute")

            @limiter.limit(rate_limit_default)
            def _check_auth_with_rate_limit() -> "tuple[Response, int] | None":
                """Check authentication with rate limiting applied."""
                return require_metrics_api_key()

        else:

            def _check_auth_with_rate_limit() -> "tuple[Response, int] | None":
                """Check authentication without rate limiting."""
                return require_metrics_api_key()

        @app.before_request
        def authenticate_metrics() -> "tuple[Response, int] | None":
            """Authenticate /metrics endpoint requests.

            Validates API key via Authorization header before allowing
            access to Prometheus metrics endpoint.

            Returns:
                Error response tuple if authentication fails, None otherwise.
            """
            if request.path == "/metrics":
                # Check authentication (and rate limit if enabled)
                return _check_auth_with_rate_limit()
            return None

    # Configure CORS
    if app.config.get("CORS_ORIGINS"):
        CORS(
            app,
            origins=app.config["CORS_ORIGINS"],
            supports_credentials=app.config.get("CORS_ALLOW_CREDENTIALS", True),
        )

    # Register routes
    with app.app_context():
        from app.routes import register_routes

        register_routes(app)

    # Add security headers
    if app.config.get("SECURITY_HEADERS_ENABLED"):

        @app.after_request
        def add_security_headers(response):
            """Add security headers to all responses."""
            for header, value in app.config["SECURITY_HEADERS"].items():
                response.headers[header] = value
            return response

    # Configure logging
    from app.utils.logger import setup_logging

    setup_logging(app)

    # Register CLI commands
    from app.cli import config

    app.cli.add_command(config)

    return app
