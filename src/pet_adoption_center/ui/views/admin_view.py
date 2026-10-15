"""Admin dashboard, adoption application review queue, and shelter management."""

from __future__ import annotations

from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.prompt import Prompt, Confirm

from pet_adoption_center.auth.session import session
from pet_adoption_center.services.adoption_service import adoption_service
from pet_adoption_center.services.pet_service import pet_service
from pet_adoption_center.services.user_service import user_service
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
from .pet_view import add_pet_view


def admin_dashboard_view() -> None:
    """Master administration console for shelter operators."""
    if not session.is_admin:
        print_error("Access restricted: Administrator rights required.")
        pause()
        return

    while True:
        clear_screen()
        print_banner()
        print_section("Shelter Operations Dashboard", "Rescue Analytics and Administration")

        metrics = adoption_service.get_adoption_metrics()

        # Metrics cards
        card_total = Panel(
            f"[bold cyan]{metrics['total_pets']}[/]",
            title="🐾 Total Pets",
            border_style="cyan",
            padding=(1, 2),
        )
        card_avail = Panel(
            f"[bold green]{metrics['available_pets']}[/]",
            title="✨ Available",
            border_style="green",
            padding=(1, 2),
        )
        card_pending = Panel(
            f"[bold yellow]{metrics['pending_apps']}[/]",
            title="📋 Pending Reviews",
            border_style="yellow",
            padding=(1, 2),
        )
        card_adopted = Panel(
            f"[bold magenta]{metrics['adopted_pets']}[/]",
            title="🎉 Adopted Homes",
            border_style="magenta",
            padding=(1, 2),
        )
        card_users = Panel(
            f"[bold white]{metrics['total_users']}[/]",
            title="👥 Users",
            border_style="blue",
            padding=(1, 2),
        )

        console.print(Columns([card_total, card_avail, card_pending, card_adopted, card_users]))
        console.print()

        # Species breakdown table
        species_rows = metrics.get("species_breakdown", [])
        if species_rows:
            spec_table = Table(
                title="[bold cyan]Species Distribution[/]",
                box=None,
                header_style="bold cyan",
                padding=(0, 2),
            )
            spec_table.add_column("Species", style="white")
            spec_table.add_column("Count", justify="right", style="bold gold3")
            for r in species_rows:
                spec_table.add_row(r["species"], str(r["count"]))
            console.print(Panel(spec_table, border_style="grey42", width=40))

        console.print()
        console.print("[bold cyan]Management Operations:[/]")
        console.print(" [1] [bold]Review Adoption Applications Queue[/]")
        console.print(" [2] [bold]Add New Rescue Pet[/]")
        console.print(" [3] [bold]Manage Pets Catalog[/]")
        console.print(" [4] [bold]View Registered Users[/]")
        console.print(" [0] [bold]Return to Main Menu[/]")
        console.print()

        choice = Prompt.ask("[bold cyan]Select operation[/]", choices=["1", "2", "3", "4", "0"], default="0")

        if choice == "0":
            break
        elif choice == "1":
            review_applications_queue_view()
        elif choice == "2":
            add_pet_view()
        elif choice == "3":
            manage_pets_view()
        elif choice == "4":
            view_all_users_view()


def review_applications_queue_view() -> None:
    """Queue for inspecting and acting upon adoption applications."""
    while True:
        clear_screen()
        print_banner()
        print_section("Adoption Applications Queue", "Review submitted adopter applications")

        apps = adoption_service.get_all_applications()

        if not apps:
            console.print(
                Panel(
                    "[bold green]No applications found in the system.[/]",
                    border_style="green",
                )
            )
            pause()
            break

        table = Table(border_style="cyan", show_lines=True, header_style="bold bright_white on grey23")
        table.add_column("App ID", justify="right", style="bold cyan", width=8)
        table.add_column("Pet Name", style="bold white", width=14)
        table.add_column("Applicant", style="white", width=18)
        table.add_column("Contact", width=22)
        table.add_column("Residence", width=16)
        table.add_column("Status", justify="center", width=18)

        for a in apps:
            table.add_row(
                f"#{a.id}",
                f"{a.pet_name} ({a.pet_species})",
                a.applicant_name,
                f"{a.applicant_phone} | {a.applicant_email}",
                a.living_space,
                a.status_badge,
            )

        console.print(table)
        console.print()
        console.print("[bold cyan]Enter Application ID to review[/], or [bold]0[/] to go back:")

        app_id_input = Prompt.ask("[bold cyan]Application ID[/]", default="0").strip()
        if app_id_input in ("0", "back", "exit"):
            break

        if app_id_input.isdigit():
            inspect_application_view(int(app_id_input))
        else:
            print_error("Please enter a valid numeric ID.")
            pause()


def inspect_application_view(app_id: int) -> None:
    """Detailed review and decision modal for an application."""
    app = adoption_service.get_application_by_id(app_id)
    if not app:
        print_error(f"Application #{app_id} not found.")
        pause()
        return

    clear_screen()
    print_banner()
    print_section(f"Reviewing Application #{app.id}", f"Pet: {app.pet_name} • Applicant: {app.applicant_name}")

    info_table = Table(box=None, show_header=False, padding=(0, 2))
    info_table.add_column("Field", style="bold cyan", width=20)
    info_table.add_column("Details", style="white")

    info_table.add_row("Status", app.status_badge)
    info_table.add_row("Pet", f"{app.pet_name} ({app.pet_species} - {app.pet_breed}) [ID #{app.pet_id}]")
    info_table.add_row("Applicant Name", app.applicant_name)
    info_table.add_row("Email", app.applicant_email)
    info_table.add_row("Phone", app.applicant_phone)
    info_table.add_row("Living Environment", app.living_space)
    info_table.add_row("Other Pets in Home?", "[bold green]Yes[/]" if app.has_other_pets else "[bold dim]No[/]")
    info_table.add_row(
        "Submitted At",
        app.submitted_at.strftime("%B %d, %Y %H:%M") if app.submitted_at else "Unknown",
    )
    if app.reviewer_notes:
        info_table.add_row("Current Staff Notes", f"[italic]{app.reviewer_notes}[/]")

    console.print(Panel(info_table, border_style="cyan", title="[bold cyan]Application Summary[/]"))

    console.print(
        Panel(
            f"[italic white]{app.experience_notes}[/]",
            title="[bold cyan]Applicant's Experience & Notes[/]",
            border_style="cyan",
            padding=(1, 2),
        )
    )
    console.print()

    console.print("[1] [bold green]APPROVE Application[/]")
    console.print("[2] [bold red]REJECT Application[/]")
    console.print("[0] [bold]Cancel / Return[/]")
    console.print()

    decision = Prompt.ask("[bold cyan]Select decision[/]", choices=["1", "2", "0"], default="0")
    if decision == "1":
        notes = Prompt.ask("[bold cyan]Approval notes / instructions for applicant[/]", default="Application approved! Please visit the shelter to finalize adoption and collect your pet.")
        success, msg = adoption_service.review_application(app.id, "approved", notes)
        if success:
            print_success(msg)
        else:
            print_error(msg)
        pause()
    elif decision == "2":
        notes = Prompt.ask("[bold cyan]Reason for rejection[/]", default="Thank you for your interest, but the pet has specific home requirements that are not met.")
        success, msg = adoption_service.review_application(app.id, "rejected", notes)
        if success:
            print_success(msg)
        else:
            print_error(msg)
        pause()


def manage_pets_view() -> None:
    """Allows admin to inspect and delete pets."""
    while True:
        clear_screen()
        print_banner()
        print_section("Manage Pets Catalog", "Admin controls for pet records")

        pets = pet_service.list_pets()
        from .pet_view import render_pets_table
        console.print(render_pets_table(pets, title="All Shelter Pets"))

        console.print()
        console.print("[bold cyan]Enter Pet ID to manage or [bold]0[/] to go back:")
        pet_id_str = Prompt.ask("[bold cyan]Pet ID[/]", default="0").strip()

        if pet_id_str in ("0", "back", "exit"):
            break
        if pet_id_str.isdigit():
            from .pet_view import pet_detail_view
            pet_detail_view(int(pet_id_str))
        else:
            print_error("Invalid ID.")
            pause()


def view_all_users_view() -> None:
    """Lists all registered users in PostgreSQL."""
    clear_screen()
    print_banner()
    print_section("Registered Users", "Database records in PostgreSQL 'users' table")

    users = user_service.list_users()
    table = Table(border_style="cyan", show_lines=True, header_style="bold bright_white on grey23")
    table.add_column("ID", justify="right", style="bold cyan", width=6)
    table.add_column("Username", style="bold white", width=16)
    table.add_column("Role", justify="center", width=14)
    table.add_column("Full Name", width=20)
    table.add_column("Email", width=26)
    table.add_column("Phone", width=18)
    table.add_column("Joined Date", justify="center", width=14)

    for u in users:
        role_badge = (
            "[bold black on yellow] ADMIN [/]"
            if u.is_admin
            else "[bold black on cyan] ADOPTER [/]"
        )
        joined_str = u.created_at.strftime("%b %d, %Y") if u.created_at else "Recently"
        table.add_row(
            f"#{u.id}",
            f"@{u.username}",
            role_badge,
            u.full_name,
            u.email,
            u.phone or "[dim]-[/]",
            joined_str,
        )

    console.print(table)
    pause()
