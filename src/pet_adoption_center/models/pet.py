"""Pet domain model and presentation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class Pet:
    id: int
    name: str
    species: str
    breed: str
    age_years: float
    gender: str
    size: str
    status: str
    health_status: str
    vaccinated: bool
    spayed_neutered: bool
    fee: Decimal
    description: str
    intake_date: date | None = None

    @property
    def species_icon(self) -> str:
        s = self.species.lower()
        if "dog" in s:
            return "🐶"
        if "cat" in s:
            return "🐱"
        if "rabbit" in s or "bunny" in s:
            return "🐰"
        if "bird" in s or "parrot" in s or "cockatiel" in s:
            return "🦜"
        if "hamster" in s or "guinea" in s or "hedgehog" in s:
            return "🦔"
        return "🐾"

    @property
    def status_style(self) -> str:
        s = self.status.lower()
        if s == "available":
            return "bold green"
        if s == "pending":
            return "bold yellow"
        if s == "adopted":
            return "bold magenta"
        return "dim"

    @property
    def status_badge(self) -> str:
        s = self.status.lower()
        if s == "available":
            return "[bold black on green] AVAILABLE [/]"
        if s == "pending":
            return "[bold black on yellow] PENDING [/]"
        if s == "adopted":
            return "[bold white on dark_magenta] ADOPTED [/]"
        return f"[{self.status_style}]{self.status.upper()}[/]"

    @classmethod
    def from_row(cls, row: dict) -> Pet:
        return cls(
            id=row["id"],
            name=row["name"],
            species=row["species"],
            breed=row["breed"],
            age_years=float(row["age_years"]),
            gender=row["gender"],
            size=row.get("size") or "Medium",
            status=row["status"],
            health_status=row.get("health_status") or "Healthy",
            vaccinated=bool(row.get("vaccinated", True)),
            spayed_neutered=bool(row.get("spayed_neutered", True)),
            fee=Decimal(str(row.get("fee", 0))),
            description=row.get("description") or "",
            intake_date=row.get("intake_date"),
        )
