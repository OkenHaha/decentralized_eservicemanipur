# Walkthrough: React Frontend for e-Seba replica

We have built and compiled a highly responsive, custom dark glassmorphic React frontend for the **Anti-Corruption e-Seba Replica** platform. This frontend coordinates with the FastAPI database-ledger backend to provide a fully visual test environment.

---

## 🛠️ Setup & Run Instructions

To test the full system, run the backend and frontend dev servers concurrently:

### 1. Run the Backend API
From the root directory:
```powershell
# Activate virtual environment
.venv\Scripts\activate

# Start the FastAPI server (runs on http://127.0.0.1:8000)
python main.py
```

### 2. Run the React Frontend
In a separate terminal shell:
```powershell
# Navigate to the frontend directory
cd frontend

# Install Node dependencies (already scaffolded)
npm install

# Start the Vite React development server (runs on http://localhost:5173)
npm run dev
```

Open your browser to `http://localhost:5173` to explore the interface.

---

## 🔬 End-to-End Testing Workflow

To experience the full cryptographic ledger and anti-corruption lifecycle:

### Step 1: Public Audit Trail Verification
1. On the landing page (`http://localhost:5173`), scroll to the **Verify Application Blockchain Ledger** section.
2. In the seed data, a sample application has been seeded (or you can create a new one). 
3. Type an Application ID and click **Audit Ledger**.
4. You will see a chronological view of all ledger block sequences (Genesis block, Lambu verification block, and SDO issuance block) along with their SHA-256 hashes, signee address keys, and an integrity status badge ("LEDGER INTEGRITY SECURE").

### Step 2: Citizen Aadhaar Onboarding & Draft Submission
1. Click **Citizen Portal** in the top navigation header.
2. Fill out the Aadhaar onboarding parameters:
   - **Aadhaar Number:** Enter a 12-digit number (e.g. `999900000001` to fetch seeded details, or any other).
   - **Mobile Phone:** Enter a 10-digit number.
   - **CAPTCHA:** Enter the value shown in the gold block.
3. Click **Request Authentication OTP**.
4. Enter the mock OTP code: `123456` (the system logs OTP handshakes to the backend console).
5. Click **Verify & Login**. The portal will retrieve and freeze the citizen's Aadhaar profile data.
6. Click **New Application**, select a service (e.g. OBC Certificate), fill in the fields, accept the legal declaration, and click **Create Application Draft**.

### Step 3: Document Sealing & Genesis Anchoring
1. After draft creation, you will be taken to the **Document Attachment Vault**.
2. Click **Upload PDF** for the required documents list.
3. Once the **final missing document** is successfully attached:
   - The frontend automatically triggers local hash calculations.
   - The backend locks the draft application state to `SUBMITTED`.
   - The backend appends a Genesis Block to the blockchain ledger containing the document aggregate hash fingerprint.

### Step 4: Lambu Field Inspection (Official Review)
1. In the header, click the **Quick Login** key button.
2. Select **Lambu: Sanjit Singh** (`EMP-LAMBU-001` / `password123`).
3. You will be taken to the Lambu review workspace showing a queue of newly `SUBMITTED` applications.
4. Click **Open Review Workspace** for your citizen's application.
5. Review the files, check off the physical checklist, set the verdict to `VALID`, input findings details, sign it with your cryptographic signature, and click **Submit & Sign Block**.
6. This appends a `FIELD_VERIFIED` block to the ledger.

### Step 5: SDO Magistrate Issuance
1. Click the **Quick Login** button again and select **SDO: Dr. Premjit Singh** (`EMP-SDO-001` / `password123`).
2. SDO's queue will display the `FIELD_VERIFIED` application.
3. Open the workspace, inspect the Lambu findings report, select the decision `ISSUE`, and sign the approval transaction.
4. This appends an `APPROVED` block to the ledger and mints the final certificate in the database!

### Step 6: Certificate Verification
1. Click **Quick Login** and select your Citizen profile again.
2. In the dashboard, you will find the status updated to `APPROVED`.
3. Click **View Certificate** to open a high-fidelity printable digital certificate, showing the secure QR verification code, certificate details, and SDO signature.
4. Anyone can copy the Application ID and paste it on the Public Audit tab to verify that the chain of custody remains untampered!
