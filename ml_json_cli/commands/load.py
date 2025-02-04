import click
import json
from ml_json_cli.db import get_db_connection
from rich.console import Console

console = Console()


@click.command()
@click.argument("file_path", type=click.Path(exists=True))
def load(file_path):
    """Load an Elastic ML JSON file into the database, tracking changes."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        with open(file_path, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        console.print(
            f"[red]Error: Failed to parse JSON file. Check file formatting: {file_path}[/red]"
        )
        return

    jobs = data if isinstance(data, list) else [data]

    for job in jobs:
        try:
            job_id = job["job"]["job_id"]
            description = job["job"].get("description", "")
            groups = ", ".join(job["job"].get("groups", []))
            analysis_config = json.dumps(job["job"].get("analysis_config", {}))
            analysis_limits = json.dumps(job["job"].get("analysis_limits", {}))

            try:
                datafeed_config = json.dumps(
                    job.get("datafeed", {}), ensure_ascii=False
                )
            except (TypeError, ValueError):
                console.print(
                    f"[red]Error: Unable to convert datafeed_config for job {job_id}. Storing empty JSON.[/red]"
                )
                datafeed_config = "{}"

            try:
                custom_settings = json.dumps(
                    job["job"].get("custom_settings", {}), ensure_ascii=False
                )
            except (TypeError, ValueError):
                console.print(
                    f"[red]Warning: Invalid custom_settings format for job {job_id}. Storing empty JSON.[/red]"
                )
                custom_settings = "{}"

            cursor.execute(
                """
                INSERT INTO jobs (job_id, description, groups, analysis_config, analysis_limits, datafeed_config, custom_settings)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                description=excluded.description,
                groups=excluded.groups,
                analysis_config=excluded.analysis_config,
                analysis_limits=excluded.analysis_limits,
                datafeed_config=excluded.datafeed_config,
                custom_settings=excluded.custom_settings,
                last_updated=CURRENT_TIMESTAMP
            """,
                (
                    job_id,
                    description,
                    groups,
                    analysis_config,
                    analysis_limits,
                    datafeed_config,
                    custom_settings,
                ),
            )

            conn.commit()

        except KeyError as e:
            console.print(
                f"[red]Error: Missing key {str(e)} in job data. Skipping entry.[/red]"
            )
            continue

    conn.close()
    console.print(
        f"[green]Successfully loaded {len(jobs)} job(s) from {file_path}.[/green]"
    )
