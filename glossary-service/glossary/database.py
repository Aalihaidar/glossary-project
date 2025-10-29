import logging
import os
import sqlite3


def get_db_connection(db_path: str) -> sqlite3.Connection:
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(db_path)
    return conn


def init_db(db_path: str):
    """
    Initializes the glossary database. It creates the necessary 'terms' table
    with a UNIQUE constraint on the name field. This function is idempotent.
    """
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            logging.info("Ensuring 'terms' table exists with the correct schema.")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS terms (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    definition TEXT NOT NULL
                )
                """
            )
            conn.commit()
            logging.info("Glossary database schema is up to date.")
    except sqlite3.Error as e:
        logging.error(f"Glossary database initialization failed: {e}")
        raise
