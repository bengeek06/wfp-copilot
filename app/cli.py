# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro

"""Flask CLI commands for configuration and diagnostics.

Provides custom Click commands to inspect environment variables,
configuration state, and service health.
"""

import os
from typing import Any

import click
from flask import current_app
from flask.cli import with_appcontext


def _mask_secret(value: str | None) -> str:
    """Mask sensitive values for display.

    Args:
        value: The secret value to mask.

    Returns:
        Masked string showing only first/last chars, or indication if missing.

    Examples:
        >>> _mask_secret("secret-key-12345")
        's***5'
        >>> _mask_secret(None)
        '<not set>'
    """
    if not value:
        return "<not set>"
    if len(value) <= 4:
        return "***"
    return f"{value[0]}{'*' * (len(value) - 2)}{value[-1]}"


def _format_value(key: str, value: Any) -> str:
    """Format configuration value for display, masking secrets.

    Args:
        key: Configuration key name.
        value: Configuration value.

    Returns:
        Formatted string representation of the value.

    Examples:
        >>> _format_value("DEBUG", True)
        'True'
        >>> _format_value("JWT_SECRET_KEY", "secret123")
        's*******3'
    """
    # List of sensitive keys to mask
    sensitive_keys = {
        "SECRET_KEY",
        "JWT_SECRET_KEY",
        "GUARDIAN_SERVICE_API_KEY",
        "DATABASE_URL",
        "SQLALCHEMY_DATABASE_URI",
    }

    # Check if key contains sensitive information
    if any(sensitive in key.upper() for sensitive in sensitive_keys):
        return _mask_secret(str(value) if value else None)

    # Format boolean values
    if isinstance(value, bool):
        return str(click.style(str(value), fg="green" if value else "red"))

    # Format None values
    if value is None:
        return str(click.style("<not set>", fg="yellow"))

    # Format list/tuple values
    if isinstance(value, (list, tuple)):
        if not value:
            return "[]"
        return f"[{', '.join(str(v) for v in value)}]"

    return str(value)


@click.group()
def config() -> None:
    """Configuration management commands."""


@config.command("show")
@with_appcontext
def show_config() -> None:
    """Display current application configuration and environment variables.

    Shows critical configuration values with secrets masked for security.
    Useful for debugging configuration issues without exposing sensitive data.

    Examples:
        $ flask config show
    """
    click.echo(
        click.style("\n=== Application Configuration ===\n", fg="cyan", bold=True)
    )

    # Get current config class name
    config_name = current_app.config.get("ENV", "unknown")
    click.echo(
        f"Active Environment: {click.style(config_name.upper(), fg='green', bold=True)}\n"
    )

    # Critical configuration sections
    sections = {
        "Application": [
            "DEBUG",
            "TESTING",
            "SECRET_KEY",
            "LOG_LEVEL",
            "LOG_FORMAT",
            "REQUEST_LOGGING_ENABLED",
        ],
        "Database": [
            "SQLALCHEMY_DATABASE_URI",
            "SQLALCHEMY_TRACK_MODIFICATIONS",
            "SQLALCHEMY_ECHO",
        ],
        "JWT Authentication": [
            "JWT_SECRET_KEY",
            "JWT_ALGORITHM",
            "JWT_COOKIE_NAME",
            "JWT_ACCESS_TOKEN_EXPIRES",
            "JWT_COOKIE_SECURE",
            "JWT_COOKIE_HTTPONLY",
            "JWT_COOKIE_SAMESITE",
        ],
        "Guardian RBAC": [
            "GUARDIAN_SERVICE_URL",
            "GUARDIAN_SERVICE_API_KEY",
            "GUARDIAN_SERVICE_TIMEOUT",
            "SERVICE_NAME",
        ],
        "Security": [
            "SECURITY_HEADERS_ENABLED",
            "CORS_ORIGINS",
        ],
        "Rate Limiting": [
            "RATE_LIMIT_ENABLED",
            "RATE_LIMIT_STORAGE_URL",
        ],
        "Metrics": [
            "PROMETHEUS_ENABLED",
        ],
    }

    for section_name, keys in sections.items():
        click.echo(click.style(f"{section_name}:", fg="yellow", bold=True))

        for key in keys:
            value = current_app.config.get(key)
            formatted_value = _format_value(key, value)
            click.echo(f"  {key:.<40} {formatted_value}")

        click.echo()  # Empty line between sections

    # Environment variables section
    click.echo(click.style("=== Environment Variables ===\n", fg="cyan", bold=True))

    env_vars = {
        "FLASK_ENV": os.getenv("FLASK_ENV"),
        "FLASK_DEBUG": os.getenv("FLASK_DEBUG"),
        "DOCKER_CONTAINER": os.getenv("DOCKER_CONTAINER"),
        "DATABASE_URL": os.getenv("DATABASE_URL"),
        "GUARDIAN_SERVICE_URL": os.getenv("GUARDIAN_SERVICE_URL"),
        "GUARDIAN_SERVICE_API_KEY": os.getenv("GUARDIAN_SERVICE_API_KEY"),
    }

    for key, value in env_vars.items():
        formatted_value = _format_value(key, value)
        status = "✓" if value else "✗"
        status_color = "green" if value else "red"
        click.echo(
            f"  {click.style(status, fg=status_color)} {key:.<40} {formatted_value}"
        )

    click.echo(
        click.style(
            "\n💡 Tip: Secrets are masked for security. Check .env files for actual values.\n",
            fg="blue",
        )
    )


@config.command("validate")
@with_appcontext
def validate_config() -> None:
    """Validate critical configuration and report issues.

    Checks for common configuration problems and missing required values.

    Examples:
        $ flask config validate
    """
    click.echo(
        click.style("\n=== Configuration Validation ===\n", fg="cyan", bold=True)
    )

    errors = []
    warnings = []

    # Check critical production settings
    if not current_app.config.get("TESTING"):
        # SECRET_KEY validation
        secret_key = current_app.config.get("SECRET_KEY")
        if not secret_key or secret_key == "dev-secret-key-change-in-production":  # nosec B105
            errors.append("SECRET_KEY is using default value (SECURITY RISK)")

        # JWT_SECRET_KEY validation
        jwt_secret = current_app.config.get("JWT_SECRET_KEY")
        if not jwt_secret or jwt_secret == "dev-jwt-secret-change-in-production":  # nosec B105
            errors.append("JWT_SECRET_KEY is using default value (SECURITY RISK)")

        # Database validation
        db_uri = current_app.config.get("SQLALCHEMY_DATABASE_URI")
        if not db_uri or "sqlite:///:memory:" in db_uri:
            warnings.append("Using in-memory database (data will be lost on restart)")

        # Guardian validation
        guardian_url = current_app.config.get("GUARDIAN_SERVICE_URL")
        if not guardian_url:
            errors.append("GUARDIAN_SERVICE_URL is not configured")

        guardian_key = current_app.config.get("GUARDIAN_SERVICE_API_KEY")
        if not guardian_key:
            warnings.append("GUARDIAN_SERVICE_API_KEY is not set")

        # CORS validation
        cors_origins = current_app.config.get("CORS_ORIGINS", [])
        if not cors_origins and not current_app.config.get("DEBUG"):
            warnings.append("CORS_ORIGINS is empty (no cross-origin access allowed)")

    # Report results
    if not errors and not warnings:
        click.echo(click.style("✓ Configuration is valid\n", fg="green", bold=True))
    else:
        if errors:
            click.echo(click.style("ERRORS:", fg="red", bold=True))
            for error in errors:
                click.echo(click.style(f"  ✗ {error}", fg="red"))
            click.echo()

        if warnings:
            click.echo(click.style("WARNINGS:", fg="yellow", bold=True))
            for warning in warnings:
                click.echo(click.style(f"  ⚠ {warning}", fg="yellow"))
            click.echo()

    if errors:
        click.echo(
            click.style(
                "⛔ Configuration has critical errors. Fix before deploying to production.\n",
                fg="red",
                bold=True,
            )
        )
        raise click.ClickException("Configuration validation failed")
