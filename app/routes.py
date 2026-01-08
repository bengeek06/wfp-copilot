# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro

"""Route registration."""

from flask_restful import Api

from app.resources.health import HealthResource, ReadyResource, VersionResource


def register_routes(app):
    """Register all API routes.

    Registers health endpoints first (no version prefix), then versioned
    API routes. Health endpoints are required for Kubernetes probes and
    monitoring systems.

    Args:
        app: Flask application instance.
    """
    api = Api(app)

    # Health endpoints (no version prefix, no authentication)
    api.add_resource(HealthResource, "/health")
    api.add_resource(ReadyResource, "/ready")
    api.add_resource(VersionResource, "/version")

    # Versioned API endpoints will be registered here
