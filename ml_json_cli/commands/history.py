import click
from ml_json_cli.db import get_db_connection


@click.command()
@click.option(
    "--job-id", type=str, required=True, help="Show history of changes for a job."
)
def history(job_id):
    """Show job version history."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT version, timestamp FROM job_versions WHERE job_id = ? ORDER BY timestamp DESC",
        (job_id,),
    )
    versions = cursor.fetchall()

    if not versions:
        click.echo(f"No history found for job: {job_id}")
    else:
        click.echo(f"History for Job: {job_id}")
        for row in versions:
            click.echo(f"Version {row['version']} - {row['timestamp']}")

    conn.close()
