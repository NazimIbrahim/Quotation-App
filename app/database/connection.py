"""
Database connection management using Peewee ORM with SQLite.
"""
from peewee import SqliteDatabase
from app.config import DB_PATH

# Configure SQLite database with pragmas for performance and foreign key support
db = SqliteDatabase(
    str(DB_PATH),
    pragmas={
        'foreign_keys': 1,
        'journal_mode': 'wal',
        'cache_size': -1024 * 64,  # 64MB cache
    }
)

def get_db():
    return db
