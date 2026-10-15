"""Authentication views: Login, Registration, and User Profile."""

from __future__ import annotations

from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm

from pet_adoption_center.auth.session import session
from pet_adoption_center.services.user_service import user_service
from ..console import (
    console,
    clear_screen,
    print_banner,
    print_section,
    print_success,
    print_error,
    pause,
)


def login_view() -> bool:
    """Renders the login prompt. Returns True if login succeeded."""
    clear_screen()
    print_banner()
    print_section("User Login", "Enter your credentials to access your account")

    console.print(
        Panel(
            "[dim]Default credentials for testing:\n"
            "  • [bold cyan]admin[/] / [bold cyan]admin123[/] (Shelter Director)\n"
            "  • [bold cyan]adopter[/] / [bold cyan]user123[/] (Adopter Account)[/]",
            title="[bold yellow]💡 Demo Credentials[/]",
            border_style="yellow",
            padding=(0, 1),
        )
    )
    console.print()

    username = Prompt.ask("[bold cyan]Username[/]")
    if not username:
        return False

    password = Prompt.ask("[bold cyan]Password[/]", password=True)
    if not password:
        return False

    with console.status("[bold cyan]Authenticating...[/]", spinner="dots"):
        success, message = session.login(username, password)

    if success:
        print_success(message)
        pause()
        return True
    else:
        print_error(message)
        pause("Press Enter to try again...")
        return False


def register_view() -> bool:
    """Renders the user registration wizard."""
    clear_screen()
    print_banner()
    print_section("Create New Account", "Join our community to adopt a pet or volunteer")

    username = Prompt.ask("[bold cyan]Choose Username[/] (min 3 characters)")
    if not username:
        return False

    password = Prompt.ask("[bold cyan]Choose Password[/] (min 6 characters)", password=True)
    confirm_pw = Prompt.ask("[bold cyan]Confirm Password[/]", password=True)

    if password != confirm_pw:
        print_error("Passwords do not match!")
        pause()
        return False

    full_name = Prompt.ask("[bold cyan]Full Name[/]")
    email = Prompt.ask("[bold cyan]Email Address[/]")
    phone = Prompt.ask("[bold cyan]Phone Number[/] (optional)", default="")

    with console.status("[bold cyan]Creating account in PostgreSQL...[/]", spinner="dots"):
        success, message = session.register(
            username=username,
            password=password,
            full_name=full_name,
            email=email,
            phone=phone,
            role="adopter",
        )

    if success:
        print_success(message)
        pause()
        return True
    else:
        print_error(message)
        pause("Press Enter to continue...")
        return False


def profile_view() -> None:
    """Displays the currently logged in user profile with option to edit."""
    if not session.is_authenticated or not session.current_user:
        print_error("You must be logged in to view your profile.")
        pause()
        return

    user = session.current_user

    while True:
        clear_screen()
        print_banner()
        print_section("My Account Profile", f"Details for @{user.username}")

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Field", style="bold cyan", width=18)
        table.add_column("Value", style="white")

        role_badge = (
            "[bold black on yellow] 🛡️ Shelter Admin [/]"
            if user.is_admin
            else "[bold black on cyan] 🐾 Adopter [/]"
        )

        table.add_row("User ID", f"#{user.id}")
        table.add_row("Username", f"@{user.username}")
        table.add_row("Role", role_badge)
        table.add_row("Full Name", user.full_name)
        table.add_row("Email", user.email)
        table.add_row("Phone", user.phone or "[dim]Not provided[/]")
        table.add_row(
            "Member Since",
            user.created_at.strftime("%B %d, %Y") if user.created_at else "Recently",
        )

        console.print(Panel(table, border_style="cyan", title="[bold cyan]👤 Profile Card[/]"))
        console.print()

        console.print("[1] [bold]Edit Contact Information[/]")
        console.print("[0] [bold]Back to Main Menu[/]")
        console.print()

        choice = Prompt.ask("[bold cyan]Select an option[/]", choices=["1", "0"], default="0")
        if choice == "0":
            break
        elif choice == "1":
            new_name = Prompt.ask("[bold cyan]Full Name[/]", default=user.full_name)
            new_email = Prompt.ask("[bold cyan]Email[/]", default=user.email)
            new_phone = Prompt.ask("[bold cyan]Phone[/]", default=user.phone)

            success, msg = user_service.update_profile(
                user.id, new_name, new_email, new_phone
            )
            if success:
                user.full_name = new_name
                user.email = new_email
                user.phone = new_phone
                print_success(msg)
            else:
                print_error(msg)
            pause()
