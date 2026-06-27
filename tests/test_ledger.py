import pytest
from httpx import AsyncClient

async def get_citizen_token(client: AsyncClient) -> str:
    login_request = {"employee_id": "9876543210", "password": "123456"}
    res = await client.post("/api/v1/auth/login", json=login_request)
    return res.json()["access_token"]

async def get_official_token(client: AsyncClient, emp_id: str) -> str:
    login_request = {"employee_id": emp_id, "password": "password123"}
    res = await client.post("/api/v1/auth/login", json=login_request)
    return res.json()["access_token"]

@pytest.mark.asyncio
async def test_full_blockchain_ledger_lifecycle_and_tamper_detection(client: AsyncClient):
    """
    Comprehensive test of the full hash-chained ledger pipeline:
    Genesis (Upload docs) -> Field Verification (Lambu) -> Authorization (SDO) -> Public Audit.
    Includes testing for file tampering prevention.
    """
    citizen_token = await get_citizen_token(client)
    citizen_headers = {"Authorization": f"Bearer {citizen_token}"}

    # 1. Create a new OBC Certificate Application in DRAFT
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
        "declaration_accepted": True
    }
    app_res = await client.post("/api/v1/applications/", json=payload, headers=citizen_headers)
    assert app_res.status_code == 201
    app_id = app_res.json()["application_id"]

    # 2. Upload some documents (but not all) - remains in DRAFT
    files_to_upload = {
        "PassportSizePhoto": b"passport-photo-raw-bytes-content-1",
        "VoterID_Proof": b"voter-id-raw-bytes-content-2",
        "ApplicantIdentityProof": b"aadhaar-id-raw-bytes-content-3",
        "UpToDate_Jamabandi_Or_Patta": b"patta-raw-bytes-content-4",
        "Self_Declaration_Non_Creamy_Layer": b"creamy-layer-decl-raw-bytes-content-5"
    }

    # Upload first 4
    for doc_type in list(files_to_upload.keys())[:-1]:
        res = await client.post(
            f"/api/v1/applications/{app_id}/documents",
            headers=citizen_headers,
            params={"document_type": doc_type},
            files={"file": (f"{doc_type}.pdf", files_to_upload[doc_type], "application/pdf")}
        )
        assert res.status_code == 201
        assert res.json()["is_locked_and_submitted"] is False

    # Upload 5th and final required document - transitions to SUBMITTED and anchors on blockchain
    final_doc_type = list(files_to_upload.keys())[-1]
    res_final = await client.post(
        f"/api/v1/applications/{app_id}/documents",
        headers=citizen_headers,
        params={"document_type": final_doc_type},
        files={"file": (f"{final_doc_type}.pdf", files_to_upload[final_doc_type], "application/pdf")}
    )
    assert res_final.status_code == 201
    assert res_final.json()["is_locked_and_submitted"] is True

    # Check application is now SUBMITTED
    app_check = await client.get(f"/api/v1/applications/{app_id}", headers=citizen_headers)
    assert app_check.json()["current_status"] == "SUBMITTED"

    # --- TAMPER DETECTION TEST ---
    # Log in as Lambu
    lambu_token = await get_official_token(client, "EMP-LAMBU-001")
    lambu_headers = {"Authorization": f"Bearer {lambu_token}"}

    # If we modify a document on disk, verification should fail with a TAMPERING error
    # Let's locate the uploaded file path from the document database schema
    uploaded_doc_url = app_check.json()["documents"][0]["storage_url"]
    
    # Modify the file content on disk to simulate tampering
    with open(uploaded_doc_url, "w") as f:
        f.write("TAMPERED FILE CONTENT HERE")

    # Attempt to verify - should trigger TAMPERING error
    verification_payload = {
        "verdict": "VALID",
        "findings": "All house visits checked out fine",
        "lambu_signature_token": "0xLAMBU_KEY_IMPHAL_WEST"
    }
    tamper_res = await client.post(
        f"/api/v1/verify/{app_id}",
        headers=lambu_headers,
        json=verification_payload
    )
    assert tamper_res.status_code == 400
    assert "DATA_TAMPERING: Document mismatch" in tamper_res.json()["detail"]

    # Restore correct file content
    doc_type_0 = app_check.json()["documents"][0]["document_type"]
    original_content = files_to_upload[doc_type_0]
    with open(uploaded_doc_url, "wb") as f:
        f.write(original_content)

    # 3. Lambu Verification - Successful verification
    verify_res = await client.post(
        f"/api/v1/verify/{app_id}",
        headers=lambu_headers,
        json=verification_payload
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["verdict"] == "VALID"

    # 4. SDO Authorization - Final approval and minting
    sdo_token = await get_official_token(client, "EMP-SDO-001")
    sdo_headers = {"Authorization": f"Bearer {sdo_token}"}

    auth_payload = {
        "decision": "ISSUE",
        "sdo_signature_token": "0xSDO_KEY_IMPHAL_WEST"
    }
    auth_res = await client.post(
        f"/api/v1/authorize/{app_id}",
        headers=sdo_headers,
        json=auth_payload
    )
    assert auth_res.status_code == 200
    assert "certificate_number" in auth_res.json()
    assert auth_res.json()["certificate_type"] == "OBC"

    # 5. Public Audit Trail verification (no authentication needed)
    audit_res = await client.get(f"/api/v1/audit/{app_id}")
    assert audit_res.status_code == 200
    trail = audit_res.json()
    assert len(trail) == 3  # Submission (Genesis) -> Verified -> Issued
    assert trail[0]["stage"] == "SUBMITTED"
    assert trail[1]["stage"] == "FIELD_VERIFIED"
    assert trail[2]["stage"] == "APPROVED"

    # 6. Public Ledger Integrity Check
    integrity_res = await client.get(f"/api/v1/audit/{app_id}/verify-integrity")
    assert integrity_res.status_code == 200
    assert integrity_res.json()["is_integrity_intact"] is True
    assert integrity_res.json()["status"] == "SECURE"
