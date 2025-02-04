import click
import sqlite3
from ml_json_cli.db import get_db_connection
from rich.console import Console

console = Console()


@click.command()
@click.argument("job_id", type=str)
def undo(job_id):
    """Undo the last update to a job, rolling back to the previous version."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM job_versions WHERE job_id = ? ORDER BY version DESC LIMIT 1
    """,
        (job_id,),
    )

    job_version = cursor.fetchone()

    if not job_version:
        console.print(
            f"[red]No previous version found for job {job_id}. Cannot undo.[/red]"
        )
        conn.close()
        return

    cursor.execute(
        """
        DELETE FROM jobs WHERE job_id = ?
    """,
        (job_id,),
    )

    cursor.execute(
        """
        INSERT INTO jobs (job_id, description, groups, analysis_config, analysis_limits,
                          datafeed_config, custom_settings, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """,
        (
            job_version["job_id"],
            job_version["description"],
            job_version["groups"],
            job_version["analysis_config"],
            job_version["analysis_limits"],
            job_version["datafeed_config"],
            job_version["custom_settings"],
        ),
    )

    cursor.execute(
        """
        DELETE FROM job_versions WHERE job_id = ? AND version = ?
    """,
        (job_id, job_version["version"]),
    )

    conn.commit()
    conn.close()

    console.print(
        f"[green]Successfully rolled back {job_id} to version {job_version['version']}.[/green]"
    )
