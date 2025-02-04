"""@DOCSTRING"""

import json
import click
from deepdiff import DeepDiff
from rich.console import Console
from rich.table import Table
from rich import box
from ml_json_cli.db import get_db_connection

console = Console()


@click.command()
@click.option(
    "--job-id", type=str, required=True, help="Compare versions of a specific job."
)
@click.option(
    "--version1",
    type=int,
    help="First version to compare (defaults to previous version).",
)
@click.option(
    "--version2",
    type=int,
    help="Second version to compare (defaults to latest version).",
)
@click.option(
    "--latest",
    is_flag=True,
    help="Compare any version with the current version in `jobs`.",
)
@click.option(
    "--show-json", is_flag=True, help="Show raw JSON diff instead of a table."
)
def compare(job_id, version1, version2, latest, show_json):
    """Compare two versions of a job. Defaults to latest and previous versions."""

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT description, groups, analysis_config, analysis_limits,
               datafeed_config, custom_settings
        FROM jobs WHERE job_id = ?
        """,
        (job_id,),
    )
    latest_job = cursor.fetchone()

    if not latest_job:
        console.print(f"[red]Error: No current version found for job '{job_id}'.[/red]")
        return

    # Fetch the most recent previous version from `job_versions`
    cursor.execute(
        """
        SELECT version, description, groups, analysis_config, analysis_limits,
               datafeed_config, custom_settings
        FROM job_versions
        WHERE job_id = ? ORDER BY version DESC LIMIT 1
        """,
        (job_id,),
    )
    previous_version = cursor.fetchone()

    if not previous_version and version1 is None and not latest:
        console.print(
            f"[red]Error: No previous versions found for job '{job_id}'. Cannot compare.[/red]"
        )
        return

    if version1 is None:
        version1 = previous_version["version"] if previous_version else None
    if version2 is None:
        version2 = "latest"

    if latest and version1 is None:
        console.print(
            "[red]Error: You must specify --version1 when using --latest.[/red]"
        )
        return
    if latest:
        version2 = "latest"

    if version1 != "latest":
        cursor.execute(
            """
            SELECT description, groups, analysis_config, analysis_limits,
                   datafeed_config, custom_settings
            FROM job_versions WHERE job_id = ? AND version = ?
            """,
            (job_id, version1),
        )
        version1_data = cursor.fetchone()
    else:
        version1_data = latest_job

    if version2 != "latest":
        cursor.execute(
            """
            SELECT description, groups, analysis_config, analysis_limits,
                   datafeed_config, custom_settings
            FROM job_versions WHERE job_id = ? AND version = ?
            """,
            (job_id, version2),
        )
        version2_data = cursor.fetchone()
    else:
        version2_data = latest_job

    if not version1_data or not version2_data:
        console.print(
            f"[red]Error: One or both versions not found for job '{job_id}'.[/red]"
        )
        return

    old_data = {key: version1_data[key] for key in version1_data.keys()}
    new_data = {key: version2_data[key] for key in version2_data.keys()}

    for key in [
        "analysis_config",
        "analysis_limits",
        "datafeed_config",
        "custom_settings",
    ]:
        try:
            old_data[key] = json.loads(old_data[key]) if old_data[key] else {}
            new_data[key] = json.loads(new_data[key]) if new_data[key] else {}
        except json.JSONDecodeError:
            console.print(f"[red]Error: Invalid JSON in field '{key}'[/red]")

    diff = DeepDiff(old_data, new_data, ignore_order=True)

    if not diff:
        console.print("[green]No changes detected.[/green]")
        return

    if show_json:
        console.print_json(json.dumps(diff, indent=2))
        conn.close()
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
            clean_field = field.replace("root['", "").replace("']", "")
            table.add_row(
                clean_field, str(change["old_value"]), str(change["new_value"])
            )

    if "dictionary_item_added" in diff:
        for field in diff["dictionary_item_added"]:
            clean_field = field.replace("root['", "").replace("']", "")
            table.add_row(clean_field, "-", str(new_data.get(clean_field, "-")))

    if "dictionary_item_removed" in diff:
        for field in diff["dictionary_item_removed"]:
            clean_field = field.replace("root['", "").replace("']", "")
            table.add_row(clean_field, str(old_data.get(clean_field, "-")), "-")

    console.print(table)
    conn.close()
