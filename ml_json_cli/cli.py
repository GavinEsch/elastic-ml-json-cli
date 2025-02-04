import sys
import shlex
import readline
import argcomplete
import click
from rich.console import Console
from ml_json_cli.commands.load import load
from ml_json_cli.commands.search import search
from ml_json_cli.commands.compare import compare
from ml_json_cli.commands.export import export
from ml_json_cli.commands.history import history
from ml_json_cli.commands.merge import merge
from ml_json_cli.commands.undo import undo
from ml_json_cli.db import get_db_connection


console = Console()


@click.group()
def cli():
    """Elastic ML CLI - Manage and Compare ML Jobs"""
    pass


cli.add_command(load)
cli.add_command(search)
cli.add_command(compare)
cli.add_command(export)
cli.add_command(history)
cli.add_command(merge)
cli.add_command(undo)

argcomplete.autocomplete(cli)


def get_job_ids():
    """Fetches job IDs from the database for auto-completion."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT job_id FROM jobs")
    job_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return job_ids


def completer(text, state):
    """Auto-completes available commands and job IDs."""
    commands = cli.list_commands(ctx=None)
    job_ids = get_job_ids()
    options = commands + job_ids
    matches = [c for c in options if c.startswith(text)]
    return matches[state] if state < len(matches) else None


def setup_readline():
    """Enables history and tab completion in the interactive shell."""
    if sys.platform == "darwin" or sys.platform == "linux":
        readline.parse_and_bind("tab: complete")
        readline.set_completer(completer)
        readline.set_history_length(1000)


@cli.command()
def shell():
    """Start an interactive CLI session (mlcli>)"""
    console.print(
        "[bold green]Entering interactive mode. Type 'exit' or 'quit' to leave.[/bold green]"
    )

    setup_readline()

    while True:
        try:
            command = input("mlcli> ").strip()
            if command.lower() in {"exit", "quit"}:
                console.print("[bold yellow]Exiting mlcli...[/bold yellow]")
                break
            if command:
                cli.main(prog_name="mlcli", args=shlex.split(command))
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Use 'exit' or 'quit' to leave.[/bold yellow]")
        except EOFError:
            console.print("\n[bold yellow]Exiting mlcli...[/bold yellow]")
            break


if __name__ == "__main__":
    cli()
