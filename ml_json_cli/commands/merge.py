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
        elif strategy == "earliest":
            merged_data = versions[-1]["data"]
        elif strategy == "most_common":
            # Count occurrences of each version and use the most frequent one
            data_counts = {}
            for version in versions:
                data_counts[version["data"]] = data_counts.get(version["data"], 0) + 1
            merged_data = max(data_counts, key=data_counts.get)

        cursor.execute(
            """
            UPDATE jobs SET analysis_config = ?, last_updated = CURRENT_TIMESTAMP WHERE job_id = ?
        """,
            (merged_data, job_id),
        )

    conn.commit()
    conn.close()
    click.echo(f"Merged {len(jobs_to_merge)} jobs using strategy: {strategy}")
