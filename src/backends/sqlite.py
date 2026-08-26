"""SQLite backend for local development and testing."""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
from typing import Any, Dict, List, Optional

from src.backends.base import Backend

logger = logging.getLogger("taskforge.backend.sqlite")


class SQLiteBackend(Backend):
    """Queue backend backed by a local SQLite database."""

    def __init__(self, db_path: str = "taskforge.db") -> None:
        self.db_path = db_path
        self._local = threading.local()
        self._init_schema()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_schema(self) -> None:
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS taskforge_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                queue_name TEXT NOT NULL,
                message_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                enqueued_at REAL NOT NULL,
                status TEXT DEFAULT 'pending'
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_queue_status
            ON taskforge_messages(queue_name, status, priority DESC)
        """)
        conn.commit()
        conn.close()
        logger.info("SQLite schema initialized at %s", self.db_path)

    def connect(self) -> None:
        self._get_conn()
        logger.info("SQLite backend connected (%s)", self.db_path)

    def disconnect(self) -> None:
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
        logger.info("SQLite backend disconnected")

    def push(self, queue_name: str, message: Dict[str, Any], priority: int = 0) -> None:
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO taskforge_messages
               (queue_name, message_id, payload, priority, enqueued_at, status)
               VALUES (?, ?, ?, ?, ?, 'pending')""",
            (
                queue_name,
                message.get("message_id", ""),
                json.dumps(message),
                priority,
                time.time(),
            ),
        )
        conn.commit()
        logger.debug("Pushed to SQLite queue %s", queue_name)

    def pop(self, queue_name: str) -> Optional[Dict[str, Any]]:
        conn = self._get_conn()
        cursor = conn.execute(
            """SELECT id, payload FROM taskforge_messages
               WHERE queue_name = ? AND status = 'pending'
               ORDER BY priority DESC, enqueued_at ASC
               LIMIT 1""",
            (queue_name,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        conn.execute(
            "UPDATE taskforge_messages SET status = 'processing' WHERE id = ?",
            (row["id"],),
        )
        conn.commit()
        return json.loads(row["payload"])

    def peek(self, queue_name: str, count: int = 10) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        cursor = conn.execute(
            """SELECT payload FROM taskforge_messages
               WHERE queue_name = ? AND status = 'pending'
               ORDER BY priority DESC, enqueued_at ASC
               LIMIT ?""",
            (queue_name, count),
        )
        return [json.loads(row["payload"]) for row in cursor.fetchall()]

    def length(self, queue_name: str) -> int:
        conn = self._get_conn()
        cursor = conn.execute(
            """SELECT COUNT(*) as cnt FROM taskforge_messages
               WHERE queue_name = ? AND status = 'pending'""",
            (queue_name,),
        )
        return cursor.fetchone()["cnt"]

    def purge(self, queue_name: str) -> int:
        conn = self._get_conn()
        cursor = conn.execute(
            "DELETE FROM taskforge_messages WHERE queue_name = ? AND status = 'pending'",
            (queue_name,),
        )
        conn.commit()
        return cursor.rowcount

    def ack(self, queue_name: str, message_id: str) -> bool:
        conn = self._get_conn()
        conn.execute(
            """UPDATE taskforge_messages SET status = 'completed'
               WHERE queue_name = ? AND message_id = ?""",
            (queue_name, message_id),
        )
        conn.commit()
        return True

    def nack(self, queue_name: str, message_id: str) -> bool:
        conn = self._get_conn()
        conn.execute(
            """UPDATE taskforge_messages SET status = 'pending'
               WHERE queue_name = ? AND message_id = ?""",
            (queue_name, message_id),
        )
        conn.commit()
        return True