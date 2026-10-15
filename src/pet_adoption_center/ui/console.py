"""Rich console wrapper and UI component helpers."""

from __future__ import annotations

import os
from typing import Any, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt
from rich.rule import Rule
from rich.text import Text
from rich import box

from .themes import CUSTOM_THEME, BANNER_ART
from ..auth.session import session

console = Console(theme=CUSTOM_THEME)


def clear_screen() -> None:
    """Clears the terminal screen."""
    os.system("clear" if os.name != "nt" else "cls")


def print_banner() -> None:
    """Renders the top ASCII banner and status bar."""
    console.print(BANNER_ART)
    render_status_bar()


def render_status_bar() -> None:
    """Displays user status, role badge, and quick tips."""
    if session.is_authenticated and session.current_user:
        user = session.current_user
        role_badge = (
            "[bold black on yellow] 🛡️ ADMIN [/]"
            if user.is_admin
            else "[bold black on cyan] 🐾 ADOPTER [/]"
        )
        status_text = (
            f"👤 Logged in as: [bold white]{user.full_name}[/] (@{user.username})  "
            f"{role_badge}  | 📧 {user.email}"
        )
        border_style = "gold3" if user.is_admin else "cyan"
    else:
        status_text = (
            "👤 Mode: [italic dim]Guest (Browsing)[/]  |  "
            "💡 Tip: Log in to submit adoption applications or manage the shelter"
        )
        border_style = "grey58"

    console.print(
        Panel(
            status_text,
            box=box.ROUNDED,
            style="on grey11",
            border_style=border_style,
            padding=(0, 1),
        )
    )
    console.print()


def print_section(title: str, subtitle: Optional[str] = None) -> None:
    """Renders a section separator rule."""
    console.print()
    console.print(Rule(f"[bold cyan]✦ {title.upper()} ✦[/]", style="cyan"))
    if subtitle:
        console.print(f"[dim]{subtitle}[/]", justify="center")
    console.print()


def pause(message: str = "Press Enter to continue...") -> None:
    """Pauses for user confirmation."""
    console.print()
    Prompt.ask(f"[dim]{message}[/]", default="", show_default=False)


def print_success(message: str) -> None:
    console.print(f"\n[bold green]✔[/] {message}")


def print_error(message: str) -> None:
    console.print(f"\n[bold red]✖[/] {message}")


def print_warning(message: str) -> None:
    console.print(f"\n[bold yellow]⚠[/] {message}")


def print_info(message: str) -> None:
    console.print(f"\n[bold cyan]ℹ[/] {message}")
