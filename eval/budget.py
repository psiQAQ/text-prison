"""Durable admission control. Failed and interrupted calls consume the budget."""
from __future__ import annotations

import sqlite3
import time
import uuid
from pathlib import Path


class BudgetExceeded(RuntimeError):
    pass


class Budget:
    def __init__(self, path: Path, max_calls: int = 128, max_seconds: float = 14400):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path, self.max_calls, self.max_seconds = path, max_calls, max_seconds
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS calls (id TEXT PRIMARY KEY, label TEXT, started REAL, '
                       'elapsed REAL, timeout REAL, status TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS limits (id INTEGER PRIMARY KEY, calls INTEGER, seconds REAL)')
            db.execute('INSERT OR IGNORE INTO limits VALUES (1,?,?)', (max_calls, max_seconds))
            fixed = db.execute('SELECT calls,seconds FROM limits WHERE id=1').fetchone()
            if fixed != (max_calls, max_seconds):
                raise ValueError('Budget limits are frozen; use a new experiment for different limits')

    def connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def snapshot(self) -> dict:
        with self.connect() as db:
            rows = db.execute('SELECT elapsed,timeout,status FROM calls').fetchall()
        # An interrupted invocation without a receipt is conservatively charged its timeout.
        return {'calls': len(rows), 'seconds': sum(e if e is not None else t for e, t, _ in rows),
                'pending': sum(s == 'running' for _, _, s in rows),
                'max_calls': self.max_calls, 'max_seconds': self.max_seconds}

    def claim(self, label: str, timeout: float = 300) -> tuple[str, float]:
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            rows = db.execute('SELECT elapsed,timeout,status FROM calls').fetchall()
            if any(s == 'running' for _, _, s in rows):
                raise BudgetExceeded('An unfinished call exists; inspect it and recover explicitly before resuming')
            used = sum(e if e is not None else t for e, t, _ in rows)
            remaining = self.max_seconds - used
            if len(rows) >= self.max_calls or remaining <= 0:
                raise BudgetExceeded('Experiment call/time budget exhausted')
            allotted = min(timeout, remaining)
            call_id = uuid.uuid4().hex
            db.execute('INSERT INTO calls VALUES (?,?,?,?,?,?)',
                       (call_id, label, time.time(), None, allotted, 'running'))
        return call_id, allotted

    def finish(self, call_id: str, elapsed: float, status: str) -> None:
        if elapsed < 0 or status == 'running':
            raise ValueError('Invalid completion receipt')
        with self.connect() as db:
            cursor = db.execute('UPDATE calls SET elapsed=?,status=? WHERE id=? AND status=?',
                                (elapsed, status, call_id, 'running'))
            if cursor.rowcount != 1:
                raise ValueError('Call already finished or unknown')

    def recover_interrupted(self, call_id: str) -> None:
        """Caller must first establish that the recorded child process is no longer running."""
        with self.connect() as db:
            cursor = db.execute("UPDATE calls SET status='interrupted',elapsed=timeout WHERE id=? AND status='running'", (call_id,))
            if cursor.rowcount != 1:
                raise ValueError('No running call with this ID')
