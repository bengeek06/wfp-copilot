# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro
"""Entry point for development and staging environments.

This module provides the main entry point for running the Flask application
in development and staging environments with appropriate configuration.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

from app import create_app


def main():
    """Main entry point for running the Flask application.

    This function detects the environment, loads configuration,
    creates the Flask app, and starts the development server.
    """
    # Detect environment
    env = os.environ.get("FLASK_ENV", "development")

    # Load .env file ONLY for local development (not in Docker)
    # In Docker (staging/production), variables come from orchestration tools (docker-compose, k8s, helm)
    if not os.environ.get("IN_DOCKER_CONTAINER") and not os.environ.get("APP_MODE"):
        env_file = ".env.development"
        if Path(env_file).exists():
            load_dotenv(env_file)
            print(f"Loaded environment from {env_file}")
        # Fallback to generic .env if .env.development doesn't exist
        elif Path(".env").exists():
            load_dotenv(".env")
            print("Loaded environment from .env")
        else:
            print("Warning: No .env.development or .env file found")
    else:
        print("Running in Docker container, skipping .env file loading")

    # Configuration mapping
    config_classes = {
        "development": "app.config.DevelopmentConfig",
        "testing": "app.config.TestingConfig",
        "integration": "app.config.IntegrationConfig",
        "staging": "app.config.StagingConfig",
        "production": "app.config.ProductionConfig",
    }

    config_class = config_classes.get(env, "app.config.DevelopmentConfig")
    print(f"Environment: {env}, Config: {config_class}")

    app = create_app(config_class)

    # Use Flask config DEBUG setting instead of environment detection
    debug = app.config.get("DEBUG", False)
    port = app.config.get("SERVICE_PORT", 5000)

    print(f"Starting Flask development server on port {port} (debug={debug})")
    app.run(host="0.0.0.0", port=port, debug=debug)  # nosec B104


if __name__ == "__main__":
    main()
