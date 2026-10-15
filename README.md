# PawHaven — DBMS Course Project & Pet Adoption System

A comprehensive, script-based terminal Database Management System project built with **Python 3.12+**, **Astral `uv`**, **Rich** for modern terminal UI, and **PostgreSQL** for relational database storage and advanced SQL features.

---

## 🎓 DBMS Academic & Technical Highlights

This project is structured specifically to satisfy core academic requirements for a Database Management Systems (DBMS) curriculum:

### 1. Relational Schema & 3NF Normalization
The database design consists of 7 normalized relations, strictly adhering to **Third Normal Form (3NF)** with explicit Candidate Keys and Functional Dependencies:
- **`shelters`**: Shelter locations, capacity limits, and contact information.
- **`users`**: System actors with role-based access control (`admin`, `adopter`, `staff`).
- **`pets`**: Rescued animals with physical characteristics, medical flags, and status.
- **`medical_records`**: 1-to-many relationship with pets; tracks visits, diagnoses, treatments, and costs.
- **`adoption_applications`**: Junction relation managing adoption requests and reviewer notes.
- **`adoption_payments`**: Financial ledger tracking transactions linked to approved adoptions.
- **`audit_logs`**: Change Data Capture (CDC) table storing before/after JSONB payloads.

### 2. Constraints & Integrity Enforcement
- **Primary Keys**: Surrogate integer keys (`SERIAL PRIMARY KEY`).
- **Foreign Keys**: Enforced referential integrity with cascading rules (`ON DELETE CASCADE`, `ON DELETE SET NULL`).
- **Check Constraints**: `CHECK (capacity > 0)`, `CHECK (fee >= 0)`, `CHECK (age_years >= 0)`, `CHECK (status IN (...))`.
- **Unique Constraints**: Unique usernames, emails, and transaction references.

### 3. PostgreSQL Views & Abstraction
- **`v_pet_details`**: Aggregates pets, shelters, medical visit counts, and total medical expenses using `LEFT JOIN` and `GROUP BY`.
- **`v_adoption_ledger`**: Financial report linking applications, pets, adopters, and payment transaction references.

### 4. PL/pgSQL Stored Procedures & Triggers
- **`trg_pets_audit`**: Automatically captures row modifications on `pets` (both `UPDATE` and `DELETE`), persisting previous and updated states as structured `JSONB` into `audit_logs` with timestamps and current database user.

### 5. Advanced Relational Queries
- **Multi-Table JOINs**: Combining `shelters`, `pets`, and `medical_records`.
- **Aggregation with `HAVING`**: Grouping pets by species and filtering groups by fee averages.
- **Correlated Subqueries**: Finding pets whose adoption fee exceeds the average for their specific species.
- **Window Functions**: Analytical ranking using `RANK() OVER (PARTITION BY species ORDER BY fee DESC)`.
- **Set Operations**: `UNION` and `EXCEPT` categorizing user activity.

### 6. ACID Transaction Demonstration
Interactive laboratory module testing **Atomicity**, **Consistency**, **Isolation**, and **Durability**:
- Row-level locking with `SELECT ... FOR UPDATE`.
- Multi-statement workflow: insert application $\rightarrow$ record payment $\rightarrow$ update pet status $\rightarrow$ `COMMIT`.
- Simulated integrity failure triggering automatic `ROLLBACK` to preserve database consistency.

### 7. Performance & Query Optimization
- **B-Tree Indexes**: Created on frequently filtered columns (`status`, `species`, `user_id`, composite `(species, fee)`).
- **Execution Plan Visualizer**: Runs `EXPLAIN (ANALYZE, BUFFERS, VERBOSE)` directly in the terminal to inspect sequential scans vs index scans, startup/total cost, and buffer hits.
- **System Catalog Diagnostics**: Inspects `pg_stat_user_tables` to monitor live/dead tuples, relation disk sizes (`pg_total_relation_size`), and index scan ratios.

---

## Project Structure

```
pet-adoption-center/
├── .env                       # Active PostgreSQL credentials
├── .env.example               # Environment configuration template
├── docker-compose.yml         # Containerized PostgreSQL service
├── pyproject.toml             # Astral uv dependency specification
├── README.md                  # Comprehensive DBMS documentation
├── scripts/
│   └── run_local_postgres.sh  # Local user PostgreSQL cluster manager
├── tests/
│   └── test_flow.py           # Automated integration test suite
└── src/
    └── pet_adoption_center/
        ├── __init__.py
        ├── __main__.py        # python -m pet_adoption_center launcher
        ├── config.py          # Environment settings loader
        ├── main.py            # CLI entrypoint & DB connectivity checks
        ├── db/
        │   ├── connection.py  # psycopg connection pool, DDL migrations & seeding
        │   └── schema.py      # Relational DDL, views, triggers & indexes
        ├── models/
        │   ├── user.py        # User entity model
        │   ├── pet.py         # Pet entity model & styling badges
        │   └── adoption.py    # Adoption application model
        ├── auth/
        │   ├── hasher.py      # PBKDF2 HMAC-SHA256 password security
        │   └── session.py     # Session manager & authentication state
        ├── services/
        │   ├── pet_service.py       # Pet catalog queries & mutations
        │   ├── adoption_service.py  # Application processing & review
        │   ├── user_service.py      # User account management
        │   └── dbms_service.py      # Relational analysis, queries & ACID lab
        └── ui/
            ├── console.py     # Rich console singleton & helpers
            ├── router.py      # Dynamic role-based menu router
            ├── themes.py      # Color palette & ASCII art banner
            └── views/
                ├── auth_view.py      # Login, registration & user profile
                ├── pet_view.py       # Catalog, filters, and admin forms
                ├── adoption_view.py  # Multi-step application submission
                ├── admin_view.py     # Analytics dashboard & review queue
                └── dbms_view.py      # Academic DBMS lab & SQL console
```

---

## Getting Started

### 1. Database Setup

Make sure PostgreSQL is running:

**Option A: Local User Cluster (Bundled script, no sudo or Docker needed)**
```bash
./scripts/run_local_postgres.sh start
```

**Option B: Docker Compose**
```bash
docker compose up -d
```

**Option C: Existing PostgreSQL Service**
Update connection settings in `.env`:
```ini
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DB=pet_adoption
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

### 2. Initialize Schema, Views & Triggers

Run with `uv`:
```bash
uv run pet-adoption-center --init-db
```

### 3. Launch the Application

```bash
uv run pet-adoption-center
```
Select **`[D] DBMS Academic Suite`** from the main menu to access the relational schema analysis, query optimizer, and ACID transaction demonstration.

---

## Default Accounts

| Username | Password | Role | Description |
| :--- | :--- | :--- | :--- |
| `admin` | `admin123` | Admin | Access to shelter operations, review queue, and analytics |
| `adopter` | `user123` | Adopter | Can submit adoption applications and track application status |

*(You can also register a new account from the menu.)*

---

## Running the Automated Test Suite

Execute the integration test suite (covering authentication, CRUD, views, triggers, and ACID rollback):
```bash
uv run python tests/test_flow.py
```
