"""User domain model and data structures."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    id: int
    username: str
    password_hash: str
    salt: str
    role: str
    full_name: str
    email: str
    phone: str = ""
    created_at: datetime | None = None

    @property
    def is_admin(self) -> bool:
        return self.role.lower() == "admin"

    @classmethod
    def from_row(cls, row: dict) -> User:
        return cls(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            salt=row["salt"],
            role=row["role"],
            full_name=row["full_name"],
            email=row["email"],
            phone=row.get("phone") or "",
            created_at=row.get("created_at"),
        )
