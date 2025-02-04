import click
import argcomplete
from ml_json_cli.commands import load, search, compare, history, merge, export, undo
from rich.console import Console

console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Elastic ML JSON CLI - A tool for searching, analyzing, and tracking changes in exported ML jobs."""
    if ctx.invoked_subcommand is not None:
        return
    console.print(
        "[bold cyan]ML JSON CLI Interactive Mode. Type 'help' for commands or 'exit' to quit.[/bold cyan]\n"
    )
    while True:
        try:
            command = input("mlcli> ").strip()
            lower_command = command.lower()
            if lower_command in ["exit", "quit"]:
                console.print("[bold yellow]Exiting CLI...[/bold yellow]")
                break
            if lower_command == "help":
                cli.main(["--help"])
            elif command:
                cli.main(prog_name="mlcli", args=command.split())
        except KeyboardInterrupt:
            console.print(
                "\n[bold red]Keyboard Interrupt detected. Exiting CLI...[/bold red]"
            )
            break


cli.add_command(load.load)
cli.add_command(search.search)
cli.add_command(compare.compare)
cli.add_command(history.history)
cli.add_command(merge.merge)
cli.add_command(export.export)
cli.add_command(undo.undo)

argcomplete.autocomplete(cli)

if __name__ == "__main__":
    cli()
