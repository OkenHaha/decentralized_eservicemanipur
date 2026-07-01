# e-Services Manipur: Anti-Corruption Platform Replica

A high-fidelity replica implementation of Manipur's **e-Services Manipur** certificate issuance portal. The system prevents administrative corruption, document backdating, and unauthorized data alterations by anchoring critical workflow transitions into an external, immutable cryptographic blockchain ledger.

---

## 🚀 Key Features

*   **Aadhaar-Linked Authentication:** Onboards citizens securely via a simulated OTP handshake and UIDAI registry lookup, freezing primary identity metrics (immutable fields).
*   **Normalized Database Schema:** A robust 24-table SQLite schema mapping citizen profiles, family networks, educational history, work experience, status history logs, and official designation queues.
*   **External Blockchain Ledger:** Integrates with an external blockchain node for transaction security, mining blocks for every application submission, Lambu field verification, and SDO approval stage.
*   **Cryptographic Document Locking:** Computes SHA-256 hashes of all uploaded files, locks them into a unified document fingerprint, and creates an immutable genesis block.
*   **Field Inspector Verification:** Supports circle-level field inspections (Lambu) with hardware-key cryptographic signatures and automatic document-tampering detection.
*   **Final Administrative Approval:** SDO/SDC approval workflow validating digital tokens, recording decision blocks, and minting PDF certificates with security QR hashes.
*   **Public Audit Trail:** Traverses the cryptographic linked-list blocks backwards from the current state to the genesis block, providing full, zero-auth public transparency.
*   **Ledger Chain Integrity Verification:** Sequentially re-computes all SHA-256 block hashes on the chain to detect any unauthorized database tampering or block changes.

---

## 🛠 Tech Stack

### Backend API
*   **Framework:** FastAPI (Python 3.12+)
*   **Database:** SQLite via SQLAlchemy (async engine using `aiosqlite`)
*   **Migrations:** Alembic
*   **Security:** PyJWT & Cryptography
*   **Testing:** Pytest, pytest-asyncio, HTTPX AsyncClient

### Frontend Portal
*   **Framework:** React 18+ (Vite)
*   **Styling:** Vanilla CSS (Dark Glassmorphic UI)
*   **Icons:** Lucide React

---

## ⚙️ Setup & Running the Platform

This project runs in three parts:
1. **Blockchain Simulation Node**
2. **e-Services Manipur Backend API**
3. **Vite React Frontend**

### Part 1: Blockchain Simulation Node
This repository integrates with the external blockchain simulator node. Clone, install, and run the simulator first:

1. Clone and navigate to the simulation repository:
   ```bash
   git clone https://github.com/OkenHaha/blockchain-simulation.git
   cd blockchain-simulation
   ```
2. Create and activate a virtual environment, then install requirements:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Start the node server (runs on port `8000`):
   ```bash
   uvicorn server:app --port 8000
   ```

---

### Part 2: e-Services Manipur Backend API
1. Navigate to the `decentralized_eservicemanipur` directory.
2. Create and activate a virtual environment, then install dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r pyproject.toml
   pip install pytest httpx pytest-asyncio python-dateutil
   ```
3. Run migrations and database seeding:
   ```bash
   # Apply migrations
   alembic upgrade head
   ```
4. Start the backend API on port `8001` (to avoid conflicting with the blockchain node on `8000`):
   ```bash
   uvicorn app.main:app --port 8001
   ```
   *   **API URL:** `http://127.0.0.1:8001`
   *   **Swagger Documentation:** `http://127.0.0.1:8001/docs`

---

### Part 3: Vite React Frontend
1. Navigate to the `frontend` folder:
   ```bash
   cd frontend
   ```
2. Create a `.env` file containing the backend port details:
   ```env
   VITE_API_BASE=http://localhost:8001/api/v1
   ```
3. Install dependencies and start the Vite development server (runs on `http://localhost:5173`):
   ```bash
   npm install
   npm run dev
   ```

---

## 🔬 End-to-End Testing Workflow

Open your browser to `http://localhost:5173` to explore the interface:

### Step 1: Public Audit Trail Verification
1. On the landing page scroll to the **Verify Application Blockchain Ledger** section.
2. Enter an application ID (e.g. from the seeded credentials or new submissions) and click **Audit Ledger**.
3. The interface displays the chronological sequence blocks (Genesis, Lambu field verification, SDO approval) with SHA-256 hashes, signee address keys, and a `LEDGER INTEGRITY SECURE` badge.

### Step 2: Citizen Aadhaar Onboarding & Draft Submission
1. Click **Citizen Portal** in the navigation header.
2. Onboard using a citizen credential (e.g., `9876543210` with mock OTP `123456`).
3. Fill in a service application form (e.g. OBC Certificate), accept the legal declaration, and click **Create Application Draft**.

### Step 3: Document Sealing & Genesis Anchoring
1. Upload the required PDFs in the **Document Attachment Vault**.
2. Once the **final missing document** is successfully attached:
   * The app transitions to `SUBMITTED`.
   * A transaction is broadcasted to the blockchain simulator node.
   * A **Genesis Block** containing the document hashes is mined.

### Step 4: Lambu Field Inspection
1. Click **Quick Login** and select **Lambu: Sanjit Singh** (`EMP-LAMBU-001` / `password123`).
2. Open the review workspace, verify the files, set the verdict to `VALID`, and sign it using your cryptographic signature token (`0xLAMBU_KEY_IMPHAL_WEST`).
3. This adds a `FIELD_VERIFIED` block to the blockchain ledger.

### Step 5: SDO Magistrate Issuance
1. Click **Quick Login** and select **SDO: Dr. Premjit Singh** (`EMP-SDO-001` / `password123`).
2. Open the workspace, inspect the Lambu findings report, select the decision `ISSUE`, and sign the approval transaction (`0xSDO_KEY_IMPHAL_WEST`).
3. This appends an `APPROVED` block to the ledger and mints the final certificate in the database!

### Step 6: Certificate Verification
1. Log back in as your Citizen profile.
2. In the dashboard, you will find the status updated to `APPROVED`.
3. Click **View Certificate** to open a high-fidelity printable digital certificate, showing the secure QR verification code, certificate details, and SDO signature.
4. Anyone can copy the Application ID and paste it on the Public Audit tab to verify that the chain of custody remains untampered!

---

## 🧪 Running Automated Tests

Run the backend pytest suite to verify ledger integrity rules, tamper detection, and validation logic:
```bash
pytest -v
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
