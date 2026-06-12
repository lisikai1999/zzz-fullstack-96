"""SQLite database setup and connection management."""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "observatory.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    elevation REAL DEFAULT 0,
    timezone TEXT NOT NULL DEFAULT 'UTC',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS dso_catalog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    catalog TEXT NOT NULL,
    designation TEXT NOT NULL,
    common_name TEXT,
    ra_j2000 REAL NOT NULL,
    dec_j2000 REAL NOT NULL,
    magnitude REAL,
    object_type TEXT NOT NULL,
    size_arcmin REAL,
    constellation TEXT,
    UNIQUE(catalog, designation)
);

CREATE TABLE IF NOT EXISTS equipment_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    focal_length_mm REAL NOT NULL,
    sensor_width_mm REAL NOT NULL,
    sensor_height_mm REAL NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);
"""


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
