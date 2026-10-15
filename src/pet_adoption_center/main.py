"""Main entrypoint for the Pet Adoption Center CLI application."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from .config import db_config
from .db.connection import test_connection, init_db, seed_default_data
from .ui.console import console, clear_screen, print_error, print_success, print_info
from .ui.router import router
from rich.panel import Panel
from rich.prompt import Prompt


def try_start_local_postgres() -> bool:
    """Attempts to run the bundled local postgres runner script if binaries are present."""
    script_path = Path(__file__).resolve().parent.parent.parent / "scripts" / "run_local_postgres.sh"
    if script_path.exists() and shutil.which("postgres"):
        console.print("\n[bold cyan]Attempting to start local PostgreSQL service via runner script...[/]")
        try:
            res = subprocess.run([str(script_path), "start"], capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                print_success("Local PostgreSQL instance initialized and started.")
                return True
            else:
                print_error(f"Could not start local PostgreSQL: {res.stderr or res.stdout}")
        except Exception as exc:
            print_error(f"Subprocess error: {exc}")
    return False


def ensure_postgres_connected() -> bool:
    """Checks database connectivity with interactive recovery options."""
    while True:
        connected, message = test_connection()
        if connected:
            return True

        clear_screen()
        console.print(
            Panel(
                f"[bold red]Unable to connect to PostgreSQL database![/]\n\n"
                f"[bold]Target Host:[/] [cyan]{db_config.host}:{db_config.port}[/]\n"
                f"[bold]Target Database:[/] [cyan]{db_config.database}[/]\n"
                f"[bold]User:[/] [cyan]{db_config.user}[/]\n\n"
                f"[bold yellow]Error Details:[/] {message}\n\n"
                f"[bold white]How to start PostgreSQL:[/]\n"
                f"  1. Start local user instance: [bold green]./scripts/run_local_postgres.sh start[/]\n"
                f"  2. Or start Docker container: [bold green]docker compose up -d[/]\n"
                f"  3. Or start system service:   [bold green]sudo systemctl start postgresql[/]\n"
                f"  4. Or adjust credentials in:  [bold green].env[/]",
                title="[bold red]🐘 PostgreSQL Connection Required[/]",
                border_style="red",
                padding=(1, 2),
            )
        )

        has_local_postgres = bool(shutil.which("postgres"))
        options = ["[1] Retry connection"]
        if has_local_postgres:
            options.append("[2] Start local PostgreSQL server now (automatic)")
        options.append("[0] Exit")

        console.print("\n".join(options))
        console.print()

        valid_choices = ["1", "0"]
        if has_local_postgres:
            valid_choices.append("2")

        choice = Prompt.ask("[bold cyan]Choose an option[/]", choices=valid_choices, default="1")
        if choice == "0":
            sys.exit(1)
        elif choice == "2" and has_local_postgres:
            try_start_local_postgres()


def main() -> None:
    """CLI application entrypoint."""
    parser = argparse.ArgumentParser(description="PawHaven - Modular Pet Adoption Center with Rich & PostgreSQL")
    parser.add_argument("--init-db", action="store_true", help="Initialize PostgreSQL schema and exit")
    parser.add_argument("--seed", action="store_true", help="Seed default admin, adopter, and pet records")
    args = parser.parse_args()

    # Ensure PostgreSQL is ready
    if not ensure_postgres_connected():
        sys.exit(1)

    # Initialize schema and seed data
    try:
        init_db()
        seed_default_data()
    except Exception as exc:
        print_error(f"Failed to prepare PostgreSQL tables: {exc}")
        sys.exit(1)

    if args.init_db or args.seed:
        print_success("Database initialized and sample data seeded successfully.")
        sys.exit(0)

    # Start interactive Rich application
    try:
        router.run()
    except (KeyboardInterrupt, EOFError):
        console.print("\n\n[bold cyan]Session closed. Take care! 🐾[/]\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
