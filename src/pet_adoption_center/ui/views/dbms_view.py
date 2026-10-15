"""DBMS Academic Suite UI views: Schema analysis, complex queries, query plan analyzer, and ACID lab."""

from __future__ import annotations

import json
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.prompt import Prompt, Confirm

from pet_adoption_center.services.dbms_service import dbms_service
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


def dbms_suite_menu() -> None:
    """Master entrypoint for the DBMS Course Project Explorer."""
    while True:
        clear_screen()
        print_banner()
        print_section("DBMS Academic Project Suite", "Relational Database Management System Principles in Action")

        menu = Table(box=None, show_header=False, padding=(0, 2))
        menu.add_column("Key", style="bold cyan", width=6)
        menu.add_column("Module", style="bold white", width=34)
        menu.add_column("DBMS Concepts Demonstrated", style="dim")

        menu.add_row("[1]", "Relational Schema & Normalization", "1NF, 2NF, 3NF Proof, FDs, Candidate Keys")
        menu.add_row("[2]", "Advanced SQL Queries Showcase", "Multi-table JOINs, GROUP BY/HAVING, Subqueries, Window Funcs")
        menu.add_row("[3]", "Interactive SQL & EXPLAIN ANALYZE", "Live query execution, cost estimation, Seq vs Index scans")
        menu.add_row("[4]", "ACID Transaction Demonstration", "Atomicity & Isolation test, COMMIT vs simulated ROLLBACK")
        menu.add_row("[5]", "Storage & Index Diagnostics", "pg_stat_user_tables, live/dead tuples, disk sizes, cache hits")
        menu.add_row("[6]", "Trigger-based Audit Trail", "Change Data Capture (CDC) via PostgreSQL PL/pgSQL triggers")
        menu.add_row("[0]", "Return to Main Menu", "")

        console.print(
            Panel(
                menu,
                title="[bold cyan]🎓 DBMS Laboratory Modules[/]",
                border_style="cyan",
                padding=(1, 2),
            )
        )
        console.print()

        choice = Prompt.ask("[bold cyan]Select laboratory module[/]", choices=["1", "2", "3", "4", "5", "6", "0"], default="1")

        if choice == "0":
            break
        elif choice == "1":
            view_schema_normalization()
        elif choice == "2":
            view_advanced_queries_catalog()
        elif choice == "3":
            view_interactive_sql_playground()
        elif choice == "4":
            view_acid_transaction_lab()
        elif choice == "5":
            view_storage_diagnostics()
        elif choice == "6":
            view_audit_trail()


def view_schema_normalization() -> None:
    """Displays relational schema formulas and normalization breakdown."""
    clear_screen()
    print_banner()
    print_section("Relational Schema & 3NF Normalization", "Database Design and Normal Form Mathematical Proofs")

    overview_text = dbms_service.get_relational_schema_overview()
    console.print(
        Panel(
            overview_text,
            border_style="cyan",
            title="[bold cyan]📐 Relational Schema (3NF)[/]",
            padding=(1, 2),
        )
    )
    pause()


def view_advanced_queries_catalog() -> None:
    """Allows selecting and executing academic SQL queries."""
    queries = dbms_service.get_prebuilt_queries()

    while True:
        clear_screen()
        print_banner()
        print_section("Advanced SQL Queries Showcase", "Relational Algebra mapped to SQL implementations")

        for idx, q in enumerate(queries, 1):
            console.print(f"[[bold cyan]{idx}[/]] [bold white]{q['title']}[/]")
            console.print(f"    [dim italic]{q['concept']}[/]\n")

        console.print("[bold cyan]Enter Query # to execute and view plan, or [bold]0[/] to return:[/]")
        choice = Prompt.ask("[bold cyan]Select query[/]", default="0")

        if choice in ("0", "back", "exit"):
            break

        if choice.isdigit() and 1 <= int(choice) <= len(queries):
            target = queries[int(choice) - 1]
            execute_and_display_query(target["title"], target["concept"], target["sql"])
        else:
            print_error("Invalid selection.")
            pause()


def execute_and_display_query(title: str, concept: str, sql: str) -> None:
    """Executes a query and displays syntax, tabular output, and execution plan."""
    clear_screen()
    print_banner()
    print_section(title, f"Concept: {concept}")

    # Display Syntax Highlighted SQL
    console.print(Panel(Syntax(sql, "sql", theme="monokai", line_numbers=True), title="[bold cyan]SQL Query[/]", border_style="cyan"))
    console.print()

    # Execute
    ok, headers, rows, elapsed_ms, err = dbms_service.execute_arbitrary_query(sql)
    if not ok:
        print_error(f"Execution Error: {err}")
        pause()
        return

    # Render Result Table
    table = Table(
        title=f"[bold green]Query Results[/] ({len(rows)} tuples, executed in {elapsed_ms:.2f} ms)",
        border_style="cyan",
        header_style="bold bright_white on grey23",
        show_lines=True,
    )
    for col in headers:
        table.add_column(col, style="white")

    for r in rows:
        table.add_row(*[str(val) if val is not None else "[dim]NULL[/]" for val in r])

    console.print(table)
    console.print()

    # Offer EXPLAIN ANALYZE
    if Confirm.ask("[bold cyan]Inspect PostgreSQL Query Execution Plan (EXPLAIN ANALYZE)?[/]", default=True):
        plan_ok, plan_lines, plan_err = dbms_service.explain_query_plan(sql)
        if plan_ok:
            plan_text = "\n".join(plan_lines)
            console.print()
            console.print(
                Panel(
                    Syntax(plan_text, "text", theme="ansi_dark"),
                    title="[bold yellow]⚡ Query Optimizer Execution Plan (EXPLAIN ANALYZE)[/]",
                    border_style="yellow",
                )
            )
        else:
            print_error(f"Explain Error: {plan_err}")

    pause()


def view_interactive_sql_playground() -> None:
    """Interactive SQL prompt allowing custom queries with timing and plan analysis."""
    while True:
        clear_screen()
        print_banner()
        print_section("Interactive SQL Query Console", "Run arbitrary SQL queries against PostgreSQL")

        console.print(
            Panel(
                "[dim]Type your SQL statement (SELECT queries recommended). Examples:\n"
                "  • SELECT * FROM pets WHERE status = 'available';\n"
                "  • SELECT * FROM v_adoption_ledger;\n"
                "  • SELECT species, count(*) FROM pets GROUP BY species;\n\n"
                "Type [bold cyan]exit[/] to return to the menu.[/]",
                border_style="grey42",
            )
        )
        console.print()

        raw_sql = Prompt.ask("[bold cyan]SQL>[/]").strip()
        if not raw_sql or raw_sql.lower() in ("exit", "quit", "0", "back"):
            break

        execute_and_display_query("Custom Query Execution", "Ad-hoc User SQL Statement", raw_sql)


def view_acid_transaction_lab() -> None:
    """Demonstrates ACID transaction properties with interactive commit and rollback scenarios."""
    clear_screen()
    print_banner()
    print_section("ACID Transaction Laboratory", "Demonstrating Atomicity, Consistency, Isolation, and Durability")

    console.print(
        Panel(
            "[bold white]ACID Guarantee in Relational DBMS:[/]\n"
            "  • [bold cyan]Atomicity:[/] All steps complete or none persist.\n"
            "  • [bold cyan]Consistency:[/] Integrity constraints (CHECK, FK) are never violated.\n"
            "  • [bold cyan]Isolation:[/] Concurrent transactions do not observe intermediate states.\n"
            "  • [bold cyan]Durability:[/] Once committed, changes survive system crashes.\n\n"
            "[italic]This simulator runs an atomic multi-step adoption workflow: row-locking, application creation, and payment recording.[/]",
            border_style="cyan",
            padding=(1, 2),
        )
    )
    console.print()

    console.print("[1] [bold green]Run Successful Transaction (COMMIT)[/]")
    console.print("[2] [bold red]Run Failing Transaction with Constraint Violation (ROLLBACK)[/]")
    console.print("[0] [bold]Back[/]")
    console.print()

    choice = Prompt.ask("[bold cyan]Select scenario[/]", choices=["1", "2", "0"], default="1")
    if choice == "0":
        return

    sim_failure = (choice == "2")
    res = dbms_service.demonstrate_acid_transaction(simulate_failure=sim_failure)

    console.print()
    border_color = "green" if res["success"] else "red"
    title_text = f"[bold {border_color}]Transaction Result: {res['status']}[/]"

    steps_render = "\n".join(res["steps"])
    console.print(Panel(steps_render, title=title_text, border_style=border_color, padding=(1, 2)))

    if res["success"]:
        print_success("Transaction committed! Both pet status and payment receipt atomically recorded.")
    else:
        print_warning("Integrity constraint violation caught! Transaction was completely rolled back. Database remains consistent.")
    pause()


def view_storage_diagnostics() -> None:
    """Displays PostgreSQL system catalog table statistics."""
    clear_screen()
    print_banner()
    print_section("PostgreSQL Physical Storage & Index Diagnostics", "System Catalog Inspection via pg_stat_user_tables")

    stats = dbms_service.get_database_catalog_stats()

    table = Table(border_style="cyan", show_lines=True, header_style="bold bright_white on grey23")
    table.add_column("Relation (Table)", style="bold cyan")
    table.add_column("Estimated Rows", justify="right", style="white")
    table.add_column("Disk Size", justify="right", style="bold gold3")
    table.add_column("Sequential Scans", justify="right", style="white")
    table.add_column("Index Scans", justify="right", style="bold green")
    table.add_column("Dead Tuples", justify="right", style="white")

    for s in stats:
        table.add_row(
            s["table_name"],
            str(s["estimated_row_count"]),
            str(s["total_size_on_disk"]),
            str(s["sequential_scans"]),
            str(s["index_scans"]),
            str(s["dead_tuples"]),
        )

    console.print(table)
    console.print()
    console.print("[dim]Tip: High index scans relative to sequential scans indicate effective B-Tree indexing strategy.[/]")
    pause()


def view_audit_trail() -> None:
    """Displays Change Data Capture (CDC) events recorded by PostgreSQL triggers."""
    clear_screen()
    print_banner()
    print_section("Database Audit Trail (PL/pgSQL Triggers)", "Automatic Change Data Capture from audit_logs relation")

    logs = dbms_service.get_audit_trail()

    if not logs:
        console.print(
            Panel(
                "[dim]No audit events recorded yet.\n"
                "Audit events are automatically generated by the 'trg_pets_audit' trigger whenever a pet is updated or removed.[/]",
                border_style="grey42",
            )
        )
        pause()
        return

    table = Table(border_style="cyan", show_lines=True, header_style="bold bright_white on grey23")
    table.add_column("Log ID", justify="right", style="bold cyan", width=8)
    table.add_column("Table", width=12)
    table.add_column("Action", justify="center", width=10)
    table.add_column("Record ID", justify="right", width=10)
    table.add_column("Changed By", width=14)
    table.add_column("Timestamp", justify="center", width=18)
    table.add_column("Changes (JSONB Payload)", style="italic", width=36)

    for l in logs:
        action_style = "bold yellow" if l["action_type"] == "UPDATE" else "bold red"
        act_badge = f"[{action_style}]{l['action_type']}[/]"
        time_str = l["changed_at"].strftime("%b %d, %H:%M:%S") if l["changed_at"] else "-"

        # Format old/new summary
        payload = ""
        if l.get("new_data") and l.get("old_data"):
            old_st = l["old_data"].get("status")
            new_st = l["new_data"].get("status")
            if old_st != new_st:
                payload = f"status: '{old_st}' -> '{new_st}'"
            else:
                payload = "Attributes updated"
        elif l.get("old_data"):
            payload = f"Deleted: {l['old_data'].get('name', 'Record')}"
        else:
            payload = "Change recorded"

        table.add_row(
            f"#{l['id']}",
            l["table_name"],
            act_badge,
            f"#{l['record_id']}" if l.get("record_id") else "-",
            str(l.get("changed_by") or "db_user"),
            time_str,
            payload,
        )

    console.print(table)
    pause()
