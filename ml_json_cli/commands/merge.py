"""@DOCSTRING"""

import click
from ml_json_cli.db import get_db_connection


@click.command()
@click.option(
    "--strategy",
    type=click.Choice(["latest", "earliest", "most_common"]),
    default="most_common",
    help="Conflict resolution strategy",
)
def merge(strategy):
    """Merge multiple job exports into a consolidated dataset."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT job_id, COUNT(*) FROM job_versions GROUP BY job_id HAVING COUNT(*) > 1"
    )
    jobs_to_merge = cursor.fetchall()

    if not jobs_to_merge:
        click.echo("No jobs found to merge.")
        return

    for job in jobs_to_merge:
        job_id = job["job_id"]
        cursor.execute(
            "SELECT data FROM job_versions WHERE job_id = ? ORDER BY timestamp DESC",
            (job_id,),
        )
        versions = cursor.fetchall()

        if strategy == "latest":
            merged_data = versions[0]["data"]
            database_merge(cursor, merged_data, job_id)
        elif strategy == "earliest":
            merged_data = versions[-1]["data"]
            database_merge(cursor, merged_data, job_id)
        elif strategy == "most_common":
            data_counts = {}
            for version in versions:
                data_counts[version["data"]] = data_counts.get(version["data"], 0) + 1
            merged_data = max(data_counts, key=data_counts.get)
            database_merge(cursor, merged_data, job_id)
    conn.commit()
    conn.close()
    click.echo(f"Merged {len(jobs_to_merge)} jobs using strategy: {strategy}")


def database_merge(cursor, merged_data, job_id):
    """Merge job data into the database.

    This function updates the `jobs` table with the merged data and
    updates the last_updated timestamp.
    """
    cursor.execute(
        """
            UPDATE jobs SET analysis_config = ?, last_updated = CURRENT_TIMESTAMP WHERE job_id = ?
        """,
        (merged_data, job_id),
    )
