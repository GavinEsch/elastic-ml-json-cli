import click
import json
import csv
from ml_json_cli.db import get_db_connection
from rich.console import Console

console = Console()


@click.command()
@click.option("--job-id", type=str, required=True, help="Export job history")
@click.option(
    "--format", type=click.Choice(["json", "csv"]), default="json", help="Export format"
)
@click.option(
    "--output",
    type=click.Path(),
    help="Output file (default: job_id.json or job_id.csv)",
)
def export(job_id, format, output):
    """Export job history to JSON or CSV."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT version, data, timestamp FROM job_versions WHERE job_id = ? ORDER BY timestamp DESC",
        (job_id,),
    )
    versions = cursor.fetchall()

    if not versions:
        console.print(
            f"[red]Error: No history found for job ID '{job_id}'. Check if the job exists.[/red]"
        )
        return

    if not output:
        output = f"{job_id}.{format}"

    try:
        if format == "json":
            with open(output, "w") as f:
                json.dump([dict(row) for row in versions], f, indent=4)
        elif format == "csv":
            with open(output, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Version", "Timestamp", "Data"])
                for row in versions:
                    writer.writerow([row["version"], row["timestamp"], row["data"]])
        console.print(f"[green]Exported job history to [bold]{output}[/bold][/green]")
    except Exception as e:
        console.print(f"[red]Error: Failed to write to {output}. {str(e)}[/red]")

    conn.close()
