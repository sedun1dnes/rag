from sqlalchemy import text
from .db import Base, engine

# Columns that may be missing from tables created before a schema update.
# Format: (table, column, DDL type)
_MIGRATIONS = [
    ("knowledge_bases", "created_at", "TIMESTAMP DEFAULT NOW()"),
    ("chats", "created_at", "TIMESTAMP DEFAULT NOW()"),
    ("chats", "updated_at", "TIMESTAMP DEFAULT NOW()"),
]


def create_tables():
    from .entities.knowledge_base import KnowledgeBase  # noqa: F401
    from .entities.document import Document  # noqa: F401
    from .entities.chat import Chat  # noqa: F401
    from .entities.message import Message  # noqa: F401
    Base.metadata.create_all(engine)
    _apply_migrations()


def _apply_migrations():
    with engine.connect() as conn:
        for table, column, col_def in _MIGRATIONS:
            conn.execute(text(
                f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {col_def}"
            ))
        conn.commit()
