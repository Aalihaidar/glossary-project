import logging
import os
import sqlite3


def get_db_connection(db_path: str) -> sqlite3.Connection:
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(db_path)
    return conn


def init_db(db_path: str):
    """
    Initializes the graph database. It creates the relationships table with a
    professional composite primary key if it doesn't exist. This function is
    idempotent and safe to run on every application startup.

    Args:
        db_path: The file path for the SQLite database.
    """
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            logging.info(
                "Ensuring 'relationships' table exists with the correct schema."
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS relationships (
                    from_term_id TEXT NOT NULL,
                    to_term_id TEXT NOT NULL,
                    type INTEGER NOT NULL,
                    PRIMARY KEY (from_term_id, to_term_id, type)
                )
                """
            )
            conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Graph database initialization failed: {e}")
        raise
