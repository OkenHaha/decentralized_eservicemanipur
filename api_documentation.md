# Blockchain Audit Ledger Node - API Documentation

The Blockchain Audit Ledger Node is a FastAPI-based REST API that runs on top of a SQLite-backed immutable blockchain ledger. This document provides a complete walkthrough of all available endpoints, their payload structures, and client examples using `curl` and PowerShell `Invoke-RestMethod`.

---

## Base URL
When running locally with the default configuration, the API is available at:
`http://127.0.0.1:8000`

FastAPI also provides an interactive Swagger UI documentation at:
`http://127.0.0.1:8000/docs`

---

## Endpoints Walkthrough

### 1. Root Dashboard (`GET /`)
Serves a premium, responsive HSL dark-themed HTML/JS status and management dashboard. It auto-updates stats every 10 seconds and allows users to generate keypairs, submit raw/signed transactions, mine pending blocks, and verify ledger integrity directly from a visual interface.

- **Request:**
  ```bash
  curl http://127.0.0.1:8000/
  ```
- **Response:**
  Returns `text/html` code containing the interactive UI.

---

### 2. Generate RSA Key Pair (`GET /keys`)
A helper endpoint that generates a secure, valid RSA public and private key pair. These PEM-formatted keys can be used to sign and cryptographically verify auditing log transactions.

- **Request Example:**
  *curl:*
  ```bash
  curl http://127.0.0.1:8000/keys
  ```
  *PowerShell:*
  ```powershell
  Invoke-RestMethod http://127.0.0.1:8000/keys
  ```

- **Response Example (JSON):**
  ```json
  {
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDK...",
    "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAys..."
  }
  ```

---

### 3. Get Full Blockchain Ledger (`GET /chain`)
Returns the complete list of blocks written to the SQLite database, their included transactions, indices, timestamps, nonces, and hashes. It also provides the overall ledger validity status.

- **Request Example:**
  *curl:*
  ```bash
  curl http://127.0.0.1:8000/chain
  ```
  *PowerShell:*
  ```powershell
  Invoke-RestMethod http://127.0.0.1:8000/chain | ConvertTo-Json -Depth 10
  ```

- **Response Example (JSON):**
  ```json
  {
    "chain_length": 3,
    "is_valid": true,
    "difficulty": 2,
    "blocks": [
      {
        "index": 0,
        "timestamp": 1782900219.4410362,
        "transactions": [
          {
            "sender": "Genesis",
            "receiver": "Genesis",
            "amount": 0.0,
            "message": "Genesis Block Transaction",
            "signature": "GenesisSignature"
          }
        ],
        "previous_hash": "0",
        "nonce": 0,
        "hash": "4c717d1d654a5b7bbd9fc395f1b05597e8fa57371d7516fec9412ac903f21aed"
      },
      {
        "index": 1,
        "timestamp": 1782900229.5665748,
        "transactions": [
          {
            "sender": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBg...",
            "receiver": "AuditorNode_Test_Receiver",
            "amount": 10.5,
            "message": "Audit Log: Modified Citizen Record ID 123",
            "signature": "9e007c44c3cc706787a704bdd486cd77c943..."
          },
          {
            "sender": "Network",
            "receiver": "MinerPublicKeyPlaceholder",
            "amount": 1.0,
            "message": "Miner Reward",
            "signature": "NetworkSignaturePlaceholder"
          }
        ],
        "previous_hash": "4c717d1d654a5b7bbd9fc395f1b05597e8fa57371d7516fec9412ac903f21aed",
        "nonce": 4,
        "hash": "00ca3f9f334d82ce989687373afdad080b6dd503ae6b9efc607c04e8bce1b02d"
      }
    ]
  }
  ```

---

### 4. Get Pending Queue (`GET /pending`)
Lists all transactions currently residing in the pending transaction pool (i.e. transactions that have been submitted/verified but not yet mined into a block).

- **Request Example:**
  *curl:*
  ```bash
  curl http://127.0.0.1:8000/pending
  ```

- **Response Example (JSON):**
  ```json
  [
    {
      "sender": "-----BEGIN PUBLIC KEY-----\nMIIBIj...",
      "receiver": "AuditorNode",
      "amount": 5.0,
      "message": "Log signature checkpoint verification",
      "signature": "3c02afae8840..."
    }
  ]
  ```

---

### 5. Submit Raw Transaction (`POST /transactions/new`)
Submits a new transaction directly to the pending transaction queue. If the sender matches an RSA Public Key format, the node validates the hex signature against the transaction details before adding it.

- **Payload Schema (`TransactionPayload`):**
  - `sender` (string, required): Sender public key or identifier.
  - `receiver` (string, required): Receiver public key or identifier.
  - `amount` (float, required): Transacted value/units.
  - `message` (string, optional): String message or data payload metadata.
  - `signature` (string, optional): Hex-encoded cryptographic signature.

- **Request Example:**
  *curl:*
  ```bash
  curl -X POST -H "Content-Type: application/json" \
    -d '{"sender": "AppNode", "receiver": "AuditorNode", "amount": 0.0, "message": "Raw log test"}' \
    http://127.0.0.1:8000/transactions/new
  ```
  *PowerShell:*
  ```powershell
  Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/transactions/new `
    -ContentType "application/json" `
    -Body '{"sender": "AppNode", "receiver": "AuditorNode", "amount": 0.0, "message": "Raw log test"}'
  ```

- **Response Example (JSON):**
  ```json
  {
    "message": "Transaction added successfully to the pending pool."
  }
  ```

---

### 6. Create & Sign Transaction (`POST /transactions/create-signed`)
A helper endpoint that accepts the sender's Private Key alongside transaction details. It signs the transaction on the server and automatically inserts it into the pending queue. **Note:** This is highly useful for testing or node-to-node automated integrations.

- **Payload Schema (`QuickSignedPayload`):**
  - `sender_private_key` (string, required): PEM private key to sign the transaction.
  - `sender_public_key` (string, required): PEM public key of the sender.
  - `receiver_public_key` (string, required): PEM public key or string identifier of receiver.
  - `amount` (float, required): Units/amount to transcode.
  - `message` (string, optional): Audit description/payload message.

- **Request Example:**
  *PowerShell:*
  ```powershell
  $body = @{
    sender_private_key = $myPrivateKey
    sender_public_key = $myPublicKey
    receiver_public_key = "AuditorNode"
    amount = 50.0
    message = "Audit entry logged from API"
  } | ConvertTo-Json

  Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/transactions/create-signed `
    -ContentType "application/json" `
    -Body $body
  ```

- **Response Example (JSON):**
  ```json
  {
    "message": "Signed transaction created and added to the pending pool.",
    "signature": "7809b5f2fc25d343bd742c0ec802f..."
  }
  ```

---

### 7. Mine Pending Transactions (`POST /mine`)
Selects a miner using a simplified Proof of Stake (PoS) mechanism, adds a miner reward transaction (`1.0` tokens issued by `"Network"`), mines the pending pool into a block conforming to the target difficulty, and writes it persistently to the SQLite database.

- **Request Example:**
  *curl:*
  ```bash
  curl -X POST http://127.0.0.1:8000/mine
  ```
  *PowerShell:*
  ```powershell
  Invoke-RestMethod -Method Post http://127.0.0.1:8000/mine
  ```

- **Response Example (JSON):**
  ```json
  {
    "message": "Block successfully mined and written to SQLite ledger.",
    "block_index": 2,
    "block_hash": "008442dc09bcfbd6e0ae447a781a670aaead9851517544416508131eeef8b5ba",
    "nonce": 195,
    "transactions_count": 2
  }
  ```

---

### 8. Verify SQLite Ledger Integrity (`GET /validate`)
Recalculates block hashes, validates block chain linkage sequence (previous hashes), and checks the validity of transaction signatures against stored public keys to detect offline DB tampering.

- **Request Example:**
  *curl:*
  ```bash
  curl http://127.0.0.1:8000/validate
  ```
  *PowerShell:*
  ```powershell
  Invoke-RestMethod http://127.0.0.1:8000/validate
  ```

- **Response Example (JSON):**
  ```json
  {
    "is_valid": true,
    "message": "Blockchain state is valid and secure."
  }
  ```
