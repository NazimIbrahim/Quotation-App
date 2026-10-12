"""
Database connection management using Peewee ORM with SQLite.
"""
from peewee import SqliteDatabase
from app.config import DB_PATH

# Configure SQLite database with optimal pragmas for maximum read/write performance
db = SqliteDatabase(
    str(DB_PATH),
    pragmas={
        'foreign_keys': 1,
        'journal_mode': 'wal',
        'synchronous': 1,          # Normal sync in WAL mode: crash-safe and 3x faster writes
        'cache_size': -1024 * 64,  # 64MB cache in RAM
        'temp_store': 2,           # Keep temporary tables and indices in memory
        'mmap_size': 268435456,    # 256MB memory-mapped I/O for instant reads
        'busy_timeout': 5000,      # Wait up to 5s to avoid lock contention
    }
)

def get_db():
    return db
