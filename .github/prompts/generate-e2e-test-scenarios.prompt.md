---
description: "Generate end-to-end test scenarios covering multi-step user journeys, API workflows, and integration points"
agent: "Flask API Expert"
tools: ["search", "search/codebase", "web/fetch"]
---

# Generate E2E Test Scenarios

You are an expert in end-to-end testing and API integration testing. Generate comprehensive E2E test scenarios that validate complete user journeys, multi-endpoint workflows, authentication flows, authorization checks, and cross-service integration.

## Task

Create E2E test scenarios for:
- **Complete user journeys** (login → create → update → delete)
- **Multi-endpoint workflows** testing endpoint dependencies
- **Authentication flows** (login, token refresh, logout)
- **Authorization scenarios** (different user roles, permissions)
- **Cross-service integration** (Guardian, Identity, external APIs)
- **Error recovery paths** (validation errors, conflicts, retries)
- **Data consistency checks** across operations
- **Performance scenarios** (pagination, filtering, bulk operations)

## Input Variables

- `${input:featureName}` - Feature to test (e.g., Project Management, Task Assignment)
- `${input:userJourney}` - Journey description (e.g., "Create project → Add tasks → Complete tasks → Archive project")
- `${input:roles}` - User roles to test (e.g., admin, editor, viewer)
- `${input:services}` - External services involved (Guardian, Identity)

## Workflow

### 1. Identify User Journey

Map complete user workflow:

```
Project Management Journey:
1. Login as project manager
2. Create new project
3. Add team members to project
4. Create multiple tasks
5. Assign tasks to team members
6. Update task status
7. Complete all tasks
8. Archive project
9. Verify project in archive

Success Criteria:
- All endpoints return expected status codes
- Data persists correctly between steps
- Authorization checks pass at each step
- Relationships maintained (project → tasks)
- Timestamps updated appropriately
```

### 2. Define Test Scenario Structure

**Scenario Template**:

```python
# tests/integration/test_project_journey_e2e.py
"""
End-to-End Test: Complete Project Management Journey

Tests a complete workflow from project creation to archival,
validating all CRUD operations, relationships, and authorization.
"""
import pytest
from datetime import datetime, timezone


class TestProjectManagementJourney:
    """E2E test for complete project lifecycle."""
    
    @pytest.fixture(autouse=True)
    def setup_journey(self, session, company):
        """Set up journey context."""
        self.company = company
        self.project_id = None
        self.task_ids = []
        self.team_member_ids = []
    
    def test_complete_project_journey(
        self,
        authenticated_client,
        admin_client,
        api_url,
        mock_guardian_granted
    ):
        """
        Test complete project management journey.
        
        Journey Steps:
        1. Admin creates project
        2. Admin adds team members
        3. Manager creates tasks
        4. Manager assigns tasks
        5. Team member updates task status
        6. Manager completes all tasks
        7. Admin archives project
        8. Verify project in archive
        """
        # === Step 1: Create Project ===
        project_data = {
            'name': 'E2E Test Project',
            'description': 'End-to-end test project',
            'status': 'active'
        }
        
        response = admin_client.post(
            api_url('projects'),
            json=project_data
        )
        assert response.status_code == 201
        project = response.get_json()
        self.project_id = project['id']
        
        assert project['name'] == project_data['name']
        assert project['status'] == 'active'
        assert project['company_id'] == self.company.id
        
        # === Step 2: Add Team Members ===
        # (Simulate Guardian role assignment)
        team_members = [
            {'email': 'member1@example.com', 'role': 'editor'},
            {'email': 'member2@example.com', 'role': 'editor'},
        ]
        
        # Note: Actual implementation would call Identity + Guardian APIs
        # For E2E test, we mock the authorization checks
        
        # === Step 3: Create Tasks ===
        tasks_data = [
            {
                'title': 'Task 1: Setup',
                'description': 'Setup project infrastructure',
                'status': 'todo',
                'priority': 2,
                'project_id': self.project_id
            },
            {
                'title': 'Task 2: Development',
                'description': 'Implement features',
                'status': 'todo',
                'priority': 3,
                'project_id': self.project_id
            },
            {
                'title': 'Task 3: Testing',
                'description': 'Test implementation',
                'status': 'todo',
                'priority': 2,
                'project_id': self.project_id
            },
        ]
        
        for task_data in tasks_data:
            response = authenticated_client.post(
                api_url('tasks'),
                json=task_data
            )
            assert response.status_code == 201
            task = response.get_json()
            self.task_ids.append(task['id'])
            
            assert task['project_id'] == self.project_id
            assert task['status'] == 'todo'
        
        # === Step 4: Verify Project Has Tasks ===
        response = authenticated_client.get(
            api_url(f'projects/{self.project_id}/tasks')
        )
        assert response.status_code == 200
        project_tasks = response.get_json()
        
        assert project_tasks['total'] == 3
        assert len(project_tasks['items']) == 3
        
        # === Step 5: Update Task Status (In Progress) ===
        task1_id = self.task_ids[0]
        response = authenticated_client.patch(
            api_url(f'tasks/{task1_id}'),
            json={'status': 'in_progress'}
        )
        assert response.status_code == 200
        task = response.get_json()
        assert task['status'] == 'in_progress'
        
        # === Step 6: Complete Tasks ===
        for task_id in self.task_ids:
            response = authenticated_client.patch(
                api_url(f'tasks/{task_id}'),
                json={'status': 'done'}
            )
            assert response.status_code == 200
            task = response.get_json()
            assert task['status'] == 'done'
        
        # === Step 7: Verify All Tasks Completed ===
        response = authenticated_client.get(
            api_url(f'projects/{self.project_id}/tasks?status=done')
        )
        assert response.status_code == 200
        completed_tasks = response.get_json()
        assert completed_tasks['total'] == 3
        
        # === Step 8: Archive Project ===
        response = admin_client.patch(
            api_url(f'projects/{self.project_id}'),
            json={'status': 'archived'}
        )
        assert response.status_code == 200
        project = response.get_json()
        assert project['status'] == 'archived'
        
        # === Step 9: Verify Project in Archive ===
        response = authenticated_client.get(
            api_url('projects?status=archived')
        )
        assert response.status_code == 200
        archived_projects = response.get_json()
        
        archived_project_ids = [p['id'] for p in archived_projects['items']]
        assert self.project_id in archived_project_ids
        
        # === Step 10: Cleanup (Delete) ===
        response = admin_client.delete(
            api_url(f'projects/{self.project_id}')
        )
        assert response.status_code == 204
        
        # Verify deleted
        response = authenticated_client.get(
            api_url(f'projects/{self.project_id}')
        )
        assert response.status_code == 404
```

### 3. Authentication Flow Scenarios

**Login → Access Protected Resources → Logout**:

```python
# tests/integration/test_auth_flow_e2e.py
"""E2E Test: Authentication Flow"""
import pytest


class TestAuthenticationFlow:
    """E2E tests for authentication workflows."""
    
    def test_login_access_logout_journey(self, client, api_url):
        """
        Test complete authentication flow.
        
        Steps:
        1. Login with valid credentials
        2. Receive JWT token in cookie
        3. Access protected resource with token
        4. Refresh token before expiry
        5. Logout (invalidate token)
        6. Verify cannot access protected resource
        """
        # === Step 1: Login ===
        login_data = {
            'email': 'test@example.com',
            'password': 'SecurePass123!'
        }
        
        response = client.post(
            api_url('auth/login'),
            json=login_data
        )
        assert response.status_code == 200
        
        # Extract token from Set-Cookie header
        set_cookie = response.headers.get('Set-Cookie')
        assert 'access_token=' in set_cookie
        
        # Token is automatically set in cookie jar
        
        # === Step 2: Access Protected Resource ===
        response = client.get(api_url('projects'))
        assert response.status_code == 200
        projects = response.get_json()
        assert 'items' in projects
        
        # === Step 3: Create Resource (Write Operation) ===
        response = client.post(
            api_url('projects'),
            json={'name': 'Auth Test Project'}
        )
        assert response.status_code == 201
        project = response.get_json()
        project_id = project['id']
        
        # === Step 4: Refresh Token ===
        response = client.post(api_url('auth/refresh'))
        assert response.status_code == 200
        
        # New token set in cookie
        set_cookie = response.headers.get('Set-Cookie')
        assert 'access_token=' in set_cookie
        
        # === Step 5: Logout ===
        response = client.post(api_url('auth/logout'))
        assert response.status_code == 200
        
        # Token cleared from cookie
        set_cookie = response.headers.get('Set-Cookie')
        assert 'access_token=;' in set_cookie or 'Max-Age=0' in set_cookie
        
        # === Step 6: Verify Cannot Access ===
        response = client.get(api_url('projects'))
        assert response.status_code == 401
        error = response.get_json()
        assert 'unauthorized' in error['error'].lower()
        
        # === Cleanup ===
        # Login again to delete test project
        response = client.post(api_url('auth/login'), json=login_data)
        assert response.status_code == 200
        
        response = client.delete(api_url(f'projects/{project_id}'))
        assert response.status_code == 204
    
    def test_expired_token_refresh_flow(self, client, api_url, jwt_secret):
        """
        Test token expiration and refresh.
        
        Steps:
        1. Login and get token
        2. Wait for token to expire (or mock expiry)
        3. Access resource → 401 Unauthorized
        4. Refresh token
        5. Access resource → 200 OK
        """
        # Login
        response = client.post(
            api_url('auth/login'),
            json={'email': 'test@example.com', 'password': 'SecurePass123!'}
        )
        assert response.status_code == 200
        
        # Mock token expiry by replacing with expired token
        import jwt
        from datetime import datetime, timedelta, timezone
        
        expired_claims = {
            'user_id': 'test-user-id',
            'company_id': 'test-company-id',
            'email': 'test@example.com',
            'exp': datetime.now(timezone.utc) - timedelta(hours=1),  # Expired
        }
        expired_token = jwt.encode(expired_claims, jwt_secret, algorithm='HS256')
        
        client.set_cookie('access_token', expired_token)
        
        # Try to access resource with expired token
        response = client.get(api_url('projects'))
        assert response.status_code == 401
        
        # Refresh token
        response = client.post(api_url('auth/refresh'))
        assert response.status_code == 200
        
        # Access resource with new token
        response = client.get(api_url('projects'))
        assert response.status_code == 200
```

### 4. Authorization Scenarios (Roles)

**Different User Roles → Different Access**:

```python
# tests/integration/test_authorization_e2e.py
"""E2E Test: Authorization with Different Roles"""
import pytest


class TestAuthorizationScenarios:
    """E2E tests for role-based access control."""
    
    @pytest.fixture
    def viewer_client(self, client, company, generate_jwt):
        """Client with viewer role."""
        claims = {
            'user_id': 'viewer-user-id',
            'company_id': company.id,
            'email': 'viewer@example.com',
            'roles': ['viewer']
        }
        token = generate_jwt(claims)
        client.set_cookie('access_token', token)
        return client
    
    @pytest.fixture
    def editor_client(self, client, company, generate_jwt):
        """Client with editor role."""
        claims = {
            'user_id': 'editor-user-id',
            'company_id': company.id,
            'email': 'editor@example.com',
            'roles': ['editor']
        }
        token = generate_jwt(claims)
        client.set_cookie('access_token', token)
        return client
    
    @pytest.fixture
    def admin_client(self, client, company, generate_jwt):
        """Client with admin role."""
        claims = {
            'user_id': 'admin-user-id',
            'company_id': company.id,
            'email': 'admin@example.com',
            'roles': ['admin', 'editor', 'viewer']
        }
        token = generate_jwt(claims)
        client.set_cookie('access_token', token)
        return client
    
    def test_role_based_access_journey(
        self,
        viewer_client,
        editor_client,
        admin_client,
        api_url,
        session,
        company
    ):
        """
        Test different access levels for different roles.
        
        Roles:
        - Viewer: Can list and read, cannot create/update/delete
        - Editor: Can list, read, create, update, cannot delete
        - Admin: Full access (create, read, update, delete)
        """
        from tests.factories import ProjectFactory
        
        # Create test project as admin
        test_project = ProjectFactory.create(session, company=company)
        
        # === Viewer Tests ===
        # Can list
        response = viewer_client.get(api_url('projects'))
        assert response.status_code == 200
        
        # Can read
        response = viewer_client.get(api_url(f'projects/{test_project.id}'))
        assert response.status_code == 200
        
        # Cannot create (403 Forbidden)
        with pytest.mock.patch('app.services.guardian.GuardianService.check_access') as mock_guardian:
            mock_guardian.return_value = {'access_granted': False, 'reason': 'no_permission'}
            
            response = viewer_client.post(
                api_url('projects'),
                json={'name': 'Viewer Project'}
            )
            assert response.status_code == 403
        
        # Cannot update
        with pytest.mock.patch('app.services.guardian.GuardianService.check_access') as mock_guardian:
            mock_guardian.return_value = {'access_granted': False, 'reason': 'no_permission'}
            
            response = viewer_client.patch(
                api_url(f'projects/{test_project.id}'),
                json={'name': 'Updated Name'}
            )
            assert response.status_code == 403
        
        # Cannot delete
        with pytest.mock.patch('app.services.guardian.GuardianService.check_access') as mock_guardian:
            mock_guardian.return_value = {'access_granted': False, 'reason': 'no_permission'}
            
            response = viewer_client.delete(api_url(f'projects/{test_project.id}'))
            assert response.status_code == 403
        
        # === Editor Tests ===
        # Can create
        with pytest.mock.patch('app.services.guardian.GuardianService.check_access') as mock_guardian:
            mock_guardian.return_value = {'access_granted': True, 'reason': 'granted'}
            
            response = editor_client.post(
                api_url('projects'),
                json={'name': 'Editor Project'}
            )
            assert response.status_code == 201
            editor_project = response.get_json()
        
        # Can update
        with pytest.mock.patch('app.services.guardian.GuardianService.check_access') as mock_guardian:
            mock_guardian.return_value = {'access_granted': True, 'reason': 'granted'}
            
            response = editor_client.patch(
                api_url(f'projects/{editor_project["id"]}'),
                json={'name': 'Updated Editor Project'}
            )
            assert response.status_code == 200
        
        # Cannot delete (403)
        with pytest.mock.patch('app.services.guardian.GuardianService.check_access') as mock_guardian:
            mock_guardian.return_value = {'access_granted': False, 'reason': 'no_permission'}
            
            response = editor_client.delete(api_url(f'projects/{editor_project["id"]}'))
            assert response.status_code == 403
        
        # === Admin Tests ===
        # Can delete
        with pytest.mock.patch('app.services.guardian.GuardianService.check_access') as mock_guardian:
            mock_guardian.return_value = {'access_granted': True, 'reason': 'granted'}
            
            response = admin_client.delete(api_url(f'projects/{editor_project["id"]}'))
            assert response.status_code == 204
```

### 5. Multi-Tenancy Isolation

**Verify company data isolation**:

```python
# tests/integration/test_multi_tenancy_e2e.py
"""E2E Test: Multi-Tenancy Data Isolation"""
import pytest


class TestMultiTenancyIsolation:
    """Verify companies cannot access each other's data."""
    
    def test_company_data_isolation(
        self,
        session,
        client,
        generate_jwt,
        api_url
    ):
        """
        Test that Company A cannot access Company B's data.
        
        Steps:
        1. Create data for Company A
        2. Create data for Company B
        3. Login as Company A user
        4. Verify can access only Company A data
        5. Login as Company B user
        6. Verify can access only Company B data
        7. Verify cannot access Company A data
        """
        from tests.factories import CompanyFactory, ProjectFactory
        
        # === Setup: Create two companies with data ===
        company_a = CompanyFactory.create(session, name='Company A')
        company_b = CompanyFactory.create(session, name='Company B')
        
        project_a1 = ProjectFactory.create(
            session,
            company=company_a,
            name='Company A Project 1'
        )
        project_a2 = ProjectFactory.create(
            session,
            company=company_a,
            name='Company A Project 2'
        )
        
        project_b1 = ProjectFactory.create(
            session,
            company=company_b,
            name='Company B Project 1'
        )
        project_b2 = ProjectFactory.create(
            session,
            company=company_b,
            name='Company B Project 2'
        )
        
        # === Login as Company A user ===
        claims_a = {
            'user_id': 'user-a-id',
            'company_id': company_a.id,
            'email': 'user.a@company-a.com'
        }
        token_a = generate_jwt(claims_a)
        client.set_cookie('access_token', token_a)
        
        # List projects → Should only see Company A projects
        response = client.get(api_url('projects'))
        assert response.status_code == 200
        projects = response.get_json()
        
        assert projects['total'] == 2
        project_ids = [p['id'] for p in projects['items']]
        assert project_a1.id in project_ids
        assert project_a2.id in project_ids
        assert project_b1.id not in project_ids
        assert project_b2.id not in project_ids
        
        # Try to access Company B project → 404 Not Found
        response = client.get(api_url(f'projects/{project_b1.id}'))
        assert response.status_code == 404
        
        # Try to update Company B project → 404 Not Found
        response = client.patch(
            api_url(f'projects/{project_b1.id}'),
            json={'name': 'Hacked Name'}
        )
        assert response.status_code == 404
        
        # === Login as Company B user ===
        claims_b = {
            'user_id': 'user-b-id',
            'company_id': company_b.id,
            'email': 'user.b@company-b.com'
        }
        token_b = generate_jwt(claims_b)
        client.set_cookie('access_token', token_b)
        
        # List projects → Should only see Company B projects
        response = client.get(api_url('projects'))
        assert response.status_code == 200
        projects = response.get_json()
        
        assert projects['total'] == 2
        project_ids = [p['id'] for p in projects['items']]
        assert project_b1.id in project_ids
        assert project_b2.id in project_ids
        assert project_a1.id not in project_ids
        assert project_a2.id not in project_ids
        
        # Try to access Company A project → 404 Not Found
        response = client.get(api_url(f'projects/{project_a1.id}'))
        assert response.status_code == 404
```

### 6. Error Recovery Flow

**Handle errors gracefully**:

```python
# tests/integration/test_error_recovery_e2e.py
"""E2E Test: Error Recovery and Retry Logic"""
import pytest


class TestErrorRecoveryFlow:
    """Test error scenarios and recovery paths."""
    
    def test_validation_error_recovery(
        self,
        authenticated_client,
        api_url,
        company
    ):
        """
        Test validation error handling and correction.
        
        Steps:
        1. Submit invalid data → 422 Validation Error
        2. Correct errors based on response
        3. Resubmit → 201 Created
        """
        # === Attempt 1: Invalid data ===
        invalid_data = {
            # Missing required 'name' field
            'description': 'Test project',
            'status': 'invalid_status'  # Invalid enum value
        }
        
        response = authenticated_client.post(
            api_url('projects'),
            json=invalid_data
        )
        assert response.status_code == 422
        errors = response.get_json()
        
        assert 'errors' in errors
        assert 'name' in errors['errors']  # Missing required field
        assert 'status' in errors['errors']  # Invalid enum
        
        # === Attempt 2: Fix errors and retry ===
        corrected_data = {
            'name': 'Corrected Project',  # Add missing field
            'description': 'Test project',
            'status': 'active'  # Use valid enum value
        }
        
        response = authenticated_client.post(
            api_url('projects'),
            json=corrected_data
        )
        assert response.status_code == 201
        project = response.get_json()
        
        assert project['name'] == 'Corrected Project'
        assert project['status'] == 'active'
    
    def test_conflict_resolution(
        self,
        authenticated_client,
        api_url,
        session,
        company
    ):
        """
        Test handling duplicate/conflict errors.
        
        Steps:
        1. Create project with unique name
        2. Try to create duplicate → 409 Conflict
        3. Use different name → 201 Created
        """
        from tests.factories import ProjectFactory
        
        # Create existing project
        existing = ProjectFactory.create(
            session,
            company=company,
            name='Existing Project'
        )
        
        # === Attempt to create duplicate ===
        duplicate_data = {
            'name': 'Existing Project',  # Same name
            'description': 'Duplicate'
        }
        
        response = authenticated_client.post(
            api_url('projects'),
            json=duplicate_data
        )
        assert response.status_code == 409
        error = response.get_json()
        assert 'already exists' in error['message'].lower()
        
        # === Use unique name ===
        unique_data = {
            'name': 'Unique Project',  # Different name
            'description': 'New project'
        }
        
        response = authenticated_client.post(
            api_url('projects'),
            json=unique_data
        )
        assert response.status_code == 201
```

## Best Practices

### ✅ DO

- **Test complete workflows**: Cover all steps in user journey
- **Verify state changes**: Check data persists between steps
- **Test different roles**: Verify authorization for each role
- **Check data isolation**: Multi-tenancy separation
- **Handle errors**: Test validation, conflicts, recovery
- **Clean up after**: Delete test data (or use transactions)
- **Use realistic data**: Real-world scenarios
- **Mock external services**: Guardian, Identity (for tests)
- **Assert intermediary steps**: Not just final state
- **Test performance**: Pagination, filtering, bulk ops

### ❌ DON'T

- Don't test single endpoints (that's unit/integration)
- Don't skip cleanup (causes test pollution)
- Don't hardcode IDs (use fixtures)
- Don't ignore authorization (test permissions)
- Don't forget negative cases (errors, conflicts)
- Don't run E2E on every commit (slow, run in CI pipeline)
- Don't test implementation details (test behavior)

## Test Organization

```
tests/
├── unit/                       # Fast, isolated tests
├── integration/               # Database tests
└── e2e/                       # End-to-end scenarios
    ├── test_project_journey_e2e.py
    ├── test_task_assignment_e2e.py
    ├── test_auth_flow_e2e.py
    ├── test_authorization_e2e.py
    ├── test_multi_tenancy_e2e.py
    └── test_error_recovery_e2e.py
```

## Quality Checklist

Before completing E2E tests:
- [ ] Complete user journey covered (start to finish)
- [ ] All endpoints in workflow tested
- [ ] Authentication flow validated
- [ ] Authorization checked for each role
- [ ] Multi-tenancy isolation verified
- [ ] Error scenarios tested
- [ ] Data consistency validated
- [ ] Cleanup implemented
- [ ] External services mocked
- [ ] Performance acceptable

## Example Usage

```
@flask-api-expert /generate-e2e-test-scenarios

Feature: Project Management
Journey: Create project → Add tasks → Assign → Complete → Archive
Roles: admin, editor, viewer
Services: Guardian (authorization)

# Agent generates:
# 1. Complete journey test class
# 2. Authentication flow tests
# 3. Authorization scenarios for each role
# 4. Multi-tenancy isolation test
# 5. Error recovery paths
# 6. Fixtures for different roles
# 7. Cleanup logic
```

---

**Note**: E2E tests are slower than unit/integration tests. Run them in CI pipeline or before major releases, not on every commit.
