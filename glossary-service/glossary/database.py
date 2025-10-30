import logging
import sqlite3


def create_shared_connection(db_path: str) -> sqlite3.Connection:
    """
    Establishes a long-lived, shared connection to the SQLite database.

    This is the recommended approach for multi-threaded applications like a
    gRPC server. It uses `check_same_thread=False` to allow the single
    connection to be shared across the gRPC worker threads.
    """
    try:
        # The check_same_thread=False is the key to allowing this single
        # connection to be used by all threads in the gRPC server's pool.
        conn = sqlite3.connect(db_path, check_same_thread=False)
        logging.info(f"Successfully created shared database connection to {db_path}")
        return conn
    except sqlite3.Error as e:
        logging.error(f"Failed to create shared database connection: {e}")
        raise


def init_db(conn: sqlite3.Connection):
    """
    Initializes the database schema using a shared connection.

    This function is idempotent and ensures the 'terms' table exists.
    """
    try:
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
