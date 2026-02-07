"""Database migrations for Reverie."""

import sqlite3

# Current schema version
SCHEMA_VERSION = 1

# Schema creation SQL
SCHEMA_SQL = """
-- Campaigns table
CREATE TABLE IF NOT EXISTS campaigns (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    character_id TEXT,
    current_location_id TEXT,
    playtime_seconds INTEGER DEFAULT 0
);

-- Characters table
CREATE TABLE IF NOT EXISTS characters (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL,
    name TEXT NOT NULL,
    data TEXT NOT NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
);

-- World elements table
CREATE TABLE IF NOT EXISTS world_elements (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL,
    element_type TEXT NOT NULL,
    name TEXT NOT NULL,
    data TEXT NOT NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
);

-- NPCs table
CREATE TABLE IF NOT EXISTS npcs (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL,
    name TEXT NOT NULL,
    location_id TEXT,
    data TEXT NOT NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
);

-- Quests table
CREATE TABLE IF NOT EXISTS quests (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    data TEXT NOT NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
);

-- Events table
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    description TEXT NOT NULL,
    data TEXT NOT NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
);

-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_characters_campaign ON characters(campaign_id);
CREATE INDEX IF NOT EXISTS idx_world_elements_campaign ON world_elements(campaign_id);
CREATE INDEX IF NOT EXISTS idx_world_elements_type ON world_elements(element_type);
CREATE INDEX IF NOT EXISTS idx_npcs_campaign ON npcs(campaign_id);
CREATE INDEX IF NOT EXISTS idx_npcs_location ON npcs(location_id);
CREATE INDEX IF NOT EXISTS idx_quests_campaign ON quests(campaign_id);
CREATE INDEX IF NOT EXISTS idx_quests_status ON quests(status);
CREATE INDEX IF NOT EXISTS idx_events_campaign ON events(campaign_id);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
"""


def get_schema_version(conn: sqlite3.Connection) -> int:
    """Get current schema version from database."""
    try:
        cursor = conn.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
        row = cursor.fetchone()
        return row[0] if row else 0
    except sqlite3.OperationalError:
        return 0


def set_schema_version(conn: sqlite3.Connection, version: int) -> None:
    """Set schema version in database."""
    conn.execute("INSERT OR REPLACE INTO schema_version (version) VALUES (?)", (version,))
    conn.commit()


def run_migrations(conn: sqlite3.Connection) -> int:
    """Run all pending migrations.
    
    Returns:
        Final schema version
    """
    current_version = get_schema_version(conn)
    
    if current_version < 1:
        # Initial schema creation
        conn.executescript(SCHEMA_SQL)
        set_schema_version(conn, 1)
        current_version = 1
    
    # Future migrations would go here:
    # if current_version < 2:
    #     run_migration_2(conn)
    #     set_schema_version(conn, 2)
    #     current_version = 2
    
    return current_version


def reset_schema(conn: sqlite3.Connection) -> None:
    """Drop all tables and recreate schema.
    
    WARNING: This destroys all data!
    """
    # Get all table names
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    tables = [row[0] for row in cursor.fetchall()]
    
    # Drop all tables
    for table in tables:
        conn.execute(f"DROP TABLE IF EXISTS {table}")
    
    conn.commit()
    
    # Recreate schema
    run_migrations(conn)
