import logging
import os
import sqlite3
import uuid

INITIAL_TERMS = [
    {
        "name": "Microservice",
        "definition": (
            "A software development technique that structures an "
            "application as a collection of loosely coupled services."
        ),
        "source_url": "https://en.wikipedia.org/wiki/Microservices",
    },
    {
        "name": "Docker",
        "definition": (
            "A platform that uses OS-level virtualization to deliver "
            "software in packages called containers."
        ),
        "source_url": "https://en.wikipedia.org/wiki/Docker_(software)",
    },
    {
        "name": "gRPC",
        "definition": (
            "A high-performance, open-source universal RPC framework "
            "developed by Google."
        ),
        "source_url": "https://grpc.io/",
    },
    {
        "name": "API Gateway",
        "definition": (
            "An API management tool that sits between a client and a "
            "collection of backend services."
        ),
        "source_url": "https://aws.amazon.com/microservices/api-gateway/",
    },
]


def get_db_connection(db_path: str) -> sqlite3.Connection:
    """
    Establishes a connection to the SQLite database.
    Enables foreign key support for future use (e.g., relationships).
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: str):
    """
    Initializes the database. It creates the necessary tables with the correct
    schema and seeds the database with initial data if it's completely empty.
    This function is designed to be idempotent and safe to run on every startup.

    Args:
        db_path: The file path for the SQLite database.
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
                    definition TEXT NOT NULL,
                    source_url TEXT
                )
            """
            )

            cursor.execute("SELECT COUNT(*) FROM terms")
            term_count = cursor.fetchone()[0]

            if term_count == 0:
                logging.info("Database is empty. Seeding with initial terms.")
                for term in INITIAL_TERMS:
                    term_id = str(uuid.uuid4())
                    cursor.execute(
                        "INSERT INTO terms (id, name, definition, source_url) VALUES (?, ?, ?, ?)",
                        (term_id, term["name"], term["definition"], term["source_url"]),
                    )
                logging.info(f"{len(INITIAL_TERMS)} terms have been added.")
            else:
                logging.info("Database already contains data. Skipping seed.")

            conn.commit()

    except sqlite3.Error as e:
        logging.error(f"Database initialization failed: {e}")
        raise
