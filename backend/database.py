import sqlite3
from contextlib import contextmanager

DB_PATH = "load_manager.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS appliances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    wattage INTEGER NOT NULL,
    priority INTEGER NOT NULL,
    state TEXT NOT NULL CHECK(state IN ('running', 'off', 'shed'))
);

CREATE TABLE IF NOT EXISTS event_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    appliance_id INTEGER,
    appliance_name TEXT NOT NULL,
    action TEXT NOT NULL,
    reason TEXT NOT NULL
);
"""

def init_db():
    """Create table if they don't exist. Call once on startup."""
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
