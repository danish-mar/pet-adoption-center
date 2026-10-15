"""Pet catalog views, search filters, detail inspection, and admin CRUD."""

from __future__ import annotations

from decimal import Decimal
from typing import Optional
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.prompt import Prompt, Confirm, FloatPrompt

from pet_adoption_center.models.pet import Pet
from pet_adoption_center.services.pet_service import pet_service
from pet_adoption_center.auth.session import session
from ..console import (
    console,
    clear_screen,
    print_banner,
    print_section,
    print_success,
    print_error,
    print_warning,
    print_info,
    pause,
)


def render_pets_table(pets: list[Pet], title: str = "Rescued Pets") -> Table:
    """Builds a styled Rich table for pet listings."""
    table = Table(
        title=f"[bold cyan]✦ {title} ✦[/] ({len(pets)} found)",
        header_style="bold bright_white on grey23",
        border_style="cyan",
        show_lines=True,
    )
    table.add_column("ID", justify="right", style="bold cyan", width=5)
    table.add_column("Species", justify="center", width=10)
    table.add_column("Name", style="bold white", width=14)
    table.add_column("Breed", style="white", width=22)
    table.add_column("Age", justify="center", width=8)
    table.add_column("Gender", justify="center", width=8)
    table.add_column("Size", justify="center", width=9)
    table.add_column("Fee", justify="right", style="bold green", width=9)
    table.add_column("Status", justify="center", width=16)

    for p in pets:
        age_str = f"{p.age_years:.1f}y" if p.age_years >= 1.0 else f"{int(p.age_years * 12)}m"
        table.add_row(
            f"#{p.id}",
            f"{p.species_icon} {p.species}",
            p.name,
            p.breed,
            age_str,
            p.gender,
            p.size,
            f"${p.fee:.2f}",
            p.status_badge,
        )
    return table


def browse_pets_view() -> None:
    """Main pet catalog loop with search, filters, and detail view navigation."""
    status_filter: Optional[str] = None
    species_filter: Optional[str] = None
    search_keyword: Optional[str] = None

    while True:
        clear_screen()
        print_banner()

        # Build current filter subtitle
        filters_applied = []
        if status_filter:
            filters_applied.append(f"Status: [bold yellow]{status_filter.upper()}[/]")
        if species_filter:
            filters_applied.append(f"Species: [bold yellow]{species_filter}[/]")
        if search_keyword:
            filters_applied.append(f"Search: [bold yellow]'{search_keyword}'[/]")
        subtitle = " | ".join(filters_applied) if filters_applied else "Showing all pets"

        print_section("Pet Adoption Catalog", subtitle)

        pets = pet_service.list_pets(
            status=status_filter,
            species=species_filter,
            search=search_keyword,
        )

        if not pets:
            console.print(
                Panel(
                    "[bold yellow]No pets match your current filter criteria.[/]\n"
                    "Try resetting your filters or searching for something else.",
                    border_style="yellow",
                )
            )
        else:
            console.print(render_pets_table(pets))

        console.print()
        console.print("[bold cyan]Actions:[/]  "
                      "[bold][V][/]iew Pet Details  |  "
                      "[bold][S][/]earch  |  "
                      "[bold][F][/]ilter by Species  |  "
                      "[bold][T][/]oggle Status Filter  |  "
                      "[bold][R][/]eset Filters  |  "
                      "[bold][0][/] Back to Main Menu")

        choice = Prompt.ask("\n[bold cyan]Select action or Pet ID[/]", default="0").strip().lower()

        if choice in ("0", "back", "exit"):
            break
        elif choice in ("r", "reset"):
            status_filter = None
            species_filter = None
            search_keyword = None
        elif choice in ("s", "search"):
            query = Prompt.ask("[bold cyan]Enter search query (name, breed, description)[/]").strip()
            search_keyword = query if query else None
        elif choice in ("f", "filter"):
            species_list = pet_service.get_species_list()
            if not species_list:
                print_info("No species recorded yet.")
                pause()
                continue
            console.print("\n[bold]Available species:[/]")
            for idx, spec in enumerate(species_list, 1):
                console.print(f" [{idx}] {spec}")
            console.print(" [0] Clear species filter")
            idx_choice = Prompt.ask("[bold cyan]Select species[/]", default="0")
            if idx_choice.isdigit() and 1 <= int(idx_choice) <= len(species_list):
                species_filter = species_list[int(idx_choice) - 1]
            elif idx_choice == "0":
                species_filter = None
        elif choice in ("t", "status"):
            console.print("\n[1] Available only\n[2] Pending applications\n[3] Adopted\n[0] All statuses")
            st_choice = Prompt.ask("[bold cyan]Filter by status[/]", choices=["1", "2", "3", "0"], default="0")
            if st_choice == "1":
                status_filter = "available"
            elif st_choice == "2":
                status_filter = "pending"
            elif st_choice == "3":
                status_filter = "adopted"
            else:
                status_filter = None
        elif choice in ("v", "view") or choice.isdigit():
            target_id_str = choice if choice.isdigit() else Prompt.ask("[bold cyan]Enter Pet ID[/]")
            if target_id_str.isdigit():
                pet_detail_view(int(target_id_str))
            else:
                print_error("Please enter a valid numeric Pet ID.")
                pause()


def pet_detail_view(pet_id: int) -> None:
    """Detailed view for a specific pet with application actions."""
    from .adoption_view import apply_for_pet_view

    while True:
        pet = pet_service.get_pet_by_id(pet_id)
        if not pet:
            print_error(f"Pet #{pet_id} was not found.")
            pause()
            return

        clear_screen()
        print_banner()
        print_section(f"Meet {pet.name} {pet.species_icon}", f"Pet Reference ID: #{pet.id}")

        # Overview Table
        info_table = Table(box=None, show_header=False, padding=(0, 2))
        info_table.add_column("Field", style="bold cyan")
        info_table.add_column("Value", style="white")

        age_str = f"{pet.age_years:.1f} years" if pet.age_years >= 1.0 else f"{int(pet.age_years * 12)} months"

        info_table.add_row("Species & Breed", f"{pet.species_icon} {pet.species} • {pet.breed}")
        info_table.add_row("Age & Gender", f"{age_str} • {pet.gender}")
        info_table.add_row("Size", pet.size)
        info_table.add_row("Adoption Fee", f"[bold green]${pet.fee:.2f}[/]")
        info_table.add_row("Status", pet.status_badge)

        # Medical Table
        med_table = Table(box=None, show_header=False, padding=(0, 2))
        med_table.add_column("Field", style="bold cyan")
        med_table.add_column("Value", style="white")

        vax_badge = "[bold green]✔ Yes[/]" if pet.vaccinated else "[bold red]✖ Pending[/]"
        spayed_badge = "[bold green]✔ Yes[/]" if pet.spayed_neutered else "[bold red]✖ Pending[/]"

        med_table.add_row("Health Status", pet.health_status)
        med_table.add_row("Vaccinated", vax_badge)
        med_table.add_row("Spayed / Neutered", spayed_badge)
        if pet.intake_date:
            med_table.add_row("Intake Date", pet.intake_date.strftime("%B %d, %Y"))

        col1 = Panel(info_table, title="[bold cyan]🐾 Vital Details[/]", border_style="cyan")
        col2 = Panel(med_table, title="[bold cyan]🩺 Medical & Care[/]", border_style="cyan")
        console.print(Columns([col1, col2]))

        # Bio panel
        console.print(
            Panel(
                f"[italic white]{pet.description}[/]",
                title=f"[bold cyan]📖 About {pet.name}[/]",
                border_style="cyan",
                padding=(1, 2),
            )
        )
        console.print()

        # Action choices
        options = []
        if pet.status.lower() in ("available", "pending"):
            options.append("[1] [bold green]Apply to Adopt this Pet[/]")
        else:
            options.append("[dim]This pet has already found a forever home![/]")

        if session.is_admin:
            options.append("[2] [bold yellow]Change Pet Status (Admin)[/]")
            options.append("[3] [bold red]Delete Pet Listing (Admin)[/]")

        options.append("[0] [bold]Back[/]")

        for opt in options:
            console.print(opt)
        console.print()

        choice = Prompt.ask("[bold cyan]Select action[/]", default="0")
        if choice == "0":
            break
        elif choice == "1" and pet.status.lower() in ("available", "pending"):
            if not session.is_authenticated:
                print_warning("You must be logged in to apply for adoption.")
                pause("Press Enter to log in...")
                from .auth_view import login_view
                if login_view():
                    apply_for_pet_view(pet)
            else:
                apply_for_pet_view(pet)
        elif choice == "2" and session.is_admin:
            new_st = Prompt.ask(
                "[bold cyan]New status[/]",
                choices=["available", "pending", "adopted"],
                default=pet.status,
            )
            pet_service.update_pet_status(pet.id, new_st)
            print_success(f"Status updated to '{new_st}'.")
            pause()
        elif choice == "3" and session.is_admin:
            if Confirm.ask(f"[bold red]Are you sure you want to delete {pet.name} from the database?[/]"):
                pet_service.delete_pet(pet.id)
                print_success(f"Pet #{pet.id} deleted.")
                pause()
                break


def add_pet_view() -> None:
    """Admin wizard for adding a new pet."""
    if not session.is_admin:
        print_error("Access denied. Admin privileges required.")
        pause()
        return

    clear_screen()
    print_banner()
    print_section("Register New Rescue Pet", "Enter the pet's background and medical information")

    name = Prompt.ask("[bold cyan]Pet Name[/]")
    if not name:
        return

    species = Prompt.ask(
        "[bold cyan]Species[/]",
        choices=["Dog", "Cat", "Rabbit", "Bird", "Small Animal", "Other"],
        default="Dog",
    )
    breed = Prompt.ask("[bold cyan]Breed[/]", default="Mixed Breed")
    age = FloatPrompt.ask("[bold cyan]Age (in years, e.g. 1.5 or 0.5 for 6 months)[/]", default=1.0)
    gender = Prompt.ask("[bold cyan]Gender[/]", choices=["Male", "Female", "Unknown"], default="Female")
    size = Prompt.ask("[bold cyan]Size[/]", choices=["Small", "Medium", "Large", "Extra Large"], default="Medium")
    fee = FloatPrompt.ask("[bold cyan]Adoption Fee ($)[/]", default=50.00)
    health = Prompt.ask("[bold cyan]Health Status[/]", default="Healthy, Active & Vaccinated")
    vax = Confirm.ask("[bold cyan]Vaccinated?[/]", default=True)
    spayed = Confirm.ask("[bold cyan]Spayed or Neutered?[/]", default=True)
    description = Prompt.ask("[bold cyan]Bio / Description[/]", default="Sweet, loving companion seeking a cozy home.")

    with console.status("[bold cyan]Saving pet to PostgreSQL...[/]", spinner="dots"):
        new_pet = pet_service.add_pet(
            name=name,
            species=species,
            breed=breed,
            age_years=age,
            gender=gender,
            size=size,
            fee=fee,
            description=description,
            health_status=health,
            vaccinated=vax,
            spayed_neutered=spayed,
        )

    print_success(f"Pet '{new_pet.name}' added with ID #{new_pet.id}!")
    pause()
