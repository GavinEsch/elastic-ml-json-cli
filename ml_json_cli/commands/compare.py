import click
import json
from ml_json_cli.db import get_db_connection
from deepdiff import DeepDiff
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()


@click.command()
@click.option(
    "--job-id", type=str, required=True, help="Compare versions of a specific job."
)
@click.option("--version1", type=int, required=True, help="First version to compare")
@click.option("--version2", type=int, required=True, help="Second version to compare")
def compare(job_id, version1, version2):
    """Compare two versions of a job."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT data FROM job_versions WHERE job_id = ? AND version = ?",
        (job_id, version1),
    )
    version1_data = cursor.fetchone()

    cursor.execute(
        "SELECT data FROM job_versions WHERE job_id = ? AND version = ?",
        (job_id, version2),
    )
    version2_data = cursor.fetchone()

    if not version1_data:
        console.print(
            f"[red]Error: Version {version1} not found for job '{job_id}'.[/red]"
        )
        return
    if not version2_data:
        console.print(
            f"[red]Error: Version {version2} not found for job '{job_id}'.[/red]"
        )
        return

    old_data = json.loads(version1_data["data"])
    new_data = json.loads(version2_data["data"])

    diff = DeepDiff(old_data, new_data, ignore_order=True)

    if not diff:
        console.print("[green]No changes detected.[/green]")
        return

    console.print(
        f"\n[bold yellow]Comparison: {job_id} (v{version1} → v{version2})[/bold yellow]"
    )

    table = Table(title="Changes Detected", box=box.SIMPLE)
    table.add_column("Field", style="cyan", min_width=25)
    table.add_column("Old Value", style="red", min_width=30)
    table.add_column("New Value", style="green", min_width=30)

    if "values_changed" in diff:
        for field, change in diff["values_changed"].items():
            table.add_row(
                field.replace("root[", "").replace("']", ""),
                str(change["old_value"]),
                str(change["new_value"]),
            )

    console.print(table)
    conn.close()
