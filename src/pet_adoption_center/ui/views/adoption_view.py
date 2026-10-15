"""Adoption application submission wizard and applicant status tracker."""

from __future__ import annotations

from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm

from pet_adoption_center.models.pet import Pet
from pet_adoption_center.auth.session import session
from pet_adoption_center.services.adoption_service import adoption_service
from ..console import (
    console,
    clear_screen,
    print_banner,
    print_section,
    print_success,
    print_error,
    print_warning,
    pause,
)


def apply_for_pet_view(pet: Pet) -> None:
    """Multi-step adoption application form."""
    if not session.is_authenticated or not session.current_user:
        print_warning("You must be logged in to submit an adoption application.")
        pause()
        return

    user = session.current_user

    clear_screen()
    print_banner()
    print_section(
        f"Adoption Application: {pet.name} {pet.species_icon}",
        f"Species: {pet.species} • Breed: {pet.breed} • Fee: ${pet.fee:.2f}",
    )

    console.print(
        Panel(
            "[dim]Thank you for opening your heart to a rescue animal!\n"
            "Please provide accurate answers so our shelter team can review your suitability.[/]",
            border_style="cyan",
        )
    )
    console.print()

    applicant_name = Prompt.ask("[bold cyan]Your Full Name[/]", default=user.full_name)
    applicant_email = Prompt.ask("[bold cyan]Email[/]", default=user.email)
    applicant_phone = Prompt.ask("[bold cyan]Phone Number[/]", default=user.phone or "")

    living_space = Prompt.ask(
        "[bold cyan]Your Living Space[/]",
        choices=["House with fenced yard", "House without yard", "Apartment", "Condo / Townhouse", "Farm / Acreage"],
        default="House with fenced yard",
    )

    has_other_pets = Confirm.ask(
        "[bold cyan]Do you currently have other pets in your household?[/]",
        default=False,
    )

    experience = Prompt.ask(
        "[bold cyan]Tell us about your pet experience & why you'd be a great match for this pet[/]",
        default="I have cared for family pets and have plenty of love and time to dedicate.",
    )

    console.print()
    if not Confirm.ask(f"[bold cyan]Ready to submit your application for {pet.name}?[/]", default=True):
        print_warning("Application submission cancelled.")
        pause()
        return

    with console.status("[bold cyan]Submitting application to PostgreSQL...[/]", spinner="dots"):
        success, message, app_id = adoption_service.submit_application(
            pet_id=pet.id,
            user_id=user.id,
            applicant_name=applicant_name,
            applicant_phone=applicant_phone,
            applicant_email=applicant_email,
            living_space=living_space,
            has_other_pets=has_other_pets,
            experience_notes=experience,
        )

    if success:
        print_success(f"{message} (Application Reference: #{app_id})")
        console.print("[dim]You can track the status in 'My Applications' from the main menu.[/]")
    else:
        print_error(message)
    pause()


def my_applications_view() -> None:
    """Lists all adoption applications submitted by the current user."""
    if not session.is_authenticated or not session.current_user:
        print_warning("Please log in to view your applications.")
        pause()
        return

    user = session.current_user

    while True:
        clear_screen()
        print_banner()
        print_section("My Adoption Applications", f"Applications filed by {user.full_name}")

        apps = adoption_service.get_user_applications(user.id)

        if not apps:
            console.print(
                Panel(
                    "[bold yellow]You haven't submitted any adoption applications yet.[/]\n"
                    "Explore our available pets in the catalog and find your new companion!",
                    border_style="yellow",
                )
            )
            pause("Press Enter to return...")
            break

        table = Table(
            border_style="cyan",
            show_lines=True,
            header_style="bold bright_white on grey23",
        )
        table.add_column("App ID", justify="right", style="bold cyan", width=8)
        table.add_column("Pet Name", style="bold white", width=16)
        table.add_column("Species & Breed", width=22)
        table.add_column("Status", justify="center", width=18)
        table.add_column("Submitted", justify="center", width=14)
        table.add_column("Shelter Feedback / Notes", style="italic", width=28)

        for a in apps:
            submitted_str = a.submitted_at.strftime("%b %d, %Y") if a.submitted_at else "Recently"
            notes = a.reviewer_notes if a.reviewer_notes else "[dim]In review by shelter staff[/]"
            table.add_row(
                f"#{a.id}",
                a.pet_name,
                f"{a.pet_species} ({a.pet_breed})",
                a.status_badge,
                submitted_str,
                notes,
            )

        console.print(table)
        console.print()
        console.print("[0] [bold]Back to Main Menu[/]")
        choice = Prompt.ask("[bold cyan]Select action[/]", choices=["0"], default="0")
        if choice == "0":
            break
