# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro

"""Guardian service client for RBAC authorization.

This module provides a client for interacting with the Guardian service
to check user permissions and enforce role-based access control.
"""

from enum import Enum
from typing import Any

import requests
from flask import current_app


class Operation(str, Enum):
    """Supported RBAC operations.

    Attributes:
        LIST: List all resources.
        CREATE: Create a new resource.
        READ: Read a specific resource.
        UPDATE: Update a specific resource.
        DELETE: Delete a specific resource.
    """

    LIST = "LIST"
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class GuardianError(Exception):
    """Exception raised when Guardian service communication fails.

    Attributes:
        message: Error description.
        status_code: HTTP status code (default: 503).
    """

    def __init__(self, message: str, status_code: int = 503) -> None:
        """Initialize Guardian error.

        Args:
            message: Error description.
            status_code: HTTP status code (default: 503 Service Unavailable).
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class GuardianService:
    """Client for Guardian RBAC service.

    Handles communication with Guardian service for permission checks.
    """

    @staticmethod
    def check_access(
        user_id: str,
        company_id: str,
        resource_name: str,
        operation: Operation,
        context: dict[str, Any] | None = None,
    ) -> tuple[bool, str]:
        """Check if user has permission to perform operation on resource.

        Args:
            user_id: Unique identifier of the user.
            company_id: Unique identifier of the user's company.
            resource_name: Name of the resource being accessed.
            operation: Operation to perform (LIST, CREATE, READ, UPDATE, DELETE).
            context: Optional context data (e.g., {"project_id": "uuid"}).

        Returns:
            Tuple of (access_granted: bool, reason: str).

        Raises:
            GuardianError: If Guardian service is unreachable or returns error.

        Examples:
            >>> access, reason = GuardianService.check_access(
            ...     user_id="user-123",
            ...     company_id="company-456",
            ...     resource_name="projects",
            ...     operation=Operation.READ,
            ...     context={"project_id": "proj-789"}
            ... )
            >>> if not access:
            ...     return jsonify({"error": reason}), 403
        """
        url = f"{current_app.config['GUARDIAN_SERVICE_URL']}/check-access"
        timeout = current_app.config["GUARDIAN_SERVICE_TIMEOUT"]
        api_key = current_app.config["GUARDIAN_SERVICE_API_KEY"]

        payload = {
            "service": current_app.config["SERVICE_NAME"],
            "user_id": user_id,
            "company_id": company_id,
            "resource_name": resource_name,
            "operation": operation.value,
        }

        if context:
            payload["context"] = context

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["X-API-Key"] = api_key

        try:
            current_app.logger.debug(
                "Checking access with Guardian",
                extra={
                    "user_id": user_id,
                    "company_id": company_id,
                    "resource_name": resource_name,
                    "operation": operation.value,
                },
            )

            response = requests.post(
                url, json=payload, headers=headers, timeout=timeout
            )

            if response.status_code == 200:
                data = response.json()
                access_granted = data.get("access_granted", False)
                reason = data.get("reason", "unknown")

                current_app.logger.info(
                    "Guardian access check completed",
                    extra={
                        "user_id": user_id,
                        "resource_name": resource_name,
                        "operation": operation.value,
                        "access_granted": access_granted,
                        "reason": reason,
                    },
                )

                return access_granted, reason

            current_app.logger.error(
                "Guardian service returned error",
                extra={
                    "status_code": response.status_code,
                    "response": response.text,
                },
            )
            raise GuardianError(
                f"Guardian service error: {response.status_code}",
                status_code=503,
            )

        except requests.exceptions.Timeout:
            current_app.logger.error(
                "Guardian service timeout",
                extra={"url": url, "timeout": timeout},
            )
            raise GuardianError("Guardian service timeout", status_code=503)

        except requests.exceptions.ConnectionError:
            current_app.logger.error(
                "Guardian service connection error",
                extra={"url": url},
            )
            raise GuardianError("Guardian service unavailable", status_code=503)

        except requests.exceptions.RequestException as e:
            current_app.logger.error(
                "Guardian service request failed",
                extra={"error": str(e)},
            )
            raise GuardianError(f"Guardian service error: {str(e)}", status_code=503)
