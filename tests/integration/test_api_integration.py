"""
Integration Tests for Doctor Doom API Services
Tests the complete flow from image ingestion to report generation
"""
import pytest
import httpx
import asyncio
from typing import AsyncGenerator

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test@doctor-doom.com"
TEST_PASSWORD = "test123"
TEST_USER = "Test User"


@pytest.fixture(scope="session")
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create async HTTP client for testing"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        yield client


@pytest.fixture(scope="session")
async def auth_token(client: httpx.AsyncClient) -> str:
    """Register test user and get auth token"""
    # Try to register
    try:
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "full_name": TEST_USER,
            }
        )
    except:
        pass  # User might already exist

    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    data = response.json()
    return data["access_token"]


@pytest.mark.asyncio
async def test_health_check(client: httpx.AsyncClient):
    """Test health endpoint"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_auth_register_login(client: httpx.AsyncClient):
    """Test registration and login flow"""
    # Register
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@test.com",
            "password": "password123",
            "full_name": "New User",
        },
    )
    assert register_response.status_code in [200, 400]  # May already exist

    # Login
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "newuser@test.com", "password": "password123"},
    )
    assert login_response.status_code == 200
    data = login_response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_get_current_user(client: httpx.AsyncClient, auth_token: str):
    """Test getting current user"""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "email" in data
    assert "full_name" in data


@pytest.mark.asyncio
async def test_get_sites(client: httpx.AsyncClient, auth_token: str):
    """Test getting sites list"""
    response = await client.get(
        "/api/v1/sites",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_site_details(client: httpx.AsyncClient, auth_token: str):
    """Test getting site details with modules"""
    # First get sites
    sites_response = await client.get(
        "/api/v1/sites",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    sites = sites_response.json()

    if sites:
        site_id = sites[0]["id"]
        response = await client.get(
            f"/api/v1/sites/{site_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "modules" in data


@pytest.mark.asyncio
async def test_get_defects(client: httpx.AsyncClient, auth_token: str):
    """Test getting defects with filters"""
    # Get all defects
    response = await client.get(
        "/api/v1/defects",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    # Get critical defects
    response = await client.get(
        "/api/v1/defects",
        params={"severity": "critical"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_inspections(client: httpx.AsyncClient, auth_token: str):
    """Test getting inspections"""
    response = await client.get(
        "/api/v1/inspections",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_submit_thermal_image(client: httpx.AsyncClient, auth_token: str):
    """Test submitting thermal image for processing"""
    response = await client.post(
        "/api/v1/ingest/thermal",
        json={
            "image_id": "test_img_001",
            "module_id": "mod_001_01",
            "inspection_id": "insp_001",
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert data["stream"] == "thermal:ingest"


@pytest.mark.asyncio
async def test_generate_report(client: httpx.AsyncClient, auth_token: str):
    """Test report generation"""
    response = await client.post(
        "/api/v1/reports/generate",
        content="site_id=site_001&inspection_id=insp_001",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "report_id" in data or "status" in data


@pytest.mark.asyncio
async def test_module_telemetry(client: httpx.AsyncClient, auth_token: str):
    """Test getting module telemetry"""
    # Get a module from first site
    sites_response = await client.get(
        "/api/v1/sites",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    sites = sites_response.json()

    if sites:
        site_response = await client.get(
            f"/api/v1/sites/{sites[0]['id']}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        site_data = site_response.json()
        modules = site_data.get("modules", [])

        if modules:
            module_id = modules[0]["id"]
            response = await client.get(
                f"/api/v1/modules/{module_id}/telemetry?days=7",
                headers={"Authorization": f"Bearer {auth_token}"},
            )
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)


@pytest.mark.asyncio
async def test_spatial_queries(client: httpx.AsyncClient, auth_token: str):
    """Test spatial query endpoints"""
    sites_response = await client.get(
        "/api/v1/sites",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    sites = sites_response.json()

    if sites:
        site_id = sites[0]["id"]

        # Test defect heatmap
        response = await client.get(
            "/api/v1/spatial/defects/heatmap",
            params={"site_id": site_id, "resolution": 100},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_ml_inference_service(client: httpx.AsyncClient):
    """Test ML inference service directly"""
    # Health check
    response = await httpx.AsyncClient().get("http://localhost:8001/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_geo_service(client: httpx.AsyncClient):
    """Test Geo service directly"""
    response = await httpx.AsyncClient().get("http://localhost:7800/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_report_service(client: httpx.AsyncClient):
    """Test Report service directly"""
    response = await httpx.AsyncClient().get("http://localhost:8002/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_notify_service(client: httpx.AsyncClient):
    """Test Notify service directly"""
    response = await httpx.AsyncClient().get("http://localhost:8003/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_auth_service(client: httpx.AsyncClient):
    """Test Auth service directly"""
    response = await httpx.AsyncClient().get("http://localhost:8004/health")
    assert response.status_code == 200


# Integration test for complete workflow
@pytest.mark.asyncio
async def test_complete_inspection_workflow(client: httpx.AsyncClient, auth_token: str):
    """Test complete inspection workflow"""
    # 1. Get sites
    sites_response = await client.get(
        "/api/v1/sites",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    sites = sites_response.json()
    assert len(sites) > 0

    # 2. Get site details
    site_id = sites[0]["id"]
    site_response = await client.get(
        f"/api/v1/sites/{site_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    site_data = site_response.json()
    modules = site_data.get("modules", [])
    assert len(modules) > 0

    # 3. Get defects for site
    defects_response = await client.get(
        f"/api/v1/defects?site_id={site_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    defects = defects_response.json()
    assert isinstance(defects, list)

    # 4. Submit new thermal image
    if modules:
        ingest_response = await client.post(
            "/api/v1/ingest/thermal",
            json={
                "image_id": f"test_{site_id}_001",
                "module_id": modules[0]["id"],
                "inspection_id": "insp_001",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert ingest_response.status_code == 200

    # 5. Generate report
    inspections_response = await client.get(
        "/api/v1/inspections",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    inspections = inspections_response.json()

    if inspections:
        report_response = await client.post(
            "/api/v1/reports/generate",
            content=f"site_id={site_id}&inspection_id={inspections[0]['id']}",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        assert report_response.status_code == 200
