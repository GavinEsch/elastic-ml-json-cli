import click
import json
import sqlite3
from datetime import datetime
from fuzzywuzzy import fuzz
from ml_json_cli.db import get_db_connection
from rich.table import Table
from rich.console import Console

console = Console()


@click.command()
@click.option("--job-id", type=str, help="Search by job ID (case-insensitive)")
@click.option("--fuzzy", type=str, help="Fuzzy search on job ID")
@click.option("--group", type=str, help="Filter by job group (case-insensitive)")
@click.option("--bucket-span", type=str, help="Filter by bucket span (e.g., '15m')")
@click.option("--influencers", type=str, help="Filter by influencers (comma-separated)")
@click.option(
    "--created-by", type=str, help="Filter by 'created_by' field in custom settings"
)
@click.option("--model-memory-limit", type=str, help="Filter by model memory limit")
@click.option(
    "--detector-function", type=str, help="Filter by detector function (e.g., 'rare')"
)
@click.option(
    "--start-date", type=str, help="Filter jobs updated after this date (YYYY-MM-DD)"
)
@click.option(
    "--end-date", type=str, help="Filter jobs updated before this date (YYYY-MM-DD)"
)
@click.option(
    "--page", type=int, default=1, help="Page number for pagination (default: 1)"
)
@click.option("--limit", type=int, default=10, help="Results per page (default: 10)")
def search(
    job_id,
    fuzzy,
    group,
    bucket_span,
    influencers,
    created_by,
    model_memory_limit,
    detector_function,
    start_date,
    end_date,
    page,
    limit,
):
    """Search ML jobs in the database with enhanced filtering, fuzzy search, and pagination."""
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT job_id, description, groups,
               analysis_config, analysis_limits, datafeed_config,
               custom_settings, last_updated
        FROM jobs
        WHERE 1=1
    """
    params = []

    if job_id:
        query += " AND LOWER(job_id) LIKE ?"
        params.append(f"%{job_id.lower()}%")

    if group:
        query += " AND LOWER(groups) LIKE ?"
        params.append(f"%{group.lower()}%")

    if start_date:
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            query += " AND last_updated >= ?"
            params.append(start_date)
        except ValueError:
            console.print(
                "[red]Error: Invalid --start-date format. Use YYYY-MM-DD.[/red]"
            )
            return

    if end_date:
        try:
            datetime.strptime(end_date, "%Y-%m-%d")
            query += " AND last_updated <= ?"
            params.append(end_date)
        except ValueError:
            console.print(
                "[red]Error: Invalid --end-date format. Use YYYY-MM-DD.[/red]"
            )
            return

    query += " ORDER BY last_updated DESC LIMIT ? OFFSET ?"
    params.extend((limit, (page - 1) * limit))
    cursor.execute(query, tuple(params))
    jobs = cursor.fetchall()

    if not jobs:
        console.print("[red]No jobs found matching your search criteria.[/red]")
        conn.close()
        return

    table = Table(title=f"ML Jobs (Page {page})", show_lines=True)
    table.add_column("Job ID", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Groups", style="white")
    table.add_column("Bucket Span", style="white")
    table.add_column("Influencers", style="white")
    table.add_column("Model Memory", style="white")
    table.add_column("Detector Function", style="white")
    table.add_column("Created By", style="white")
    table.add_column("Last Updated", style="white")

    results = []

    for job in jobs:
        bucket_span_value = "-"
        influencers_value = "-"
        detector_function_value = "-"
        created_by_value = "-"

        try:
            analysis_config = (
                json.loads(job["analysis_config"]) if job["analysis_config"] else {}
            )
            bucket_span_value = analysis_config.get("bucket_span", "-")
            influencers_value = ", ".join(analysis_config.get("influencers", []))
            if analysis_config.get("detectors"):
                detector_function_value = analysis_config["detectors"][0].get(
                    "function", "-"
                )
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

        try:
            analysis_limits = (
                json.loads(job["analysis_limits"]) if job["analysis_limits"] else {}
            )
            model_memory_limit_value = analysis_limits.get("model_memory_limit", "-")
        except json.JSONDecodeError:
            console.print(
                f"[red]Warning: Invalid JSON in analysis_limits for job {job['job_id']}[/red]"
            )

        if detector_function and detector_function_value != detector_function:
            continue

        if fuzzy and fuzz.partial_ratio(fuzzy.lower(), job["job_id"].lower()) < 80:
            continue

        results.append(
            (
                job["job_id"],
                job["description"],
                job["groups"],
                bucket_span_value,
                influencers_value,
                model_memory_limit_value,
                detector_function_value,
                created_by_value,
                job["last_updated"],
            )
        )

    for row in results:
        table.add_row(*row)

    console.print(table)
    conn.close()
