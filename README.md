# Anti-Corruption e-Seba Replica

A production-ready replica implementation of Manipur's **e-Seba Anti-Corruption Platform**. Built with **FastAPI**, **SQLAlchemy (SQLite)**, and a **simulated cryptographic hash-chained blockchain ledger** for complete tracking transparency, anti-tampering, and document security.

---

## 🚀 Key Features

*   **Aadhaar-Linked Authentication:** Onboards citizens securely via a simulated OTP handshake and UIDAI registry lookup, freezing primary identity metrics (immutable fields).
*   **Normalized Database Schema:** A robust 24-table SQLite schema mapping citizen profiles, family networks, educational history, work experience, status history logs, and official designation queues.
*   **Cryptographic Document Locking:** Computes SHA-256 hashes of all uploaded files, locks them into a unified document fingerprint, and creates an immutable genesis block.
*   **Field Inspector Verification:** Supports circle-level field inspections (Lambu) with cryptographic signatures and automatic document-tampering detection.
*   **Final Administrative Approval:** SDO/SDC approval workflow validating digital tokens, recording decision blocks, and minting PDF certificates with security QR hashes.
*   **Public Audit Trail:** Traverses the cryptographic linked-list blocks backwards from the current state to the genesis block, providing full, zero-auth public transparency.
*   **Ledger Chain Integrity Verification:** Sequentially re-computes all SHA-256 block hashes in the database to detect any unauthorized database tampering.

---

## 🛠 Tech Stack

*   **Framework:** FastAPI (Python 3.12+)
*   **Database:** SQLite via SQLAlchemy (async engine using `aiosqlite`)
*   **Migrations:** Alembic
*   **Security:** PyJWT & Cryptography
*   **Testing:** Pytest, pytest-asyncio, HTTPX AsyncClient

---

## 📁 Project Structure

```
local_agent/
├── app/
│   ├── main.py                     # FastAPI entry point & database initialization
│   ├── config.py                   # Pydantic Settings & environment config
│   ├── database.py                 # SQLAlchemy async engine & SessionLocal
│   ├── dependencies.py             # Auth verification (JWT, Roles, etc.)
│   ├── api/                        # Route controller endpoints
│   ├── models/                     # SQLAlchemy 2.0 database models
│   ├── schemas/                    # Pydantic v2 schemas
│   ├── services/                   # Business logic (Ingestion, Locking, Approval)
│   └── simulators/                 # Simulated external systems (Aadhaar, OTP, DSC)
├── migrations/                     # Alembic async migration files
├── tests/                          # Automated Pytest suite
├── README.md                       # Project documentation
├── pyproject.toml                  # Project metadata and dependencies
└── main.py                         # FastAPI runner script
```

---

## ⚙️ Setup & Installation

### 1. Prerequisites
Ensure you have Python 3.12+ and `uv` (recommended) or `pip` installed.

### 2. Setup Virtual Environment & Install Dependencies
Using `uv`:
```bash
uv pip install -e .
uv pip install pytest httpx pytest-asyncio
```
Using standard `pip`:
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
pip install pytest httpx pytest-asyncio
```

### 3. Database Initialization & Seeding
Initialize the tables and seed default offices, roles, services, test citizens, and official credentials:
```bash
# Run migrations
.venv\Scripts\alembic upgrade head

# Seed default mock data
.venv\Scripts\python app/seed/run_seed.py
```

---

## 💻 Running the Application

Start the local server using the runner script:
```bash
.venv\Scripts\python main.py
```

*   **API URL:** `http://127.0.0.1:8000`
*   **Interactive API Docs (Swagger):** `http://127.0.0.1:8000/docs`

---

## 🧪 Running tests

Execute the automated test suite to verify auth flows, validation pipelines, and cryptographic integrity:
```bash
.venv\Scripts\pytest -v
```

---

## 🔍 Simulation Test Credentials

For local development and Swagger testing:

### Citizens
*   **Laishram Tomba Singh**
    *   Phone/User ID: `9876543210`
    *   Password/OTP: `123456`
*   **Oinam Bembem Devi**
    *   Phone/User ID: `9876543211`
    *   Password/OTP: `123456`

### Government Officials
*   **Lambu (Field Inspector):**
    *   Employee ID: `EMP-LAMBU-001`
    *   Password: `password123`
    *   DSC Token: `0xLAMBU_KEY_IMPHAL_WEST`
*   **SDO (Sub-Divisional Officer):**
    *   Employee ID: `EMP-SDO-001`
    *   Password: `password123`
    *   DSC Token: `0xSDO_KEY_IMPHAL_WEST`
