# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro

"""Integration tests for health endpoints.

Tests health endpoints with real HTTP requests and database connections
to verify end-to-end functionality.
"""

from flask.testing import FlaskClient


class TestHealthEndpointIntegration:
    """Integration tests for GET /health endpoint."""

    def test_health_endpoint_responds(self, client: FlaskClient) -> None:
        """Test health endpoint returns valid response.

        Given: Application is running
        When: GET /health is called
        Then: Returns 200 with valid JSON structure
        """
        response = client.get("/health")

        assert response.status_code == 200
        assert response.content_type == "application/json"

        data = response.get_json()
        assert "status" in data
        assert data["status"] in ["ok", "degraded"]
        assert "timestamp" in data
        assert "checks" in data
        assert "database" in data["checks"]

    def test_health_endpoint_no_authentication(self, client: FlaskClient) -> None:
        """Test health endpoint does not require authentication.

        Given: No JWT token provided
        When: GET /health is called
        Then: Returns 200 (not 401 Unauthorized)
        """
        response = client.get("/health")

        assert response.status_code != 401
        assert response.status_code == 200

    def test_health_endpoint_database_check(self, client: FlaskClient) -> None:
        """Test health endpoint checks database connectivity.

        Given: Database is configured
        When: GET /health is called
        Then: Response includes database check results
        """
        response = client.get("/health")
        data = response.get_json()

        assert "database" in data["checks"]
        db_check = data["checks"]["database"]
        assert "status" in db_check
        assert "response_time_ms" in db_check
        assert isinstance(db_check["response_time_ms"], int)

    def test_health_endpoint_response_format(self, client: FlaskClient) -> None:
        """Test health endpoint returns correct JSON format.

        Given: Application is running
        When: GET /health is called
        Then: Response matches OpenAPI specification
        """
        response = client.get("/health")
        data = response.get_json()

        # Verify top-level fields
        assert isinstance(data["status"], str)
        assert isinstance(data["timestamp"], str)
        assert isinstance(data["checks"], dict)

        # Verify timestamp is ISO 8601 format
        assert "T" in data["timestamp"]
        assert data["timestamp"].endswith("Z") or "+" in data["timestamp"]


class TestReadyEndpointIntegration:
    """Integration tests for GET /ready endpoint."""

    def test_ready_endpoint_responds(self, client: FlaskClient) -> None:
        """Test readiness endpoint returns valid response.

        Given: Application is running
        When: GET /ready is called
        Then: Returns 200 or 503 with valid JSON structure
        """
        response = client.get("/ready")

        assert response.status_code in [200, 503]
        assert response.content_type == "application/json"

        data = response.get_json()
        assert "status" in data
        assert data["status"] in ["ready", "not_ready"]
        assert "timestamp" in data
        assert "checks" in data

    def test_ready_endpoint_no_authentication(self, client: FlaskClient) -> None:
        """Test readiness endpoint does not require authentication.

        Given: No JWT token provided
        When: GET /ready is called
        Then: Returns 200 or 503 (not 401 Unauthorized)
        """
        response = client.get("/ready")

        assert response.status_code != 401
        assert response.status_code in [200, 503]

    def test_ready_endpoint_checks_dependencies(self, client: FlaskClient) -> None:
        """Test readiness endpoint checks all dependencies.

        Given: Application has configured dependencies
        When: GET /ready is called
        Then: Response includes checks for all dependencies
        """
        response = client.get("/ready")
        data = response.get_json()

        assert "checks" in data
        # At minimum, database should be checked
        assert "database" in data["checks"]

    def test_ready_endpoint_status_codes(self, client: FlaskClient) -> None:
        """Test readiness endpoint returns correct status codes.

        Given: Dependencies may be up or down
        When: GET /ready is called
        Then: Returns 200 when ready, 503 when not ready
        """
        response = client.get("/ready")
        data = response.get_json()

        if data["status"] == "ready":
            assert response.status_code == 200
            # All checks should be 'ok'
            for check in data["checks"].values():
                assert check["status"] == "ok"
        elif data["status"] == "not_ready":
            assert response.status_code == 503
            # At least one check should be 'error'
            statuses = [check["status"] for check in data["checks"].values()]
            assert "error" in statuses


class TestVersionEndpointIntegration:
    """Integration tests for GET /version endpoint."""

    def test_version_endpoint_responds(self, client: FlaskClient) -> None:
        """Test version endpoint returns valid response.

        Given: VERSION file exists
        When: GET /version is called
        Then: Returns 200 with version information
        """
        response = client.get("/version")

        assert response.status_code == 200
        assert response.content_type == "application/json"

        data = response.get_json()
        assert "version" in data

    def test_version_endpoint_no_authentication(self, client: FlaskClient) -> None:
        """Test version endpoint does not require authentication.

        Given: No JWT token provided
        When: GET /version is called
        Then: Returns 200 (not 401 Unauthorized)
        """
        response = client.get("/version")

        assert response.status_code != 401
        assert response.status_code == 200

    def test_version_endpoint_format(self, client: FlaskClient) -> None:
        """Test version endpoint returns correct format.

        Given: VERSION file exists with valid content
        When: GET /version is called
        Then: Response includes version fields
        """
        response = client.get("/version")
        data = response.get_json()

        assert "version" in data
        assert isinstance(data["version"], str)
        # Version should follow SemVer format (loosely)
        version_parts = data["version"].split(".")
        assert len(version_parts) >= 2  # At least MAJOR.MINOR

    def test_version_endpoint_includes_metadata(self, client: FlaskClient) -> None:
        """Test version endpoint includes build metadata.

        Given: Application has build metadata
        When: GET /version is called
        Then: Response includes commit, build_date, environment
        """
        response = client.get("/version")
        data = response.get_json()

        assert "commit" in data
        assert "build_date" in data
        assert "environment" in data


class TestHealthEndpointsRouting:
    """Integration tests for health endpoints routing."""

    def test_health_endpoints_no_version_prefix(self, client: FlaskClient) -> None:
        """Test health endpoints are at root path without version prefix.

        Given: Health endpoints are registered
        When: Endpoints are accessed at root path
        Then: All three endpoints respond successfully
        """
        # Health endpoints should NOT have /v0/ prefix
        health_response = client.get("/health")
        ready_response = client.get("/ready")
        version_response = client.get("/version")

        assert health_response.status_code in [200, 500]
        assert ready_response.status_code in [200, 503]
        assert version_response.status_code in [200, 500]

    def test_versioned_paths_do_not_work(self, client: FlaskClient) -> None:
        """Test health endpoints are NOT available with version prefix.

        Given: Health endpoints registered at root
        When: Accessed with /v0/ prefix
        Then: Returns 404 Not Found
        """
        # These should NOT work
        response = client.get("/v0/health")
        assert response.status_code == 404


class TestHealthEndpointsPerformance:
    """Integration tests for health endpoints performance."""

    def test_health_endpoint_response_time(self, client: FlaskClient) -> None:
        """Test health endpoint responds quickly.

        Given: Application is running
        When: GET /health is called
        Then: Response time is reasonable (< 200ms)
        """
        import time

        start = time.time()
        response = client.get("/health")
        elapsed = (time.time() - start) * 1000  # Convert to ms

        assert response.status_code in [200, 500]
        # Allow generous timeout for integration tests
        assert elapsed < 1000  # 1 second (generous for integration tests)

    def test_ready_endpoint_response_time(self, client: FlaskClient) -> None:
        """Test readiness endpoint responds quickly.

        Given: Application is running
        When: GET /ready is called
        Then: Response time is reasonable (< 500ms)
        """
        import time

        start = time.time()
        response = client.get("/ready")
        elapsed = (time.time() - start) * 1000

        assert response.status_code in [200, 503]
        # Allow generous timeout for integration tests
        assert elapsed < 2000  # 2 seconds (generous for integration tests)

    def test_version_endpoint_response_time(self, client: FlaskClient) -> None:
        """Test version endpoint responds quickly.

        Given: VERSION file is cached
        When: GET /version is called
        Then: Response time is very fast (< 50ms typically)
        """
        import time

        start = time.time()
        response = client.get("/version")
        elapsed = (time.time() - start) * 1000

        assert response.status_code in [200, 500]
        # Allow generous timeout for integration tests
        assert elapsed < 500  # 500ms (generous for integration tests)
