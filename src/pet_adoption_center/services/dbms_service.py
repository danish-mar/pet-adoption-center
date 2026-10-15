"""DBMS Service: Relational schema analysis, complex query demonstrations, EXPLAIN ANALYZE, ACID tests, and diagnostics."""

from __future__ import annotations

import time
from typing import Any, List, Dict, Tuple, Optional
import psycopg
from psycopg.rows import dict_row

from ..db.connection import get_connection


class DBMSService:
    """Academic and practical DBMS operations for schema exploration and query analysis."""

    @staticmethod
    def get_relational_schema_overview() -> str:
        """Returns structured 3NF relational schema equations and functional dependencies."""
        return """
[bold cyan]1. RELATIONAL SCHEMA FORMULATION (3NF Normalized)[/]

  • [bold white]SHELTERS[/] (
      [bold underline]id[/] INT PK,
      name VARCHAR(100) UNIQUE,
      address VARCHAR(200),
      city VARCHAR(60),
      state VARCHAR(30),
      capacity INT CHECK (capacity > 0),
      phone VARCHAR(30),
      created_at TIMESTAMP
    )
    [dim]FD: {id} -> {name, address, city, state, capacity, phone, created_at}[/]

  • [bold white]USERS[/] (
      [bold underline]id[/] INT PK,
      username VARCHAR(50) UNIQUE,
      password_hash VARCHAR(128),
      salt VARCHAR(64),
      role VARCHAR(20) CHECK (role IN ('admin', 'adopter', 'staff')),
      full_name VARCHAR(100),
      email VARCHAR(100) UNIQUE,
      phone VARCHAR(30),
      created_at TIMESTAMP
    )
    [dim]FD: {id} -> {username, password_hash, salt, role, full_name, email, phone}[/]
    [dim]FD: {username} -> {id, ...}  (Candidate Key)[/]
    [dim]FD: {email} -> {id, ...}     (Candidate Key)[/]

  • [bold white]PETS[/] (
      [bold underline]id[/] INT PK,
      [italic]shelter_id[/] INT FK -> SHELTERS(id) ON DELETE SET NULL,
      name VARCHAR(60),
      species VARCHAR(30),
      breed VARCHAR(60),
      age_years NUMERIC(4,1) CHECK (age_years >= 0),
      gender VARCHAR(10) CHECK (gender IN ('Male', 'Female', 'Unknown')),
      size VARCHAR(20),
      status VARCHAR(20) CHECK (status IN ('available', 'pending', 'adopted')),
      health_status VARCHAR(100),
      vaccinated BOOLEAN,
      spayed_neutered BOOLEAN,
      fee NUMERIC(8,2) CHECK (fee >= 0),
      description TEXT,
      intake_date DATE
    )
    [dim]FD: {id} -> {shelter_id, name, species, breed, age_years, gender, size, status, fee, ...}[/]

  • [bold white]MEDICAL_RECORDS[/] (
      [bold underline]id[/] INT PK,
      [italic]pet_id[/] INT FK -> PETS(id) ON DELETE CASCADE,
      visit_date DATE,
      diagnosis VARCHAR(150),
      treatment TEXT,
      vet_name VARCHAR(100),
      cost NUMERIC(8,2) CHECK (cost >= 0)
    )
    [dim]FD: {id} -> {pet_id, visit_date, diagnosis, treatment, vet_name, cost}[/]

  • [bold white]ADOPTION_APPLICATIONS[/] (
      [bold underline]id[/] INT PK,
      [italic]pet_id[/] INT FK -> PETS(id) ON DELETE CASCADE,
      [italic]user_id[/] INT FK -> USERS(id) ON DELETE CASCADE,
      status VARCHAR(20) CHECK (status IN ('pending', 'approved', 'rejected', 'withdrawn')),
      applicant_name VARCHAR(100),
      applicant_phone VARCHAR(30),
      applicant_email VARCHAR(100),
      living_space VARCHAR(50),
      has_other_pets BOOLEAN,
      experience_notes TEXT,
      reviewer_notes TEXT,
      submitted_at TIMESTAMP,
      updated_at TIMESTAMP
    )
    [dim]FD: {id} -> {pet_id, user_id, status, applicant_name, applicant_email, ...}[/]

  • [bold white]ADOPTION_PAYMENTS[/] (
      [bold underline]id[/] INT PK,
      [italic]application_id[/] INT UNIQUE FK -> ADOPTION_APPLICATIONS(id) ON DELETE CASCADE,
      amount NUMERIC(8,2) CHECK (amount >= 0),
      payment_method VARCHAR(30),
      transaction_ref VARCHAR(64) UNIQUE,
      status VARCHAR(20),
      paid_at TIMESTAMP
    )
    [dim]FD: {id} -> {application_id, amount, payment_method, transaction_ref, status, paid_at}[/]

  • [bold white]AUDIT_LOGS[/] (
      [bold underline]id[/] INT PK,
      table_name VARCHAR(50),
      action_type VARCHAR(20),
      record_id INT,
      old_data JSONB,
      new_data JSONB,
      changed_by VARCHAR(50),
      changed_at TIMESTAMP
    )

[bold cyan]2. NORMALIZATION JUSTIFICATION (3NF / BCNF)[/]
  ✔ [bold]1NF:[/] All column values are atomic (e.g. no comma-separated lists of vaccines or treatments; medical records are separated into their own entity).
  ✔ [bold]2NF:[/] All non-prime attributes are fully functionally dependent on the whole candidate key (all tables possess single-attribute surrogate primary keys).
  ✔ [bold]3NF:[/] No non-prime attribute is transitively dependent on any candidate key (e.g. Shelter location details depend on shelter_id, not on pet_id).
"""

    @staticmethod
    def get_prebuilt_queries() -> List[Dict[str, str]]:
        """Catalog of advanced academic SQL queries showcasing DBMS concepts."""
        return [
            {
                "title": "1. Multi-Table JOIN with Aggregation & Grouping",
                "concept": "INNER JOIN, LEFT JOIN, COUNT, SUM, COALESCE across 3 relations",
                "sql": """
SELECT 
    s.name AS shelter_name,
    s.city,
    COUNT(p.id) AS hosted_pets,
    COALESCE(SUM(m.cost), 0.00) AS total_medical_investment,
    ROUND(AVG(p.fee), 2) AS avg_adoption_fee
FROM shelters s
JOIN pets p ON s.id = p.shelter_id
LEFT JOIN medical_records m ON p.id = m.pet_id
GROUP BY s.id, s.name, s.city
ORDER BY total_medical_investment DESC;
                """.strip(),
            },
            {
                "title": "2. Aggregate Query with HAVING Filter",
                "concept": "GROUP BY with HAVING condition on aggregated expression",
                "sql": """
SELECT 
    species,
    COUNT(*) AS total_count,
    ROUND(AVG(fee), 2) AS avg_adoption_fee,
    MIN(fee) AS min_fee,
    MAX(fee) AS max_fee
FROM pets
GROUP BY species
HAVING AVG(fee) >= 40.00
ORDER BY avg_adoption_fee DESC;
                """.strip(),
            },
            {
                "title": "3. Correlated Subquery",
                "concept": "Nested query referencing outer query's species attribute",
                "sql": """
SELECT 
    p1.id,
    p1.name,
    p1.species,
    p1.breed,
    p1.fee,
    (SELECT ROUND(AVG(p2.fee), 2) FROM pets p2 WHERE p2.species = p1.species) AS species_avg_fee
FROM pets p1
WHERE p1.fee > (
    SELECT AVG(p2.fee) 
    FROM pets p2 
    WHERE p2.species = p1.species
)
ORDER BY p1.species, p1.fee DESC;
                """.strip(),
            },
            {
                "title": "4. Window Functions (Analytical Ranking)",
                "concept": "RANK() OVER (PARTITION BY species ORDER BY fee DESC) and DENSE_RANK()",
                "sql": """
SELECT 
    id,
    name,
    species,
    breed,
    fee,
    RANK() OVER (PARTITION BY species ORDER BY fee DESC) AS fee_rank_in_species,
    ROUND(AVG(fee) OVER (PARTITION BY species), 2) AS species_avg_fee
FROM pets
ORDER BY species, fee_rank_in_species;
                """.strip(),
            },
            {
                "title": "5. Set Operation (INTERSECT & EXCEPT Analysis)",
                "concept": "UNION / EXCEPT set operations to find users without submitted applications",
                "sql": """
SELECT id, username, email, 'Applied for Adoption' AS category
FROM users
WHERE id IN (SELECT user_id FROM adoption_applications)
UNION
SELECT id, username, email, 'Registered without Applications' AS category
FROM users
WHERE id NOT IN (SELECT user_id FROM adoption_applications);
                """.strip(),
            },
            {
                "title": "6. Querying PostgreSQL View (v_pet_details)",
                "concept": "Abstracted relational view joining pets, shelters & medical visit totals",
                "sql": """
SELECT 
    pet_id,
    name,
    species,
    breed,
    status,
    fee,
    shelter_name,
    medical_visit_count,
    total_medical_expenses
FROM v_pet_details
ORDER BY medical_visit_count DESC, pet_id ASC;
                """.strip(),
            },
        ]

    @staticmethod
    def execute_arbitrary_query(sql: str) -> Tuple[bool, List[str], List[List[Any]], float, str]:
        """Safely executes a read-only query and returns (ok, headers, rows, elapsed_ms, error_msg)."""
        start = time.perf_counter()
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    if cur.description:
                        headers = [col.name for col in cur.description]
                        rows = [list(r.values()) if isinstance(r, dict) else list(r) for r in cur.fetchall()]
                    else:
                        headers = ["Status"]
                        rows = [["Command executed successfully."]]
                    elapsed_ms = (time.perf_counter() - start) * 1000.0
                    return True, headers, rows, elapsed_ms, ""
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            return False, [], [], elapsed_ms, str(exc)

    @staticmethod
    def explain_query_plan(sql: str) -> Tuple[bool, List[str], str]:
        """Runs EXPLAIN (ANALYZE, BUFFERS, VERBOSE) on the query to show execution cost and index usage."""
        explain_sql = f"EXPLAIN (ANALYZE, BUFFERS, VERBOSE, FORMAT TEXT) {sql}"
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(explain_sql)
                    lines = [
                        r.get("QUERY PLAN", list(r.values())[0]) if isinstance(r, dict) else r[0]
                        for r in cur.fetchall()
                    ]
                    return True, lines, ""
        except Exception as exc:
            return False, [], str(exc)

    @staticmethod
    def demonstrate_acid_transaction(simulate_failure: bool = False) -> Dict[str, Any]:
        """Simulates atomic adoption transaction demonstrating COMMIT vs ROLLBACK."""
        steps: list[str] = []
        status = "unknown"

        with get_connection() as conn:
            # We control manual transaction
            conn.autocommit = False
            try:
                steps.append("[cyan]1. Executed: BEGIN TRANSACTION;[/]")
                with conn.cursor() as cur:
                    cur.execute("SELECT id, name, fee FROM pets WHERE status = 'available' LIMIT 1 FOR UPDATE;")
                    pet = cur.fetchone()
                    if not pet:
                        cur.execute("SELECT id, name, fee FROM pets ORDER BY id ASC LIMIT 1 FOR UPDATE;")
                        pet = cur.fetchone()
                    if not pet:
                        conn.rollback()
                        return {"success": False, "status": "ABORTED", "steps": steps, "reason": "No pets found in database."}

                    pet_id = pet["id"]
                    pet_name = pet["name"]
                    fee = pet["fee"]
                    steps.append(f"[cyan]2. Locked target row: Pet #{pet_id} ('{pet_name}') with FOR UPDATE[/]")

                    # Step 2: Insert adoption application
                    cur.execute(
                        """
                        INSERT INTO adoption_applications (
                            pet_id, user_id, status, applicant_name, applicant_phone,
                            applicant_email, living_space, has_other_pets, experience_notes
                        ) VALUES (%s, 1, 'approved', 'ACID Test Applicant', '555-0000', 'acid@pawhaven.org', 'House', false, 'ACID Demo')
                        RETURNING id;
                        """,
                        (pet_id,),
                    )
                    app_id = cur.fetchone()["id"]
                    steps.append(f"[cyan]3. Inserted: Application #{app_id} (Status: APPROVED)[/]")

                    # Step 3: Trigger intentional failure if requested
                    if simulate_failure:
                        steps.append("[bold red]4. SIMULATING FAILURE:[/] Inserting payment with negative amount violating CHECK (amount >= 0)...")
                        # This causes a DB check violation
                        cur.execute(
                            """
                            INSERT INTO adoption_payments (application_id, amount, payment_method, transaction_ref, status)
                            VALUES (%s, -100.00, 'Card', 'TX_FAIL_9999', 'failed');
                            """,
                            (app_id,),
                        )
                    else:
                        import secrets
                        tx_ref = f"TX_ACID_{secrets.token_hex(4).upper()}"
                        cur.execute(
                            """
                            INSERT INTO adoption_payments (application_id, amount, payment_method, transaction_ref, status)
                            VALUES (%s, %s, 'Card', %s, 'completed');
                            """,
                            (app_id, fee, tx_ref),
                        )
                        steps.append(f"[cyan]4. Inserted: Payment receipt {tx_ref} for ${fee:.2f}[/]")

                        # Step 4: Update Pet status to adopted
                        cur.execute("UPDATE pets SET status = 'adopted' WHERE id = %s;", (pet_id,))
                        steps.append(f"[cyan]5. Updated: Pet #{pet_id} status -> 'ADOPTED'[/]")

                conn.commit()
                status = "COMMITTED"
                steps.append("[bold green]6. Executed: COMMIT;[/] All mutations atomically persisted to disk (Durability).")
                return {"success": True, "status": status, "steps": steps, "pet_name": pet_name}

            except Exception as exc:
                conn.rollback()
                status = "ROLLED BACK"
                steps.append(f"[bold red]5. EXCEPTION CAUGHT:[/] {exc}")
                steps.append("[bold yellow]6. Executed: ROLLBACK;[/] Database returned to clean pre-transaction state (Atomicity preserved).")
                return {"success": False, "status": status, "steps": steps, "reason": str(exc)}

    @staticmethod
    def get_database_catalog_stats() -> List[Dict[str, Any]]:
        """Queries pg_stat_user_tables and relation sizes for physical database diagnostics."""
        query = """
        SELECT 
            c.relname AS table_name,
            c.reltuples::bigint AS estimated_row_count,
            pg_size_pretty(pg_total_relation_size(c.oid)) AS total_size_on_disk,
            COALESCE(s.seq_scan, 0) AS sequential_scans,
            COALESCE(s.idx_scan, 0) AS index_scans,
            COALESCE(s.n_dead_tup, 0) AS dead_tuples
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        LEFT JOIN pg_stat_user_tables s ON s.relid = c.oid
        WHERE n.nspname = 'public' AND c.relkind = 'r'
        ORDER BY pg_total_relation_size(c.oid) DESC;
        """
        stats: list[dict] = []
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                for r in cur.fetchall():
                    stats.append(r)
        return stats

    @staticmethod
    def get_audit_trail() -> List[Dict[str, Any]]:
        """Queries audit_logs populated by database triggers."""
        query = """
        SELECT id, table_name, action_type, record_id, changed_by, changed_at, old_data, new_data
        FROM audit_logs
        ORDER BY changed_at DESC
        LIMIT 25;
        """
        logs: list[dict] = []
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                for r in cur.fetchall():
                    logs.append(r)
        return logs


dbms_service = DBMSService()
