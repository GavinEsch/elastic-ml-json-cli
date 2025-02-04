import sqlite3
import os

DB_FILE = "ml_jobs.db"


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            description TEXT,
            groups TEXT,
            analysis_config TEXT,
            analysis_limits TEXT,
            datafeed_config TEXT,
            custom_settings TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS job_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT,
            version INTEGER,
            description TEXT,
            groups TEXT,
            analysis_config TEXT,
            analysis_limits TEXT,
            datafeed_config TEXT,
            custom_settings TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs (job_id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TRIGGER IF NOT EXISTS increment_version
        AFTER INSERT ON job_versions
        FOR EACH ROW
        WHEN (SELECT COUNT(*) FROM job_versions WHERE job_id = NEW.job_id) > 0
        BEGIN
            UPDATE job_versions SET version = (SELECT MAX(version) + 1 FROM job_versions WHERE job_id = NEW.job_id)
            WHERE id = NEW.id;
        END;
        """
    )

    conn.commit()
    conn.close()


if not os.path.exists(DB_FILE):
    init_db()
