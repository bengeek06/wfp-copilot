---
title: Health, Readiness and Version Endpoints Specification
version: 1.0
date_created: 2026-01-07
last_updated: 2026-01-07
owner: Backend Team
tags: [infrastructure, health-check, monitoring, template]
---

# Introduction

This specification defines three standard observability endpoints that MUST be present in all Waterfall microservices built from the wfp-flask-template. These endpoints enable Kubernetes health probes, monitoring, and version tracking without requiring authentication.

## 1. Purpose & Scope

**Purpose:**
- Provide standardized health checking for Kubernetes liveness and readiness probes
- Enable version tracking and debugging across deployed services
- Support operational observability and incident response

**Scope:**
- Three endpoints: `/health`, `/ready`, `/version`
- No authentication required (public endpoints)
- No API version prefix (available at root path)
- Included in base wfp-flask-template

**Target Audience:**
- DevOps/SRE teams configuring Kubernetes probes
- Monitoring systems and dashboards
- Developers debugging deployment issues

**Assumptions:**
- Services deployed on Kubernetes clusters
- PostgreSQL database as primary data store
- Optional Redis cache
- VERSION file exists at repository root

## 2. Definitions

| Term | Definition |
|------|------------|
| Liveness Probe | Kubernetes mechanism to detect if a container needs restart |
| Readiness Probe | Kubernetes mechanism to detect if a container can accept traffic |
| Degraded State | Service is running but one or more non-critical dependencies are unavailable |
| Health Check | Verification that service and dependencies are functioning |
| SemVer | Semantic Versioning (MAJOR.MINOR.PATCH) |

## 3. Requirements, Constraints & Guidelines

### Functional Requirements (REQ-xxx)

**REQ-001**: Service SHALL expose three health endpoints: `/health`, `/ready`, `/version`
**REQ-002**: Endpoints SHALL be available without API version prefix (not `/v0/health`)
**REQ-003**: Endpoints SHALL NOT require authentication or JWT token
**REQ-004**: `/health` endpoint SHALL check database connectivity
**REQ-005**: `/ready` endpoint SHALL check all critical dependencies (DB, external services)
**REQ-006**: `/version` endpoint SHALL read version from `VERSION` file at repository root
**REQ-007**: All endpoints SHALL return JSON responses
**REQ-008**: Endpoints SHALL be registered before versioned API routes

### Security Requirements (SEC-xxx)

**SEC-001**: Endpoints SHALL NOT require JWT authentication (public access)
**SEC-002**: Endpoints SHALL NOT expose sensitive information (credentials, internal IPs, stack traces)
**SEC-003**: Endpoints SHALL rate limit to 100 requests per minute per IP
**SEC-004**: Database health checks SHALL use read-only queries
**SEC-005**: Version information SHALL NOT include developer names or internal paths

### Performance Requirements (PERF-xxx)

**PERF-001**: `/health` endpoint SHALL respond in < 200ms (99th percentile)
**PERF-002**: `/ready` endpoint SHALL respond in < 500ms (99th percentile)
**PERF-003**: `/version` endpoint SHALL respond in < 50ms (cached file read)
**PERF-004**: Health checks SHALL use connection pooling (no new connections)
**PERF-005**: Health checks SHALL timeout after 3 seconds

### Constraints (CON-xxx)

**CON-001**: Endpoints MUST NOT use versioned routes (`/v0/`, `/v1/`)
**CON-002**: VERSION file MUST exist at repository root
**CON-003**: Database check MUST be a lightweight query (e.g., `SELECT 1`)
**CON-004**: Responses MUST be valid JSON (not plain text)

### Guidelines (GUD-xxx)

**GUD-001**: Use `HealthResource`, `ReadyResource`, `VersionResource` class names
**GUD-002**: Place resources in `app/resources/health.py`
**GUD-003**: Do not create database models for these endpoints
**GUD-004**: Cache VERSION file content on application startup
**GUD-005**: Log health check failures at WARNING level (not ERROR)

## 4. Interfaces & Data Contracts

### 4.1 GET /health - Liveness Probe

**Endpoint:** `GET /health`

**Description:** Checks if the application is alive and functioning. Used by Kubernetes liveness probes to detect if the container needs restart.

#### Path Parameters
None

#### Query Parameters
None

#### Request Headers
None required

#### Request Body
None

#### Response Schemas

**Success Response (200 OK - Healthy):**
```json
{
  "status": "ok",
  "timestamp": "2026-01-07T10:30:00Z",
  "checks": {
    "database": {
      "status": "ok",
      "response_time_ms": 15
    }
  }
}
```

**Success Response (200 OK - Degraded):**
```json
{
  "status": "degraded",
  "timestamp": "2026-01-07T10:30:00Z",
  "checks": {
    "database": {
      "status": "error",
      "response_time_ms": 3000,
      "error": "Connection timeout"
    }
  }
}
```

**Error Response (500 Internal Server Error):**
```json
{
  "status": "error",
  "timestamp": "2026-01-07T10:30:00Z",
  "error": "Application initialization failed"
}
```

#### Status Codes

| Code | Description | When to Use |
|------|-------------|-------------|
| 200 | OK | Service is alive (even if degraded) |
| 500 | Internal Server Error | Application itself is broken (not dependencies) |

#### Response Headers
```
Content-Type: application/json
Cache-Control: no-cache, no-store, must-revalidate
```

---

### 4.2 GET /ready - Readiness Probe

**Endpoint:** `GET /ready`

**Description:** Checks if the application is ready to accept traffic. Used by Kubernetes readiness probes to control load balancer routing.

#### Path Parameters
None

#### Query Parameters
None

#### Request Headers
None required

#### Request Body
None

#### Response Schemas

**Success Response (200 OK - Ready):**
```json
{
  "status": "ready",
  "timestamp": "2026-01-07T10:30:00Z",
  "checks": {
    "database": {
      "status": "ok",
      "response_time_ms": 12
    },
    "redis": {
      "status": "ok",
      "response_time_ms": 5
    },
    "guardian_service": {
      "status": "ok",
      "response_time_ms": 45
    }
  }
}
```

**Error Response (503 Service Unavailable - Not Ready):**
```json
{
  "status": "not_ready",
  "timestamp": "2026-01-07T10:30:00Z",
  "checks": {
    "database": {
      "status": "error",
      "response_time_ms": 3000,
      "error": "Connection refused"
    },
    "redis": {
      "status": "ok",
      "response_time_ms": 5
    },
    "guardian_service": {
      "status": "ok",
      "response_time_ms": 45
    }
  }
}
```

#### Status Codes

| Code | Description | When to Use |
|------|-------------|-------------|
| 200 | OK | Service is ready to accept traffic |
| 503 | Service Unavailable | Critical dependency unavailable (DB, required external service) |

#### Response Headers
```
Content-Type: application/json
Cache-Control: no-cache, no-store, must-revalidate
```

---

### 4.3 GET /version - Version Information

**Endpoint:** `GET /version`

**Description:** Returns version information about the deployed service for debugging and tracking.

#### Path Parameters
None

#### Query Parameters
None

#### Request Headers
None required

#### Request Body
None

#### Response Schemas

**Success Response (200 OK):**
```json
{
  "version": "1.2.3",
  "git_commit": "a1b2c3d",
  "build_date": "2026-01-07T08:00:00Z",
  "environment": "production"
}
```

**Error Response (500 Internal Server Error):**
```json
{
  "error": "VERSION file not found",
  "timestamp": "2026-01-07T10:30:00Z"
}
```

#### Status Codes

| Code | Description | When to Use |
|------|-------------|-------------|
| 200 | OK | Version information retrieved |
| 500 | Internal Server Error | VERSION file missing or unreadable |

#### Response Headers
```
Content-Type: application/json
Cache-Control: public, max-age=3600
```

## 5. Acceptance Criteria

### AC-001: /health Endpoint
- **Given** the application is running
- **When** GET /health is called
- **Then** response status is 200
- **And** response contains "status" field with value "ok" or "degraded"
- **And** response contains "timestamp" in ISO 8601 format
- **And** response contains "checks.database" object

### AC-002: /health with Database Down
- **Given** the database is unavailable
- **When** GET /health is called
- **Then** response status is 200 (not 503)
- **And** "status" field is "degraded"
- **And** "checks.database.status" is "error"
- **And** "checks.database.error" contains error description

### AC-003: /ready Endpoint Success
- **Given** all critical dependencies are available
- **When** GET /ready is called
- **Then** response status is 200
- **And** "status" field is "ready"
- **And** all checks show "status": "ok"

### AC-004: /ready with Database Down
- **Given** the database is unavailable
- **When** GET /ready is called
- **Then** response status is 503
- **And** "status" field is "not_ready"
- **And** "checks.database.status" is "error"

### AC-005: /version Endpoint
- **Given** VERSION file exists at repository root
- **When** GET /version is called
- **Then** response status is 200
- **And** response contains "version" field from VERSION file
- **And** response contains "git_commit" field
- **And** response contains "build_date" field
- **And** version follows SemVer format (e.g., "1.2.3")

### AC-006: No Authentication Required
- **Given** no JWT token provided
- **When** any health endpoint is called
- **Then** response is successful (not 401 Unauthorized)

### AC-007: Rate Limiting
- **Given** 101 requests from same IP in 1 minute
- **When** request 101 is made
- **Then** response status is 429 Too Many Requests

### AC-008: Response Time
- **Given** healthy system
- **When** GET /health is called
- **Then** response time is < 200ms (99th percentile)

## 6. Test Automation Strategy

**Test Levels:**
- Unit tests: Health check logic, version file parsing
- Integration tests: Database connectivity, external service checks
- End-to-end tests: Kubernetes probe simulation

**Frameworks:**
- pytest for unit/integration tests
- FlaskClient for endpoint testing
- Docker Compose for integration test dependencies

**Test Data Management:**
- Mock VERSION file content
- Mock database connection success/failure
- Mock external service responses

**CI/CD Integration:**
- Run on every commit
- Required for PR approval
- Part of deployment pipeline

**Coverage Requirements:**
- Minimum 90% code coverage for health resources
- All status codes tested
- All error scenarios covered

**Performance Testing:**
- Load test with 1000 req/s
- Verify response times under load
- Ensure no memory leaks in health checks

## 7. Rationale & Context

**Why no authentication?**
- Kubernetes probes cannot provide JWT tokens
- Health endpoints don't expose sensitive data
- Rate limiting provides sufficient protection

**Why separate /health and /ready?**
- Kubernetes best practice: separate liveness from readiness
- Prevents unnecessary pod restarts due to transient dependency failures
- Allows graceful degradation while maintaining service availability

**Why read VERSION from file?**
- Single source of truth for versioning
- No need to update code for version bumps
- CI/CD can inject version during build

**Why 200 for degraded state?**
- Avoid pod restarts when only dependencies are down
- Service itself is functional
- Allows monitoring to alert without immediate action

**Why detailed checks object?**
- Enables better debugging and incident response
- Monitoring dashboards can show which dependency is failing
- No need to check logs for basic health issues

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: PostgreSQL Database - Primary data store for all services
- **EXT-002**: Redis Cache - Optional caching layer
- **EXT-003**: Guardian Service - Authorization service (optional dependency)
- **EXT-004**: Identity Service - Authentication service (optional dependency)

### Infrastructure Dependencies
- **INF-001**: Kubernetes - Container orchestration platform
- **INF-002**: Load Balancer - Routes traffic based on readiness
- **INF-003**: Monitoring - Prometheus/Grafana for metrics

### Data Dependencies
- **DAT-001**: VERSION file - Text file at repository root containing SemVer version

### Technology Platform Dependencies
- **PLT-001**: Flask web framework - For HTTP endpoint handling
- **PLT-002**: SQLAlchemy - For database connection pooling and queries
- **PLT-003**: Python 3.11+ - Runtime environment

## 9. Examples & Edge Cases

### Example 1: Normal Operation
```bash
# Health check - all systems operational
curl http://localhost:5000/health

# Response: 200 OK
{
  "status": "ok",
  "timestamp": "2026-01-07T10:30:00Z",
  "checks": {
    "database": {
      "status": "ok",
      "response_time_ms": 15
    }
  }
}
```

### Example 2: Database Degraded
```bash
# Health check - database slow but responding
curl http://localhost:5000/health

# Response: 200 OK (degraded but not down)
{
  "status": "degraded",
  "timestamp": "2026-01-07T10:30:00Z",
  "checks": {
    "database": {
      "status": "error",
      "response_time_ms": 2800,
      "error": "Query timeout exceeded 2000ms threshold"
    }
  }
}
```

### Example 3: Readiness Check Failure
```bash
# Ready check - database unavailable
curl http://localhost:5000/ready

# Response: 503 Service Unavailable
{
  "status": "not_ready",
  "timestamp": "2026-01-07T10:30:00Z",
  "checks": {
    "database": {
      "status": "error",
      "response_time_ms": 3000,
      "error": "Connection refused: [Errno 111] Connection refused"
    },
    "redis": {
      "status": "ok",
      "response_time_ms": 5
    }
  }
}
```

### Example 4: Version Information
```bash
# Version check
curl http://localhost:5000/version

# Response: 200 OK
{
  "version": "1.2.3",
  "git_commit": "a1b2c3d",
  "build_date": "2026-01-07T08:00:00Z",
  "environment": "production"
}
```

### Edge Case 1: Missing VERSION File
```bash
curl http://localhost:5000/version

# Response: 500 Internal Server Error
{
  "error": "VERSION file not found at repository root",
  "timestamp": "2026-01-07T10:30:00Z"
}
```

### Edge Case 2: Database Connection Pool Exhausted
```bash
curl http://localhost:5000/ready

# Response: 503 Service Unavailable
{
  "status": "not_ready",
  "timestamp": "2026-01-07T10:30:00Z",
  "checks": {
    "database": {
      "status": "error",
      "response_time_ms": 3000,
      "error": "Connection pool exhausted: QueuePool limit of size 10 overflow 10 reached"
    }
  }
}
```

### Edge Case 3: Multiple Rapid Health Checks
```bash
# 100 requests in quick succession
for i in {1..100}; do curl http://localhost:5000/health; done

# All succeed: 200 OK
# Request 101:
curl http://localhost:5000/health

# Response: 429 Too Many Requests
{
  "message": "Rate limit exceeded: 100 per minute",
  "retry_after": 45
}
```

## 10. Validation Criteria

- **VAL-001**: All three endpoints return valid JSON (validated with jsonschema)
- **VAL-002**: /health returns 200 in all scenarios except application crash
- **VAL-003**: /ready returns 503 when any critical dependency is down
- **VAL-004**: /version matches content of VERSION file
- **VAL-005**: Response times meet performance requirements (PERF-001, PERF-002, PERF-003)
- **VAL-006**: No authentication errors (401) when called without token
- **VAL-007**: Rate limiting triggers at 101st request within 1 minute
- **VAL-008**: Database health check uses `SELECT 1` query (lightweight)
- **VAL-009**: No sensitive information in error messages
- **VAL-010**: Timestamps use ISO 8601 format with UTC timezone

## 11. Related Specifications / Further Reading

- [Kubernetes Liveness and Readiness Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Health Check Response Format for HTTP APIs (RFC Draft)](https://datatracker.ietf.org/doc/html/draft-inadarei-api-health-check)
- [Semantic Versioning 2.0.0](https://semver.org/)
- [wfp-flask-template Architecture Documentation](../docs/architecture.md)
- [Guardian Service Integration Guide](../docs/guardian-integration.md)
