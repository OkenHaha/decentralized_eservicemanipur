import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_captcha_generation(client: AsyncClient):
    """
    Test generating CAPTCHA challenges.
    """
    response = await client.post("/api/v1/auth/captcha")
    assert response.status_code == 200
    data = response.json()
    assert "captcha_id" in data
    assert "captcha_text" in data
    assert len(data["captcha_text"]) == 6

@pytest.mark.asyncio
async def test_citizen_registration_and_login_flow(client: AsyncClient):
    """
    Test the full citizen Aadhaar registration and subsequent login flow.
    """
    # 1. Generate CAPTCHA
    captcha_res = await client.post("/api/v1/auth/captcha")
    captcha_data = captcha_res.json()
    captcha_id = captcha_data["captcha_id"]
    captcha_text = captcha_data["captcha_text"]

    # 2. Request OTP
    otp_request = {
        "mobile": "9876543213",  # Maps to citizen-999900000004
        "captcha_id": captcha_id,
        "captcha_value": captcha_text
    }
    otp_res = await client.post("/api/v1/auth/otp/send", json=otp_request)
    assert otp_res.status_code == 200
    assert otp_res.json()["status"] == "SUCCESS"

    # 3. Register citizen with Aadhaar 999900000004
    register_request = {
        "aadhaar_number": "999900000004",
        "mobile": "9876543213",
        "otp_code": "123456"
    }
    reg_res = await client.post("/api/v1/auth/register", json=register_request)
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["role"] == "CITIZEN"
    assert "access_token" in reg_data
    assert reg_data["name"] == "Keisham Ranbir Singh"

    # 4. Login using phone + OTP
    login_request = {
        "employee_id": "9876543213",  # Primary phone
        "password": "123456"          # Simulated OTP
    }
    login_res = await client.post("/api/v1/auth/login", json=login_request)
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["role"] == "CITIZEN"
    assert "access_token" in login_data
    assert login_data["user_id"] == reg_data["user_id"]

@pytest.mark.asyncio
async def test_official_login(client: AsyncClient):
    """
    Test logging in as a government official (Lambu and SDO).
    """
    # Test Lambu login
    lambu_login = {
        "employee_id": "EMP-LAMBU-001",
        "password": "password123"
    }
    res = await client.post("/api/v1/auth/login", json=lambu_login)
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "REVENUE_LAMBU"
    assert "access_token" in data
    assert data["name"] == "Laishram Sanjit Singh"

    # Test SDO login
    sdo_login = {
        "employee_id": "EMP-SDO-001",
        "password": "password123"
    }
    res_sdo = await client.post("/api/v1/auth/login", json=sdo_login)
    assert res_sdo.status_code == 200
    data_sdo = res_sdo.json()
    assert data_sdo["role"] == "SDO"
    assert data_sdo["name"] == "Dr. Ningombam Premjit Singh"
