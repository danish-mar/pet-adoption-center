"""Adoption application domain model and status badges."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class AdoptionApplication:
    id: int
    pet_id: int
    user_id: int
    status: str
    applicant_name: str
    applicant_phone: str
    applicant_email: str
    living_space: str
    has_other_pets: bool
    experience_notes: str
    reviewer_notes: str = ""
    submitted_at: datetime | None = None
    updated_at: datetime | None = None
    # Joined fields
    pet_name: str = ""
    pet_species: str = ""
    pet_breed: str = ""

    @property
    def status_badge(self) -> str:
        s = self.status.lower()
        if s == "pending":
            return "[bold black on yellow] PENDING REVIEW [/]"
        if s == "approved":
            return "[bold black on green] APPROVED [/]"
        if s == "rejected":
            return "[bold white on red] NOT APPROVED [/]"
        if s == "withdrawn":
            return "[dim white on grey27] WITHDRAWN [/]"
        return f"[bold]{self.status.upper()}[/]"

    @classmethod
    def from_row(cls, row: dict) -> AdoptionApplication:
        return cls(
            id=row["id"],
            pet_id=row["pet_id"],
            user_id=row["user_id"],
            status=row["status"],
            applicant_name=row["applicant_name"],
            applicant_phone=row["applicant_phone"],
            applicant_email=row["applicant_email"],
            living_space=row.get("living_space") or "House",
            has_other_pets=bool(row.get("has_other_pets", False)),
            experience_notes=row.get("experience_notes") or "",
            reviewer_notes=row.get("reviewer_notes") or "",
            submitted_at=row.get("submitted_at"),
            updated_at=row.get("updated_at"),
            pet_name=row.get("pet_name") or "",
            pet_species=row.get("pet_species") or "",
            pet_breed=row.get("pet_breed") or "",
        )
