---
description: "Generate Guardian RBAC configuration for API resources with operations, roles, and permission mappings"
agent: "API Architect"
tools: ["search", "search/codebase", "edit", "read/problems"]
---

# Generate Guardian Configuration

You are an expert in authorization systems. Generate complete Guardian RBAC configuration for API resources with operations, roles, and permission mappings.

## Task

Generate Guardian configuration including:
- **Service registration** in Guardian
- **Resource definitions** (collections and items)
- **Operations** per resource (LIST, CREATE, READ, UPDATE, DELETE)
- **Role definitions** and permission mappings
- **Context-based authorization** (company_id, resource_id)
- **Integration code** for Flask decorators

## Input Variables

- `${input:specFile}` - Path to specification file
- `${input:serviceName}` - Service name (e.g., `projects-service`)
- `${input:resourceName}` - Resource name (e.g., `projects`)

## Workflow

### 1. Parse Specification

Read specification:
```
${specFile}
```

Extract:
- All endpoints (GET, POST, PATCH, DELETE)
- Security requirements (AUTH-xxx, GUARD-xxx, SEC-xxx)
- User roles mentioned in spec
- Authorization rules and constraints

### 2. Define Guardian Service

Register service in Guardian:

```json
{
  "service": {
    "name": "${serviceName}",
    "display_name": "${Service Display Name}",
    "description": "${description}",
    "version": "1.0.0",
    "base_url": "https://api.example.com",
    "contact": {
      "team": "Backend Team",
      "email": "backend@example.com"
    },
    "created_at": "2026-01-07T00:00:00Z"
  }
}
```

### 3. Define Resources

For each resource, define:

```json
{
  "resources": [
    {
      "service": "${serviceName}",
      "name": "${resource_plural}",
      "display_name": "${Resource Display Name}",
      "description": "${description}",
      "resource_type": "collection",
      "operations": [
        {
          "name": "LIST",
          "display_name": "List ${resources}",
          "description": "View list of ${resources} with pagination",
          "http_methods": ["GET"],
          "endpoint_pattern": "/v0/${resource_plural}",
          "context_fields": ["company_id"],
          "requires_ownership": false
        },
        {
          "name": "CREATE",
          "display_name": "Create ${resource}",
          "description": "Create new ${resource}",
          "http_methods": ["POST"],
          "endpoint_pattern": "/v0/${resource_plural}",
          "context_fields": ["company_id"],
          "requires_ownership": false
        },
        {
          "name": "READ",
          "display_name": "Read ${resource}",
          "description": "View single ${resource} details",
          "http_methods": ["GET"],
          "endpoint_pattern": "/v0/${resource_plural}/{id}",
          "context_fields": ["company_id", "${resource}_id"],
          "requires_ownership": true
        },
        {
          "name": "UPDATE",
          "display_name": "Update ${resource}",
          "description": "Modify existing ${resource}",
          "http_methods": ["PATCH", "PUT"],
          "endpoint_pattern": "/v0/${resource_plural}/{id}",
          "context_fields": ["company_id", "${resource}_id"],
          "requires_ownership": true
        },
        {
          "name": "DELETE",
          "display_name": "Delete ${resource}",
          "description": "Remove ${resource}",
          "http_methods": ["DELETE"],
          "endpoint_pattern": "/v0/${resource_plural}/{id}",
          "context_fields": ["company_id", "${resource}_id"],
          "requires_ownership": true
        }
      ]
    }
  ]
}
```

### 4. Define Roles and Permissions

Standard role structure for multi-tenant SaaS:

```json
{
  "roles": [
    {
      "name": "${resource}_viewer",
      "display_name": "${Resource} Viewer",
      "description": "Can view ${resources} only",
      "permissions": [
        {
          "service": "${serviceName}",
          "resource": "${resource_plural}",
          "operations": ["LIST", "READ"]
        }
      ],
      "scope": "company"
    },
    {
      "name": "${resource}_editor",
      "display_name": "${Resource} Editor",
      "description": "Can view and edit ${resources}",
      "permissions": [
        {
          "service": "${serviceName}",
          "resource": "${resource_plural}",
          "operations": ["LIST", "READ", "CREATE", "UPDATE"]
        }
      ],
      "scope": "company"
    },
    {
      "name": "${resource}_admin",
      "display_name": "${Resource} Administrator",
      "description": "Full access to ${resources}",
      "permissions": [
        {
          "service": "${serviceName}",
          "resource": "${resource_plural}",
          "operations": ["LIST", "READ", "CREATE", "UPDATE", "DELETE"]
        }
      ],
      "scope": "company"
    },
    {
      "name": "company_admin",
      "display_name": "Company Administrator",
      "description": "Full access to all resources in company",
      "permissions": [
        {
          "service": "${serviceName}",
          "resource": "*",
          "operations": ["*"]
        }
      ],
      "scope": "company"
    }
  ]
}
```

### 5. Context-Based Authorization

Define context fields for authorization checks:

```python
# Context fields passed to Guardian

# For collection operations (LIST, CREATE)
context = {
    "company_id": jwt_claims['company_id'],  # From JWT
    "user_id": jwt_claims['user_id'],        # From JWT
}

# For item operations (READ, UPDATE, DELETE)
context = {
    "company_id": jwt_claims['company_id'],   # From JWT
    "user_id": jwt_claims['user_id'],         # From JWT
    "${resource}_id": resource_id,            # From URL path
}

# Guardian checks:
# 1. User has role with required operation permission
# 2. User's company_id matches resource's company_id
# 3. For ownership-required ops, user owns resource or has admin role
```

### 6. Flask Integration Code

Generate decorator usage for Flask-RESTful resources:

```python
"""${Resource} resource with Guardian authorization.

This module implements REST endpoints for ${resource_plural} with
JWT authentication and Guardian RBAC authorization.
"""

from flask import request
from flask_restful import Resource
from ..utils.auth import require_jwt_auth, get_jwt_claims
from ..utils.access_control import access_required, Operation
from ..utils.rate_limit import limiter


class ${Resource}ListResource(Resource):
    """${Resource} collection operations."""
    
    @require_jwt_auth
    @access_required(Operation.LIST, "${resource_plural}")
    @limiter.limit("100 per minute")
    def get(self):
        """List ${resources} with pagination.
        
        Authorization:
            - JWT: Required
            - Guardian: Requires LIST permission on ${resource_plural}
            - Context: company_id from JWT
        
        Returns:
            200: Paginated list of ${resources}
            401: Missing or invalid JWT token
            403: User lacks LIST permission
            429: Rate limit exceeded
        """
        claims = get_jwt_claims()
        company_id = claims['company_id']
        
        # Query filtered by company_id automatically
        # Guardian has already verified LIST permission
        ...
    
    @require_jwt_auth
    @access_required(Operation.CREATE, "${resource_plural}")
    @limiter.limit("50 per minute")
    def post(self):
        """Create new ${resource}.
        
        Authorization:
            - JWT: Required
            - Guardian: Requires CREATE permission on ${resource_plural}
            - Context: company_id from JWT (auto-assigned)
        
        Returns:
            201: ${Resource} created successfully
            400: Invalid request data
            401: Missing or invalid JWT token
            403: User lacks CREATE permission
            422: Validation error
            429: Rate limit exceeded
        """
        claims = get_jwt_claims()
        company_id = claims['company_id']
        
        # Auto-assign company_id from JWT (user cannot override)
        # Guardian has already verified CREATE permission
        ...


class ${Resource}Resource(Resource):
    """${Resource} item operations."""
    
    @require_jwt_auth
    @access_required(Operation.READ, "${resource_plural}")
    @limiter.limit("100 per minute")
    def get(self, ${resource}_id: str):
        """Retrieve ${resource} by ID.
        
        Authorization:
            - JWT: Required
            - Guardian: Requires READ permission on ${resource_plural}
            - Context: company_id from JWT, ${resource}_id from URL
            - Ownership: Resource must belong to user's company
        
        Returns:
            200: ${Resource} details
            401: Missing or invalid JWT token
            403: User lacks READ permission or wrong company
            404: ${Resource} not found
            429: Rate limit exceeded
        """
        claims = get_jwt_claims()
        company_id = claims['company_id']
        
        # Query by id AND company_id (security!)
        # Guardian has already verified READ permission
        # If not found OR wrong company → 404
        ...
    
    @require_jwt_auth
    @access_required(Operation.UPDATE, "${resource_plural}")
    @limiter.limit("50 per minute")
    def patch(self, ${resource}_id: str):
        """Update ${resource}.
        
        Authorization:
            - JWT: Required
            - Guardian: Requires UPDATE permission on ${resource_plural}
            - Context: company_id from JWT, ${resource}_id from URL
            - Ownership: Resource must belong to user's company
        
        Returns:
            200: ${Resource} updated
            400: Invalid request data
            401: Missing or invalid JWT token
            403: User lacks UPDATE permission or wrong company
            404: ${Resource} not found
            422: Validation error
            429: Rate limit exceeded
        """
        claims = get_jwt_claims()
        company_id = claims['company_id']
        
        # Verify ownership via company_id
        # Guardian has already verified UPDATE permission
        ...
    
    @require_jwt_auth
    @access_required(Operation.DELETE, "${resource_plural}")
    @limiter.limit("50 per minute")
    def delete(self, ${resource}_id: str):
        """Delete ${resource}.
        
        Authorization:
            - JWT: Required
            - Guardian: Requires DELETE permission on ${resource_plural}
            - Context: company_id from JWT, ${resource}_id from URL
            - Ownership: Resource must belong to user's company
        
        Returns:
            204: ${Resource} deleted
            401: Missing or invalid JWT token
            403: User lacks DELETE permission or wrong company
            404: ${Resource} not found
            409: Cannot delete (has dependencies)
            429: Rate limit exceeded
        """
        claims = get_jwt_claims()
        company_id = claims['company_id']
        
        # Verify ownership via company_id
        # Guardian has already verified DELETE permission
        # Check cascade constraints
        ...
```

### 7. Guardian API Integration

How `@access_required` decorator calls Guardian:

```python
# In app/utils/access_control.py

from enum import Enum
from functools import wraps
from flask import request
import requests
from .auth import get_jwt_claims


class Operation(Enum):
    """Guardian operations."""
    LIST = "LIST"
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


def access_required(operation: Operation, resource_name: str):
    """Check Guardian authorization before executing endpoint.
    
    Args:
        operation: Operation type (LIST, CREATE, READ, UPDATE, DELETE)
        resource_name: Resource name (e.g., "projects")
    
    Returns:
        Decorator that checks authorization
    
    Raises:
        403: If user lacks required permission
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            claims = get_jwt_claims()
            
            # Build context
            context = {
                "company_id": claims['company_id'],
                "user_id": claims['user_id'],
            }
            
            # Add resource_id if item operation
            if operation in [Operation.READ, Operation.UPDATE, Operation.DELETE]:
                resource_id_key = f"{resource_name.rstrip('s')}_id"
                if resource_id_key in kwargs:
                    context[resource_id_key] = kwargs[resource_id_key]
            
            # Call Guardian /check-access endpoint
            response = requests.post(
                f"{GUARDIAN_URL}/check-access",
                json={
                    "service": "${serviceName}",
                    "resource_name": resource_name,
                    "operation": operation.value,
                    "context": context
                },
                headers={"Authorization": f"Bearer {claims['access_token']}"},
                timeout=5
            )
            
            if response.status_code != 200:
                abort(403, "Access denied")
            
            data = response.json()
            if not data.get("access_granted"):
                reason = data.get("reason", "no_permission")
                abort(403, f"Access denied: {reason}")
            
            # Access granted, proceed
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
```

### 8. Generate Documentation

Create comprehensive Guardian documentation:

```markdown
# Guardian Authorization Configuration
## ${Service Name}

### Service Registration

**Service**: \`${serviceName}\`
**Version**: 1.0.0
**Base URL**: https://api.example.com

### Resources

#### ${Resource_Plural}

**Resource Name**: \`${resource_plural}\`
**Type**: Collection + Item
**Description**: ${description}

### Operations

| Operation | HTTP Method | Endpoint | Context | Requires Ownership |
|-----------|-------------|----------|---------|-------------------|
| LIST | GET | /v0/${resource_plural} | company_id | No |
| CREATE | POST | /v0/${resource_plural} | company_id | No |
| READ | GET | /v0/${resource_plural}/{id} | company_id, ${resource}_id | Yes |
| UPDATE | PATCH | /v0/${resource_plural}/{id} | company_id, ${resource}_id | Yes |
| DELETE | DELETE | /v0/${resource_plural}/{id} | company_id, ${resource}_id | Yes |

### Roles and Permissions

#### ${Resource} Viewer
- **Permissions**: LIST, READ
- **Use Case**: Users who need read-only access

#### ${Resource} Editor
- **Permissions**: LIST, READ, CREATE, UPDATE
- **Use Case**: Users who manage ${resources} but cannot delete

#### ${Resource} Administrator
- **Permissions**: LIST, READ, CREATE, UPDATE, DELETE
- **Use Case**: Full management of ${resources}

#### Company Administrator
- **Permissions**: All operations on all resources
- **Use Case**: Company-wide admin access

### Context-Based Authorization

**Company Isolation**:
All operations automatically filter by \`company_id\` from JWT. Users can only access resources belonging to their company.

**Ownership**:
For item operations (READ, UPDATE, DELETE), the resource must belong to the user's company. Guardian verifies \`company_id\` matches.

### Integration

**Flask Decorators**:
\`\`\`python
@require_jwt_auth                          # Step 1: Validate JWT
@access_required(Operation.LIST, "projects")  # Step 2: Check Guardian permission
def get(self):
    ...
\`\`\`

**Guardian API Call**:
\`\`\`json
POST https://guardian.example.com/check-access
{
  "service": "${serviceName}",
  "resource_name": "${resource_plural}",
  "operation": "LIST",
  "context": {
    "company_id": "uuid-from-jwt",
    "user_id": "uuid-from-jwt"
  }
}

Response:
{
  "access_granted": true,
  "reason": "granted"
}
\`\`\`

### Setup Instructions

1. **Register Service** in Guardian:
   \`\`\`bash
   curl -X POST https://guardian.example.com/api/v1/services \
     -H "Authorization: Bearer $ADMIN_TOKEN" \
     -d @guardian-service.json
   \`\`\`

2. **Register Resources**:
   \`\`\`bash
   curl -X POST https://guardian.example.com/api/v1/resources \
     -H "Authorization: Bearer $ADMIN_TOKEN" \
     -d @guardian-resources.json
   \`\`\`

3. **Create Roles**:
   \`\`\`bash
   curl -X POST https://guardian.example.com/api/v1/roles \
     -H "Authorization: Bearer $ADMIN_TOKEN" \
     -d @guardian-roles.json
   \`\`\`

4. **Assign Roles** to users via Guardian Admin UI or API

### Testing

\`\`\`bash
# Test LIST permission
curl -X GET https://api.example.com/v0/${resource_plural} \
  -H "Cookie: access_token=$JWT"

# Should return 200 if user has LIST permission
# Should return 403 if user lacks permission
\`\`\`
```

## Quality Checklist

Before completing:
- [ ] Service registered in Guardian
- [ ] All CRUD operations defined
- [ ] Context fields specified (company_id, resource_id)
- [ ] Roles defined with appropriate permissions
- [ ] Ownership requirements clear
- [ ] Flask decorators documented
- [ ] Guardian API integration code provided
- [ ] Setup instructions complete
- [ ] Testing guidelines included

## Example Usage

```
@api-architect /generate-guardian-config
Spec: spec/schema-api-projects-crud.md
Service: projects-service
Resource: projects
```

Output:
1. Guardian service/resource/role JSON configuration
2. Flask decorator integration code
3. Documentation with setup instructions
4. Testing guidelines

---

**Note**: Guardian configuration follows Waterfall RBAC patterns with company-based multi-tenancy.
