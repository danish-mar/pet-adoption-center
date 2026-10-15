"""User management service for profiles and administrative user listings."""

from __future__ import annotations

from typing import List, Optional
from ..db.connection import get_connection
from ..models.user import User


class UserService:
    """User account operations and administration."""

    @staticmethod
    def list_users() -> List[User]:
        """Fetches all registered users."""
        users: list[User] = []
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users ORDER BY id ASC;")
                for row in cur.fetchall():
                    users.append(User.from_row(row))
        return users

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Fetches a specific user by ID."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE id = %s;", (user_id,))
                row = cur.fetchone()
                if row:
                    return User.from_row(row)
        return None

    @staticmethod
    def update_profile(
        user_id: int, full_name: str, email: str, phone: str
    ) -> tuple[bool, str]:
        """Updates contact info for a user."""
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE users
                        SET full_name = %s, email = %s, phone = %s
                        WHERE id = %s;
                        """,
                        (full_name.strip(), email.strip().lower(), phone.strip(), user_id),
                    )
                    conn.commit()
                    return True, "Profile updated successfully."
        except Exception as exc:
            return False, f"Failed to update profile: {exc}"


user_service = UserService()
