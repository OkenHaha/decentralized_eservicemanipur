# Entity-Relationship (ER) Schema Documentation
## System: e-Seba Replica (Hybrid Blockchain-Database Architecture)

This documentation provides the complete data structure layout for a hybrid architecture designed to combat corruption, ensure tracking transparency, and eliminate document tampering.

The schema is organized into **5 domains**:
1. **Citizen Domain** — Profile, addresses, education, family, work history
2. **Application Domain** — Submissions, status tracking, documents, fees
3. **Admin Domain** — Offices, officials, roles, assignments, workflow
4. **Verification & Certificate Domain** — Field reports, issued certificates
5. **Blockchain & Audit Domain** — Immutable ledger, system audit logs

---

## 1. Complete Mermaid ER Diagram

```mermaid
erDiagram

    %% ========================================
    %% CITIZEN DOMAIN
    %% ========================================

    CITIZEN ||--o{ CITIZEN_ADDRESS : "has"
    CITIZEN ||--o{ CITIZEN_EDUCATION : "has"
    CITIZEN ||--o{ CITIZEN_FAMILY_MEMBER : "has"
    CITIZEN ||--o{ CITIZEN_WORK_EXPERIENCE : "has"
    CITIZEN ||--o{ CITIZEN_LANGUAGE : "speaks"
    CITIZEN ||--o{ APPLICATION : "submits"
    CITIZEN ||--o{ NOTIFICATION : "receives"

    CITIZEN {
        uuid citizen_id PK
        string aadhaar_hash UK "SHA-256 of Aadhaar number — never store raw"
        string full_name "Immutable — locked from Aadhaar registry"
        string father_name "Immutable — locked from Aadhaar registry"
        date date_of_birth "Immutable — locked from Aadhaar registry"
        string gender "Immutable — locked from Aadhaar registry"
        string religion "User-provided on first application"
        string caste_category "GENERAL | OBC | SC | ST"
        string sub_caste "Specific sub-caste or tribe name"
        string phone_primary "OTP-verified mobile number"
        string phone_secondary "Optional alternate contact"
        string email "Optional email address"
        string epic_number "Voter ID EPIC number"
        string marital_status "SINGLE | MARRIED | DIVORCED | WIDOWED"
        string blood_group "A+ | A- | B+ | B- | AB+ | AB- | O+ | O-"
        string profile_photo_url "S3 path to passport-size photo"
        boolean is_active "Account active flag"
        string session_token "Current active session JWT reference"
        timestamp registered_at "Account creation timestamp"
        timestamp last_login_at "Most recent login"
        timestamp updated_at "Profile last modified"
    }

    CITIZEN_ADDRESS {
        uuid address_id PK
        uuid citizen_id FK
        string address_type "PERMANENT | PRESENT | CORRESPONDENCE"
        string house_no "House or flat number"
        string street_locality "Street name or locality"
        string village_town "Village or town name"
        string post_office "Nearest post office"
        string police_station "Jurisdictional police station"
        string circle "Revenue circle"
        string sub_division "Administrative sub-division"
        string district "District name"
        string state "State — defaults to Manipur"
        string pin_code "6-digit PIN code"
        string area_type "URBAN | RURAL"
        boolean is_primary "Flag for default address"
        timestamp created_at
        timestamp updated_at
    }

    CITIZEN_EDUCATION {
        uuid education_id PK
        uuid citizen_id FK
        string exam_passed "e.g. HSLC, Class XII, BA, MA, BTech"
        string board_or_university "Board or University name"
        string institute_name "School or college attended"
        string subjects_list "Comma-separated subjects"
        string division_or_grade "First | Second | Third | Distinction"
        decimal percentage_or_cgpa "Marks percentage or CGPA"
        int year_of_passing "Year of passing"
        int course_duration_years "Duration in years"
        string instruction_medium "English | Hindi | Manipuri | etc"
        string certificate_doc_url "S3 path to uploaded certificate"
        bytes32 certificate_doc_hash "SHA-256 of certificate file"
        int sort_order "Display ordering — highest qualification first"
        timestamp created_at
    }

    CITIZEN_FAMILY_MEMBER {
        uuid family_member_id PK
        uuid citizen_id FK
        string relationship "FATHER | MOTHER | SPOUSE | GUARDIAN | SIBLING"
        string full_name "Family member full name"
        string occupation "Occupation of the family member"
        decimal annual_income "Annual income — used for income certificates"
        string phone "Contact number if available"
        boolean is_alive "Living status"
        timestamp created_at
    }

    CITIZEN_WORK_EXPERIENCE {
        uuid experience_id PK
        uuid citizen_id FK
        string employer_name "Organization or employer name"
        string post_held "Job title or post held"
        string nature_of_work "Description of work performed"
        string experience_type "GOVERNMENT | PRIVATE | SELF_EMPLOYED"
        string job_type "FULL_TIME | PART_TIME | CONTRACT"
        decimal pay_on_leaving "Last drawn salary"
        date from_date "Employment start date"
        date to_date "Employment end date — null if current"
        string experience_doc_url "S3 path to experience letter"
        bytes32 experience_doc_hash "SHA-256 of experience document"
        timestamp created_at
    }

    CITIZEN_LANGUAGE {
        uuid language_id PK
        uuid citizen_id FK
        string language_name "e.g. Manipuri, English, Hindi, Bengali"
        boolean can_read "Reading proficiency"
        boolean can_write "Writing proficiency"
        boolean can_speak "Speaking proficiency"
        timestamp created_at
    }

    CITIZEN_PHYSICAL_STANDARD {
        uuid physical_id PK
        uuid citizen_id FK
        decimal height_cm "Height in centimeters"
        decimal weight_kg "Weight in kilograms"
        decimal chest_normal_cm "Chest measurement normal"
        decimal chest_expanded_cm "Chest measurement expanded"
        boolean wears_glasses "Do they wear spectacles"
        string disability_status "NONE | PARTIAL | FULL"
        string disability_type "If applicable — vision, hearing, locomotor, etc"
        timestamp recorded_at "When these metrics were last recorded"
    }

    CITIZEN ||--o| CITIZEN_PHYSICAL_STANDARD : "has"

    %% ========================================
    %% APPLICATION DOMAIN
    %% ========================================

    APPLICATION ||--|{ APPLICATION_DOCUMENT : "contains"
    APPLICATION ||--|{ APPLICATION_STATUS_LOG : "tracks"
    APPLICATION ||--o| APPLICATION_FEE : "charges"
    APPLICATION ||--o{ APPLICATION_REMARK : "has"
    APPLICATION ||--o{ APPLICATION_ASSIGNMENT : "assigned via"
    APPLICATION }o--|| SERVICE_CATALOG : "is for"
    APPLICATION }o--|| OFFICE : "processed at"
    APPLICATION ||--o{ BLOCKCHAIN_LEDGER_ENTRY : "anchored by"
    APPLICATION ||--o| ISSUED_CERTIFICATE : "produces"

    SERVICE_CATALOG {
        uuid service_id PK
        string service_code UK "e.g. OBC_CERT, SC_CERT, INCOME_CERT, PRC, DOMICILE, EMP_NEW, EMP_RENEW"
        string service_name "Human-readable name"
        string department "REVENUE | EMPLOYMENT_EXCHANGE | SOCIAL_WELFARE"
        string description "What this service provides"
        jsonb required_fields_schema "JSON schema defining mandatory form fields"
        jsonb required_documents_schema "JSON schema defining mandatory uploads"
        int max_file_size_kb "Max upload size per file — 200 for Revenue, 100 for Employment"
        decimal fee_amount "Application fee if applicable"
        int expected_processing_days "SLA — expected days to process"
        boolean is_active "Whether this service is currently available"
        timestamp created_at
        timestamp updated_at
    }

    APPLICATION {
        string application_id PK "Format: MN-REV-YYYY-XXXXX or MN-EMP-YYYY-XXXXX"
        uuid citizen_id FK "Who submitted this application"
        uuid service_id FK "Which service they applied for"
        uuid processing_office_id FK "Which office handles this"
        string current_status "DRAFT | SUBMITTED | UNDER_REVIEW | FIELD_VERIFICATION | FIELD_VERIFIED | FIELD_REJECTED | APPROVED | CERTIFICATE_ISSUED | REJECTED | RETURNED"
        jsonb form_data "Flexible JSONB for service-specific form inputs"
        string purpose "Stated purpose for requesting the certificate"
        boolean declaration_accepted "Citizen accepted statutory declaration"
        string rejection_reason "If rejected — reason text"
        string return_reason "If returned for correction — what to fix"
        int priority_level "0=Normal, 1=Urgent, 2=VIP"
        timestamp submitted_at "When the citizen hit submit"
        timestamp last_status_change_at "When status last changed"
        timestamp expected_completion_date "SLA deadline"
        timestamp created_at
        timestamp updated_at
    }

    APPLICATION_DOCUMENT {
        uuid document_id PK
        string application_id FK "Which application this belongs to"
        string document_type "PassportPhoto | Jamabandi | VoterID | CasteCert | etc"
        string document_label "Human-readable label for display"
        string original_filename "Original file name as uploaded"
        string storage_url "S3 or MinIO object storage path"
        bytes32 file_hash UK "SHA-256 fingerprint — anti-tampering check"
        int file_size_bytes "File size for validation"
        string mime_type "image/jpeg | application/pdf | etc"
        boolean is_verified "Has an official verified this document"
        uuid verified_by FK "Official who verified — nullable"
        timestamp uploaded_at
        timestamp verified_at
    }

    APPLICATION_STATUS_LOG {
        uuid log_id PK
        string application_id FK "Which application this tracks"
        string from_status "Previous status — null for initial submission"
        string to_status "New status after transition"
        uuid changed_by FK "citizen_id or official_id who triggered the change"
        string changed_by_role "CITIZEN | LAMBU | MANDAL | SDO | SDC | SYSTEM"
        string remarks "Reason or note for the status change"
        jsonb metadata "Any extra context — IP address, device, etc"
        timestamp changed_at "Exact time of status transition"
    }

    APPLICATION_FEE {
        uuid fee_id PK
        string application_id FK
        decimal amount "Fee amount charged"
        string payment_method "UPI | NET_BANKING | CASH | CHALLAN | FEE_WAIVED"
        string transaction_reference "Payment gateway transaction ID"
        string payment_status "PENDING | COMPLETED | FAILED | REFUNDED"
        timestamp paid_at
        timestamp created_at
    }

    APPLICATION_REMARK {
        uuid remark_id PK
        string application_id FK
        uuid official_id FK "Which official wrote this"
        string remark_type "OBSERVATION | QUERY | OBJECTION | INSTRUCTION | INTERNAL_NOTE"
        text remark_text "The actual remark content"
        boolean is_internal "If true — visible only to officials, not citizen"
        boolean requires_citizen_response "Does the citizen need to reply"
        string citizen_response "Citizen reply if applicable"
        timestamp responded_at "When citizen responded"
        timestamp created_at
    }

    %% ========================================
    %% ADMIN DOMAIN — Offices, Officials, Roles, Assignments
    %% ========================================

    OFFICE ||--o{ GOVERNMENT_OFFICIAL : "employs"
    OFFICE ||--o{ APPLICATION : "processes"
    GOVERNMENT_OFFICIAL ||--o{ APPLICATION_ASSIGNMENT : "handles"
    GOVERNMENT_OFFICIAL ||--o{ APPLICATION_REMARK : "writes"
    GOVERNMENT_OFFICIAL ||--o{ APPLICATION_STATUS_LOG : "triggers"
    GOVERNMENT_OFFICIAL ||--o{ VERIFICATION_REPORT : "conducts"
    GOVERNMENT_OFFICIAL ||--o{ BLOCKCHAIN_LEDGER_ENTRY : "signs"
    GOVERNMENT_OFFICIAL ||--o{ NOTIFICATION : "receives"
    ROLE ||--o{ GOVERNMENT_OFFICIAL : "assigned to"

    OFFICE {
        uuid office_id PK
        string office_code UK "e.g. SDO-IW, SDO-LP, DC-IW"
        string office_name "e.g. SDO Office Lamphel, DC Office Imphal West"
        string office_type "DC_OFFICE | SDO_OFFICE | CIRCLE_OFFICE | EMPLOYMENT_EXCHANGE"
        string district "District this office serves"
        string sub_division "Sub-division if applicable"
        string full_address "Physical address of the office"
        string phone "Office contact number"
        string email "Office email"
        uuid parent_office_id FK "Hierarchy — Circle reports to SDO reports to DC"
        boolean is_active
        timestamp created_at
    }

    ROLE {
        uuid role_id PK
        string role_code UK "REVENUE_LAMBU | MANDAL | SDO | SDC | DC | ADMIN | EMP_EXCHANGE_OFFICER"
        string role_name "Human-readable name"
        string department "REVENUE | EMPLOYMENT | ADMIN"
        int authority_level "Numeric hierarchy — higher = more authority"
        jsonb permissions "List of allowed actions"
        timestamp created_at
    }

    GOVERNMENT_OFFICIAL {
        uuid official_id PK
        uuid office_id FK "Which office they belong to"
        uuid role_id FK "Their role and authority level"
        string full_name "Official full name"
        string employee_id UK "Government employee ID"
        string designation "Lambu | SDO | SDC | DC | Mandal"
        string phone "Contact number"
        string email "Official email"
        address blockchain_wallet_address UK "Public key from physical DSC token"
        string dsc_serial_number "Digital Signature Certificate serial"
        boolean is_active "Currently active and can process applications"
        string password_hash "Argon2/bcrypt hashed password"
        timestamp last_login_at
        timestamp created_at
        timestamp updated_at
    }

    APPLICATION_ASSIGNMENT {
        uuid assignment_id PK
        string application_id FK "Which application"
        uuid assigned_to FK "Which official is responsible"
        uuid assigned_by FK "Who made the assignment — system or senior official"
        string assignment_type "AUTO | MANUAL | ESCALATION | REASSIGNMENT"
        string assignment_status "ACTIVE | COMPLETED | REASSIGNED | TIMED_OUT"
        timestamp assigned_at
        timestamp completed_at
        timestamp deadline "SLA deadline for this assignment"
    }

    WORKFLOW_STAGE {
        uuid stage_id PK
        uuid service_id FK "Which service this workflow belongs to"
        int stage_order "Sequence number — 1, 2, 3..."
        string stage_code "SUBMITTED | LAMBU_REVIEW | MANDAL_REVIEW | SDO_APPROVAL | CERTIFICATE_GENERATION"
        string stage_name "Human readable stage name"
        string required_role "Which role handles this stage"
        int sla_hours "Maximum hours allowed at this stage"
        boolean is_terminal "Is this a final stage — approved or rejected"
        timestamp created_at
    }

    SERVICE_CATALOG ||--|{ WORKFLOW_STAGE : "defines"

    %% ========================================
    %% VERIFICATION & CERTIFICATE DOMAIN
    %% ========================================

    APPLICATION ||--o| VERIFICATION_REPORT : "verified by"

    VERIFICATION_REPORT {
        uuid report_id PK
        string application_id FK "Which application was verified"
        uuid verifier_id FK "Lambu or field officer who conducted verification"
        string verification_type "FIELD_VISIT | DOCUMENT_CHECK | IDENTITY_CHECK"
        string verdict "VALID | INVALID | INCONCLUSIVE"
        text findings "Detailed verification findings and observations"
        text recommendation "Verifier recommendation to SDO"
        date verification_date "Date the field visit occurred"
        string visit_location "Where the verification took place"
        jsonb checklist_responses "Structured checklist answers as JSON"
        bytes32 documents_hash_at_verification "SHA-256 of docs at time of verification — tampering check"
        boolean hash_match "Did the hash match the original submission"
        string photo_evidence_url "S3 path to photos taken during field visit"
        timestamp created_at
    }

    ISSUED_CERTIFICATE {
        uuid certificate_id PK
        string application_id FK "Which application this certificate is for"
        uuid citizen_id FK "Which citizen this was issued to"
        uuid issued_by FK "SDO or authority who issued"
        string certificate_number UK "Official certificate number"
        string certificate_type "OBC | SC | ST | PRC | DOMICILE | INCOME"
        bytes32 certificate_hash "SHA-256 of the full certificate content"
        bytes32 qr_code_hash "Hash encoded in the verification QR code"
        string qr_code_image_url "S3 path to generated QR code image"
        string certificate_pdf_url "S3 path to generated certificate PDF"
        date valid_from "Certificate validity start"
        date valid_until "Certificate expiry — null if permanent"
        boolean is_revoked "Has this certificate been revoked"
        string revocation_reason "If revoked — why"
        timestamp issued_at
        timestamp revoked_at
    }

    %% ========================================
    %% EMPLOYMENT EXCHANGE SPECIFIC
    %% ========================================

    CITIZEN ||--o| EMPLOYMENT_REGISTRATION : "registers at"

    EMPLOYMENT_REGISTRATION {
        string registration_id PK "Format: MN-EMP-YYYY-XXXXX"
        uuid citizen_id FK
        uuid processing_office_id FK "Employment Exchange office"
        string current_state "PENDING_VERIFICATION | ACTIVE | RENEWED_SUBMITTED | RENEWED_ACTIVE | EXPIRED | MUTATION_PENDING_REVIEW | SUSPENDED"
        date seniority_date "Original registration date — never changes on renewal"
        date lifespan_expiry_date "Current expiry — extended on renewal"
        date last_renewal_date "When was the card last renewed"
        int renewal_count "How many times renewed"
        jsonb physical_standards_snapshot "Height, weight, chest, glasses etc at registration time"
        timestamp created_at
        timestamp updated_at
    }

    %% ========================================
    %% BLOCKCHAIN & AUDIT DOMAIN
    %% ========================================

    BLOCKCHAIN_LEDGER_ENTRY {
        bytes32 block_hash PK "SHA-256 hash of this block — unique"
        string application_id FK "Links to the application in the DB"
        bytes32 previous_block_hash "Hash of previous block — cryptographic chain link — null for genesis"
        bytes32 aggregate_data_hash "SHA-256 checkpoint of application state + documents"
        string status_at_block "SUBMITTED | UNDER_REVIEW | FIELD_VERIFIED | FIELD_REJECTED | CERTIFICATE_ISSUED | REJECTED"
        address signee_address FK "Public key of the official or system that signed"
        string signee_role "SYSTEM | LAMBU | MANDAL | SDO"
        text action_description "Human readable description of what happened"
        uint256 block_timestamp "Immutable network timestamp"
        int block_sequence "Sequential block number for this application"
    }

    AUDIT_LOG {
        uuid log_id PK
        string entity_type "CITIZEN | APPLICATION | OFFICIAL | DOCUMENT | CERTIFICATE"
        string entity_id "ID of the affected entity"
        string action "CREATE | READ | UPDATE | DELETE | LOGIN | LOGOUT | DOWNLOAD | VERIFY"
        uuid actor_id "Who performed the action"
        string actor_type "CITIZEN | OFFICIAL | SYSTEM"
        string actor_ip_address "IP address of the actor"
        string user_agent "Browser or client identifier"
        jsonb old_values "Previous state — for UPDATE actions"
        jsonb new_values "New state — for UPDATE and CREATE actions"
        timestamp performed_at
    }

    %% ========================================
    %% NOTIFICATIONS
    %% ========================================

    NOTIFICATION {
        uuid notification_id PK
        uuid recipient_id FK "citizen_id or official_id"
        string recipient_type "CITIZEN | OFFICIAL"
        string application_id "Related application if applicable"
        string channel "SMS | EMAIL | IN_APP | PUSH"
        string title "Notification title"
        text message_body "Full notification text"
        string notification_type "STATUS_UPDATE | DOCUMENT_REQUEST | DEADLINE_ALERT | ASSIGNMENT | SYSTEM"
        boolean is_read "Has the recipient seen this"
        boolean is_sent "Has it been dispatched"
        timestamp sent_at
        timestamp read_at
        timestamp created_at
    }
```

---

## 2. Domain Breakdown

### Domain A: Citizen (7 tables)

| Table | Purpose | Driven by |
|-------|---------|-----------|
| `CITIZEN` | Core identity — Aadhaar-locked immutable fields + mutable profile data | algo_one |
| `CITIZEN_ADDRESS` | Multiple addresses (permanent, present, correspondence) — needed for every application | algo_two, algo_three |
| `CITIZEN_EDUCATION` | Educational qualifications array — each row is one qualification | algo_three (QualificationsArray) |
| `CITIZEN_FAMILY_MEMBER` | Father, mother, spouse — used for relationship details, income declarations | algo_two (RelationshipDetails, ParentsNames) |
| `CITIZEN_WORK_EXPERIENCE` | Employment history — employer, pay, dates, nature of work | algo_three (ExperienceBlock) |
| `CITIZEN_LANGUAGE` | Language proficiency table (read/write/speak) | algo_three (LanguagesArray) |
| `CITIZEN_PHYSICAL_STANDARD` | Height, weight, chest, glasses, blood group — 1:1 per citizen | algo_three (PhysicalStandardsMap) |

### Domain B: Application (6 tables)

| Table | Purpose | Driven by |
|-------|---------|-----------|
| `SERVICE_CATALOG` | Master list of available services + their field/doc schemas + file size limits | algo_two CASE block, algo_three |
| `APPLICATION` | Core application record with status, form data, office assignment | algo_two, algo_three |
| `APPLICATION_DOCUMENT` | Every uploaded file — with SHA-256 hash for tampering detection | file_locking, verification_transaction |
| `APPLICATION_STATUS_LOG` | **Full history** of every status transition — who, when, why | Missing from your original ER |
| `APPLICATION_FEE` | Payment tracking — UPI, net banking, challan | Missing from original |
| `APPLICATION_REMARK` | Official observations, queries, objections — with citizen response flow | Missing from original |

### Domain C: Admin (5 tables)

| Table | Purpose | Driven by |
|-------|---------|-----------|
| `OFFICE` | Office hierarchy — DC → SDO → Circle, with district/sub-division mapping | algo_two (SelectedOfficeDropdown) |
| `ROLE` | Role definitions with authority levels and permissions | authorization (SDO role check) |
| `GOVERNMENT_OFFICIAL` | Officials with DSC wallet addresses, office assignments, credentials | authorization, verification_transaction |
| `APPLICATION_ASSIGNMENT` | Who's currently responsible for which application — with SLA deadlines | Missing from original |
| `WORKFLOW_STAGE` | Per-service workflow pipeline definition — which role handles which stage | Missing from original |

### Domain D: Verification & Certificates (3 tables)

| Table | Purpose | Driven by |
|-------|---------|-----------|
| `VERIFICATION_REPORT` | Lambu field verification details — findings, hash comparison, photo evidence | verification_transaction |
| `ISSUED_CERTIFICATE` | Final issued certificates with QR hash, PDF, validity dates, revocation | authorization |
| `EMPLOYMENT_REGISTRATION` | Employment Exchange card — seniority date, expiry, renewal tracking | algo_three (renewal, mutation) |

### Domain E: Blockchain & System (3 tables)

| Table | Purpose | Driven by |
|-------|---------|-----------|
| `BLOCKCHAIN_LEDGER_ENTRY` | Immutable hash-chained ledger — one block per state transition | file_locking, verification_transaction, authorization |
| `AUDIT_LOG` | System-wide audit trail — every read, write, login, download | public_audit + security requirement |
| `NOTIFICATION` | Multi-channel notifications to citizens and officials | Missing from original |

---

## 3. Key Design Decisions

### Why separate `APPLICATION_STATUS_LOG` from `APPLICATION.current_status`?
The `APPLICATION` table holds the **current** status for fast queries ("show me all SUBMITTED applications"). The `APPLICATION_STATUS_LOG` table holds the **complete history** — every transition, who triggered it, when, and why. This is critical for:
- Citizen tracking ("where is my application?")
- SLA monitoring ("how long has it been stuck at LAMBU_REVIEW?")
- Accountability ("who moved this to APPROVED and when?")

### Why `SERVICE_CATALOG` with JSON schemas?
Your algo_two has a massive CASE block defining required fields and documents per service type. Instead of hardcoding these, we store them as JSON schemas in `SERVICE_CATALOG`. This means:
- Adding a new service type = inserting a row, not changing code
- Validation rules are data-driven and auditable
- Different offices can enable/disable services independently

### Why `APPLICATION_ASSIGNMENT` is separate?
In real government workflows, applications get **reassigned** — a Lambu goes on leave, an SDO gets transferred, workload gets rebalanced. Tracking assignments separately gives you:
- Assignment history (who had it, for how long)
- SLA tracking per assignment
- Auto-escalation when deadlines are missed

### Why `EMPLOYMENT_REGISTRATION` is its own table?
The Employment Exchange card has a **different lifecycle** from a one-time certificate application. It has seniority dates, renewals (3-year cycles), qualification mutations — it's a living record, not a submit-and-done flow.