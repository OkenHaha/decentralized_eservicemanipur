# Production Implementation Plan: e-Seba Platform

## Decisions Locked In

| Decision | Answer |
|----------|--------|
| **Blockchain** | Simulated — SQLite hash-chained append-only table with application-level immutability enforcement |
| **Aadhaar** | Simulated — mock gateway returns dummy citizen data from a seed pool |
| **OTP** | Simulated — always `123456` in dev mode, logged to console instead of SMS |
| **DSC Tokens** | Simulated — mock signature verification, officials use password + role-based auth |
| **Storage** | Local filesystem (can swap to real S3/MinIO later) |
| **Database** | SQLite via SQLAlchemy (sync) + Alembic migrations — zero config, single file |
| **Framework** | FastAPI with Uvicorn |
| **Frontend** | Not in this iteration — API-first with Swagger UI for testing |

---

## Architecture Overview

```mermaid
graph TB
    subgraph "Client Layer"
        SWAGGER["Swagger UI<br/>(Auto-generated)"]
    end

    subgraph "API Layer — FastAPI"
        AUTH["/api/v1/auth/*"]
        APP["/api/v1/applications/*"]
        VERIFY["/api/v1/verify/*"]
        AUTHORIZE["/api/v1/authorize/*"]
        AUDIT["/api/v1/audit/*"]
        ADMIN["/api/v1/admin/*"]
    end

    subgraph "Service Layer"
        ID_SVC["Identity Service<br/>(Simulated Aadhaar + OTP)"]
        APP_SVC["Application Service<br/>(Validation + Submission)"]
        LEDGER_SVC["Ledger Service<br/>(Hash-Chain Ops)"]
        CRYPTO_SVC["Crypto Service<br/>(SHA-256 + Signatures)"]
        CERT_SVC["Certificate Service<br/>(QR + PDF Generation)"]
    end

    subgraph "Data Layer"
        DB["SQLite<br/>(eseba.db)"]
        FS["Local File Storage<br/>(Documents)"]
    end

    SWAGGER --> AUTH & APP & VERIFY & AUTHORIZE & AUDIT & ADMIN
    AUTH --> ID_SVC
    APP --> APP_SVC
    VERIFY --> LEDGER_SVC
    AUTHORIZE --> LEDGER_SVC & CERT_SVC
    AUDIT --> LEDGER_SVC
    ADMIN --> APP_SVC

    ID_SVC & APP_SVC & LEDGER_SVC & CERT_SVC --> DB
    APP_SVC --> FS
    ID_SVC --> CRYPTO_SVC
    LEDGER_SVC --> CRYPTO_SVC
end
```

---

## Project Structure

```
local_agent/
├── app/
│   ├── __init__.py
│   ├── main.py                          # FastAPI app entry point + lifespan
│   ├── config.py                        # Pydantic Settings — env-based config
│   ├── database.py                      # SQLAlchemy engine, SessionLocal, Base
│   ├── dependencies.py                  # Shared FastAPI dependencies (get_db, get_current_user)
│   │
│   ├── models/                          # SQLAlchemy ORM — maps 1:1 to the ER schema
│   │   ├── __init__.py                  # Exports all models
│   │   ├── citizen.py                   # Citizen, CitizenAddress, CitizenEducation,
│   │   │                                #   CitizenFamilyMember, CitizenWorkExperience,
│   │   │                                #   CitizenLanguage, CitizenPhysicalStandard
│   │   ├── application.py               # Application, ApplicationDocument,
│   │   │                                #   ApplicationStatusLog, ApplicationFee,
│   │   │                                #   ApplicationRemark, ApplicationAssignment
│   │   ├── admin.py                     # Office, Role, GovernmentOfficial,
│   │   │                                #   WorkflowStage, ServiceCatalog
│   │   ├── ledger.py                    # BlockchainLedgerEntry, AuditLog
│   │   ├── certificate.py              # IssuedCertificate, VerificationReport
│   │   ├── employment.py               # EmploymentRegistration
│   │   └── notification.py             # Notification
│   │
│   ├── schemas/                         # Pydantic v2 request/response models
│   │   ├── __init__.py
│   │   ├── auth.py                      # CaptchaResponse, OTPRequest, OTPVerify, RegisterRequest
│   │   ├── citizen.py                   # CitizenProfile, AddressCreate, EducationCreate, etc.
│   │   ├── application.py              # ApplicationCreate, ApplicationResponse, StatusLogResponse
│   │   ├── admin.py                     # OfficialLogin, AssignmentCreate, RemarkCreate
│   │   ├── verification.py             # VerificationSubmit, AuthorizationSubmit
│   │   └── audit.py                     # AuditTrailResponse
│   │
│   ├── api/                             # Route handlers — thin layer, delegates to services
│   │   ├── __init__.py
│   │   ├── router.py                    # Master router that includes all sub-routers
│   │   ├── auth.py                      # Citizen registration + login (algo_one)
│   │   ├── citizen.py                   # Profile, address, education CRUD
│   │   ├── applications.py             # Submit, track, list applications (algo_two)
│   │   ├── employment.py               # Employment Exchange workflows (algo_three)
│   │   ├── documents.py                # File upload + hash locking (file_locking)
│   │   ├── verification.py             # Lambu field verification (verification_transaction)
│   │   ├── authorization.py            # SDO certificate approval (authorization)
│   │   ├── audit.py                     # Public transparency trail (public_audit)
│   │   └── admin.py                     # Office/official management, assignments, dashboard
│   │
│   ├── services/                        # Business logic — your 6 algorithms live here
│   │   ├── __init__.py
│   │   ├── identity_service.py          # Simulated Aadhaar + OTP + CAPTCHA
│   │   ├── application_service.py       # Validation, submission, status transitions
│   │   ├── employment_service.py        # Employment Exchange: register, renew, mutate
│   │   ├── ledger_service.py            # Hash-chain: append, traverse, verify integrity
│   │   ├── crypto_service.py            # SHA-256 hashing, simulated signature ops
│   │   ├── certificate_service.py       # QR code generation, certificate minting
│   │   ├── assignment_service.py        # Auto-assign applications to officials
│   │   └── notification_service.py      # Create + dispatch notifications (console in dev)
│   │
│   ├── simulators/                      # All mocked external systems
│   │   ├── __init__.py
│   │   ├── aadhaar_gateway.py           # Returns dummy citizen data from a seed pool
│   │   ├── otp_provider.py              # Always accepts 123456, logs to console
│   │   └── dsc_verifier.py              # Mock DSC token validation for officials
│   │
│   └── seed/                            # Database seed data
│       ├── __init__.py
│       ├── seed_services.py             # Populate SERVICE_CATALOG with all 6+ service types
│       ├── seed_offices.py              # Populate OFFICE hierarchy (DC → SDO → Circle)
│       ├── seed_roles.py                # Populate ROLE table
│       ├── seed_officials.py            # Create test officials with mock DSC keys
│       ├── seed_citizens.py             # Create test citizens with dummy Aadhaar data
│       └── run_seed.py                  # Master script to seed everything
│
├── migrations/                          # Alembic
│   ├── env.py
│   ├── alembic.ini
│   └── versions/                        # Auto-generated migration files
│
├── uploads/                             # Local file storage for documents
│   └── .gitkeep
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                      # Test fixtures — test DB, test client, seeded data
│   ├── test_auth.py                     # Registration + login flow
│   ├── test_applications.py             # Application submission + validation
│   ├── test_ledger.py                   # Hash-chain integrity
│   ├── test_verification.py             # Lambu verification + tampering detection
│   ├── test_authorization.py            # SDO approval flow
│   └── test_audit.py                    # Audit trail traversal
│
├── docs/                                # Original design docs (preserved)
│   ├── algo_one.md
│   ├── algo_two.md
│   ├── algo_three.md
│   ├── authorizatoin.md
│   ├── file_locking.md
│   ├── public_audit.md
│   └── verification_transaction.md
│
├── er.md                                # Updated ER schema (24 tables)
├── pyproject.toml                       # Updated with all dependencies
├── .env                                 # Local environment variables
├── .env.example                         # Template for other developers
├── .gitignore                           # Updated
└── README.md                            # Project documentation
```

---

## Simulators (Detailed Design)

### Simulated Aadhaar Gateway (`simulators/aadhaar_gateway.py`)

A pool of ~10 fake citizens. When `query_aadhaar(aadhaar_number, mobile)` is called:
- If the Aadhaar number matches a seed record → returns dummy profile (name, DOB, gender, father's name, address)
- If not found → returns an error mimicking the real UIDAI response
- Any 12-digit number starting with `9` will always succeed (for easy testing)

```
Seed examples:
  999900000001 → "Laishram Tomba Singh", M, 1995-03-15, Imphal West
  999900000002 → "Oinam Bembem Devi", F, 1988-07-22, Thoubal
  999900000003 → "Naorem Roshibina Chanu", F, 2001-11-08, Bishnupur
  ...
```

### Simulated OTP (`simulators/otp_provider.py`)

- `send_otp(mobile)` → logs `"[DEV OTP] Sent 123456 to 91XXXXXXXX"` to console, returns success
- `verify_otp(mobile, code)` → accepts `123456` always, rejects anything else
- In production, swap this for an actual SMS gateway (MSG91, Twilio, etc.)

### Simulated DSC Verifier (`simulators/dsc_verifier.py`)

- Each test official gets a mock wallet address (`0xABCD...`) and a simulated DSC serial
- `verify_signature(token, expected_role)` → checks if the token matches a known official's mock key and role
- No real cryptographic signing — just a lookup validation

---

## Build Phases

### Phase 1: Foundation
> Database + Models + Config + Migrations

| File | What it does |
|------|-------------|
| `app/config.py` | Load SECRET_KEY, UPLOAD_DIR, DEV_MODE from `.env` — DB is just `sqlite:///eseba.db` |
| `app/database.py` | SQLAlchemy engine (SQLite), `SessionLocal`, `Base` declarative base |
| `app/models/*.py` | All 24 tables as SQLAlchemy models — matching the ER schema exactly |
| `migrations/` | Alembic init + initial migration generating all tables |
| `pyproject.toml` | Dependencies: `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `aiosqlite`, `alembic`, `pydantic-settings`, `python-jose[cryptography]`, `passlib[bcrypt]`, `python-multipart`, `qrcode[pil]` |

### Phase 2: Simulators + Crypto + Seeds
> Mock external systems + hash utilities + test data

| File | What it does |
|------|-------------|
| `app/simulators/aadhaar_gateway.py` | Dummy Aadhaar data pool with ~10 test citizens |
| `app/simulators/otp_provider.py` | Console-logged OTP, always `123456` |
| `app/simulators/dsc_verifier.py` | Mock DSC token validation |
| `app/services/crypto_service.py` | SHA-256 file hashing, hash-chain block computation |
| `app/seed/*.py` | Seed scripts for services, offices, roles, officials, citizens |

### Phase 3: Auth + Identity
> Citizen registration and login — implements algo_one

| File | What it does |
|------|-------------|
| `app/schemas/auth.py` | Request/response models for CAPTCHA, OTP, registration |
| `app/services/identity_service.py` | CAPTCHA generation, OTP flow, Aadhaar lookup, profile creation |
| `app/api/auth.py` | `POST /captcha`, `POST /otp/send`, `POST /otp/verify`, `POST /register` |
| `app/dependencies.py` | `get_current_citizen` — JWT token extraction + validation |

### Phase 4: Applications + Documents
> Application submission and document upload — implements algo_two + file_locking

| File | What it does |
|------|-------------|
| `app/schemas/application.py` | Application create/response, document upload models |
| `app/services/application_service.py` | Per-service validation (driven by SERVICE_CATALOG), submission, tracking |
| `app/services/ledger_service.py` | Genesis block creation on submission, hash-chain append |
| `app/api/applications.py` | `POST /applications`, `GET /applications/{id}`, `GET /applications/mine` |
| `app/api/documents.py` | `POST /documents/upload`, file hash computation + storage |

### Phase 5: Admin + Verification + Authorization
> Official workflows — implements verification_transaction + authorization

| File | What it does |
|------|-------------|
| `app/schemas/admin.py` | Official login, assignment, remark models |
| `app/schemas/verification.py` | Verification verdict, authorization decision models |
| `app/api/admin.py` | Official login, view queue, manage assignments |
| `app/api/verification.py` | `POST /verify/{id}` — Lambu field verification with tampering check |
| `app/api/authorization.py` | `POST /authorize/{id}` — SDO approval + certificate generation |
| `app/services/certificate_service.py` | QR hash generation, certificate record creation |

### Phase 6: Audit + Employment Exchange
> Public audit trail + Employment Exchange — implements public_audit + algo_three

| File | What it does |
|------|-------------|
| `app/api/audit.py` | `GET /audit/{id}` — public, no auth, full chronological trail |
| `app/api/employment.py` | `POST /employment/register`, `POST /employment/renew`, `POST /employment/update` |
| `app/services/employment_service.py` | Registration, renewal (3yr+3mo), qualification/experience mutation |

### Phase 7: Tests + Polish
> Automated tests + error handling + documentation

| File | What it does |
|------|-------------|
| `tests/conftest.py` | Test DB setup, fixtures, seeded data |
| `tests/test_*.py` | Tests for each major flow |
| `app/main.py` | CORS, error handlers, startup seed, Swagger metadata |
| `README.md` | Setup instructions, API docs, architecture overview |

---

## API Endpoint Summary

### Citizen Auth (`/api/v1/auth`)
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/captcha` | Generate CAPTCHA challenge | None |
| POST | `/otp/send` | Send OTP to mobile (simulated) | CAPTCHA |
| POST | `/otp/verify` | Verify OTP + get session token | None |
| POST | `/register` | Complete registration with Aadhaar (simulated) | OTP verified |
| POST | `/login` | Login with phone + OTP | None |

### Citizen Profile (`/api/v1/citizens`)
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/me` | Get own profile | Citizen |
| PUT | `/me` | Update mutable fields (phone, email, etc.) | Citizen |
| POST | `/me/addresses` | Add an address | Citizen |
| POST | `/me/education` | Add education qualification | Citizen |
| POST | `/me/family` | Add family member | Citizen |
| POST | `/me/experience` | Add work experience | Citizen |

### Applications (`/api/v1/applications`)
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/services` | List available services from catalog | None |
| POST | `/` | Submit a new application | Citizen |
| GET | `/mine` | List my applications | Citizen |
| GET | `/{application_id}` | Get application details + status | Citizen/Official |
| GET | `/{application_id}/status-history` | Full status transition log | Citizen/Official |
| POST | `/{application_id}/documents` | Upload documents | Citizen |

### Employment Exchange (`/api/v1/employment`)
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/register` | New Employment Exchange registration | Citizen |
| POST | `/renew` | Renew existing registration | Citizen |
| POST | `/update` | Add qualification or experience | Citizen |
| GET | `/{registration_id}` | View registration details | Citizen/Official |

### Official Admin (`/api/v1/admin`)
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/login` | Official login | None |
| GET | `/queue` | View assigned application queue | Official |
| GET | `/queue/office` | View all applications for the office | Official |
| POST | `/assign/{application_id}` | Assign application to an official | Senior Official |
| POST | `/remark/{application_id}` | Add remark/observation/query | Official |

### Verification (`/api/v1/verify`)
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/{application_id}` | Submit field verification verdict | Lambu/Mandal |
| GET | `/{application_id}/report` | View verification report | Official |

### Authorization (`/api/v1/authorize`)
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/{application_id}` | Issue or deny certificate | SDO/SDC |

### Public Audit (`/api/v1/audit`)
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/{application_id}` | Full chronological audit trail | **None — public** |
| GET | `/{application_id}/verify-integrity` | Verify hash-chain is unbroken | **None — public** |

---

## Algo-to-Code Mapping

| Pseudocode | → Service | → API Route | Simulated Parts |
|------------|-----------|-------------|-----------------|
| `algo_one` (Aadhaar Ingestion) | `identity_service.py` | `/auth/*` | Aadhaar lookup, OTP, CAPTCHA |
| `algo_two` (Revenue Application) | `application_service.py` | `/applications/*` | None — real validation logic |
| `algo_three` (Employment Exchange) | `employment_service.py` | `/employment/*` | None — real validation logic |
| `file_locking` (Document Hashing) | `ledger_service.py` + `crypto_service.py` | `/applications/{id}/documents` | None — real SHA-256 hashing |
| `verification_transaction` (Lambu) | `ledger_service.py` | `/verify/{id}` | DSC token verification |
| `authorizatoin` (SDO Approval) | `ledger_service.py` + `certificate_service.py` | `/authorize/{id}` | DSC token, QR code is real |
| `public_audit` (Transparency) | `ledger_service.py` | `/audit/{id}` | None — real hash-chain traversal |

---

## Verification Plan

### Automated Tests
```bash
# Run all tests
pytest tests/ -v

# Test specific flows
pytest tests/test_auth.py -v          # Registration + login
pytest tests/test_applications.py -v  # Application submission + validation
pytest tests/test_ledger.py -v        # Hash-chain integrity verification
pytest tests/test_verification.py -v  # Tampering detection
```

### Manual Verification via Swagger UI
1. Start the server: `uvicorn app.main:app --reload`
2. Open `http://localhost:8000/docs`
3. Walk through the full flow:
   - Register a citizen (simulated Aadhaar + OTP)
   - Submit an OBC certificate application
   - Upload documents → verify SHA-256 hashes are computed
   - Login as Lambu → run field verification
   - Login as SDO → approve + issue certificate
   - Hit the public audit endpoint → see the full hash-chained trail
4. Attempt tampering: re-upload a modified document after submission → verify hash mismatch is caught
