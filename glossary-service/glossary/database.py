import sqlite3
import logging
import uuid
import os

# --- Initial Data for Seeding ---
INITIAL_TERMS = [
    {
        "name": "Microservice",
        "definition": "A software development technique that structures an application as a collection of loosely coupled services.",
        "source_url": "https://en.wikipedia.org/wiki/Microservices"
    },
    {
        "name": "Docker",
        "definition": "A platform that uses OS-level virtualization to deliver software in packages called containers.",
        "source_url": "https://en.wikipedia.org/wiki/Docker_(software)"
    },
    {
        "name": "gRPC",
        "definition": "A high-performance, open-source universal RPC framework developed by Google.",
        "source_url": "https://grpc.io/"
    },
    {
        "name": "API Gateway",
        "definition": "An API management tool that sits between a client and a collection of backend services.",
        "source_url": "https://aws.amazon.com/microservices/api-gateway/"
    }
]

def get_db_connection(db_path):
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path):
    """Initializes the database, creates the table, and seeds it with initial data if empty."""
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
        
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='terms'")
    if cursor.fetchone() is None:
        logging.info("Creating 'terms' table.")
        cursor.execute("""
            CREATE TABLE terms (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                definition TEXT NOT NULL,
                source_url TEXT
            )
        """)
    
    # Check if table is empty before seeding
    cursor.execute("SELECT COUNT(*) FROM terms")
    if cursor.fetchone()[0] == 0:
        logging.info("Seeding the database with initial terms.")
        for term in INITIAL_TERMS:
            term_id = str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO terms (id, name, definition, source_url) VALUES (?, ?, ?, ?)",
                (term_id, term['name'], term['definition'], term['source_url'])
            )
        logging.info(f"{len(INITIAL_TERMS)} terms have been added.")

    conn.commit()
    conn.close()