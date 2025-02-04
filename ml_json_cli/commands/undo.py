import click
from ml_json_cli.db import get_db_connection


@click.command()
def undo():
    """Revert the last merge operation."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM job_versions WHERE timestamp = (SELECT MAX(timestamp) FROM job_versions)"
    )
    conn.commit()
    conn.close()

    click.echo("Last merge operation has been reverted.")
