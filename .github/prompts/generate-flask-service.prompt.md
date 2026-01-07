---
description: "Generate a service client for external microservices (Guardian, Identity, etc.) with proper error handling, timeouts, and retries"
agent: "Flask API Expert"
tools: ["edit", "search", "search/codebase", "read/problems"]
---

# Generate Flask External Service Client

You are an expert in building resilient microservice clients for Flask applications, implementing proper error handling, retries, timeouts, and circuit breakers following wfp-flask-template patterns.

## Task

Generate a service client file for communicating with external microservices:
- HTTP client with requests library
- Proper error handling and custom exceptions
- Retry logic with exponential backoff
- Request/response logging
- Timeout configuration
- Optional circuit breaker pattern
- Type hints and comprehensive docs

## Input Variables

- `${input:serviceName}` - Service name (e.g., "guardian", "identity", "notification")
- `${input:baseUrl}` - Service base URL from environment
- `${input:targetDir:src/app}` - Base directory
- `${input:useCircuitBreaker:false}` - Implement circuit breaker

## File Structure

Generate: `${targetDir}/services/${serviceName}_service.py`

## Service Client Template

```python
"""${serviceName.capitalize()} service client.

HTTP client for communicating with ${serviceName.capitalize()} microservice.
Implements retry logic, timeouts, and comprehensive error handling.
"""

import logging
import os
from typing import Any, Optional
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException, Timeout, ConnectionError
from urllib3.util.retry import Retry

from ..utils.exceptions import ServiceUnavailableError, ExternalServiceError

logger = logging.getLogger(__name__)


class ${serviceName.capitalize()}Service:
    """Client for ${serviceName.capitalize()} microservice.
    
    Provides methods for interacting with ${serviceName.capitalize()} API endpoints
    with automatic retries, timeouts, and error handling.
    
    Attributes:
        base_url: Base URL of the ${serviceName} service.
        timeout: Request timeout in seconds.
        session: Configured requests session with retry logic.
    
    Examples:
        >>> service = ${serviceName.capitalize()}Service()
        >>> result = service.check_access(user_id="123", resource="users", operation="READ")
        >>> print(result["access_granted"])
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 10,
        max_retries: int = 3
    ) -> None:
        """Initialize ${serviceName.capitalize()} service client.
        
        Args:
            base_url: Base URL of ${serviceName} service (defaults to env var).
            timeout: Request timeout in seconds (default: 10).
            max_retries: Maximum number of retry attempts (default: 3).
        """
        self.base_url = base_url or os.getenv(
            "${serviceName.upper()}_SERVICE_URL",
            "http://localhost:5000"
        )
        self.timeout = timeout
        
        # Configure session with retry logic
        self.session = self._create_session(max_retries)
        
        logger.info(
            f"${serviceName.capitalize()}Service initialized",
            extra={"base_url": self.base_url, "timeout": timeout}
        )
    
    def _create_session(self, max_retries: int) -> requests.Session:
        """Create configured requests session with retry logic.
        
        Args:
            max_retries: Maximum number of retry attempts.
        
        Returns:
            Configured requests session.
        """
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,  # Wait 1, 2, 4, 8 seconds between retries
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            raise_on_status=False
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "wfp-flask-service/1.0"
        })
        
        return session
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any
    ) -> dict[str, Any]:
        """Make HTTP request to ${serviceName} service.
        
        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE).
            endpoint: API endpoint path.
            **kwargs: Additional arguments for requests (json, params, headers, etc.).
        
        Returns:
            Response data as dictionary.
        
        Raises:
            ServiceUnavailableError: If service is unavailable.
            ExternalServiceError: If service returns error response.
            Timeout: If request times out.
        """
        url = urljoin(self.base_url, endpoint)
        
        try:
            logger.debug(
                f"${serviceName.capitalize()} request",
                extra={
                    "method": method,
                    "url": url,
                    "kwargs": {k: v for k, v in kwargs.items() if k != "json"}
                }
            )
            
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            
            # Log response
            logger.debug(
                f"${serviceName.capitalize()} response",
                extra={
                    "status_code": response.status_code,
                    "url": url
                }
            )
            
            # Handle error responses
            if response.status_code >= 500:
                raise ServiceUnavailableError(
                    f"${serviceName.capitalize()} service unavailable: {response.status_code}"
                )
            
            if response.status_code >= 400:
                error_detail = response.json() if response.content else {}
                raise ExternalServiceError(
                    f"${serviceName.capitalize()} error: {response.status_code}",
                    status_code=response.status_code,
                    details=error_detail
                )
            
            # Return JSON response
            return response.json() if response.content else {}
            
        except Timeout:
            logger.error(
                f"${serviceName.capitalize()} request timeout",
                extra={"url": url, "timeout": self.timeout}
            )
            raise ServiceUnavailableError(
                f"${serviceName.capitalize()} service timeout after {self.timeout}s"
            )
        except ConnectionError as e:
            logger.error(
                f"${serviceName.capitalize()} connection error",
                extra={"url": url, "error": str(e)}
            )
            raise ServiceUnavailableError(
                f"Cannot connect to ${serviceName.capitalize()} service"
            )
        except RequestException as e:
            logger.error(
                f"${serviceName.capitalize()} request failed",
                extra={"url": url, "error": str(e)},
                exc_info=True
            )
            raise ExternalServiceError(
                f"${serviceName.capitalize()} request failed: {str(e)}"
            )
    
    # Example method - customize based on actual service API
    def check_access(
        self,
        user_id: str,
        resource: str,
        operation: str,
        context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Check if user has access to perform operation on resource.
        
        Args:
            user_id: User UUID.
            resource: Resource name (e.g., "users", "projects").
            operation: Operation type (e.g., "READ", "CREATE", "UPDATE").
            context: Optional context data for access check.
        
        Returns:
            Access check result with access_granted boolean.
        
        Examples:
            >>> service.check_access("user-123", "projects", "READ")
            {"access_granted": True, "reason": "granted"}
        """
        payload = {
            "user_id": user_id,
            "resource": resource,
            "operation": operation,
            "context": context or {}
        }
        
        return self._make_request(
            "POST",
            "/check-access",
            json=payload
        )
    
    def get_user_info(self, user_id: str) -> dict[str, Any]:
        """Get user information by ID.
        
        Args:
            user_id: User UUID.
        
        Returns:
            User information dictionary.
        """
        return self._make_request(
            "GET",
            f"/users/{user_id}"
        )
    
    def health_check(self) -> dict[str, Any]:
        """Check ${serviceName} service health.
        
        Returns:
            Health status dictionary.
        """
        return self._make_request(
            "GET",
            "/health"
        )


# Singleton instance for application-wide use
_${serviceName}_service_instance: Optional[${serviceName.capitalize()}Service] = None


def get_${serviceName}_service() -> ${serviceName.capitalize()}Service:
    """Get or create ${serviceName} service singleton instance.
    
    Returns:
        ${serviceName.capitalize()}Service instance.
    """
    global _${serviceName}_service_instance
    
    if _${serviceName}_service_instance is None:
        _${serviceName}_service_instance = ${serviceName.capitalize()}Service()
    
    return _${serviceName}_service_instance
```

## Step-by-Step Process

### 1. Analyze Service API
- Review external service documentation
- Identify required endpoints
- Determine authentication mechanism
- Check rate limiting requirements

### 2. Configure HTTP Client
Essential features:
- **Retries**: Exponential backoff for transient failures
- **Timeouts**: Prevent hanging requests
- **Connection pooling**: Reuse connections
- **Headers**: Content-Type, User-Agent, Auth

### 3. Implement Error Handling
Handle service-specific errors:

```python
# Service unavailable (5xx)
if response.status_code >= 500:
    raise ServiceUnavailableError("Service unavailable")

# Client errors (4xx)
if response.status_code >= 400:
    raise ExternalServiceError("Request failed", status_code=status_code)

# Timeout
except Timeout:
    raise ServiceUnavailableError("Request timeout")

# Connection error
except ConnectionError:
    raise ServiceUnavailableError("Cannot connect")
```

### 4. Add Service-Specific Methods
Common patterns:

**Access Check (Guardian)**:
```python
def check_access(self, user_id: str, resource: str, operation: str) -> dict:
    return self._make_request("POST", "/check-access", json={...})
```

**User Info (Identity)**:
```python
def get_user_info(self, user_id: str) -> dict:
    return self._make_request("GET", f"/users/{user_id}")
```

**Send Notification**:
```python
def send_email(self, to: str, subject: str, body: str) -> dict:
    return self._make_request("POST", "/emails", json={...})
```

### 5. Implement Singleton Pattern
For application-wide reuse:

```python
_service_instance: Optional[ServiceClass] = None

def get_service() -> ServiceClass:
    """Get singleton instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ServiceClass()
    return _service_instance
```

### 6. Add Circuit Breaker (Optional)
For high-traffic services:

```python
from pybreaker import CircuitBreaker

class ServiceWithCircuitBreaker:
    def __init__(self):
        self.breaker = CircuitBreaker(
            fail_max=5,
            timeout_duration=60
        )
    
    def call_service(self):
        return self.breaker.call(self._make_request, ...)
```

### 7. Environment Configuration
Required env vars:

```bash
${serviceName.upper()}_SERVICE_URL=https://${serviceName}.example.com
${serviceName.upper()}_API_KEY=secret  # If needed
${serviceName.upper()}_TIMEOUT=10
```

## Common Service Patterns

### Guardian Service (RBAC)
```python
def check_access(
    self,
    service: str,
    resource_name: str,
    operation: str,
    user_id: str,
    company_id: str,
    context: Optional[dict] = None
) -> dict:
    """Check access permissions."""
    payload = {
        "service": service,
        "resource_name": resource_name,
        "operation": operation,
        "user_id": user_id,
        "company_id": company_id,
        "context": context or {}
    }
    return self._make_request("POST", "/check-access", json=payload)
```

### Identity Service (User Management)
```python
def get_user_by_id(self, user_id: str) -> dict:
    """Get user details."""
    return self._make_request("GET", f"/users/{user_id}")

def get_company_by_id(self, company_id: str) -> dict:
    """Get company details."""
    return self._make_request("GET", f"/companies/{company_id}")
```

### Notification Service
```python
def send_email(
    self,
    to: list[str],
    subject: str,
    body: str,
    template_id: Optional[str] = None
) -> dict:
    """Send email notification."""
    payload = {
        "to": to,
        "subject": subject,
        "body": body,
        "template_id": template_id
    }
    return self._make_request("POST", "/emails", json=payload)
```

## Quality Checklist

- [ ] Retry logic with exponential backoff
- [ ] Timeout configuration from environment
- [ ] Comprehensive error handling
- [ ] Request/response logging
- [ ] Type hints on all methods
- [ ] Docstrings (English) for all public methods
- [ ] Singleton factory function
- [ ] Environment variable configuration
- [ ] Health check endpoint
- [ ] Connection pooling via session
- [ ] Custom exceptions for service errors

## Constraints to Follow

**NEVER:**
- Make synchronous calls in async contexts
- Ignore timeouts (always set them)
- Log sensitive data (tokens, passwords)
- Hard-code URLs or credentials
- Swallow exceptions without logging

**ALWAYS:**
- Use session for connection pooling
- Implement retries for transient failures
- Set reasonable timeouts (< 30s)
- Log requests/responses (without sensitive data)
- Follow services.instructions.md
- Handle all HTTP status codes appropriately

## Testing Services

Mock external calls in tests:

```python
@patch("app.services.guardian_service.GuardianService._make_request")
def test_check_access(mock_request):
    """Test access check."""
    mock_request.return_value = {"access_granted": True}
    
    service = GuardianService()
    result = service.check_access("user-123", "projects", "READ")
    
    assert result["access_granted"] is True
    mock_request.assert_called_once()
```

## Output

Present generated service file path and required environment variables.
