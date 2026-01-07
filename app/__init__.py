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
from typing import Optional

from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
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

    # Configure rate limiting
    if app.config.get("RATE_LIMIT_ENABLED"):
        limiter.init_app(app)

    # Configure Prometheus metrics
    if app.config.get("PROMETHEUS_METRICS_ENABLED"):
        global metrics
        metrics = PrometheusMetrics(app)
        # Don't register app_info gauge if already exists (for tests)
        with suppress(ValueError):
            metrics.info(
                "app_info",
                "Application info",
                version=app.config.get("SERVICE_VERSION", "1.0.0"),
            )

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

    return app
