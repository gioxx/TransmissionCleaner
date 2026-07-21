import datetime
import sqlite3
from dataclasses import dataclass
from contextlib import closing

from app.models import CleanupResult


@dataclass(frozen=True)
class CleanupRecord:
    id: int
    timestamp: datetime.datetime
    trigger: str
    deleted_count: int
    error_count: int
    log: str


class HistoryRepository:
    def __init__(self, path: str = "/config/cleanups.db") -> None:
        self.path = path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with closing(self._connect()) as db:
            with db:
                db.executescript("""
                CREATE TABLE IF NOT EXISTS cleanups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    trigger TEXT NOT NULL,
                    deleted_count INTEGER NOT NULL,
                    error_count INTEGER NOT NULL,
                    log TEXT NOT NULL
                );
                CREATE VIRTUAL TABLE IF NOT EXISTS cleanups_fts USING fts5(
                    log, trigger, content='cleanups', content_rowid='id'
                );
                CREATE TRIGGER IF NOT EXISTS cleanups_ai AFTER INSERT ON cleanups BEGIN
                    INSERT INTO cleanups_fts(rowid, log, trigger) VALUES (new.id, new.log, new.trigger);
                END;
                CREATE TRIGGER IF NOT EXISTS cleanups_ad AFTER DELETE ON cleanups BEGIN
                    INSERT INTO cleanups_fts(cleanups_fts, rowid, log, trigger) VALUES ('delete', old.id, old.log, old.trigger);
                END;
                """)
                db.execute("INSERT INTO cleanups_fts(cleanups_fts) VALUES ('rebuild')")

    def record(self, result: CleanupResult, trigger: str) -> int:
        if result.dry_run:
            raise ValueError("dry runs cannot be persisted")
        with closing(self._connect()) as db:
            with db:
                cursor = db.execute(
                "INSERT INTO cleanups(timestamp, trigger, deleted_count, error_count, log) VALUES (?, ?, ?, ?, ?)",
                (result.timestamp.isoformat(), trigger, result.deleted_count, result.error_count, result.to_log()),
                )
                return int(cursor.lastrowid)

    @staticmethod
    def _record(row: sqlite3.Row) -> CleanupRecord:
        return CleanupRecord(
            id=row["id"], timestamp=datetime.datetime.fromisoformat(row["timestamp"]),
            trigger=row["trigger"], deleted_count=row["deleted_count"],
            error_count=row["error_count"], log=row["log"],
        )

    def latest(self) -> CleanupRecord | None:
        with closing(self._connect()) as db:
            row = db.execute("SELECT * FROM cleanups ORDER BY timestamp DESC, id DESC LIMIT 1").fetchone()
        return self._record(row) if row else None

    def search(self, query: str = "", page: int = 1, page_size: int = 20) -> tuple[list[CleanupRecord], int]:
        page = max(1, page)
        page_size = min(100, max(1, page_size))
        with closing(self._connect()) as db:
            if query.strip():
                phrase = '"' + query.strip().replace('"', '""') + '"'
                where, params = "WHERE cleanups.id IN (SELECT rowid FROM cleanups_fts WHERE cleanups_fts MATCH ?)", (phrase,)
            else:
                where, params = "", ()
            total = db.execute(f"SELECT COUNT(*) FROM cleanups {where}", params).fetchone()[0]
            rows = db.execute(f"SELECT cleanups.* FROM cleanups {where} ORDER BY timestamp DESC, id DESC LIMIT ? OFFSET ?", (*params, page_size, (page - 1) * page_size)).fetchall()
        return [self._record(row) for row in rows], total
