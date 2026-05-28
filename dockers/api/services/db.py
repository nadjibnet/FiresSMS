"""SQLite connection handling for the Gammu SMSD database."""
import os
import sqlite3
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("GAMMU_DB_PATH", "/var/lib/gammu/smsd.db")


def get_db_connection():
    """Return a SQLite connection to the Gammu DB (rows accessible by name)."""
    if not os.path.exists(DB_PATH):
        logger.error("SQLite database does not exist: %s", DB_PATH)
        raise FileNotFoundError(f"Database not found at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
