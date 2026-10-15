"""Pet service handling catalog operations, filtering, and administration."""

from __future__ import annotations

from decimal import Decimal
from typing import Optional, List
from ..db.connection import get_connection
from ..models.pet import Pet


class PetService:
    """Operations for querying and mutating pets in PostgreSQL."""

    @staticmethod
    def list_pets(
        status: Optional[str] = None,
        species: Optional[str] = None,
        search: Optional[str] = None,
        order_by: str = "id ASC",
    ) -> List[Pet]:
        """Queries pets with optional status, species, and keyword search filters."""
        query = "SELECT * FROM pets WHERE 1=1"
        params: list = []

        if status:
            query += " AND LOWER(status) = LOWER(%s)"
            params.append(status)

        if species:
            query += " AND LOWER(species) = LOWER(%s)"
            params.append(species)

        if search:
            query += " AND (LOWER(name) LIKE %s OR LOWER(breed) LIKE %s OR LOWER(description) LIKE %s)"
            pattern = f"%{search.lower()}%"
            params.extend([pattern, pattern, pattern])

        # Allowed sorting safely
        allowed_orders = {
            "id ASC": "id ASC",
            "id DESC": "id DESC",
            "age ASC": "age_years ASC",
            "age DESC": "age_years DESC",
            "fee ASC": "fee ASC",
            "fee DESC": "fee DESC",
            "name ASC": "name ASC",
        }
        order_clause = allowed_orders.get(order_by, "id ASC")
        query += f" ORDER BY {order_clause};"

        pets: list[Pet] = []
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                for row in cur.fetchall():
                    pets.append(Pet.from_row(row))
        return pets

    @staticmethod
    def get_pet_by_id(pet_id: int) -> Optional[Pet]:
        """Retrieves a single pet by ID."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM pets WHERE id = %s;", (pet_id,))
                row = cur.fetchone()
                if row:
                    return Pet.from_row(row)
        return None

    @staticmethod
    def add_pet(
        name: str,
        species: str,
        breed: str,
        age_years: float,
        gender: str,
        size: str,
        fee: float | Decimal,
        description: str,
        health_status: str = "Healthy & Up to date on shots",
        vaccinated: bool = True,
        spayed_neutered: bool = True,
    ) -> Pet:
        """Adds a new pet into the database."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO pets (
                        name, species, breed, age_years, gender, size,
                        status, health_status, vaccinated, spayed_neutered,
                        fee, description
                    ) VALUES (%s, %s, %s, %s, %s, %s, 'available', %s, %s, %s, %s, %s)
                    RETURNING *;
                    """,
                    (
                        name,
                        species,
                        breed,
                        age_years,
                        gender,
                        size,
                        health_status,
                        vaccinated,
                        spayed_neutered,
                        fee,
                        description,
                    ),
                )
                row = cur.fetchone()
                conn.commit()
                return Pet.from_row(row)

    @staticmethod
    def update_pet_status(pet_id: int, new_status: str) -> bool:
        """Updates the adoption status of a pet."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE pets SET status = %s WHERE id = %s;",
                    (new_status.lower(), pet_id),
                )
                conn.commit()
                return cur.rowcount > 0

    @staticmethod
    def delete_pet(pet_id: int) -> bool:
        """Removes a pet record and cascaded applications."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM pets WHERE id = %s;", (pet_id,))
                conn.commit()
                return cur.rowcount > 0

    @staticmethod
    def get_species_list() -> List[str]:
        """Returns distinct species available in the system."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT DISTINCT species FROM pets ORDER BY species ASC;")
                return [r["species"] for r in cur.fetchall()]


pet_service = PetService()
