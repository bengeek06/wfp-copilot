---
description: "Generate a comprehensive REST API endpoint specification following the specification agent template with detailed requirements, acceptance criteria, and OpenAPI schemas"
agent: "agent"
tools: ["edit", "search", "search/codebase", "web/fetch"]
---

# Generate API Endpoint Specification

You are an expert REST API architect specializing in creating precise, comprehensive, and AI-ready API endpoint specifications following industry best practices and OpenAPI 3.x standards.

## Task

Generate a complete specification document for a REST API endpoint in the `/spec/` directory following the specification agent template with:
- Clear purpose and scope
- Detailed requirements and constraints
- Request/Response schemas with examples
- Authentication and authorization requirements
- Error handling specifications
- Acceptance criteria in Given-When-Then format
- Performance and rate limiting requirements

## Input Variables

- `${input:endpointPath}` - API endpoint path (e.g., "/v0/users/{userId}")
- `${input:httpMethod}` - HTTP method (GET, POST, PUT, PATCH, DELETE)
- `${input:resourceName}` - Resource name (e.g., "User", "Project")
- `${input:operation}` - Operation description (e.g., "Retrieve user", "Create project")

## Specification Template

```markdown
---
title: API Endpoint Specification - ${httpMethod} ${endpointPath}
version: 1.0
date_created: ${currentDate}
last_updated: ${currentDate}
owner: API Team
tags: [api, rest, endpoint, ${resourceName.toLowerCase()}]
---

# Introduction

This specification defines the ${operation} endpoint for the ${resourceName} resource in the REST API. It establishes the complete contract including request/response formats, validation rules, authentication requirements, and error handling behavior.

## 1. Purpose & Scope

### Purpose
Define the technical contract for the **${httpMethod} ${endpointPath}** endpoint that allows clients to ${operation.toLowerCase()}.

### Scope
- **In Scope**: Request/response formats, validation, authentication, rate limiting, error handling
- **Out of Scope**: Internal implementation details, database schema design
- **Intended Audience**: API consumers, backend developers, QA engineers, AI code generators

### Assumptions
- Clients use HTTPS for all API communications
- Clients include valid JWT tokens in Authorization header
- API follows RESTful principles and semantic versioning

## 2. Definitions

| Term | Definition |
|------|------------|
| **JWT** | JSON Web Token - Used for authentication and authorization |
| **UUID** | Universally Unique Identifier - Used for resource IDs |
| **RBAC** | Role-Based Access Control - Authorization mechanism |
| **Rate Limit** | Maximum number of requests allowed per time window |
| **Idempotency** | Property ensuring repeated identical requests produce same result |
| **${resourceName}** | [Define the resource entity] |

## 3. Requirements, Constraints & Guidelines

### Functional Requirements

- **REQ-001**: Endpoint SHALL accept ${httpMethod} requests at ${endpointPath}
- **REQ-002**: Request body SHALL be validated against defined schema before processing
- **REQ-003**: Response SHALL include appropriate HTTP status code and JSON body
- **REQ-004**: All timestamps SHALL be in ISO 8601 format with UTC timezone
- **REQ-005**: Resource IDs SHALL be UUIDs in RFC 4122 format
- **REQ-006**: Pagination SHALL be supported for collection endpoints (GET)
- **REQ-007**: Filtering and sorting SHALL be available via query parameters

### Security Requirements

- **SEC-001**: Endpoint SHALL require valid JWT authentication token
- **SEC-002**: JWT SHALL be verified for signature, expiration, and issuer
- **SEC-003**: Authorization SHALL be checked via Guardian service for required permissions
- **SEC-004**: Sensitive data SHALL NOT be logged or exposed in error messages
- **SEC-005**: Rate limiting SHALL be enforced per user/IP address
- **SEC-006**: Request body size SHALL be limited to 1MB maximum
- **SEC-007**: SQL injection and XSS attacks SHALL be prevented via input validation

### Performance Requirements

- **PERF-001**: Endpoint response time SHALL be < 200ms at p95 for normal load
- **PERF-002**: Endpoint SHALL support minimum 100 requests/second per instance
- **PERF-003**: Database queries SHALL use indexes for ID and common filters
- **PERF-004**: Response payload SHALL be < 5MB for single resource

### Data Validation Constraints

- **CON-001**: String fields SHALL be trimmed of leading/trailing whitespace
- **CON-002**: Required fields SHALL return 400 Bad Request if missing
- **CON-003**: Field length constraints SHALL be enforced as per schema
- **CON-004**: Enum values SHALL be validated against allowed list
- **CON-005**: Dates SHALL be validated for proper ISO 8601 format
- **CON-006**: Foreign key references SHALL be validated for existence

### API Design Guidelines

- **GUD-001**: Follow RESTful resource naming conventions (plural nouns)
- **GUD-002**: Use appropriate HTTP status codes (200, 201, 400, 401, 403, 404, 500)
- **GUD-003**: Include correlation ID in all responses for tracing
- **GUD-004**: Return consistent error response format across all endpoints
- **GUD-005**: Support content negotiation (Accept: application/json)
- **GUD-006**: Include API version in URL path (/v0/, /v1/)
- **GUD-007**: Use HATEOAS links for related resources (optional)

### Rate Limiting Patterns

- **PAT-001**: Apply rate limiting per authenticated user
- **PAT-002**: Return 429 Too Many Requests with Retry-After header
- **PAT-003**: Use token bucket or sliding window algorithm
- **PAT-004**: Different limits for read vs write operations

## 4. Interfaces & Data Contracts

### Endpoint Details

**Base URL**: `https://api.example.com`

**Full Path**: `${httpMethod} ${endpointPath}`

**Content-Type**: `application/json`

**Authentication**: Bearer JWT in Authorization header

### Path Parameters

${httpMethod === 'GET' || httpMethod === 'PUT' || httpMethod === 'PATCH' || httpMethod === 'DELETE' ? `
| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| userId | UUID | Yes | Unique identifier of the user | 123e4567-e89b-12d3-a456-426614174000 |
` : 'N/A - No path parameters for collection endpoint'}

### Query Parameters (for GET requests)

${httpMethod === 'GET' ? `
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| page | integer | No | 1 | Page number for pagination (min: 1) |
| per_page | integer | No | 20 | Items per page (min: 1, max: 100) |
| search | string | No | null | Search term for filtering |
| sort_by | string | No | created_at | Field to sort by |
| sort_order | string | No | desc | Sort direction (asc/desc) |
| is_active | boolean | No | null | Filter by active status |
` : 'N/A - Query parameters not applicable for this method'}

### Request Headers

```
Authorization: Bearer <jwt_token>
Content-Type: application/json
Accept: application/json
X-Correlation-ID: <optional-correlation-id>
Idempotency-Key: <optional-for-POST-PUT>
```

### Request Body Schema

${httpMethod === 'POST' || httpMethod === 'PUT' || httpMethod === 'PATCH' ? `
\`\`\`json
{
  "name": {
    "type": "string",
    "minLength": 1,
    "maxLength": 255,
    "required": true,
    "description": "Resource name"
  },
  "description": {
    "type": "string",
    "maxLength": 1000,
    "required": false,
    "description": "Optional description"
  },
  "is_active": {
    "type": "boolean",
    "required": ${httpMethod === 'PUT' ? 'true' : 'false'},
    "default": true,
    "description": "Active status flag"
  }
}
\`\`\`

#### Request Example

\`\`\`json
{
  "name": "Example Resource",
  "description": "This is an example resource for testing",
  "is_active": true
}
\`\`\`
` : 'N/A - No request body for GET/DELETE methods'}

### Response Body Schema

#### Success Response (200/201)

```json
{
  "data": {
    "id": "uuid",
    "name": "string",
    "description": "string",
    "is_active": "boolean",
    "created_at": "string (ISO 8601)",
    "updated_at": "string (ISO 8601)"
  },
  "message": "string (optional)"
}
```

${httpMethod === 'GET' && endpointPath.includes('{') === false ? `
#### Paginated List Response (200)

\`\`\`json
{
  "data": [
    {
      "id": "uuid",
      "name": "string",
      "is_active": "boolean",
      "created_at": "string",
      "updated_at": "string"
    }
  ],
  "page": 1,
  "per_page": 20,
  "total": 100,
  "total_pages": 5
}
\`\`\`
` : ''}

#### Error Response (4xx/5xx)

```json
{
  "message": "Human-readable error message",
  "errors": {
    "field_name": ["Specific error for this field"]
  },
  "correlation_id": "uuid"
}
```

### HTTP Status Codes

| Status Code | Meaning | When to Return |
|-------------|---------|----------------|
| 200 OK | Success (GET, PATCH, PUT) | Request processed successfully |
| 201 Created | Resource created (POST) | New resource created successfully |
| 204 No Content | Success (DELETE) | Resource deleted successfully |
| 400 Bad Request | Validation error | Invalid request data or parameters |
| 401 Unauthorized | Authentication failed | Missing or invalid JWT token |
| 403 Forbidden | Authorization failed | User lacks required permissions |
| 404 Not Found | Resource not found | Requested resource does not exist |
| 409 Conflict | Resource conflict | Duplicate resource or constraint violation |
| 429 Too Many Requests | Rate limit exceeded | User exceeded rate limit |
| 500 Internal Server Error | Server error | Unexpected server-side error |
| 503 Service Unavailable | Service unavailable | Dependency service is down |

### Response Headers

```
Content-Type: application/json
X-Correlation-ID: <correlation-id>
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1673123456
```

## 5. Acceptance Criteria

### Authentication & Authorization

- **AC-001**: Given a request without Authorization header, When endpoint is called, Then return 401 Unauthorized
- **AC-002**: Given an expired JWT token, When endpoint is called, Then return 401 Unauthorized with "Token expired" message
- **AC-003**: Given a valid JWT but insufficient permissions, When endpoint is called, Then return 403 Forbidden
- **AC-004**: Given a valid JWT with required permissions, When endpoint is called, Then process request normally

### Request Validation

- **AC-005**: Given a request with missing required field, When ${httpMethod} is called, Then return 400 with field-specific error
- **AC-006**: Given a request with invalid field type, When ${httpMethod} is called, Then return 400 with type error
- **AC-007**: Given a request with field exceeding max length, When ${httpMethod} is called, Then return 400 with length error
- **AC-008**: Given a request with invalid UUID format, When endpoint is called, Then return 400 with format error

### Business Logic

${httpMethod === 'POST' ? `
- **AC-009**: Given valid request data, When POST is called, Then create resource and return 201 with created resource
- **AC-010**: Given duplicate resource name, When POST is called, Then return 409 Conflict
- **AC-011**: Given valid creation, When POST succeeds, Then resource SHALL have generated UUID and timestamps
` : ''}

${httpMethod === 'GET' ? `
- **AC-009**: Given valid resource ID, When GET is called, Then return 200 with resource data
- **AC-010**: Given non-existent resource ID, When GET is called, Then return 404 Not Found
- **AC-011**: Given pagination parameters, When GET list is called, Then return paginated results with metadata
- **AC-012**: Given search parameter, When GET list is called, Then return only matching resources
` : ''}

${httpMethod === 'PUT' || httpMethod === 'PATCH' ? `
- **AC-009**: Given valid resource ID and update data, When ${httpMethod} is called, Then update resource and return 200
- **AC-010**: Given non-existent resource ID, When ${httpMethod} is called, Then return 404 Not Found
- **AC-011**: Given valid update, When ${httpMethod} succeeds, Then updated_at timestamp SHALL be updated
` : ''}

${httpMethod === 'DELETE' ? `
- **AC-009**: Given valid resource ID, When DELETE is called, Then delete resource and return 204
- **AC-010**: Given non-existent resource ID, When DELETE is called, Then return 404 Not Found
- **AC-011**: Given successful deletion, When DELETE completes, Then resource SHALL not be retrievable
` : ''}

### Performance & Rate Limiting

- **AC-012**: Given normal load, When endpoint is called, Then response time SHALL be < 200ms at p95
- **AC-013**: Given rate limit exceeded, When endpoint is called, Then return 429 with Retry-After header
- **AC-014**: Given concurrent requests, When endpoint is called multiple times, Then all requests SHALL be processed correctly

### Error Handling

- **AC-015**: Given database connection failure, When endpoint is called, Then return 503 Service Unavailable
- **AC-016**: Given Guardian service unavailable, When endpoint is called, Then return 503 with service error
- **AC-017**: Given any error response, When error occurs, Then include correlation_id in response
- **AC-018**: Given validation error, When endpoint is called, Then return detailed field-level error messages

## 6. Test Automation Strategy

### Test Levels

**Unit Tests** (70% coverage target)
- Schema validation logic
- Request parsing and transformation
- Response formatting
- Error handling logic

**Integration Tests** (20% coverage target)
- Full request/response cycle with test database
- Authentication and authorization flows
- External service integration (Guardian, Identity)
- Database transaction handling

**Contract Tests** (10% coverage target)
- API contract validation against OpenAPI spec
- Request/response schema compliance
- Backward compatibility verification

### Test Frameworks

- **pytest**: Main testing framework
- **pytest-flask**: Flask test fixtures
- **marshmallow**: Schema validation testing
- **responses**: HTTP mocking for external services
- **faker**: Test data generation

### Test Data Management

- Use fixtures for consistent test data
- Create/cleanup test resources in transaction
- Use factory pattern for test data generation
- Separate test data per test suite

### CI/CD Integration

- Run tests on every pull request
- Enforce 80% minimum code coverage
- Run contract tests against live staging API
- Performance tests in dedicated environment

### Coverage Requirements

- Line coverage: 80% minimum
- Branch coverage: 75% minimum
- Critical paths: 100% coverage
- Error handling: 100% coverage

## 7. Rationale & Context

### Design Decisions

**UUID for IDs**: UUIDs prevent ID enumeration attacks and support distributed systems without coordination.

**JWT Authentication**: JWTs are stateless, scalable, and support microservices architecture.

**Guardian Authorization**: Centralized RBAC service ensures consistent permissions across services.

**Rate Limiting**: Protects API from abuse and ensures fair resource allocation.

**ISO 8601 Timestamps**: Standard format ensures cross-platform compatibility and timezone handling.

**Pagination**: Limits response size and improves performance for large collections.

### Alternative Approaches Considered

- **Integer IDs**: Rejected due to enumeration vulnerability and distributed system limitations
- **Session-based Auth**: Rejected due to stateful nature incompatible with microservices
- **No Rate Limiting**: Rejected due to abuse and DoS attack risk

## 8. Dependencies & External Integrations

### External Systems

- **EXT-001**: Guardian Service - RBAC authorization checks via `/check-access` endpoint
- **EXT-002**: Identity Service - User/company information retrieval
- **EXT-003**: Database - PostgreSQL for persistent storage with JSONB support

### Third-Party Services

- **SVC-001**: JWT Provider - Token validation and signature verification
  - Must support RS256 algorithm
  - SLA: 99.9% availability
  - Response time: < 50ms

### Infrastructure Dependencies

- **INF-001**: Load Balancer - Distributes traffic across API instances
- **INF-002**: Redis Cache - Rate limiting state and session storage
- **INF-003**: Message Queue - Async operations and event publishing (optional)

### Data Dependencies

- **DAT-001**: Configuration Service - Runtime configuration and feature flags
- **DAT-002**: Logging Service - Structured logging with correlation IDs

### Technology Platform Dependencies

- **PLT-001**: Python 3.11+ - Runtime environment with typing support
- **PLT-002**: Flask 3.x - Web framework for REST API
- **PLT-003**: SQLAlchemy 2.x - ORM for database access
- **PLT-004**: Marshmallow 3.x - Schema validation and serialization

## 9. Examples & Edge Cases

### Successful Request Example

\`\`\`bash
curl -X ${httpMethod} https://api.example.com${endpointPath} \\
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \\
  -H "Content-Type: application/json" \\
  ${httpMethod !== 'GET' && httpMethod !== 'DELETE' ? `-d '{
    "name": "Example Resource",
    "description": "Test resource",
    "is_active": true
  }'` : ''}
\`\`\`

**Response (${httpMethod === 'POST' ? '201' : httpMethod === 'DELETE' ? '204' : '200'})**:
\`\`\`json
${httpMethod === 'DELETE' ? '(No body - 204 No Content)' : `{
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Example Resource",
    "description": "Test resource",
    "is_active": true,
    "created_at": "2024-01-07T10:30:00Z",
    "updated_at": "2024-01-07T10:30:00Z"
  }${httpMethod === 'POST' ? ',\n  "message": "Resource created successfully"' : ''}
}`}
\`\`\`

### Edge Cases

#### Empty String Handling
\`\`\`json
// Request with empty name
{
  "name": "",
  "description": "Test"
}

// Response 400
{
  "message": "Validation failed",
  "errors": {
    "name": ["Name cannot be empty or whitespace only"]
  }
}
\`\`\`

#### Null vs Missing Field
\`\`\`json
// Null value for optional field - ACCEPTED
{
  "name": "Test",
  "description": null
}

// Missing optional field - ACCEPTED (uses default)
{
  "name": "Test"
}
\`\`\`

#### Special Characters
\`\`\`json
// Valid special characters in name
{
  "name": "Test-Resource_2024 (v1.0)",
  "description": "UTF-8: 测试, Émoji: 🚀"
}
\`\`\`

#### Concurrent Updates (${httpMethod === 'PUT' || httpMethod === 'PATCH' ? 'applicable' : 'N/A'})
${httpMethod === 'PUT' || httpMethod === 'PATCH' ? `
Last-write-wins strategy. Later update overwrites earlier update.
Consider using optimistic locking with ETag header for conflict detection.
` : ''}

## 10. Validation Criteria

### Specification Compliance Checklist

- [ ] All requirements (REQ-xxx) are testable and unambiguous
- [ ] Security requirements (SEC-xxx) cover authentication, authorization, and data protection
- [ ] Performance requirements (PERF-xxx) have measurable targets
- [ ] Request/response schemas include all required fields with types
- [ ] All HTTP status codes are documented with usage conditions
- [ ] Error response format is consistent and includes correlation ID
- [ ] Acceptance criteria use Given-When-Then format
- [ ] Examples cover success cases and common edge cases
- [ ] Dependencies are clearly identified with rationale
- [ ] Test strategy defines coverage targets and frameworks

### OpenAPI Specification Validation

- [ ] Specification can be converted to valid OpenAPI 3.x YAML
- [ ] All request/response schemas validate with openapi-spec-validator
- [ ] Generated documentation is readable and complete
- [ ] API contract tests pass against specification

### Implementation Validation

- [ ] Implementation passes all acceptance criteria tests
- [ ] Response format matches specification exactly
- [ ] Error handling follows specified behavior
- [ ] Performance meets specified requirements
- [ ] Security controls are implemented as specified

## 11. Related Specifications / Further Reading

- [OpenAPI Specification 3.1.0](https://spec.openapis.org/oas/latest.html)
- [REST API Design Best Practices](https://restfulapi.net/)
- [HTTP Status Code Definitions](https://httpstatuses.com/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [Internal: API Versioning Strategy](../docs/api-versioning.md)
- [Internal: Authentication & Authorization Guide](../docs/auth-guide.md)
```

## Step-by-Step Process

### 1. Gather Information
Prompt user for:
- Endpoint path and HTTP method
- Resource name and operation description
- Special requirements (pagination, filtering, etc.)
- Business context and constraints

### 2. Analyze Existing Patterns
- Search codebase for similar endpoints
- Identify existing models and schemas
- Check authentication/authorization patterns
- Review error handling conventions

### 3. Generate Complete Specification
- Fill in template with gathered information
- Add appropriate requirements based on HTTP method
- Include relevant acceptance criteria
- Provide realistic examples

### 4. Create Specification File
- Save to `/spec/schema-api-${resourceName.toLowerCase()}-${httpMethod.toLowerCase()}.md`
- Follow naming convention
- Include proper front matter

### 5. Validate Specification
- Check completeness of all sections
- Verify examples are valid JSON
- Ensure requirements are testable
- Review acceptance criteria clarity

## Quality Checklist

- [ ] Specification follows template structure exactly
- [ ] All placeholders replaced with actual values
- [ ] Requirements use clear MUST/SHALL/SHOULD language
- [ ] Acceptance criteria follow Given-When-Then format
- [ ] Request/response examples are valid JSON
- [ ] HTTP status codes mapped to specific conditions
- [ ] Security requirements cover auth, authz, and data protection
- [ ] Performance requirements have measurable metrics
- [ ] Error handling is comprehensive
- [ ] Examples include edge cases
- [ ] Dependencies clearly identified
- [ ] Test strategy is actionable

## Output

After generating specification:
1. Save file to `/spec/` directory
2. Display file path and summary
3. List key requirements (REQ-xxx, SEC-xxx)
4. Suggest next steps (OpenAPI generation, implementation, tests)
