"""PostgreSQL database connection manager, initialization, and seeding."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator, Any
import psycopg
from psycopg.rows import dict_row

from ..config import db_config
from .schema import SCHEMA_SQL

logger = logging.getLogger(__name__)


def test_connection() -> tuple[bool, str]:
    """Tests if PostgreSQL is reachable using configured credentials."""
    try:
        kwargs = db_config.get_connection_kwargs()
        with psycopg.connect(**kwargs) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                v = cur.fetchone()
                return True, f"Connected to PostgreSQL ({v[0] if v else 'OK'})"
    except Exception as exc:
        # Check if the error is just missing database (which we can create automatically)
        err_msg = str(exc)
        if f'database "{db_config.database}" does not exist' in err_msg:
            # We can connect to maintenance DB and create it
            return True, f"PostgreSQL server reachable. Target database '{db_config.database}' will be created."
        return False, err_msg


def ensure_database_exists() -> None:
    """Connects to default PostgreSQL maintenance database to ensure target database exists."""
    if db_config.database_url:
        return

    kwargs = db_config.get_maintenance_kwargs()
    try:
        with psycopg.connect(**kwargs, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s;",
                    (db_config.database,),
                )
                exists = cur.fetchone()
                if not exists:
                    # Sanitize DB name (alphanumeric and underscore only)
                    safe_db_name = "".join(c for c in db_config.database if c.isalnum() or c == "_")
                    cur.execute(f'CREATE DATABASE "{safe_db_name}";')
    except Exception as exc:
        logger.warning("Could not auto-create database from maintenance connection: %s", exc)


@contextmanager
def get_connection() -> Generator[psycopg.Connection, None, None]:
    """Yields an active PostgreSQL connection with dict_row factory."""
    kwargs = db_config.get_connection_kwargs()
    with psycopg.connect(**kwargs, row_factory=dict_row) as conn:
        yield conn


def init_db() -> None:
    """Creates tables and indexes if they do not already exist."""
    ensure_database_exists()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
        conn.commit()


def seed_default_data() -> None:
    """Populates default admin user, demo adopter, and initial pets if database is empty."""
    from ..auth.hasher import hash_password

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Check if any users exist
            cur.execute("SELECT COUNT(*) AS count FROM users;")
            row = cur.fetchone()
            if row and row["count"] == 0:
                # Create admin
                admin_hash, admin_salt = hash_password("admin123")
                cur.execute(
                    """
                    INSERT INTO users (username, password_hash, salt, role, full_name, email, phone)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                    """,
                    ("admin", admin_hash, admin_salt, "admin", "Shelter Director", "director@pawhaven.org", "+1 (555) 019-2831"),
                )

                # Create regular adopter
                user_hash, user_salt = hash_password("user123")
                cur.execute(
                    """
                    INSERT INTO users (username, password_hash, salt, role, full_name, email, phone)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                    """,
                    ("adopter", user_hash, user_salt, "adopter", "Maya Lin", "maya@example.com", "+1 (555) 014-9988"),
                )

            # Check if pets exist
            cur.execute("SELECT COUNT(*) AS count FROM pets;")
            p_row = cur.fetchone()
            if p_row and p_row["count"] == 0:
                sample_pets = [
                    (
                        "Barnaby",
                        "Dog",
                        "Golden Retriever Mix",
                        2.5,
                        "Male",
                        "Large",
                        "available",
                        "Fully Vaccinated, Microchipped",
                        True,
                        True,
                        120.00,
                        "Gentle giant who loves tennis balls and paddling in kiddie pools. Great with kids and other dogs.",
                    ),
                    (
                        "Luna",
                        "Cat",
                        "Domestic Short Hair",
                        1.0,
                        "Female",
                        "Small",
                        "available",
                        "Healthy & playful, spayed",
                        True,
                        True,
                        75.00,
                        "Curious lap cat who enjoys sunbeams, chirping at birds through the window, and gentle chin scratches.",
                    ),
                    (
                        "Mochi",
                        "Rabbit",
                        "Netherland Dwarf",
                        0.8,
                        "Female",
                        "Small",
                        "available",
                        "Litter-box trained, neutered",
                        True,
                        True,
                        45.00,
                        "Inquisitive little bun with soft smoky fur. Loves fresh Timothy hay, cilantro leaves, and cardboard mazes.",
                    ),
                    (
                        "Zeus",
                        "Dog",
                        "Siberian Husky",
                        3.0,
                        "Male",
                        "Large",
                        "available",
                        "High energy, vocal, healthy",
                        True,
                        True,
                        150.00,
                        "Athletic adventure companion with piercing blue eyes. Needs an active runner or hiker and a secure yard.",
                    ),
                    (
                        "Pippin",
                        "Bird",
                        "Cockatiel",
                        1.5,
                        "Male",
                        "Small",
                        "available",
                        "Healthy beak & feathers, whistles tunes",
                        True,
                        False,
                        35.00,
                        "Cheerful whistler who knows the Addams Family theme song. Likes head scritches and millet treats.",
                    ),
                    (
                        "Cleo",
                        "Cat",
                        "Tortoiseshell",
                        4.0,
                        "Female",
                        "Medium",
                        "pending",
                        "Quiet, healthy senior-in-training",
                        True,
                        True,
                        60.00,
                        "Sweet, calm lady who purrs like a gentle motor engine. Perfect companion for quiet home offices.",
                    ),
                ]

                cur.executemany(
                    """
                    INSERT INTO pets (
                        name, species, breed, age_years, gender, size,
                        status, health_status, vaccinated, spayed_neutered,
                        fee, description
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """,
                    sample_pets,
                )

            # Seed Shelters if empty
            cur.execute("SELECT COUNT(*) AS count FROM shelters;")
            s_row = cur.fetchone()
            if s_row and s_row["count"] == 0:
                cur.execute(
                    """
                    INSERT INTO shelters (name, address, city, state, capacity, phone)
                    VALUES 
                    ('PawHaven Central Shelter', '104 Animal Rescue Blvd', 'Seattle', 'WA', 50, '+1 (555) 010-4400'),
                    ('Northside Mountain Sanctuary', '882 Evergreen Terrace', 'Bellevue', 'WA', 30, '+1 (555) 012-7711')
                    ON CONFLICT DO NOTHING;
                    """
                )
                # Link existing pets to shelters (round robin)
                cur.execute("UPDATE pets SET shelter_id = 1 WHERE id % 2 = 1 AND shelter_id IS NULL;")
                cur.execute("UPDATE pets SET shelter_id = 2 WHERE id % 2 = 0 AND shelter_id IS NULL;")

            # Seed Medical Records if empty
            cur.execute("SELECT COUNT(*) AS count FROM medical_records;")
            m_row = cur.fetchone()
            if m_row and m_row["count"] == 0:
                cur.execute("SELECT id FROM pets ORDER BY id ASC;")
                p_ids = [r["id"] for r in cur.fetchall()]
                if p_ids:
                    med_data = [
                        (p_ids[0], "Routine Intake Examination", "Deworming, Rabies vaccine & microchip check", "Dr. Sarah Mitchell", 85.00),
                        (p_ids[0], "Dental Cleaning", "Ultrasonic scale and polish", "Dr. Sarah Mitchell", 120.00),
                    ]
                    if len(p_ids) > 1:
                        med_data.append((p_ids[1], "Post-Rescue Wellness Exam", "FVRCP booster, flea prevention applied", "Dr. Kevin Patel", 65.00))
                    if len(p_ids) > 2:
                        med_data.append((p_ids[2], "Dental & Incisor Assessment", "Molar trimming, dietary evaluation", "Dr. Lisa Wong", 45.00))
                    if len(p_ids) > 3:
                        med_data.append((p_ids[3], "Athletic Canine Assessment", "Hip evaluation, joint supplements prescribed", "Dr. Kevin Patel", 110.00))

                    cur.executemany(
                        """
                        INSERT INTO medical_records (pet_id, diagnosis, treatment, vet_name, cost)
                        VALUES (%s, %s, %s, %s, %s);
                        """,
                        med_data,
                    )

        conn.commit()
