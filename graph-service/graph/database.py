import logging
import sqlite3


def create_shared_connection(db_path: str) -> sqlite3.Connection:
    """
    Establishes a long-lived, shared connection to the SQLite database.
    This is the recommended approach for multi-threaded gRPC servers.
    """
    try:
        # check_same_thread=False allows this single connection to be used
        # by all threads in the gRPC server's thread pool.
        conn = sqlite3.connect(db_path, check_same_thread=False)
        logging.info(f"Successfully created shared database connection to {db_path}")
        return conn
    except sqlite3.Error as e:
        logging.error(f"Failed to create shared database connection: {e}")
        raise


def init_db(conn: sqlite3.Connection):
    """
    Initializes the graph database schema using a shared connection.
    This function is idempotent.
    """
    try:
        cursor = conn.cursor()
        logging.info("Ensuring 'relationships' table exists with the correct schema.")
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
        logging.info("Graph database schema is up to date.")
    except sqlite3.Error as e:
        logging.error(f"Graph database initialization failed: {e}")
        raise
