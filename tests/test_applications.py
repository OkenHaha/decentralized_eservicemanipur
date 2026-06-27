import pytest
from httpx import AsyncClient

async def get_citizen_token(client: AsyncClient) -> str:
    login_request = {
        "employee_id": "9876543210",  # Phone for citizen-tomba
        "password": "123456"
    }
    res = await client.post("/api/v1/auth/login", json=login_request)
    assert res.status_code == 200
    return res.json()["access_token"]

@pytest.mark.asyncio
async def test_list_services(client: AsyncClient):
    """
    Test retrieving available services catalog.
    """
    response = await client.get("/api/v1/applications/services")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert any(s["service_code"] == "OBC_CERTIFICATE" for s in data)

@pytest.mark.asyncio
async def test_submit_application_validation_error(client: AsyncClient):
    """
    Test submitting an application with missing required fields raises validation error.
    """
    token = await get_citizen_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Missing fields: ApplicantName, etc.
    payload = {
        "service_code": "OBC_CERTIFICATE",
        "form_data": {
            "ApplicantName": "Laishram Tomba Singh"
            # Missing other required fields like MobileNumber, District, and OBC specifics
        },
        "declaration_accepted": True
    }
    
    res = await client.post("/api/v1/applications/", json=payload, headers=headers)
    assert res.status_code == 400
    assert "INPUT_ERROR: Mandatory input field missing" in res.json()["detail"]

@pytest.mark.asyncio
async def test_submit_application_success(client: AsyncClient):
    """
    Test successfully submitting an application. It starts in DRAFT status.
    """
    token = await get_citizen_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "service_code": "OBC_CERTIFICATE",
        "form_data": {
            "ApplicantName": "Laishram Tomba Singh",
            "Gender": "MALE",
            "MobileNumber": "9876543210",
            "District": "Imphal West",
            "SubDivision": "Lamphelpat",
            "Circle": "Lamphel",
            "Locality": "Kwakeithel",
            "Pin Code": "795001",
            "Purpose": "Higher Education",
            "SelectedOfficeDropdown": "SDO-IW",
            "DeclarationCheckbox": True,
            "DateOfBirth": "1995-03-15",
            "PlaceOfBirth": "Imphal",
            "Religion": "Hinduism",
            "SubCaste": "Meitei",
            "RelationshipDetails": "Son of Laishram Ibohal Singh"
        },
        "declaration_accepted": True,
        "purpose": "Higher Education"
    }

    res = await client.post("/api/v1/applications/", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["current_status"] == "DRAFT"
    assert data["application_id"].startswith("MN-REV-")
