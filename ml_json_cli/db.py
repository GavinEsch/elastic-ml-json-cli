import sqlite3
import os

DB_FILE = "ml_jobs.db"


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Enables column access by name
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Main jobs table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            description TEXT,
            groups TEXT,
            analysis_config TEXT,
            datafeed_config TEXT,
            custom_settings TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Job versions table for tracking changes
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS job_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT,
            version INTEGER,
            data TEXT,
            custom_settings TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs (job_id)
        )
    """
    )

    conn.commit()
    conn.close()


if not os.path.exists(DB_FILE):
    init_db()
