import os
import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.store.memory import InMemoryStore


def build_checkpointer(db_path: str) -> SqliteSaver:
    """Build SqliteSaver from langgraph-checkpoint-sqlite."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    return SqliteSaver(conn)


def build_store() -> InMemoryStore:
    """Build InMemoryStore for per-run fast blackboard."""
    return InMemoryStore()
