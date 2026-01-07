---
description: "Generate API changelog documenting version changes, breaking changes, deprecations, and migration guides"
agent: "specification"
tools: ["search", "search/codebase", "search/changes"]
---

# Generate API Changelog

You are an expert in API documentation and version management. Generate comprehensive API changelogs documenting version changes, new features, improvements, bug fixes, breaking changes, deprecations, and migration guides following Keep a Changelog format.

## Task

Create API changelog with:
- **Version sections** (semantic versioning: major.minor.patch)
- **Change categories** (Added, Changed, Deprecated, Removed, Fixed, Security)
- **Breaking changes** clearly highlighted with migration paths
- **Deprecation notices** with sunset timeline
- **Migration guides** for major version upgrades
- **Links to specifications** and documentation
- **Impact assessment** (backward compatibility)
- **Release dates** and version metadata

## Input Variables

- `${input:version}` - Version number (e.g., 1.0.0, 1.1.0, 2.0.0)
- `${input:releaseDate}` - Release date (YYYY-MM-DD)
- `${input:changes}` - List of changes (from commits, PRs, issues)
- `${input:breakingChanges}` - Breaking changes requiring migration

## Changelog Format

Follow [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format:

```markdown
# Changelog

All notable changes to the Projects API will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New features in development

### Changed
- Changes to existing functionality

## [1.2.0] - 2026-01-15

### Added
- New endpoint: `GET /projects/:id/analytics` for project metrics
- Support for filtering projects by multiple statuses: `?status=active,completed`
- Pagination support for task comments: `GET /tasks/:id/comments?page=1`
- New field `estimated_hours` in Task schema
- Batch operations: `POST /projects/batch` for creating multiple projects

### Changed
- Improved performance of `GET /projects` endpoint (50% faster)
- Updated `priority` field from string to integer (1=low, 2=medium, 3=high)
- Changed default pagination limit from 10 to 20 items per page
- Enhanced error messages with detailed validation feedback

### Deprecated
- `GET /projects/:id/stats` endpoint (use `/projects/:id/analytics` instead)
- `priority` as string values ('low', 'medium', 'high') - will be removed in v2.0.0

### Fixed
- Fixed pagination bug causing duplicate results
- Corrected timezone handling in `created_at` and `updated_at` fields
- Fixed 500 error when updating project with null description

### Security
- Added rate limiting to authentication endpoints (10 requests/minute)
- Implemented CSRF protection for state-changing operations

## [1.1.0] - 2025-12-01

### Added
- Task dependencies: `parent_id` field in Task schema
- Bulk task update: `PATCH /tasks/bulk`
- Webhook support for project events
- Export endpoint: `GET /projects/:id/export?format=csv`

### Changed
- Increased maximum `per_page` limit from 50 to 100
- Improved Guardian integration with context-based permissions

### Fixed
- Fixed race condition in concurrent project creation
- Corrected company isolation bug in task listing

## [1.0.0] - 2025-10-15

### Added
- Initial stable release
- Complete CRUD operations for Projects
- Complete CRUD operations for Tasks
- JWT authentication with cookie-based tokens
- Guardian integration for authorization
- Multi-tenancy support with company isolation
- Pagination and filtering
- OpenAPI 3.0 specification

[Unreleased]: https://github.com/example/projects-api/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/example/projects-api/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/example/projects-api/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/example/projects-api/releases/tag/v1.0.0
```

## Change Categories

### Added
New features, endpoints, fields, capabilities:

```markdown
### Added
- **New endpoint**: `POST /projects/:id/duplicate` - Duplicate existing project with all tasks
  - Request body: `{"name": "New Project Name", "include_tasks": true}`
  - Response: 201 Created with duplicated project
  - Spec: [REQ-DUP-001](link-to-spec)
  
- **New field**: `tags` array in Project schema
  - Type: `string[]`
  - Example: `["frontend", "urgent", "q1-2026"]`
  - Nullable: true
  - Spec: [REQ-TAGS-001](link-to-spec)
  
- **Webhook events**: Real-time notifications for project changes
  - Events: `project.created`, `project.updated`, `project.deleted`
  - Configuration: `POST /webhooks` endpoint
  - Spec: [REQ-WEBHOOK-001](link-to-spec)
```

### Changed
Modifications to existing functionality:

```markdown
### Changed
- **Performance improvement**: `GET /projects` endpoint now 60% faster
  - Added database indexes on `company_id` and `status`
  - Implemented Redis caching for frequently accessed projects
  - Impact: No API changes, fully backward compatible
  
- **Validation enhancement**: Stricter validation for `email` fields
  - Now validates against RFC 5322 standard
  - Rejects invalid formats with 422 error
  - Impact: May reject previously accepted invalid emails
  
- **Default value change**: `per_page` default increased from 20 to 50
  - Old: `GET /projects` returned 20 items by default
  - New: `GET /projects` returns 50 items by default
  - Impact: Client may receive more data per request
  - Migration: Explicitly set `?per_page=20` to maintain old behavior
```

### Deprecated
Features marked for future removal:

```markdown
### Deprecated
- **Endpoint**: `GET /projects/:id/stats` (deprecated in v1.2.0)
  - **Replacement**: Use `GET /projects/:id/analytics` instead
  - **Removal date**: v2.0.0 (estimated 2026-06-01)
  - **Migration guide**: See [Migration from stats to analytics](#migration-stats-to-analytics)
  - **Impact**: Stats endpoint still works but returns deprecation warning in headers
  
- **Field**: `priority` string values in Task schema (deprecated in v1.2.0)
  - **Old format**: `"priority": "medium"` (string)
  - **New format**: `"priority": 2` (integer: 1=low, 2=medium, 3=high)
  - **Removal date**: v2.0.0 (estimated 2026-06-01)
  - **Migration guide**: Update clients to use integer values
  - **Impact**: API accepts both formats in v1.x, will remove string support in v2.0.0
  
- **Header**: `X-API-Version` header (deprecated in v1.1.0)
  - **Replacement**: Use URL versioning (`/v1/projects` instead of `/projects`)
  - **Removal date**: v2.0.0
```

### Removed
Features removed in this version:

```markdown
### Removed
- **Endpoint**: `DELETE /projects/all` (removed in v2.0.0)
  - **Reason**: Too dangerous, accidental bulk deletions
  - **Alternative**: Delete projects individually or use bulk delete with explicit IDs
  - **Breaking change**: Clients using this endpoint will receive 404
  
- **Field**: `legacy_id` in Project schema (removed in v2.0.0)
  - **Reason**: Migration from old system complete
  - **Impact**: Field no longer returned in responses
  - **Breaking change**: Clients reading this field will receive null
  
- **Query parameter**: `include_archived` (removed in v2.0.0)
  - **Reason**: Replaced by `status` filter
  - **Alternative**: Use `?status=archived` or `?status=active,archived`
  - **Breaking change**: Parameter ignored if sent
```

### Fixed
Bug fixes:

```markdown
### Fixed
- **Bug**: Fixed pagination returning duplicate results when sorting by `name`
  - **Issue**: [#123](link-to-issue)
  - **Impact**: Pagination now works correctly with all sort fields
  - **Version**: Affects v1.0.0 - v1.1.2, fixed in v1.2.0
  
- **Bug**: Corrected timezone handling for `created_at` timestamps
  - **Issue**: Timestamps were returned in server timezone instead of UTC
  - **Impact**: All timestamps now consistently in UTC with 'Z' suffix
  - **Version**: Affects v1.0.0 - v1.1.5, fixed in v1.2.0
  
- **Bug**: Fixed 500 error when updating project with `description: null`
  - **Issue**: [#145](link-to-issue)
  - **Impact**: Null descriptions now accepted (clears existing description)
  - **Version**: Affects v1.1.0 - v1.1.3, fixed in v1.2.0
```

### Security
Security-related changes:

```markdown
### Security
- **Rate limiting**: Added rate limiting to authentication endpoints
  - Login: 10 attempts per 15 minutes per IP
  - Register: 5 attempts per hour per IP
  - Impact: Prevents brute-force attacks
  - Response: 429 Too Many Requests when limit exceeded
  
- **CSRF protection**: Implemented CSRF tokens for state-changing operations
  - All POST, PATCH, PUT, DELETE requests require CSRF token
  - Token provided in response to GET requests
  - Impact: Clients must include `X-CSRF-Token` header
  - Migration: Update clients to send CSRF token
  
- **Input validation**: Enhanced SQL injection prevention
  - All query parameters properly sanitized
  - Impact: No API changes, improved security
```

## Breaking Changes Section

Highlight breaking changes prominently:

```markdown
## Breaking Changes in v2.0.0

### ⚠️ URL Versioning Required

**What changed**: All endpoints now require version prefix in URL.

**Before** (v1.x):
```http
GET /projects
```

**After** (v2.0.0):
```http
GET /v2/projects
```

**Migration**:
- Update all API calls to include `/v2` prefix
- Old URLs without prefix will return 404

---

### ⚠️ Priority Field Type Change

**What changed**: Task `priority` field changed from string to integer.

**Before** (v1.x):
```json
{
  "title": "My Task",
  "priority": "medium"
}
```

**After** (v2.0.0):
```json
{
  "title": "My Task",
  "priority": 2
}
```

**Mapping**:
- `"low"` → `1`
- `"medium"` → `2`
- `"high"` → `3`

**Migration**:
```python
# Python example
priority_map = {"low": 1, "medium": 2, "high": 3}
task["priority"] = priority_map[task["priority"]]
```

---

### ⚠️ Pagination Response Structure

**What changed**: Pagination metadata moved to top-level object.

**Before** (v1.x):
```json
{
  "data": [/* items */],
  "meta": {
    "total": 100,
    "page": 1,
    "per_page": 20
  }
}
```

**After** (v2.0.0):
```json
{
  "items": [/* items */],
  "total": 100,
  "page": 1,
  "per_page": 20,
  "total_pages": 5
}
```

**Migration**:
- Update JSON parsing: `response.data` → `response.items`
- Update metadata access: `response.meta.total` → `response.total`

---

### ⚠️ Error Response Format

**What changed**: Error responses now follow RFC 7807 Problem Details.

**Before** (v1.x):
```json
{
  "error": "Validation failed",
  "details": ["Name is required"]
}
```

**After** (v2.0.0):
```json
{
  "type": "https://api.example.com/errors/validation",
  "title": "Validation Error",
  "status": 422,
  "detail": "Request validation failed",
  "errors": {
    "name": ["This field is required"]
  }
}
```

**Migration**:
- Update error handling to parse new format
- Use `errors` object for field-specific validation errors
```

## Migration Guides

Provide step-by-step migration guides:

```markdown
## Migration Guide: v1.x to v2.0

### Overview

Version 2.0 introduces several breaking changes to improve API consistency and performance. This guide will help you migrate from v1.x to v2.0.

**Estimated migration time**: 2-4 hours for typical integration

**Prerequisites**:
- Review breaking changes above
- Test migration on staging environment
- Update client libraries to v2.0 compatible versions

### Step 1: Update Base URL

Change base URL to include version prefix:

```python
# Before
BASE_URL = "https://api.example.com"

# After
BASE_URL = "https://api.example.com/v2"
```

### Step 2: Update Priority Values

Convert string priorities to integers:

```python
# Before
task = {
    "title": "My Task",
    "priority": "medium"
}

# After
PRIORITY_MAP = {"low": 1, "medium": 2, "high": 3}
task = {
    "title": "My Task",
    "priority": PRIORITY_MAP["medium"]  # 2
}

# Helper function
def convert_priority(priority_str):
    return {"low": 1, "medium": 2, "high": 3}.get(priority_str, 2)
```

### Step 3: Update Response Parsing

Adjust pagination response parsing:

```python
# Before
def parse_projects(response):
    projects = response["data"]
    total = response["meta"]["total"]
    return projects, total

# After
def parse_projects(response):
    projects = response["items"]
    total = response["total"]
    page = response["page"]
    total_pages = response["total_pages"]
    return projects, total, page, total_pages
```

### Step 4: Update Error Handling

Handle new error format:

```python
# Before
def handle_error(response):
    if response.status_code >= 400:
        error = response.json()
        print(f"Error: {error['error']}")
        if 'details' in error:
            for detail in error['details']:
                print(f"  - {detail}")

# After
def handle_error(response):
    if response.status_code >= 400:
        error = response.json()
        print(f"Error: {error['title']} ({error['status']})")
        print(f"Detail: {error['detail']}")
        if 'errors' in error:
            for field, messages in error['errors'].items():
                for msg in messages:
                    print(f"  - {field}: {msg}")
```

### Step 5: Remove Deprecated Endpoints

Replace deprecated endpoints:

```python
# Before: Using deprecated stats endpoint
response = requests.get(f"{BASE_URL}/projects/{project_id}/stats")
stats = response.json()

# After: Use analytics endpoint
response = requests.get(f"{BASE_URL}/projects/{project_id}/analytics")
analytics = response.json()

# Note: Response structure is similar but with more details
```

### Step 6: Test Migration

Test checklist:
- [ ] All API calls use `/v2` prefix
- [ ] Priority values are integers
- [ ] Response parsing updated for new structure
- [ ] Error handling supports new format
- [ ] Deprecated endpoints replaced
- [ ] Integration tests passing
- [ ] E2E tests passing

### Step 7: Deploy and Monitor

Deployment checklist:
- [ ] Deploy to staging and verify
- [ ] Run smoke tests
- [ ] Monitor error rates
- [ ] Check response times
- [ ] Verify data consistency
- [ ] Deploy to production
- [ ] Monitor for 24 hours

### Rollback Plan

If issues arise:
1. Keep v1.x client code available
2. Switch `BASE_URL` back to v1
3. Redeploy previous version
4. Investigate and fix issues
5. Retry migration

### Support

Questions or issues?
- Documentation: https://docs.example.com/api/v2
- Support: api-support@example.com
- Slack: #api-v2-migration
```

## Version Comparison

Create comparison tables:

```markdown
## API Version Comparison

| Feature | v1.0 | v1.1 | v1.2 | v2.0 |
|---------|------|------|------|------|
| URL Versioning | ❌ | ❌ | ⚠️ Deprecated | ✅ Required |
| Priority Type | String | String | Both | Integer only |
| Pagination Format | Meta object | Meta object | Meta object | Top-level |
| Rate Limiting | ❌ | ❌ | ✅ Auth only | ✅ All endpoints |
| Webhooks | ❌ | ✅ Basic | ✅ Enhanced | ✅ Full support |
| Batch Operations | ❌ | ✅ Tasks | ✅ Projects/Tasks | ✅ All resources |
| CSRF Protection | ❌ | ❌ | ✅ | ✅ |
| RFC 7807 Errors | ❌ | ❌ | ❌ | ✅ |

**Legend**:
- ✅ Fully supported
- ⚠️ Deprecated (still works)
- ❌ Not available
```

## Deprecation Timeline

Visualize deprecation schedule:

```markdown
## Deprecation Timeline

### Current (v1.2.0) - January 2026
- ⚠️ `GET /projects/:id/stats` deprecated → use `/analytics`
- ⚠️ String `priority` values deprecated → use integers
- ⚠️ Header-based versioning deprecated → use URL versioning

### v1.3.0 - March 2026
- ⚠️ Last version supporting deprecated features
- ⚠️ Warning headers added to deprecated endpoints
- 📢 Final migration warning emails sent

### v2.0.0 - June 2026
- ❌ Removed: `/projects/:id/stats` endpoint
- ❌ Removed: String `priority` support
- ❌ Removed: Header-based versioning
- ✅ All clients must migrate to v2.0

### Post-v2.0.0
- v1.x endpoints available at `/v1/` prefix
- v1.x support ends December 2026
- All v1.x endpoints return 410 Gone after December 2026
```

## Best Practices

### ✅ DO

- **Use semantic versioning**: Major.Minor.Patch
- **Document breaking changes**: Clearly highlight with migration paths
- **Provide deprecation warnings**: Give users time to migrate (3-6 months)
- **Link to specifications**: Reference OpenAPI spec sections
- **Include examples**: Before/after code samples
- **Date all changes**: Release dates for each version
- **Group by category**: Added, Changed, Deprecated, Removed, Fixed, Security
- **Maintain version links**: GitHub compare URLs

### ❌ DON'T

- Don't remove features without deprecation period
- Don't make breaking changes in minor versions
- Don't use vague descriptions ("improved performance")
- Don't skip migration guides for breaking changes
- Don't forget to update OpenAPI spec
- Don't break backward compatibility without major version bump

## Quality Checklist

Before publishing changelog:
- [ ] All changes categorized correctly
- [ ] Breaking changes clearly marked with ⚠️
- [ ] Migration guides provided for breaking changes
- [ ] Deprecation timeline specified
- [ ] Links to specs, issues, PRs included
- [ ] Release date specified
- [ ] Version comparison table updated
- [ ] Examples include before/after code
- [ ] OpenAPI spec updated to match changes
- [ ] Team reviewed changelog

## Example Usage

```
@specification /generate-api-changelog

Version: 2.0.0
Release Date: 2026-06-01
Changes: URL versioning required, priority field type change, pagination format change
Breaking Changes: Yes (3 breaking changes)

# Agent generates:
# 1. Complete changelog following Keep a Changelog format
# 2. Breaking changes section with migration examples
# 3. Migration guide with step-by-step instructions
# 4. Version comparison table
# 5. Deprecation timeline visualization
# 6. Links to specification updates
```

---

**Note**: Keep changelog updated with every release. Use conventional commits to automate changelog generation where possible.
