import sqlite3
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / "images.db"

def init_db():
    if DB_PATH.exists():
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create tables and indexes
    cursor.execute('PRAGMA foreign_keys = ON')

    cursor.execute('''
        CREATE TABLE images (
            image_id TEXT PRIMARY KEY,
            mime_type TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            original_file_name TEXT NOT NULL
        )
    ''')
    conn.commit()

    cursor.execute('''
        CREATE TABLE tags (
            image_id TEXT NOT NULL,
            tag TEXT NOT NULL,
            FOREIGN KEY(image_id) REFERENCES images(image_id) ON DELETE CASCADE,
            PRIMARY KEY (image_id, tag)
        )
    ''')

    cursor.execute('CREATE INDEX idx_tags_tag ON tags(tag)')
    cursor.execute('CREATE INDEX idx_tags_image_id ON tags(image_id)')
    conn.commit()
    conn.close()

def get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
