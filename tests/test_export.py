import pytest
import json
import os
from click.testing import CliRunner
from ml_json_cli.commands.export import export
from ml_json_cli.db import get_db_connection


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def setup_test_data():
    """Setup test database with sample job versions."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM jobs")
    cursor.execute("DELETE FROM job_versions")

    cursor.execute(
        "INSERT INTO jobs (job_id, description) VALUES ('test_job', 'Test description')"
    )
    cursor.execute(
        "INSERT INTO job_versions (job_id, version, data) VALUES ('test_job', 1, '{\"bucket_span\": \"15m\"}')"
    )
    cursor.execute(
        "INSERT INTO job_versions (job_id, version, data) VALUES ('test_job', 2, '{\"bucket_span\": \"10m\"}')"
    )

    conn.commit()
    conn.close()


def test_export_json(runner, setup_test_data):
    """Test exporting job history to JSON."""
    output_file = "test_job.json"

    result = runner.invoke(
        export, ["--job-id", "test_job", "--format", "json", "--output", output_file]
    )

    assert result.exit_code == 0
    assert "Exported job history to test_job.json" in result.output

    with open(output_file, "r") as f:
        data = json.load(f)

    assert len(data) == 2
    assert data[0]["version"] == 1
    assert data[1]["version"] == 2

    os.remove(output_file)


def test_export_csv(runner, setup_test_data):
    """Test exporting job history to CSV."""
    output_file = "test_job.csv"

    result = runner.invoke(
        export, ["--job-id", "test_job", "--format", "csv", "--output", output_file]
    )

    assert result.exit_code == 0
    assert "Exported job history to test_job.csv" in result.output

    with open(output_file, "r") as f:
        lines = f.readlines()

    assert len(lines) == 3  # Header + 2 data rows
    assert "Version,Timestamp,Data" in lines[0]

    os.remove(output_file)
