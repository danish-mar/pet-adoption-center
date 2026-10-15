"""Application menu router and interactive navigation loop."""

from __future__ import annotations

import sys
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

from pet_adoption_center.auth.session import session
from .console import (
    console,
    clear_screen,
    print_banner,
    print_section,
    print_info,
    pause,
)
from .views.pet_view import browse_pets_view
from .views.adoption_view import my_applications_view
from .views.auth_view import login_view, register_view, profile_view
from .views.admin_view import admin_dashboard_view
from .views.dbms_view import dbms_suite_menu


class AppRouter:
    """Manages menu routing and user interaction transitions."""

    def run(self) -> None:
        """Main navigation event loop."""
        while True:
            clear_screen()
            print_banner()

            menu_table = Table(box=None, show_header=False, padding=(0, 2))
            menu_table.add_column("Key", style="bold cyan", width=6)
            menu_table.add_column("Option", style="white")

            menu_table.add_row("[1]", "🐾  [bold]Browse Pet Catalog[/] (Dogs, Cats, Rabbits & more)")

            if session.is_authenticated:
                user = session.current_user
                if user and user.is_admin:
                    menu_table.add_row("[2]", "🛡️  [bold yellow]Shelter Admin Dashboard[/] (Applications & Analytics)")
                else:
                    menu_table.add_row("[2]", "📋  [bold]My Adoption Applications[/] (Track Status)")

                menu_table.add_row("[3]", "👤  [bold]My Account Profile[/]")
                menu_table.add_row("[4]", "🚪  [bold]Log Out[/]")
            else:
                menu_table.add_row("[2]", "🔑  [bold]Log In[/] (Access applications or admin panel)")
                menu_table.add_row("[3]", "✨  [bold]Register New Account[/]")

            menu_table.add_row("[D]", "🎓  [bold gold3]DBMS Academic Suite[/] (Schema, 3NF, EXPLAIN ANALYZE, ACID)")
            menu_table.add_row("[0]", "👋  [dim]Exit Application[/]")

            console.print(
                Panel(
                    menu_table,
                    title="[bold cyan]✦ Main Menu ✦[/]",
                    border_style="cyan",
                    padding=(1, 2),
                )
            )
            console.print()

            valid_choices = ["1", "2", "3", "d", "D", "0"]
            if session.is_authenticated:
                valid_choices.append("4")

            choice = Prompt.ask(
                "[bold cyan]Select an option[/]",
                choices=valid_choices,
                default="1",
            ).lower()

            if choice == "0":
                clear_screen()
                console.print("\n[bold cyan]Thank you for supporting rescue animals. Goodbye! 🐾[/]\n")
                sys.exit(0)
            elif choice == "d":
                dbms_suite_menu()
            elif choice == "1":
                browse_pets_view()
            elif choice == "2":
                if session.is_authenticated:
                    if session.is_admin:
                        admin_dashboard_view()
                    else:
                        my_applications_view()
                else:
                    login_view()
            elif choice == "3":
                if session.is_authenticated:
                    profile_view()
                else:
                    register_view()
            elif choice == "4" and session.is_authenticated:
                session.logout()
                print_info("You have been logged out.")
                pause()


router = AppRouter()
