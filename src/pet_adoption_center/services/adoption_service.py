"""Adoption application workflows, review operations, and statistical metrics."""

from __future__ import annotations

from typing import Optional, List, Dict, Any
from ..db.connection import get_connection
from ..models.adoption import AdoptionApplication


class AdoptionService:
    """Handles pet adoption submissions, queries, and reviews."""

    @staticmethod
    def submit_application(
        pet_id: int,
        user_id: int,
        applicant_name: str,
        applicant_phone: str,
        applicant_email: str,
        living_space: str,
        has_other_pets: bool,
        experience_notes: str,
    ) -> tuple[bool, str, Optional[int]]:
        """Submits a new adoption application for review."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Verify pet exists and is available or pending
                cur.execute("SELECT name, status FROM pets WHERE id = %s;", (pet_id,))
                pet = cur.fetchone()
                if not pet:
                    return False, f"Pet #{pet_id} not found.", None
                if pet["status"].lower() == "adopted":
                    return False, f"Sorry, {pet['name']} has already been adopted!", None

                # Check if user already has an active pending application for this pet
                cur.execute(
                    """
                    SELECT id FROM adoption_applications
                    WHERE pet_id = %s AND user_id = %s AND status = 'pending';
                    """,
                    (pet_id, user_id),
                )
                if cur.fetchone():
                    return False, "You already have a pending application for this pet.", None

                cur.execute(
                    """
                    INSERT INTO adoption_applications (
                        pet_id, user_id, applicant_name, applicant_phone, applicant_email,
                        living_space, has_other_pets, experience_notes, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')
                    RETURNING id;
                    """,
                    (
                        pet_id,
                        user_id,
                        applicant_name,
                        applicant_phone,
                        applicant_email,
                        living_space,
                        has_other_pets,
                        experience_notes,
                    ),
                )
                app_id = cur.fetchone()["id"]

                # Mark pet status as pending
                cur.execute(
                    "UPDATE pets SET status = 'pending' WHERE id = %s AND status = 'available';",
                    (pet_id,),
                )
                conn.commit()
                return True, "Your adoption application has been submitted successfully!", app_id

    @staticmethod
    def get_user_applications(user_id: int) -> List[AdoptionApplication]:
        """Lists applications submitted by a specific user."""
        query = """
        SELECT 
            a.*,
            p.name AS pet_name,
            p.species AS pet_species,
            p.breed AS pet_breed
        FROM adoption_applications a
        JOIN pets p ON a.pet_id = p.id
        WHERE a.user_id = %s
        ORDER BY a.submitted_at DESC;
        """
        apps: list[AdoptionApplication] = []
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (user_id,))
                for row in cur.fetchall():
                    apps.append(AdoptionApplication.from_row(row))
        return apps

    @staticmethod
    def get_all_applications(status: Optional[str] = None) -> List[AdoptionApplication]:
        """Lists all applications with optional status filter for administrators."""
        query = """
        SELECT 
            a.*,
            p.name AS pet_name,
            p.species AS pet_species,
            p.breed AS pet_breed
        FROM adoption_applications a
        JOIN pets p ON a.pet_id = p.id
        """
        params: list = []
        if status:
            query += " WHERE LOWER(a.status) = LOWER(%s)"
            params.append(status)
        query += " ORDER BY a.submitted_at DESC;"

        apps: list[AdoptionApplication] = []
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                for row in cur.fetchall():
                    apps.append(AdoptionApplication.from_row(row))
        return apps

    @staticmethod
    def get_application_by_id(app_id: int) -> Optional[AdoptionApplication]:
        """Fetches single application with joined pet data."""
        query = """
        SELECT 
            a.*,
            p.name AS pet_name,
            p.species AS pet_species,
            p.breed AS pet_breed
        FROM adoption_applications a
        JOIN pets p ON a.pet_id = p.id
        WHERE a.id = %s;
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (app_id,))
                row = cur.fetchone()
                if row:
                    return AdoptionApplication.from_row(row)
        return None

    @staticmethod
    def review_application(
        app_id: int, new_status: str, reviewer_notes: str
    ) -> tuple[bool, str]:
        """Admin decision on application (approved / rejected / withdrawn)."""
        new_status = new_status.lower()
        if new_status not in ("approved", "rejected", "withdrawn"):
            return False, "Invalid status choice."

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT pet_id, status FROM adoption_applications WHERE id = %s;", (app_id,))
                row = cur.fetchone()
                if not row:
                    return False, "Application not found."

                pet_id = row["pet_id"]

                cur.execute(
                    """
                    UPDATE adoption_applications
                    SET status = %s, reviewer_notes = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s;
                    """,
                    (new_status, reviewer_notes, app_id),
                )

                if new_status == "approved":
                    # Mark the pet as adopted
                    cur.execute("UPDATE pets SET status = 'adopted' WHERE id = %s;", (pet_id,))
                    # Reject or notify other pending applications for the same pet
                    cur.execute(
                        """
                        UPDATE adoption_applications
                        SET status = 'rejected',
                            reviewer_notes = 'Pet has been matched with another applicant.',
                            updated_at = CURRENT_TIMESTAMP
                        WHERE pet_id = %s AND id != %s AND status = 'pending';
                        """,
                        (pet_id, app_id),
                    )
                elif new_status in ("rejected", "withdrawn"):
                    # Check if any other pending applications exist for this pet
                    cur.execute(
                        "SELECT COUNT(*) AS count FROM adoption_applications WHERE pet_id = %s AND status = 'pending';",
                        (pet_id,),
                    )
                    count_row = cur.fetchone()
                    if count_row and count_row["count"] == 0:
                        cur.execute("UPDATE pets SET status = 'available' WHERE id = %s;", (pet_id,))

                conn.commit()
                return True, f"Application #{app_id} marked as {new_status.upper()}."

    @staticmethod
    def get_adoption_metrics() -> Dict[str, Any]:
        """Calculates summary numbers for dashboard."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS count FROM pets;")
                total_pets = cur.fetchone()["count"]

                cur.execute("SELECT COUNT(*) AS count FROM pets WHERE status = 'available';")
                available_pets = cur.fetchone()["count"]

                cur.execute("SELECT COUNT(*) AS count FROM pets WHERE status = 'pending';")
                pending_pets = cur.fetchone()["count"]

                cur.execute("SELECT COUNT(*) AS count FROM pets WHERE status = 'adopted';")
                adopted_pets = cur.fetchone()["count"]

                cur.execute("SELECT COUNT(*) AS count FROM adoption_applications WHERE status = 'pending';")
                pending_apps = cur.fetchone()["count"]

                cur.execute("SELECT COUNT(*) AS count FROM users;")
                total_users = cur.fetchone()["count"]

                cur.execute(
                    """
                    SELECT species, COUNT(*) as count 
                    FROM pets 
                    GROUP BY species 
                    ORDER BY count DESC;
                    """
                )
                species_breakdown = cur.fetchall()

                return {
                    "total_pets": total_pets,
                    "available_pets": available_pets,
                    "pending_pets": pending_pets,
                    "adopted_pets": adopted_pets,
                    "pending_apps": pending_apps,
                    "total_users": total_users,
                    "species_breakdown": species_breakdown,
                }


adoption_service = AdoptionService()
