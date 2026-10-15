"""Session and authentication service for user login, registration, and state management."""

from __future__ import annotations

import re
from typing import Optional
import psycopg

from ..db.connection import get_connection
from ..models.user import User
from .hasher import hash_password, verify_password


class SessionManager:
    """Manages the current user session and authentication actions."""

    def __init__(self) -> None:
        self.current_user: Optional[User] = None

    @property
    def is_authenticated(self) -> bool:
        return self.current_user is not None

    @property
    def is_admin(self) -> bool:
        return self.current_user is not None and self.current_user.is_admin

    def login(self, username: str, password: str) -> tuple[bool, str]:
        """Authenticates user against PostgreSQL users table."""
        username = username.strip()
        if not username or not password:
            return False, "Username and password cannot be empty."

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, username, password_hash, salt, role, full_name, email, phone, created_at
                        FROM users
                        WHERE LOWER(username) = LOWER(%s);
                        """,
                        (username,),
                    )
                    row = cur.fetchone()
                    if not row:
                        return False, "Invalid username or password."

                    if not verify_password(password, row["password_hash"], row["salt"]):
                        return False, "Invalid username or password."

                    self.current_user = User.from_row(row)
                    return True, f"Welcome back, {self.current_user.full_name}!"
        except Exception as exc:
            return False, f"Database error during login: {exc}"

    def register(
        self,
        username: str,
        password: str,
        full_name: str,
        email: str,
        phone: str = "",
        role: str = "adopter",
    ) -> tuple[bool, str]:
        """Validates and creates a new user account."""
        username = username.strip()
        full_name = full_name.strip()
        email = email.strip().lower()
        phone = phone.strip()

        if len(username) < 3:
            return False, "Username must be at least 3 characters long."
        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            return False, "Username may only contain letters, numbers, and underscores."
        if len(password) < 6:
            return False, "Password must be at least 6 characters long."
        if not full_name:
            return False, "Full name is required."
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            return False, "Please enter a valid email address."

        pwd_hash, salt = hash_password(password)

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # Check existing username or email
                    cur.execute(
                        "SELECT username, email FROM users WHERE LOWER(username) = LOWER(%s) OR LOWER(email) = %s;",
                        (username, email),
                    )
                    existing = cur.fetchone()
                    if existing:
                        if existing["username"].lower() == username.lower():
                            return False, f"Username '{username}' is already taken."
                        return False, f"Email '{email}' is already registered."

                    cur.execute(
                        """
                        INSERT INTO users (username, password_hash, salt, role, full_name, email, phone)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id, username, password_hash, salt, role, full_name, email, phone, created_at;
                        """,
                        (username, pwd_hash, salt, role, full_name, email, phone),
                    )
                    new_row = cur.fetchone()
                    conn.commit()

                    if new_row:
                        self.current_user = User.from_row(new_row)
                        return True, f"Account created! Welcome, {full_name}!"
                    return False, "Failed to register user."
        except Exception as exc:
            return False, f"Database error during registration: {exc}"

    def logout(self) -> None:
        """Clears the active session."""
        self.current_user = None


# Global session instance
session = SessionManager()
