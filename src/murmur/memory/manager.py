import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiosqlite
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.store.memory import InMemoryStore


class MemoryManager:
    """
    Wraps SqliteSaver + InMemoryStore + long-term SQLite tables.
    Tracks tasks, locks, and history.
    """

    def __init__(self, checkpointer: SqliteSaver, store: InMemoryStore, db_path: str):
        self.checkpointer = checkpointer
        self.store = store
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def start(self) -> None:
        """Initialize connection and execute table creation schemas."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._conn = await aiosqlite.connect(self.db_path)

        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS task_runs (
                plan_id TEXT,
                session_id TEXT,
                command TEXT,
                task TEXT,
                status TEXT,
                created_at TEXT,
                completed_at TEXT,
                summary TEXT
            )
        """)

        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS file_summaries (
                file_path TEXT PRIMARY KEY,
                summary_text TEXT,
                embedding_json TEXT,
                last_updated TEXT
            )
        """)

        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                agent_id TEXT,
                description TEXT,
                rationale TEXT,
                timestamp TEXT
            )
        """)

        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS file_locks (
                file_path TEXT PRIMARY KEY,
                agent_id TEXT,
                session_id TEXT,
                locked_at TEXT
            )
        """)

        await self._conn.commit()

    async def stop(self) -> None:
        if self._conn:
            await self._conn.close()

    async def claim_file(self, path: str, agent_id: str, session_id: str) -> bool:
        """Atomic claim. Returns True if claimed, False if locked by another."""
        if not self._conn:
            return False

        async with self._conn.execute(
            "SELECT agent_id FROM file_locks WHERE file_path = ?", (path,)
        ) as cursor:
            row = await cursor.fetchone()

        if row and row[0] != agent_id:
            return False

        await self._conn.execute(
            "INSERT OR REPLACE INTO file_locks (file_path, agent_id, session_id, locked_at) VALUES (?, ?, ?, ?)",
            (path, agent_id, session_id, datetime.utcnow().isoformat()),
        )
        await self._conn.commit()
        return True

    async def release_file(self, path: str, agent_id: str, session_id: str) -> None:
        """Release the file if the agent owns it."""
        if not self._conn:
            return

        await self._conn.execute(
            "DELETE FROM file_locks WHERE file_path = ? AND agent_id = ? AND session_id = ?",
            (path, agent_id, session_id),
        )
        await self._conn.commit()

    async def release_all(self, session_id: str) -> None:
        if not self._conn:
            return

        await self._conn.execute(
            "DELETE FROM file_locks WHERE session_id = ?", (session_id,)
        )
        await self._conn.commit()

    async def save_task_run(self, data: Dict[str, Any]) -> None:
        if not self._conn:
            return

        await self._conn.execute(
            """INSERT INTO task_runs 
               (plan_id, session_id, command, task, status, created_at, completed_at, summary)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data.get("plan_id"),
                data.get("session_id"),
                data.get("command"),
                data.get("task"),
                data.get("status"),
                data.get("created_at"),
                data.get("completed_at"),
                data.get("summary"),
            ),
        )
        await self._conn.commit()

    async def list_task_runs(self) -> List[Dict[str, Any]]:
        self._conn.row_factory = aiosqlite.Row
        async with self._conn.execute(
            "SELECT * FROM task_runs ORDER BY created_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def save_file_summary(self, path: str, summary: str, embedding: str) -> None:
        await self._conn.execute(
            "INSERT OR REPLACE INTO file_summaries VALUES (?, ?, ?, ?)",
            (path, summary, embedding, datetime.utcnow().isoformat()),
        )
        await self._conn.commit()

    async def search_file_summaries(self, query: str) -> List[Dict[str, Any]]:
        # Dummy fuzzy mapping
        return []

    async def record_decision(self, data: Dict[str, Any]) -> None:
        await self._conn.execute(
            "INSERT INTO decisions VALUES (?, ?, ?, ?, ?, ?)",
            (
                data["id"],
                data["session_id"],
                data["agent_id"],
                data["description"],
                data["rationale"],
                datetime.utcnow().isoformat(),
            ),
        )
        await self._conn.commit()

    async def clear_all(self) -> None:
        await self._conn.execute("DELETE FROM task_runs")
        await self._conn.execute("DELETE FROM file_summaries")
        await self._conn.execute("DELETE FROM decisions")
        await self._conn.execute("DELETE FROM file_locks")
        await self._conn.commit()
