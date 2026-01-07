# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro

"""JWT authentication and RBAC authorization decorators.

This module provides decorators for JWT-based authentication and
Guardian-based authorization, extracting user claims and checking permissions.
"""

from collections.abc import Callable
from functools import wraps
from typing import Any

import jwt
from flask import current_app, g, jsonify, request
from jwt.exceptions import DecodeError, ExpiredSignatureError, InvalidTokenError

from app.services.guardian_service import GuardianError, GuardianService, Operation


class JWTError(Exception):
    """Base exception for JWT-related errors.

    Attributes:
        message: Error description.
        status_code: HTTP status code for the error.
    """

    def __init__(self, message: str, status_code: int = 401) -> None:
        """Initialize JWT error.

        Args:
            message: Error description.
            status_code: HTTP status code (default: 401 Unauthorized).
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def require_jwt_auth(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to require JWT authentication.

    Validates JWT token from access_token cookie, decodes it, and places
    user claims (user_id, company_id, email) in Flask g context.

    The decorator expects the following claims in the JWT:
    - user_id: Unique identifier of the user
    - company_id: Unique identifier of the user's company
    - email: User's email address

    Args:
        f: Function to decorate.

    Returns:
        Decorated function with JWT authentication.

    Raises:
        JWTError: If token is missing, invalid, or expired.

    Examples:
        >>> @require_jwt_auth
        ... def protected_route():
        ...     user_id = g.user_id
        ...     return jsonify({"user_id": user_id})
    """

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        """Wrapper function that validates JWT before calling original.

        Args:
            *args: Positional arguments for wrapped function.
            **kwargs: Keyword arguments for wrapped function.

        Returns:
            Response from wrapped function or error response.
        """
        # Get token from cookie
        token = request.cookies.get(current_app.config["JWT_COOKIE_NAME"])

        if not token:
            current_app.logger.warning(
                "Missing JWT token",
                extra={"correlation_id": getattr(g, "correlation_id", "N/A")},
            )
            return (
                jsonify(
                    {
                        "error": "Unauthorized",
                        "message": "Authentication required. No token provided.",
                    }
                ),
                401,
            )

        try:
            # Decode and verify token
            payload = jwt.decode(
                token,
                current_app.config["JWT_SECRET_KEY"],
                algorithms=[current_app.config["JWT_ALGORITHM"]],
            )

            # Extract required claims
            g.user_id = payload.get("user_id")
            g.company_id = payload.get("company_id")
            g.email = payload.get("email")

            # Validate that required claims are present
            if not g.user_id or not g.company_id:
                current_app.logger.error(
                    "JWT token missing required claims",
                    extra={
                        "correlation_id": getattr(g, "correlation_id", "N/A"),
                        "has_user_id": bool(g.user_id),
                        "has_company_id": bool(g.company_id),
                    },
                )
                return (
                    jsonify(
                        {
                            "error": "Unauthorized",
                            "message": "Invalid token: missing required claims.",
                        }
                    ),
                    401,
                )

            current_app.logger.debug(
                "JWT authentication successful",
                extra={
                    "correlation_id": getattr(g, "correlation_id", "N/A"),
                    "user_id": g.user_id,
                    "company_id": g.company_id,
                },
            )

            # Call original function
            return f(*args, **kwargs)

        except ExpiredSignatureError:
            current_app.logger.warning(
                "JWT token expired",
                extra={"correlation_id": getattr(g, "correlation_id", "N/A")},
            )
            return (
                jsonify({"error": "Unauthorized", "message": "Token has expired."}),
                401,
            )
        except DecodeError:
            current_app.logger.error(
                "JWT decode error",
                extra={"correlation_id": getattr(g, "correlation_id", "N/A")},
            )
            return (
                jsonify({"error": "Unauthorized", "message": "Invalid token format."}),
                401,
            )
        except InvalidTokenError as e:
            current_app.logger.error(
                "JWT validation error",
                extra={
                    "correlation_id": getattr(g, "correlation_id", "N/A"),
                    "error": str(e),
                },
            )
            return (
                jsonify({"error": "Unauthorized", "message": "Invalid token."}),
                401,
            )

    return decorated_function


def get_current_user_id() -> str | None:
    """Get the current authenticated user ID from context.

    Returns:
        User ID from JWT claims or None if not authenticated.

    Examples:
        >>> @require_jwt_auth
        ... def my_route():
        ...     user_id = get_current_user_id()
        ...     return jsonify({"user_id": user_id})
    """
    return getattr(g, "user_id", None)


def get_current_company_id() -> str | None:
    """Get the current authenticated user's company ID from context.

    Returns:
        Company ID from JWT claims or None if not authenticated.

    Examples:
        >>> @require_jwt_auth
        ... def my_route():
        ...     company_id = get_current_company_id()
        ...     return jsonify({"company_id": company_id})
    """
    return getattr(g, "company_id", None)


def get_current_user_email() -> str | None:
    """Get the current authenticated user's email from context.

    Returns:
        Email from JWT claims or None if not authenticated.

    Examples:
        >>> @require_jwt_auth
        ... def my_route():
        ...     email = get_current_user_email()
        ...     return jsonify({"email": email})
    """
    return getattr(g, "email", None)


def access_required(
    operation: Operation, resource_name: str | None = None
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to require Guardian RBAC authorization.

    Checks if the authenticated user has permission to perform
    the specified operation on the resource. Must be used after
    @require_jwt_auth as it depends on user_id and company_id in context.

    Args:
        operation: RBAC operation (LIST, CREATE, READ, UPDATE, DELETE).
        resource_name: Name of the resource (default: extracted from route).

    Returns:
        Decorator function that enforces authorization.

    Raises:
        GuardianError: If Guardian service is unavailable.

    Examples:
        >>> @require_jwt_auth
        ... @access_required(Operation.READ, "projects")
        ... def get_project(project_id):
        ...     return jsonify({"id": project_id})
    """

    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            """Wrapper that checks Guardian permissions before calling original.

            Args:
                *args: Positional arguments for wrapped function.
                **kwargs: Keyword arguments for wrapped function.

            Returns:
                Response from wrapped function or 403 error.
            """
            # Extract resource name from route if not provided
            nonlocal resource_name
            if not resource_name:
                # Try to get from endpoint name
                endpoint = request.endpoint
                if endpoint:
                    # Convert 'api.user_resource' -> 'users'
                    parts = endpoint.split(".")
                    if len(parts) > 1:
                        resource_name = parts[-1].replace("_resource", "s")

            if not resource_name:
                current_app.logger.error(
                    "Cannot determine resource name for access check",
                    extra={
                        "endpoint": request.endpoint,
                        "correlation_id": getattr(g, "correlation_id", "N/A"),
                    },
                )
                return (
                    jsonify(
                        {
                            "error": "Internal Server Error",
                            "message": "Cannot determine resource for authorization.",
                        }
                    ),
                    500,
                )

            # Get user context from JWT (set by @require_jwt_auth)
            user_id = get_current_user_id()
            company_id = get_current_company_id()

            if not user_id or not company_id:
                current_app.logger.error(
                    "Missing user context for authorization",
                    extra={
                        "correlation_id": getattr(g, "correlation_id", "N/A"),
                    },
                )
                return (
                    jsonify(
                        {
                            "error": "Unauthorized",
                            "message": "User context missing. Use @require_jwt_auth first.",
                        }
                    ),
                    401,
                )

            # Build context from route parameters
            context = {key: str(value) for key, value in kwargs.items()}

            try:
                # Check access with Guardian
                access_granted, reason = GuardianService.check_access(
                    user_id=user_id,
                    company_id=company_id,
                    resource_name=resource_name,
                    operation=operation,
                    context=context if context else None,
                )

                if not access_granted:
                    current_app.logger.warning(
                        "Access denied by Guardian",
                        extra={
                            "user_id": user_id,
                            "company_id": company_id,
                            "resource_name": resource_name,
                            "operation": operation.value,
                            "reason": reason,
                            "correlation_id": getattr(g, "correlation_id", "N/A"),
                        },
                    )
                    return (
                        jsonify(
                            {
                                "error": "Forbidden",
                                "message": f"Access denied: {reason}",
                            }
                        ),
                        403,
                    )

                # Access granted, call original function
                return f(*args, **kwargs)

            except GuardianError as e:
                current_app.logger.error(
                    "Guardian service error",
                    extra={
                        "error": str(e),
                        "correlation_id": getattr(g, "correlation_id", "N/A"),
                    },
                )
                return (
                    jsonify(
                        {
                            "error": "Service Unavailable",
                            "message": "Authorization service unavailable.",
                        }
                    ),
                    503,
                )

        return decorated_function

    return decorator
