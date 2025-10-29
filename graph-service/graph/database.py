import sqlite3
import logging
import os

def get_db_connection(db_path):
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path):
    """Initializes the database and creates the relationships table if it doesn't exist."""
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
        
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='relationships'")
    if cursor.fetchone() is None:
        logging.info("Creating 'relationships' table.")
        cursor.execute("""
            CREATE TABLE relationships (
                from_term_id TEXT NOT NULL,
                to_term_id TEXT NOT NULL,
                type INTEGER NOT NULL,
                PRIMARY KEY (from_term_id, to_term_id)
            )
        """)
    
    conn.commit()
    conn.close()