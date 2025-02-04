import click
import json
from ml_json_cli.db import get_db_connection
from rich.table import Table
from rich.console import Console

console = Console()


@click.command()
@click.option("--job-id", type=str, help="Search by job ID (case-insensitive)")
@click.option("--group", type=str, help="Filter by job group (case-insensitive)")
@click.option("--bucket-span", type=str, help="Filter by bucket span (e.g., '15m')")
@click.option("--influencers", type=str, help="Filter by influencers (comma-separated)")
@click.option(
    "--created-by", type=str, help="Filter by 'created_by' field in custom settings"
)
@click.option(
    "--start-date", type=str, help="Filter jobs updated after this date (YYYY-MM-DD)"
)
@click.option(
    "--end-date", type=str, help="Filter jobs updated before this date (YYYY-MM-DD)"
)
@click.option("--limit", type=int, default=10, help="Limit results (default: 10)")
def search(
    job_id, group, bucket_span, influencers, created_by, start_date, end_date, limit
):
    """Search ML jobs in the database with enhanced filtering."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT job_id, description, groups,
               analysis_config, datafeed_config,
               custom_settings, last_updated
        FROM jobs
        WHERE 1=1
    """
    params = []

    # Filtering by Job ID
    if job_id:
        query += " AND LOWER(job_id) LIKE ?"
        params.append(f"%{job_id.lower()}%")

    # Filtering by Group
    if group:
        query += " AND LOWER(groups) LIKE ?"
        params.append(f"%{group.lower()}%")

    # Filtering by Date Range
    if start_date:
        query += " AND last_updated >= ?"
        params.append(start_date)

    if end_date:
        query += " AND last_updated <= ?"
        params.append(end_date)

    query += " ORDER BY last_updated DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, tuple(params))
    jobs = cursor.fetchall()

    if not jobs:
        console.print("[red]No jobs found matching your search criteria.[/red]")
        conn.close()
        return

    jobs = [dict(job) for job in jobs]  # Convert sqlite3.Row to dictionary

    table = Table(title="ML Jobs", show_lines=True)
    table.add_column("Job ID", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Groups", style="white")
    table.add_column("Bucket Span", style="white")
    table.add_column("Influencers", style="white")
    table.add_column("Created By", style="white")
    table.add_column("Last Updated", style="white")

    for job in jobs:
        bucket_span_value = "-"
        influencers_value = "-"
        created_by_value = "-"

        # Extract values from JSON fields safely
        try:
            analysis_config = (
                json.loads(job["analysis_config"]) if job["analysis_config"] else {}
            )
            bucket_span_value = analysis_config.get("bucket_span", "-")
            influencers_value = ", ".join(analysis_config.get("influencers", []))
        except json.JSONDecodeError:
            console.print(
                f"[red]Warning: Invalid JSON in analysis_config for job {job['job_id']}[/red]"
            )

        try:
            custom_settings = (
                json.loads(job["custom_settings"]) if job["custom_settings"] else {}
            )
            created_by_value = custom_settings.get("created_by", "-")
        except json.JSONDecodeError:
            console.print(
                f"[red]Warning: Invalid JSON in custom_settings for job {job['job_id']}[/red]"
            )

        # Apply bucket_span and influencers filtering after JSON parsing
        if bucket_span and bucket_span_value != bucket_span:
            continue
        if influencers and not set(influencers.split(",")).issubset(
            set(influencers_value.split(", "))
        ):
            continue
        if created_by and created_by_value != created_by:
            continue

        table.add_row(
            job["job_id"],
            job["description"],
            job["groups"],
            bucket_span_value,
            influencers_value,
            created_by_value,
            job["last_updated"],
        )

    console.print(table)
    conn.close()
