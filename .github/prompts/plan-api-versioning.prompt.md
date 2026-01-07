---
description: "Plan API versioning strategy including URL/header versioning, deprecation policy, backward compatibility, and migration timeline"
agent: "API Architect"
tools: ["search", "search/codebase", "web/fetch"]
---

# Plan API Versioning Strategy

You are an expert in API versioning and lifecycle management. Design comprehensive API versioning strategies covering versioning schemes, deprecation policies, backward compatibility guidelines, migration timelines, and multi-version support patterns.

## Task

Create versioning strategy for:
- **Versioning scheme** (URL, header, content negotiation)
- **Version format** (semantic versioning, date-based)
- **Deprecation policy** (timeline, warnings, sunset)
- **Backward compatibility** rules
- **Breaking change guidelines** (when to bump major version)
- **Multi-version support** (how many versions to maintain)
- **Migration timeline** (announcement → deprecation → removal)
- **Version discovery** (how clients know about versions)
- **Documentation per version**

## Input Variables

- `${input:apiName}` - API name (e.g., Projects API, Tasks API)
- `${input:currentVersion}` - Current version (e.g., 1.2.0)
- `${input:versioningType}` - Versioning type (URL, header, content-type)
- `${input:breakingChanges}` - Planned breaking changes

## Versioning Schemes

### 1. URL Versioning (Recommended)

Most explicit and discoverable approach:

**Pattern**: `https://api.example.com/{version}/{resource}`

```http
# Version in URL path
GET https://api.example.com/v1/projects
GET https://api.example.com/v2/projects

# Major version only
GET https://api.example.com/v1/projects
GET https://api.example.com/v2/projects

# Major.minor version (less common)
GET https://api.example.com/v1.2/projects
GET https://api.example.com/v2.0/projects
```

**Pros**:
- ✅ Explicit and visible in URLs
- ✅ Easy to test different versions
- ✅ Simple to route and cache
- ✅ Clear in logs and monitoring
- ✅ No special headers needed

**Cons**:
- ❌ URL changes when version changes
- ❌ Multiple URLs for same resource

**Best for**: Public APIs, RESTful services, microservices

**Implementation**:
```python
# Flask routing
from flask import Blueprint

api_v1 = Blueprint('api_v1', __name__, url_prefix='/v1')
api_v2 = Blueprint('api_v2', __name__, url_prefix='/v2')

@api_v1.route('/projects')
def list_projects_v1():
    # v1 implementation
    return jsonify({"data": projects, "meta": metadata})

@api_v2.route('/projects')
def list_projects_v2():
    # v2 implementation (different response structure)
    return jsonify({"items": projects, "total": len(projects)})

app.register_blueprint(api_v1)
app.register_blueprint(api_v2)
```

### 2. Header Versioning

Version in custom header:

**Pattern**: `Accept-Version` or `API-Version` header

```http
GET https://api.example.com/projects
Accept-Version: v1

GET https://api.example.com/projects
API-Version: 2.0
```

**Pros**:
- ✅ URL stays constant
- ✅ Clean URLs
- ✅ Can version per request

**Cons**:
- ❌ Less visible (hidden in headers)
- ❌ Harder to test in browser
- ❌ Can be forgotten by clients
- ❌ Complicates caching

**Best for**: Internal APIs, versioned by client type

**Implementation**:
```python
from flask import request

@app.route('/projects')
def list_projects():
    version = request.headers.get('API-Version', 'v1')
    
    if version == 'v1':
        return jsonify({"data": projects, "meta": metadata})
    elif version == 'v2':
        return jsonify({"items": projects, "total": len(projects)})
    else:
        return jsonify({"error": "Unsupported API version"}), 400
```

### 3. Content Negotiation

Version in `Accept` or `Content-Type` header:

**Pattern**: Custom media type

```http
GET https://api.example.com/projects
Accept: application/vnd.example.v1+json

GET https://api.example.com/projects
Accept: application/vnd.example.v2+json
```

**Pros**:
- ✅ RESTful and standards-compliant
- ✅ Follows HTTP spec
- ✅ Can version request and response separately

**Cons**:
- ❌ Complex to implement
- ❌ Less discoverable
- ❌ Not well understood by developers

**Best for**: Mature REST APIs following strict REST principles

### 4. Query Parameter Versioning

Version in query string (NOT recommended):

```http
GET https://api.example.com/projects?version=1
GET https://api.example.com/projects?api_version=2
```

**Pros**:
- ✅ Easy to add to existing API

**Cons**:
- ❌ Pollutes query parameters
- ❌ Caching issues
- ❌ Can conflict with resource filters
- ❌ Not RESTful

**Best for**: Temporary versioning, legacy migrations only

## Version Format

### Semantic Versioning (Recommended)

**Format**: `MAJOR.MINOR.PATCH`

```
v1.0.0 → v1.0.1 → v1.1.0 → v2.0.0

MAJOR: Breaking changes (incompatible API changes)
MINOR: New features (backward compatible)
PATCH: Bug fixes (backward compatible)
```

**In URLs**: Use major version only

```http
# URL uses major version
GET /v1/projects  (represents v1.x.x)
GET /v2/projects  (represents v2.x.x)

# Full version in response headers
X-API-Version: 1.2.3
```

**Version Bumping Rules**:

```markdown
## When to Bump MAJOR (v1.x.x → v2.0.0)

Breaking changes that require client updates:
- Removing endpoints or fields
- Changing field types (string → integer)
- Changing response structure (data → items)
- Changing authentication method
- Changing error format
- Removing query parameters
- Changing HTTP methods for endpoints
- Changing URL patterns

## When to Bump MINOR (v1.0.x → v1.1.0)

New features that are backward compatible:
- Adding new endpoints
- Adding optional fields to requests
- Adding new fields to responses
- Adding new query parameters
- Adding new enum values (at end)
- Improving performance
- Adding new error codes

## When to Bump PATCH (v1.0.0 → v1.0.1)

Bug fixes and maintenance:
- Fixing bugs
- Correcting documentation
- Security patches (non-breaking)
- Performance optimizations
- Internal refactoring
```

### Date-Based Versioning

**Format**: `YYYY-MM-DD` or `YYYY-MM`

```http
GET /2026-01-01/projects
GET /2026-01/projects
```

**Pros**:
- ✅ Clear when version was released
- ✅ Predictable release schedule

**Cons**:
- ❌ Doesn't indicate breaking changes
- ❌ Multiple releases per month unclear

**Best for**: APIs with scheduled releases (e.g., AWS)

## Deprecation Policy

### Deprecation Timeline

**Standard Timeline**: 6 months notice for breaking changes

```markdown
## Deprecation Lifecycle

### Phase 1: Announcement (Month 0)
- Announce deprecation in changelog
- Add deprecation notices to documentation
- Email API consumers
- Blog post and social media
- Update OpenAPI spec with `deprecated: true`

### Phase 2: Warning Period (Months 1-3)
- Add `Deprecation` header to responses:
  ```
  Deprecation: true
  Sunset: Sat, 01 Jun 2026 23:59:59 GMT
  Link: <https://docs.example.com/migration>; rel="deprecation"
  ```
- Log usage of deprecated endpoints
- Send automated emails to users still using deprecated features
- Provide migration tools/scripts

### Phase 3: Final Warning (Months 4-5)
- Increase warning visibility
- Personalized outreach to heavy users
- Offer migration assistance
- Final reminder 1 month before sunset

### Phase 4: Sunset (Month 6)
- Remove deprecated features
- Return 410 Gone for deprecated endpoints
- Redirect traffic to new version
- Monitor for issues

### Phase 5: Post-Sunset
- Continue monitoring for 2 weeks
- Provide support for urgent migrations
- Document lessons learned
```

### Deprecation Headers

Use standard HTTP headers:

```http
# Response from deprecated endpoint
HTTP/1.1 200 OK
Deprecation: true
Sunset: Sat, 01 Jun 2026 23:59:59 GMT
Link: <https://docs.example.com/api/v2/migration>; rel="deprecation"
Warning: 299 - "This endpoint is deprecated and will be removed on 2026-06-01. Use /v2/projects instead."
X-API-Deprecated-Version: 1
X-API-Current-Version: 2
```

**Implementation**:
```python
from datetime import datetime
from flask import make_response, jsonify

def add_deprecation_headers(response, sunset_date, new_endpoint=None):
    """Add deprecation headers to response."""
    response.headers['Deprecation'] = 'true'
    response.headers['Sunset'] = sunset_date.strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    if new_endpoint:
        response.headers['Link'] = f'<https://docs.example.com/migration>; rel="deprecation"'
        response.headers['Warning'] = (
            f'299 - "This endpoint is deprecated. Use {new_endpoint} instead. '
            f'Removal date: {sunset_date.date()}"'
        )
    
    return response

@app.route('/v1/projects/<project_id>/stats')
def project_stats_v1(project_id):
    """Deprecated endpoint."""
    # Return stats data
    stats = get_project_stats(project_id)
    response = make_response(jsonify(stats))
    
    # Add deprecation headers
    sunset_date = datetime(2026, 6, 1, 23, 59, 59)
    response = add_deprecation_headers(
        response,
        sunset_date,
        new_endpoint='/v2/projects/{id}/analytics'
    )
    
    return response
```

## Backward Compatibility Rules

### Always Backward Compatible

Safe changes that don't break existing clients:

```markdown
✅ Adding new endpoints
✅ Adding optional request fields
✅ Adding response fields (at end)
✅ Adding new query parameters (optional)
✅ Adding new HTTP headers (optional)
✅ Making required fields optional
✅ Relaxing validation rules
✅ Adding new enum values (at end of list)
✅ Improving error messages
✅ Improving performance
✅ Adding new response status codes (for new error cases)
```

### Breaking Changes

Changes that require major version bump:

```markdown
❌ Removing endpoints
❌ Removing request fields
❌ Removing response fields
❌ Making optional fields required
❌ Changing field types (string → int)
❌ Changing field names
❌ Changing response structure
❌ Changing HTTP status codes (200 → 201)
❌ Changing authentication method
❌ Changing error response format
❌ Removing query parameters
❌ Changing URL patterns
❌ Removing enum values
❌ Reordering array items (if order is significant)
```

### Maybe Breaking

Changes that might break some clients:

```markdown
⚠️ Adding required request fields (with defaults)
⚠️ Adding response fields (at beginning of object)
⚠️ Changing default values
⚠️ Tightening validation rules
⚠️ Changing rate limits
⚠️ Changing pagination defaults
⚠️ Reordering object fields (if client depends on order)
⚠️ Changing empty responses ([] vs null)
⚠️ Adding new error codes
```

**Guideline**: If in doubt, treat as breaking change.

## Multi-Version Support Strategy

### How Many Versions to Support

**Recommended**: Support N and N-1 (current and previous major version)

```markdown
## Version Support Policy

### Current Version (v2.x)
- ✅ Full support
- ✅ New features added
- ✅ Bug fixes and security patches
- ✅ Performance improvements
- ✅ Active development

### Previous Version (v1.x)
- ✅ Security patches only
- ✅ Critical bug fixes
- ⚠️ No new features
- ⚠️ Deprecated (sunset in 6 months)
- 📧 Migration support available

### Older Versions (v0.x)
- ❌ No support
- ❌ Returns 410 Gone
- 📄 Archived documentation available
```

### Support Timeline

```
v1.0.0 ───────────────────────────────────────────────────────────┐
         │ Active Development │ Security Only │ Deprecated │ Sunset │
         │                    │               │            │        │
         └────────────────────┴───────────────┴────────────┴────────┘
         Jan 2025            Jan 2026        Apr 2026     Jul 2026

v2.0.0                       ──────────────────────────────────────┐
                             │ Active Development                   │
                             │                                      │
                             └──────────────────────────────────────┘
                             Jan 2026                         Ongoing

Timeline:
- v1: 18 months active development
- v1: 6 months security-only support
- v1: 3 months deprecation warning
- v1: Sunset after 27 months total
```

## Migration Strategy

### Migration Communication Plan

```markdown
## Migration Communication Timeline

### T-180 days (6 months before)
- 📢 Blog post announcing v2.0
- 📧 Email to all API users
- 📄 Migration guide published
- 🔧 Migration tools released
- 📝 Updated documentation

### T-120 days (4 months before)
- 📧 First reminder email
- 📊 Usage analytics shared (who's on v1)
- 🎥 Migration webinar
- 💬 Office hours for migration questions

### T-60 days (2 months before)
- 📧 Second reminder email
- ⚠️ Deprecation warnings in API responses
- 📞 Direct outreach to high-volume users
- 🆘 Priority support for migration issues

### T-30 days (1 month before)
- 📧 Final warning email
- 🚨 Increased warning visibility
- 📞 Personal calls to users still on v1
- 🔥 Last-chance migration assistance

### T-0 (Sunset day)
- 🛑 v1 endpoints return 410 Gone
- 📧 Sunset announcement
- 📞 Emergency support line
- 📊 Monitor traffic and errors

### T+14 days (2 weeks after)
- 📊 Post-mortem analysis
- 📧 Thank you email to migrated users
- 📝 Document lessons learned
- 🔍 Cleanup and optimization
```

### Migration Tools

Provide tools to assist migration:

```markdown
## Migration Assistance

### 1. Version Compatibility Checker

Script to test client compatibility:

```bash
# Check if your requests are compatible with v2
curl -X POST https://api.example.com/v2/compatibility-check \
  -H "Content-Type: application/json" \
  -d @your-request.json

# Response:
{
  "compatible": false,
  "issues": [
    {
      "field": "priority",
      "issue": "Expected integer, got string",
      "fix": "Change 'medium' to 2"
    }
  ]
}
```

### 2. Request Transformer

Automatically convert v1 requests to v2:

```python
# Migration helper library
from api_migration import V1toV2Transformer

transformer = V1toV2Transformer()

# Transform v1 request to v2 format
v1_request = {"name": "Project", "priority": "medium"}
v2_request = transformer.transform(v1_request)
# Output: {"name": "Project", "priority": 2}
```

### 3. Response Adapter

Wrap v2 API to return v1-compatible responses:

```python
from api_migration import V2toV1Adapter

# Temporary adapter for gradual migration
adapter = V2toV1Adapter(base_url="https://api.example.com/v2")

# Make v2 call, receive v1-formatted response
response = adapter.get("/projects")
# v2 returns: {"items": [...], "total": 10}
# Adapter returns: {"data": [...], "meta": {"total": 10}}
```

### 4. Traffic Analyzer

Identify v1 usage patterns:

```bash
# Analyze your API usage
curl https://api.example.com/v1/usage-report \
  -H "Authorization: Bearer YOUR_TOKEN"

# Response:
{
  "total_requests_last_30_days": 15000,
  "deprecated_endpoints": [
    {
      "endpoint": "/projects/:id/stats",
      "requests": 3000,
      "percentage": 20,
      "replacement": "/projects/:id/analytics"
    }
  ],
  "migration_readiness": "60%"
}
```
```

## Version Discovery

Help clients discover available versions:

```http
# OPTIONS request to root
OPTIONS https://api.example.com/

HTTP/1.1 200 OK
Link: <https://api.example.com/v1>; rel="version"; version="1.2.3"
Link: <https://api.example.com/v2>; rel="version"; version="2.0.0"; current="true"
X-API-Versions: v1, v2
X-API-Current-Version: v2
X-API-Deprecated-Versions: v1

# Version info endpoint
GET https://api.example.com/versions

{
  "current": {
    "version": "2.0.0",
    "url": "https://api.example.com/v2",
    "docs": "https://docs.example.com/api/v2",
    "released": "2026-01-15"
  },
  "supported": [
    {
      "version": "1.2.3",
      "url": "https://api.example.com/v1",
      "docs": "https://docs.example.com/api/v1",
      "status": "deprecated",
      "sunset": "2026-07-01",
      "released": "2025-10-15"
    }
  ],
  "sunset": [
    {
      "version": "0.9.0",
      "status": "removed",
      "sunset": "2025-12-01"
    }
  ]
}
```

## Documentation Strategy

### Per-Version Documentation

Maintain separate documentation for each version:

```
docs/
├── api/
│   ├── current/              # Always points to latest
│   ├── v2/
│   │   ├── openapi.yaml
│   │   ├── README.md
│   │   ├── getting-started.md
│   │   └── migration-from-v1.md
│   ├── v1/
│   │   ├── openapi.yaml
│   │   ├── README.md
│   │   └── deprecation-notice.md
│   └── versions.md           # Version comparison
```

### Version Switcher

Add version switcher to documentation:

```markdown
## Documentation Header

Current Version: v2.0 ▼
  - v2.0 (Current)
  - v1.2 (Deprecated - sunset June 2026)
  - v0.9 (Removed)

⚠️ You're viewing documentation for v1.2 which is deprecated.
→ Migrate to v2.0: [Migration Guide](migration-from-v1.md)
```

## Best Practices

### ✅ DO

- **Use URL versioning** for simplicity and discoverability
- **Version major only** in URLs (v1, v2, not v1.2)
- **Support N and N-1** versions (current + previous)
- **Give 6+ months notice** before breaking changes
- **Use semantic versioning** for version numbers
- **Document all breaking changes** with migration guides
- **Provide migration tools** to assist clients
- **Communicate proactively** via email, blog, docs
- **Monitor usage** of deprecated endpoints
- **Offer migration support** (office hours, priority support)

### ❌ DON'T

- Don't remove features without deprecation period
- Don't support too many versions (max 2-3)
- Don't make surprise breaking changes
- Don't use query parameters for versioning
- Don't version minor/patch in URL
- Don't break backward compatibility in minor versions
- Don't forget to update OpenAPI spec
- Don't ignore client feedback during migration

## Quality Checklist

Before implementing versioning strategy:
- [ ] Versioning scheme selected and documented
- [ ] Version format defined (semantic versioning)
- [ ] Deprecation policy established (6+ months)
- [ ] Backward compatibility rules documented
- [ ] Support timeline defined (N and N-1)
- [ ] Migration communication plan created
- [ ] Migration tools identified/developed
- [ ] Version discovery mechanism implemented
- [ ] Documentation structure per version
- [ ] Changelog process established
- [ ] Team trained on versioning policy

## Example Usage

```
@api-architect /plan-api-versioning

API Name: Projects API
Current Version: 1.2.0
Versioning Type: URL versioning
Breaking Changes: Priority field type change, pagination format change, error response format

# Agent generates:
# 1. Complete versioning strategy document
# 2. Deprecation policy with timeline
# 3. Backward compatibility guidelines
# 4. Migration plan and communication schedule
# 5. Multi-version support strategy
# 6. Version discovery implementation
# 7. Documentation structure
```

---

**Note**: Good versioning strategy balances stability (don't change too often) with innovation (don't stagnate). Communicate early, communicate often.
