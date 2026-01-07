---
description: "Generate reusable pytest fixtures for Flask API testing with factory patterns and mock services"
agent: "Flask API Expert"
tools: ["search", "search/codebase", "search/changes"]
---

# Generate Test Fixtures

You are an expert in pytest fixtures and Flask API testing patterns. Generate comprehensive, reusable test fixtures following factory patterns for database models, authentication, mocking external services, and test data setup.

## Task

Create pytest fixtures for:
- **Database fixtures** with session management and cleanup
- **Model factories** using factory pattern for test data generation
- **Authentication fixtures** (JWT tokens, authenticated clients)
- **Mock service fixtures** (Guardian, Identity, external APIs)
- **Relationship fixtures** (parent-child entities, foreign keys)
- **Parametrized fixtures** for testing multiple scenarios
- **Setup/teardown fixtures** with proper scoping

## Input Variables

- `${input:modelName}` - Model to create fixtures for (e.g., Project, Task, User)
- `${input:fixtureType}` - Type of fixture (model, auth, mock, relationship)
- `${input:scope}` - Fixture scope (function, class, module, session)
- `${input:relationships}` - Related models (e.g., "Project has many Tasks")

## Fixture Categories

### 1. Database Fixtures

Core database setup/teardown:

```python
# tests/conftest.py
import pytest
from app import create_app, db as _db
from app.config import TestingConfig

@pytest.fixture(scope='session')
def app():
    """Create application for testing session."""
    app = create_app(TestingConfig)
    
    with app.app_context():
        yield app

@pytest.fixture(scope='session')
def db(app):
    """Create database schema for testing session."""
    _db.app = app
    _db.create_all()
    
    yield _db
    
    _db.drop_all()

@pytest.fixture(scope='function')
def session(db):
    """Create new database session for each test with rollback."""
    connection = db.engine.connect()
    transaction = connection.begin()
    
    session = db.create_scoped_session(
        options={"bind": connection, "binds": {}}
    )
    db.session = session
    
    yield session
    
    transaction.rollback()
    connection.close()
    session.remove()

@pytest.fixture(scope='function')
def client(app, session):
    """Create Flask test client with database session."""
    with app.test_client() as client:
        with app.app_context():
            yield client
```

**Scope Guidance**:
- `session`: App, database schema (created once)
- `module`: Shared test data across test file
- `class`: Shared data for test class
- `function`: Isolated per test (default, safest)

### 2. Model Factory Fixtures

Factory pattern for creating test models:

```python
# tests/factories.py
import uuid
from datetime import datetime, timezone
from app.models import Project, Task, User, Company

class BaseFactory:
    """Base factory with common utilities."""
    
    @staticmethod
    def _generate_uuid():
        return str(uuid.uuid4())
    
    @staticmethod
    def _utc_now():
        return datetime.now(timezone.utc)

class CompanyFactory(BaseFactory):
    """Factory for Company model."""
    
    @staticmethod
    def create(session, **kwargs):
        defaults = {
            'id': CompanyFactory._generate_uuid(),
            'name': kwargs.get('name', 'Test Company'),
            'slug': kwargs.get('slug', 'test-company'),
            'created_at': CompanyFactory._utc_now(),
            'updated_at': CompanyFactory._utc_now(),
        }
        defaults.update(kwargs)
        
        company = Company(**defaults)
        session.add(company)
        session.commit()
        return company
    
    @staticmethod
    def create_batch(session, count=3, **kwargs):
        """Create multiple companies."""
        return [
            CompanyFactory.create(
                session,
                name=f"Company {i}",
                slug=f"company-{i}",
                **kwargs
            )
            for i in range(count)
        ]

class ProjectFactory(BaseFactory):
    """Factory for Project model."""
    
    @staticmethod
    def create(session, company=None, **kwargs):
        # Create company if not provided
        if company is None:
            company = CompanyFactory.create(session)
        
        defaults = {
            'id': ProjectFactory._generate_uuid(),
            'name': kwargs.get('name', 'Test Project'),
            'description': kwargs.get('description', 'Test description'),
            'status': kwargs.get('status', 'active'),
            'company_id': company.id,
            'created_at': ProjectFactory._utc_now(),
            'updated_at': ProjectFactory._utc_now(),
        }
        defaults.update(kwargs)
        
        project = Project(**defaults)
        session.add(project)
        session.commit()
        return project
    
    @staticmethod
    def create_with_tasks(session, company=None, task_count=3, **kwargs):
        """Create project with related tasks."""
        project = ProjectFactory.create(session, company=company, **kwargs)
        tasks = TaskFactory.create_batch(
            session,
            count=task_count,
            project=project,
            company=company or project.company
        )
        return project, tasks

class TaskFactory(BaseFactory):
    """Factory for Task model."""
    
    @staticmethod
    def create(session, project=None, company=None, **kwargs):
        # Create project if not provided
        if project is None:
            project = ProjectFactory.create(session, company=company)
        
        defaults = {
            'id': TaskFactory._generate_uuid(),
            'title': kwargs.get('title', 'Test Task'),
            'description': kwargs.get('description', 'Test task description'),
            'status': kwargs.get('status', 'todo'),
            'priority': kwargs.get('priority', 'medium'),
            'project_id': project.id,
            'company_id': company.id if company else project.company_id,
            'created_at': TaskFactory._utc_now(),
            'updated_at': TaskFactory._utc_now(),
        }
        defaults.update(kwargs)
        
        task = Task(**defaults)
        session.add(task)
        session.commit()
        return task
    
    @staticmethod
    def create_batch(session, count=3, project=None, company=None, **kwargs):
        """Create multiple tasks."""
        return [
            TaskFactory.create(
                session,
                project=project,
                company=company,
                title=f"Task {i}",
                **kwargs
            )
            for i in range(count)
        ]

# tests/conftest.py
@pytest.fixture
def company(session):
    """Create test company."""
    return CompanyFactory.create(session)

@pytest.fixture
def project(session, company):
    """Create test project."""
    return ProjectFactory.create(session, company=company)

@pytest.fixture
def task(session, project, company):
    """Create test task."""
    return TaskFactory.create(session, project=project, company=company)

@pytest.fixture
def project_with_tasks(session, company):
    """Create project with multiple tasks."""
    project, tasks = ProjectFactory.create_with_tasks(
        session,
        company=company,
        task_count=5
    )
    return project, tasks
```

**Factory Pattern Benefits**:
- ✅ Centralized test data creation
- ✅ Consistent defaults
- ✅ Easy to override specific fields
- ✅ Handles relationships automatically
- ✅ Batch creation for multiple records

### 3. Authentication Fixtures

JWT and authentication helpers:

```python
# tests/conftest.py
import jwt
from datetime import datetime, timedelta, timezone
from app.config import TestingConfig

@pytest.fixture
def jwt_secret():
    """JWT secret key for testing."""
    return TestingConfig.JWT_SECRET_KEY

@pytest.fixture
def user_claims(company):
    """Standard user JWT claims."""
    return {
        'user_id': str(uuid.uuid4()),
        'company_id': company.id,
        'email': 'test@example.com',
        'roles': ['user'],
        'exp': datetime.now(timezone.utc) + timedelta(hours=1),
        'iat': datetime.now(timezone.utc),
    }

@pytest.fixture
def admin_claims(company):
    """Admin user JWT claims."""
    return {
        'user_id': str(uuid.uuid4()),
        'company_id': company.id,
        'email': 'admin@example.com',
        'roles': ['admin', 'user'],
        'exp': datetime.now(timezone.utc) + timedelta(hours=1),
        'iat': datetime.now(timezone.utc),
    }

@pytest.fixture
def expired_claims(company):
    """Expired JWT claims for testing."""
    return {
        'user_id': str(uuid.uuid4()),
        'company_id': company.id,
        'email': 'expired@example.com',
        'exp': datetime.now(timezone.utc) - timedelta(hours=1),  # Already expired
        'iat': datetime.now(timezone.utc) - timedelta(hours=2),
    }

@pytest.fixture
def generate_jwt(jwt_secret):
    """Factory to generate JWT tokens with custom claims."""
    def _generate(claims):
        return jwt.encode(claims, jwt_secret, algorithm='HS256')
    return _generate

@pytest.fixture
def user_token(user_claims, generate_jwt):
    """Generate standard user JWT token."""
    return generate_jwt(user_claims)

@pytest.fixture
def admin_token(admin_claims, generate_jwt):
    """Generate admin JWT token."""
    return generate_jwt(admin_claims)

@pytest.fixture
def expired_token(expired_claims, generate_jwt):
    """Generate expired JWT token."""
    return generate_jwt(expired_claims)

@pytest.fixture
def authenticated_client(client, user_token):
    """Test client with authentication cookie."""
    client.set_cookie('access_token', user_token)
    return client

@pytest.fixture
def admin_client(client, admin_token):
    """Test client with admin authentication."""
    client.set_cookie('access_token', admin_token)
    return client

# Usage in tests:
def test_create_project(authenticated_client, company):
    """Test project creation with authenticated user."""
    response = authenticated_client.post(
        '/v0/projects',
        json={'name': 'New Project', 'description': 'Test'}
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == 'New Project'
    assert data['company_id'] == company.id
```

**Authentication Fixture Patterns**:
- `user_claims` / `admin_claims`: Claims dictionaries
- `generate_jwt`: Factory to create tokens
- `user_token` / `admin_token`: Pre-generated tokens
- `authenticated_client` / `admin_client`: Clients with cookies set

### 4. Mock Service Fixtures

Mock external services (Guardian, Identity):

```python
# tests/conftest.py
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_guardian_granted():
    """Mock Guardian service returning access granted."""
    with patch('app.services.guardian.GuardianService.check_access') as mock:
        mock.return_value = {
            'access_granted': True,
            'reason': 'granted'
        }
        yield mock

@pytest.fixture
def mock_guardian_denied():
    """Mock Guardian service returning access denied."""
    with patch('app.services.guardian.GuardianService.check_access') as mock:
        mock.return_value = {
            'access_granted': False,
            'reason': 'no_permission'
        }
        yield mock

@pytest.fixture
def mock_guardian_error():
    """Mock Guardian service throwing error."""
    with patch('app.services.guardian.GuardianService.check_access') as mock:
        mock.side_effect = Exception("Guardian service unavailable")
        yield mock

@pytest.fixture
def mock_guardian_custom():
    """Factory to create Guardian mock with custom response."""
    def _mock(access_granted=True, reason='granted'):
        with patch('app.services.guardian.GuardianService.check_access') as mock:
            mock.return_value = {
                'access_granted': access_granted,
                'reason': reason
            }
            return mock
    return _mock

@pytest.fixture
def mock_identity_service():
    """Mock Identity service for user lookups."""
    with patch('app.services.identity.IdentityService.get_user') as mock:
        mock.return_value = {
            'id': str(uuid.uuid4()),
            'email': 'test@example.com',
            'name': 'Test User',
            'company_id': str(uuid.uuid4()),
        }
        yield mock

@pytest.fixture
def mock_redis():
    """Mock Redis client for caching tests."""
    with patch('app.extensions.redis_client') as mock:
        redis_mock = Mock()
        redis_mock.get.return_value = None
        redis_mock.set.return_value = True
        redis_mock.delete.return_value = True
        mock.return_value = redis_mock
        yield redis_mock

# Usage in tests:
def test_create_project_with_permission(authenticated_client, company, mock_guardian_granted):
    """Test project creation with Guardian permission."""
    response = authenticated_client.post(
        '/v0/projects',
        json={'name': 'New Project'}
    )
    assert response.status_code == 201
    
    # Verify Guardian was called
    mock_guardian_granted.assert_called_once()
    call_args = mock_guardian_granted.call_args[1]
    assert call_args['operation'] == 'CREATE'
    assert call_args['resource_name'] == 'projects'

def test_create_project_without_permission(authenticated_client, company, mock_guardian_denied):
    """Test project creation denied by Guardian."""
    response = authenticated_client.post(
        '/v0/projects',
        json={'name': 'New Project'}
    )
    assert response.status_code == 403
    data = response.get_json()
    assert 'access denied' in data['error'].lower()
```

**Mock Service Patterns**:
- `mock_guardian_granted/denied`: Pre-configured responses
- `mock_guardian_custom`: Factory for custom responses
- `mock_identity_service`: User lookup mocking
- `mock_redis`: Cache service mocking

### 5. Parametrized Fixtures

Test multiple scenarios with parameters:

```python
# tests/conftest.py
@pytest.fixture(params=['active', 'completed', 'archived'])
def project_status(request):
    """Parametrized fixture for different project statuses."""
    return request.param

@pytest.fixture(params=['todo', 'in_progress', 'done'])
def task_status(request):
    """Parametrized fixture for different task statuses."""
    return request.param

@pytest.fixture(params=[
    ('user', ['user']),
    ('admin', ['admin', 'user']),
    ('viewer', ['viewer']),
])
def user_role(request):
    """Parametrized fixture for different user roles."""
    role_name, role_list = request.param
    return {'name': role_name, 'roles': role_list}

# Usage in tests (runs 3x, once per status):
def test_filter_projects_by_status(authenticated_client, session, company, project_status):
    """Test filtering projects by different statuses."""
    # Create project with specific status
    project = ProjectFactory.create(session, company=company, status=project_status)
    
    response = authenticated_client.get(f'/v0/projects?status={project_status}')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['items']) >= 1
    assert all(p['status'] == project_status for p in data['items'])

# Parametrize multiple fixtures
@pytest.fixture(params=[
    ('low', 'todo'),
    ('medium', 'in_progress'),
    ('high', 'done'),
])
def task_priority_status(request):
    """Combined priority and status parameters."""
    priority, status = request.param
    return {'priority': priority, 'status': status}

def test_task_combinations(authenticated_client, session, project, task_priority_status):
    """Test tasks with different priority/status combinations."""
    task = TaskFactory.create(
        session,
        project=project,
        company=project.company,
        **task_priority_status
    )
    
    response = authenticated_client.get(f'/v0/tasks/{task.id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['priority'] == task_priority_status['priority']
    assert data['status'] == task_priority_status['status']
```

**Parametrized Patterns**:
- Single param: Different statuses, roles, priorities
- Multiple params: Combinations (priority + status)
- Named params: Return dict with semantic keys

### 6. Relationship Fixtures

Handle complex relationships:

```python
# tests/conftest.py
@pytest.fixture
def company_with_projects(session):
    """Company with multiple projects."""
    company = CompanyFactory.create(session, name='Test Corp')
    projects = ProjectFactory.create_batch(
        session,
        count=5,
        company=company
    )
    return company, projects

@pytest.fixture
def project_hierarchy(session, company):
    """Project with tasks and subtasks."""
    project = ProjectFactory.create(session, company=company)
    
    # Parent tasks
    parent_tasks = TaskFactory.create_batch(
        session,
        count=3,
        project=project,
        company=company
    )
    
    # Subtasks for each parent
    subtasks = []
    for parent in parent_tasks:
        subs = TaskFactory.create_batch(
            session,
            count=2,
            project=project,
            company=company,
            parent_id=parent.id
        )
        subtasks.extend(subs)
    
    return {
        'project': project,
        'parent_tasks': parent_tasks,
        'subtasks': subtasks,
    }

@pytest.fixture
def multi_company_data(session):
    """Multiple companies with isolated data."""
    companies = CompanyFactory.create_batch(session, count=3)
    
    data = {}
    for company in companies:
        projects = ProjectFactory.create_batch(
            session,
            count=2,
            company=company
        )
        data[company.id] = {
            'company': company,
            'projects': projects,
        }
    
    return data

# Usage in tests:
def test_list_company_projects(authenticated_client, company_with_projects):
    """Test listing all projects for a company."""
    company, projects = company_with_projects
    
    response = authenticated_client.get('/v0/projects')
    assert response.status_code == 200
    data = response.get_json()
    
    # Should see only projects from user's company
    assert len(data['items']) == len(projects)
    assert all(p['company_id'] == company.id for p in data['items'])

def test_multi_tenancy_isolation(session, multi_company_data):
    """Test that companies can't access each other's data."""
    company1_id = list(multi_company_data.keys())[0]
    company2_id = list(multi_company_data.keys())[1]
    
    # Query company1's projects
    projects = Project.query.filter_by(company_id=company1_id).all()
    
    # Should only get company1's projects
    assert len(projects) == 2
    assert all(p.company_id == company1_id for p in projects)
    assert not any(p.company_id == company2_id for p in projects)
```

**Relationship Patterns**:
- One-to-many: Company → Projects
- Hierarchical: Parent tasks → Subtasks
- Multi-tenancy: Isolated company data

### 7. API Helper Fixtures

Common test utilities:

```python
# tests/conftest.py
@pytest.fixture
def api_url():
    """Generate versioned API URLs."""
    def _url(endpoint, version='v0'):
        return f'/{version}/{endpoint.lstrip("/")}'
    return _url

@pytest.fixture
def assert_response():
    """Helper to assert common response patterns."""
    def _assert(response, status_code=200, has_data=True, has_error=False):
        assert response.status_code == status_code
        data = response.get_json()
        
        if has_data:
            assert data is not None
        
        if has_error:
            assert 'error' in data or 'errors' in data
        else:
            assert 'error' not in data
        
        return data
    return _assert

@pytest.fixture
def create_headers():
    """Generate request headers."""
    def _headers(auth_token=None, content_type='application/json', **kwargs):
        headers = {'Content-Type': content_type}
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'
        headers.update(kwargs)
        return headers
    return _headers

# Usage in tests:
def test_list_projects(authenticated_client, api_url, assert_response):
    """Test project listing with helpers."""
    response = authenticated_client.get(api_url('projects'))
    data = assert_response(response, status_code=200)
    
    assert 'items' in data
    assert 'total' in data
    assert isinstance(data['items'], list)
```

### 8. Cleanup Fixtures

Automatic cleanup after tests:

```python
# tests/conftest.py
@pytest.fixture
def temp_files():
    """Create and cleanup temporary files."""
    files = []
    
    def _create(filename, content=''):
        import tempfile
        temp = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=filename)
        temp.write(content)
        temp.close()
        files.append(temp.name)
        return temp.name
    
    yield _create
    
    # Cleanup
    import os
    for file in files:
        if os.path.exists(file):
            os.remove(file)

@pytest.fixture
def cleanup_db_records(session):
    """Track and cleanup database records created in test."""
    records = []
    
    def _add(record):
        records.append(record)
        return record
    
    yield _add
    
    # Cleanup
    for record in records:
        session.delete(record)
    session.commit()
```

## Fixture Organization

Structure fixtures across multiple files:

```
tests/
├── conftest.py              # Root fixtures (app, db, client)
├── factories.py             # Model factories
├── fixtures/
│   ├── __init__.py
│   ├── auth.py             # Authentication fixtures
│   ├── models.py           # Model-specific fixtures
│   ├── mocks.py            # Mock service fixtures
│   └── helpers.py          # Utility fixtures
└── integration/
    └── conftest.py         # Integration-specific fixtures
```

**Import fixtures in conftest.py**:
```python
# tests/conftest.py
pytest_plugins = [
    'tests.fixtures.auth',
    'tests.fixtures.models',
    'tests.fixtures.mocks',
    'tests.fixtures.helpers',
]
```

## Best Practices

### ✅ DO

- **Use appropriate scopes**: `function` for isolation, `session` for expensive setup
- **Factory pattern**: Centralize object creation with sensible defaults
- **Clear naming**: `company_with_projects` > `fixture1`
- **Parametrize**: Test multiple scenarios with same fixture
- **Auto-cleanup**: Use yield for setup/teardown
- **Compose fixtures**: Small, focused fixtures that combine
- **Mock externals**: Mock Guardian, Identity, Redis in tests
- **Document purpose**: Docstrings for each fixture

### ❌ DON'T

- Don't create global state (use function scope)
- Don't hardcode UUIDs (generate dynamically)
- Don't skip cleanup (always rollback or teardown)
- Don't test implementation details (test behavior)
- Don't create massive fixtures (split into smaller ones)
- Don't forget company_id (multi-tenancy isolation)

## Example: Complete Fixture Set

```python
# tests/conftest.py
"""Root test configuration with core fixtures."""
import pytest
from app import create_app, db as _db
from app.config import TestingConfig

# === Application & Database ===
@pytest.fixture(scope='session')
def app():
    """Create Flask app for testing."""
    return create_app(TestingConfig)

@pytest.fixture(scope='session')
def db(app):
    """Create database schema."""
    _db.app = app
    _db.create_all()
    yield _db
    _db.drop_all()

@pytest.fixture(scope='function')
def session(db):
    """Database session with rollback."""
    connection = db.engine.connect()
    transaction = connection.begin()
    session = db.create_scoped_session(options={"bind": connection})
    db.session = session
    
    yield session
    
    transaction.rollback()
    connection.close()
    session.remove()

@pytest.fixture
def client(app, session):
    """Test client."""
    with app.test_client() as client:
        with app.app_context():
            yield client

# === Authentication ===
@pytest.fixture
def company(session):
    from tests.factories import CompanyFactory
    return CompanyFactory.create(session)

@pytest.fixture
def user_token(company):
    import jwt
    from datetime import datetime, timedelta, timezone
    from app.config import TestingConfig
    
    claims = {
        'user_id': str(uuid.uuid4()),
        'company_id': company.id,
        'email': 'test@example.com',
        'exp': datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(claims, TestingConfig.JWT_SECRET_KEY, algorithm='HS256')

@pytest.fixture
def authenticated_client(client, user_token):
    """Authenticated test client."""
    client.set_cookie('access_token', user_token)
    return client

# === Models ===
@pytest.fixture
def project(session, company):
    from tests.factories import ProjectFactory
    return ProjectFactory.create(session, company=company)

@pytest.fixture
def task(session, project):
    from tests.factories import TaskFactory
    return TaskFactory.create(session, project=project, company=project.company)

# === Mocks ===
@pytest.fixture
def mock_guardian_granted():
    from unittest.mock import patch
    with patch('app.services.guardian.GuardianService.check_access') as mock:
        mock.return_value = {'access_granted': True, 'reason': 'granted'}
        yield mock

# === Helpers ===
@pytest.fixture
def api_url():
    def _url(endpoint):
        return f'/v0/{endpoint.lstrip("/")}'
    return _url
```

## Quality Checklist

Before committing fixtures:
- [ ] Fixtures have clear, descriptive names
- [ ] Appropriate scope selected (function/module/session)
- [ ] Cleanup/teardown implemented (yield or finalizer)
- [ ] Factory pattern used for models
- [ ] Relationships handled correctly
- [ ] Multi-tenancy respected (company_id)
- [ ] External services mocked
- [ ] Docstrings explain purpose
- [ ] No hardcoded test data (use factories)
- [ ] Fixtures organized logically (conftest.py structure)

## Example Usage

```
@flask-api-expert /generate-test-fixtures

Model: Project
Type: model with relationships (has many Tasks)
Scope: function
Relationships: belongs to Company, has many Tasks

# Agent generates:
# 1. ProjectFactory with company relationship
# 2. Fixtures: company, project, project_with_tasks
# 3. Authentication fixtures for testing
# 4. Mock Guardian fixture
# 5. Example test using generated fixtures
```

---

**Note**: These fixtures follow pytest best practices and integrate with the wfp-flask-template stack (Flask, SQLAlchemy, JWT, Guardian, multi-tenancy).
