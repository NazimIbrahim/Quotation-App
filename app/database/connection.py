"""
Database connection management using Peewee ORM with SQLite or Cloud PostgreSQL.
Supports local high-performance SQLite WAL mode or seamless cloud synchronization.
"""
import os
import json
from pathlib import Path
from peewee import SqliteDatabase
from app.config import DB_PATH, DATA_DIR


def _get_configured_db():
    # 1. Environment variable takes highest priority
    db_url = os.environ.get("DATABASE_URL")

    # 2. Check local sync config file if env not set
    if not db_url:
        sync_cfg_path = DATA_DIR / "cloud_sync_config.json"
        if sync_cfg_path.exists():
            try:
                with open(sync_cfg_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    db_url = data.get("database_url")
            except Exception:
                db_url = None

    if db_url and db_url.strip():
        try:
            from playhouse.db_url import connect
            return connect(db_url.strip())
        except Exception:
            pass

    # 3. Default to local high-performance SQLite
    return SqliteDatabase(
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


db = _get_configured_db()


def get_db():
    return db
