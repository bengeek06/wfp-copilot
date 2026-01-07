---
title: Prometheus Metrics Endpoint Specification
version: 1.0
date_created: 2026-01-07
last_updated: 2026-01-07
owner: Backend Team
tags: [infrastructure, monitoring, prometheus, observability, template]
---

# Introduction

This specification defines the `/metrics` endpoint that exposes Prometheus-compatible metrics for all Waterfall microservices built from the wfp-flask-template. This endpoint enables comprehensive monitoring and observability through Prometheus scraping.

## 1. Purpose & Scope

**Purpose:**
- Expose application, HTTP, and system metrics in Prometheus format
- Enable monitoring, alerting, and performance analysis
- Provide standardized metrics across all Waterfall services

**Scope:**
- Single endpoint: `/metrics`
- API key authentication required
- Prometheus text exposition format
- Included in base wfp-flask-template
- Uses `prometheus-flask-exporter` library

**Target Audience:**
- SRE/DevOps teams configuring Prometheus scraping
- Monitoring and alerting systems
- Performance analysis and capacity planning

**Assumptions:**
- Prometheus server deployed and configured
- API key distributed to Prometheus via configuration
- Services deployed on Kubernetes with service discovery

## 2. Definitions

| Term | Definition |
|------|------------|
| Prometheus | Open-source monitoring and alerting toolkit |
| Scraping | Prometheus pulling metrics from service endpoints |
| Metric | Time-series data point with labels (e.g., http_requests_total) |
| Label | Key-value pair attached to metric (e.g., method="GET") |
| Gauge | Metric that can go up or down (e.g., memory usage) |
| Counter | Metric that only increases (e.g., request count) |
| Histogram | Metric tracking distribution (e.g., response time buckets) |
| Exposition Format | Prometheus text-based format for metrics |

## 3. Requirements, Constraints & Guidelines

### Functional Requirements (REQ-xxx)

**REQ-001**: Service SHALL expose `/metrics` endpoint in Prometheus exposition format
**REQ-002**: Endpoint SHALL return `Content-Type: text/plain; version=0.0.4; charset=utf-8`
**REQ-003**: Endpoint SHALL expose HTTP request metrics (count, duration, status codes)
**REQ-004**: Endpoint SHALL expose system metrics (CPU, memory, threads)
**REQ-005**: Endpoint SHALL expose database connection pool metrics
**REQ-006**: Endpoint SHALL use `prometheus-flask-exporter` library
**REQ-007**: Endpoint SHALL be available without API version prefix (not `/v0/metrics`)
**REQ-008**: Metrics SHALL include labels: `method`, `endpoint`, `status_code`, `service_name`
**REQ-009**: HTTP duration metrics SHALL use histogram with standard buckets

### Security Requirements (SEC-xxx)

**SEC-001**: Endpoint SHALL require API key authentication via `Authorization: Bearer <key>` header
**SEC-002**: API key SHALL be configured via `METRICS_API_KEY` environment variable
**SEC-003**: Missing or invalid API key SHALL return 401 Unauthorized
**SEC-004**: Endpoint SHALL NOT expose sensitive data (credentials, tokens, PII)
**SEC-005**: Endpoint SHALL rate limit to 10 requests per minute per IP
**SEC-006**: API key SHALL be minimum 32 characters alphanumeric
**SEC-007**: Endpoint SHALL log authentication failures at WARNING level

### Performance Requirements (PERF-xxx)

**PERF-001**: Endpoint SHALL respond in < 100ms for typical metric payload
**PERF-002**: Metric collection SHALL NOT block request processing
**PERF-003**: Metrics SHALL be cached for 5 seconds (avoid computation on every scrape)
**PERF-004**: Endpoint SHALL handle concurrent Prometheus scrapers gracefully
**PERF-005**: Memory overhead for metrics SHALL be < 50MB

### Constraints (CON-xxx)

**CON-001**: Endpoint MUST use Prometheus text exposition format (not JSON)
**CON-002**: Endpoint MUST NOT use versioned routes (`/v0/`, `/v1/`)
**CON-003**: Metric names MUST follow Prometheus naming conventions (lowercase, underscores)
**CON-004**: METRICS_API_KEY environment variable MUST be set (no default)
**CON-005**: Histogram buckets MUST use standard Prometheus defaults

### Guidelines (GUD-xxx)

**GUD-001**: Use `prometheus-flask-exporter` for automatic Flask integration
**GUD-002**: Configure metrics in `app/__init__.py` on application startup
**GUD-003**: Do not create custom resource class (prometheus-flask-exporter handles it)
**GUD-004**: Add service name label from environment variable `SERVICE_NAME`
**GUD-005**: Exclude health endpoints from HTTP metrics (reduce noise)
**GUD-006**: Use standard Prometheus metric naming (suffixes: _total, _seconds, _bytes)

## 4. Interfaces & Data Contracts

### GET /metrics - Prometheus Metrics Endpoint

**Endpoint:** `GET /metrics`

**Description:** Exposes application metrics in Prometheus text exposition format for scraping by Prometheus server.

#### Path Parameters
None

#### Query Parameters
None

#### Request Headers

| Header | Required | Description | Example |
|--------|----------|-------------|---------|
| Authorization | Yes | Bearer token with API key | `Bearer abc123def456...` |

#### Request Body
None

#### Response Format

**Success Response (200 OK):**

```text
# HELP python_info Python platform information
# TYPE python_info gauge
python_info{implementation="CPython",major="3",minor="11",patchlevel="7",version="3.11.7"} 1.0

# HELP flask_http_request_duration_seconds Flask HTTP request duration in seconds
# TYPE flask_http_request_duration_seconds histogram
flask_http_request_duration_seconds_bucket{le="0.005",method="GET",path="/v0/projects",status="200"} 145.0
flask_http_request_duration_seconds_bucket{le="0.01",method="GET",path="/v0/projects",status="200"} 234.0
flask_http_request_duration_seconds_bucket{le="0.025",method="GET",path="/v0/projects",status="200"} 289.0
flask_http_request_duration_seconds_bucket{le="0.05",method="GET",path="/v0/projects",status="200"} 310.0
flask_http_request_duration_seconds_bucket{le="0.1",method="GET",path="/v0/projects",status="200"} 325.0
flask_http_request_duration_seconds_bucket{le="0.25",method="GET",path="/v0/projects",status="200"} 340.0
flask_http_request_duration_seconds_bucket{le="0.5",method="GET",path="/v0/projects",status="200"} 345.0
flask_http_request_duration_seconds_bucket{le="1.0",method="GET",path="/v0/projects",status="200"} 348.0
flask_http_request_duration_seconds_bucket{le="2.5",method="GET",path="/v0/projects",status="200"} 350.0
flask_http_request_duration_seconds_bucket{le="5.0",method="GET",path="/v0/projects",status="200"} 350.0
flask_http_request_duration_seconds_bucket{le="10.0",method="GET",path="/v0/projects",status="200"} 350.0
flask_http_request_duration_seconds_bucket{le="+Inf",method="GET",path="/v0/projects",status="200"} 350.0
flask_http_request_duration_seconds_count{method="GET",path="/v0/projects",status="200"} 350.0
flask_http_request_duration_seconds_sum{method="GET",path="/v0/projects",status="200"} 8.75

# HELP flask_http_request_total Total number of HTTP requests
# TYPE flask_http_request_total counter
flask_http_request_total{method="GET",status="200"} 1234.0
flask_http_request_total{method="POST",status="201"} 567.0
flask_http_request_total{method="GET",status="404"} 89.0
flask_http_request_total{method="POST",status="422"} 23.0

# HELP flask_http_request_exceptions_total Total number of HTTP requests which resulted in an exception
# TYPE flask_http_request_exceptions_total counter
flask_http_request_exceptions_total 5.0

# HELP process_virtual_memory_bytes Virtual memory size in bytes
# TYPE process_virtual_memory_bytes gauge
process_virtual_memory_bytes 234567890.0

# HELP process_resident_memory_bytes Resident memory size in bytes
# TYPE process_resident_memory_bytes gauge
process_resident_memory_bytes 123456789.0

# HELP process_cpu_seconds_total Total user and system CPU time spent in seconds
# TYPE process_cpu_seconds_total counter
process_cpu_seconds_total 123.45

# HELP sqlalchemy_pool_size Current size of the connection pool
# TYPE sqlalchemy_pool_size gauge
sqlalchemy_pool_size 5.0

# HELP sqlalchemy_pool_checked_in_connections Number of connections currently checked in to the pool
# TYPE sqlalchemy_pool_checked_in_connections gauge
sqlalchemy_pool_checked_in_connections 4.0

# HELP sqlalchemy_pool_checked_out_connections Number of connections currently checked out of the pool
# TYPE sqlalchemy_pool_checked_out_connections gauge
sqlalchemy_pool_checked_out_connections 1.0

# HELP sqlalchemy_pool_overflow Number of connections in overflow
# TYPE sqlalchemy_pool_overflow gauge
sqlalchemy_pool_overflow 0.0
```

**Error Response (401 Unauthorized - Missing API Key):**

```json
{
  "message": "Missing Authorization header",
  "timestamp": "2026-01-07T10:30:00Z"
}
```

**Error Response (401 Unauthorized - Invalid API Key):**

```json
{
  "message": "Invalid API key",
  "timestamp": "2026-01-07T10:30:00Z"
}
```

**Error Response (429 Too Many Requests):**

```json
{
  "message": "Rate limit exceeded: 10 per minute",
  "retry_after": 45
}
```

#### Status Codes

| Code | Description | When to Use |
|------|-------------|-------------|
| 200 | OK | Valid API key, metrics returned |
| 401 | Unauthorized | Missing or invalid API key |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Metrics collection failed |

#### Response Headers

**Success (200):**
```
Content-Type: text/plain; version=0.0.4; charset=utf-8
Cache-Control: no-cache, no-store, must-revalidate
```

**Error (401, 429):**
```
Content-Type: application/json
Cache-Control: no-cache, no-store, must-revalidate
```

## 5. Acceptance Criteria

### AC-001: Metrics Endpoint with Valid API Key
- **Given** METRICS_API_KEY environment variable is set
- **And** Authorization header contains valid Bearer token
- **When** GET /metrics is called
- **Then** response status is 200
- **And** response Content-Type is `text/plain; version=0.0.4; charset=utf-8`
- **And** response body contains Prometheus metrics in text format

### AC-002: Missing API Key
- **Given** METRICS_API_KEY is configured
- **And** no Authorization header is provided
- **When** GET /metrics is called
- **Then** response status is 401
- **And** response is JSON with "Missing Authorization header" message

### AC-003: Invalid API Key
- **Given** METRICS_API_KEY is "validkey123"
- **And** Authorization header is "Bearer wrongkey456"
- **When** GET /metrics is called
- **Then** response status is 401
- **And** response is JSON with "Invalid API key" message

### AC-004: HTTP Metrics Exposed
- **Given** application has received HTTP requests
- **When** GET /metrics is called with valid key
- **Then** response contains `flask_http_request_total` counter
- **And** response contains `flask_http_request_duration_seconds` histogram
- **And** metrics include labels: method, path, status

### AC-005: System Metrics Exposed
- **Given** application is running
- **When** GET /metrics is called with valid key
- **Then** response contains `process_virtual_memory_bytes` gauge
- **And** response contains `process_resident_memory_bytes` gauge
- **And** response contains `process_cpu_seconds_total` counter

### AC-006: Database Pool Metrics Exposed
- **Given** database connection pool is active
- **When** GET /metrics is called with valid key
- **Then** response contains `sqlalchemy_pool_size` gauge
- **And** response contains `sqlalchemy_pool_checked_out_connections` gauge

### AC-007: Health Endpoints Excluded
- **Given** /health endpoint has been called 100 times
- **When** GET /metrics is called
- **Then** /health requests are NOT included in flask_http_request_total
- **And** /ready and /version are also excluded

### AC-008: Rate Limiting
- **Given** 11 requests from same IP in 1 minute
- **When** request 11 is made
- **Then** response status is 429

### AC-009: Response Time
- **Given** typical metric payload (100 metric series)
- **When** GET /metrics is called
- **Then** response time is < 100ms

### AC-010: Metric Naming Conventions
- **Given** metrics are exposed
- **Then** all metric names use lowercase with underscores
- **And** counter metrics end with `_total` suffix
- **And** duration metrics end with `_seconds` suffix
- **And** size metrics end with `_bytes` suffix

## 6. Test Automation Strategy

**Test Levels:**
- Unit tests: API key validation logic
- Integration tests: Prometheus metric collection and formatting
- End-to-end tests: Prometheus scraping simulation

**Frameworks:**
- pytest for unit/integration tests
- FlaskClient for endpoint testing
- prometheus-client parser for validating metric format

**Test Data Management:**
- Mock METRICS_API_KEY environment variable
- Generate test HTTP traffic for metric collection
- Mock database connection pool

**CI/CD Integration:**
- Run on every commit
- Validate Prometheus format with parser
- Check for metric regression

**Coverage Requirements:**
- Minimum 85% code coverage for authentication logic
- All status codes tested
- Metric format validation

**Performance Testing:**
- Benchmark metric collection overhead
- Verify response time under load
- Test with 1000+ metric series

## 7. Rationale & Context

**Why API key authentication?**
- Metrics can reveal system architecture and traffic patterns
- Prevents unauthorized metric scraping
- Simpler than mTLS for initial implementation
- Sufficient security for internal Prometheus scraper

**Why text/plain format (not JSON)?**
- Prometheus standard exposition format
- More efficient for Prometheus parser
- Industry standard for metrics
- Better compression for large metric sets

**Why prometheus-flask-exporter?**
- Automatic Flask integration (decorators work automatically)
- Minimal configuration required
- Battle-tested in production
- Standard histogram buckets pre-configured

**Why exclude health endpoints?**
- Health endpoints called very frequently by K8s probes
- Would dominate metrics and create noise
- Not useful for application monitoring
- Can overwhelm Prometheus with cardinality

**Why 5-second cache?**
- Balance freshness vs performance
- Prometheus default scrape interval is 15s
- Reduces CPU overhead on each scrape
- Still provides near real-time metrics

**Why standard histogram buckets?**
- Compatible with Prometheus conventions
- Covers typical API response times (5ms to 10s)
- Enables accurate percentile calculations
- Industry best practice

## 8. Dependencies & External Integrations

### External Systems
- **EXT-001**: Prometheus Server - Metrics collection and storage system

### Infrastructure Dependencies
- **INF-001**: Kubernetes Service Discovery - For Prometheus to discover service endpoints
- **INF-002**: Network Policies - Allow Prometheus scraper access to /metrics

### Technology Platform Dependencies
- **PLT-001**: prometheus-flask-exporter - Python library for Flask metrics
- **PLT-002**: prometheus-client - Core Prometheus client library
- **PLT-003**: Flask web framework - For HTTP endpoint handling
- **PLT-004**: Python 3.11+ - Runtime environment

### Data Dependencies
- **DAT-001**: METRICS_API_KEY - Environment variable containing API key
- **DAT-002**: SERVICE_NAME - Environment variable for service identification

## 9. Examples & Edge Cases

### Example 1: Normal Scraping
```bash
# Prometheus scrapes metrics
curl -H "Authorization: Bearer your-secret-api-key-here" \
     http://localhost:5000/metrics

# Response: 200 OK (text/plain)
# HELP flask_http_request_total Total number of HTTP requests
# TYPE flask_http_request_total counter
flask_http_request_total{method="GET",status="200"} 1234.0
flask_http_request_total{method="POST",status="201"} 567.0
...
```

### Example 2: Missing Authorization Header
```bash
curl http://localhost:5000/metrics

# Response: 401 Unauthorized (application/json)
{
  "message": "Missing Authorization header",
  "timestamp": "2026-01-07T10:30:00Z"
}
```

### Example 3: Invalid API Key Format
```bash
curl -H "Authorization: InvalidFormat" \
     http://localhost:5000/metrics

# Response: 401 Unauthorized
{
  "message": "Invalid Authorization format. Expected: Bearer <key>",
  "timestamp": "2026-01-07T10:30:00Z"
}
```

### Example 4: Wrong API Key
```bash
curl -H "Authorization: Bearer wrong-key-123" \
     http://localhost:5000/metrics

# Response: 401 Unauthorized
{
  "message": "Invalid API key",
  "timestamp": "2026-01-07T10:30:00Z"
}
```

### Edge Case 1: METRICS_API_KEY Not Set
```bash
# Application startup fails
RuntimeError: METRICS_API_KEY environment variable not set
Application will not start without metrics API key configured
```

### Edge Case 2: Empty Metrics (New Service)
```bash
curl -H "Authorization: Bearer valid-key" \
     http://localhost:5000/metrics

# Response: 200 OK
# Only default Python/process metrics, no HTTP metrics yet
# HELP python_info Python platform information
# TYPE python_info gauge
python_info{implementation="CPython",major="3",minor="11"} 1.0
```

### Edge Case 3: High Cardinality Warning
```bash
# If endpoint includes dynamic IDs: /v0/projects/{uuid}
# Bad: flask_http_request_total{path="/v0/projects/uuid-1"} 1.0
#      flask_http_request_total{path="/v0/projects/uuid-2"} 1.0
#      (thousands of unique paths = cardinality explosion)

# Good: Normalize path before labeling
flask_http_request_total{path="/v0/projects/<uuid>"} 1234.0
```

### Edge Case 4: Metric Collection Failure
```bash
curl -H "Authorization: Bearer valid-key" \
     http://localhost:5000/metrics

# Response: 500 Internal Server Error
{
  "message": "Failed to collect metrics",
  "error": "Database connection pool not initialized",
  "timestamp": "2026-01-07T10:30:00Z"
}
```

## 10. Validation Criteria

- **VAL-001**: Response format validates against Prometheus text exposition format parser
- **VAL-002**: All metric names follow naming conventions (lowercase, underscores, suffixes)
- **VAL-003**: HTTP histogram includes all standard buckets (0.005 to 10.0 seconds)
- **VAL-004**: API key authentication rejects invalid/missing keys with 401
- **VAL-005**: Rate limiting triggers at 11th request within 1 minute
- **VAL-006**: Response time < 100ms for typical payload (< 500 metric series)
- **VAL-007**: Health endpoints (/health, /ready, /version) excluded from HTTP metrics
- **VAL-008**: Metric labels include: method, endpoint, status_code
- **VAL-009**: No sensitive data in metric labels or values
- **VAL-010**: Application fails to start if METRICS_API_KEY not set

## 11. Related Specifications / Further Reading

- [Prometheus Exposition Formats](https://prometheus.io/docs/instrumenting/exposition_formats/)
- [Prometheus Best Practices - Metric and Label Naming](https://prometheus.io/docs/practices/naming/)
- [prometheus-flask-exporter Documentation](https://github.com/rycus86/prometheus_flask_exporter)
- [Prometheus Python Client](https://github.com/prometheus/client_python)
- [Avoiding High Cardinality in Prometheus](https://prometheus.io/docs/practices/instrumentation/#do-not-overuse-labels)
- spec/schema-api-health-endpoints.md - Related health check endpoints
