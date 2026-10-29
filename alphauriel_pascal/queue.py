import json
import sqlite3
import uuid
from datetime import datetime, timezone
from .config import DATA_DIR, DB_PATH


def now():
    return datetime.now(timezone.utc).isoformat()


def connect():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            app_name TEXT NOT NULL,
            payload TEXT NOT NULL,
            status TEXT NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            max_attempts INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            result TEXT,
            error TEXT
        )
    """)
    db.commit()
    return db


def enqueue(app_name, payload=None, max_attempts=3):
    job_id = uuid.uuid4().hex
    stamp = now()
    with connect() as db:
        db.execute(
            """INSERT INTO jobs
            (id, app_name, payload, status, attempts, max_attempts,
             created_at, updated_at)
            VALUES (?, ?, ?, 'pending', 0, ?, ?, ?)""",
            (job_id, app_name, json.dumps(payload or {}), max_attempts,
             stamp, stamp),
        )
    return job_id


def claim():
    with connect() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute(
            "SELECT * FROM jobs WHERE status='pending' "
            "ORDER BY created_at LIMIT 1"
        ).fetchone()
        if row is None:
            db.commit()
            return None
        stamp = now()
        db.execute(
            "UPDATE jobs SET status='running', attempts=attempts+1, "
            "updated_at=? WHERE id=? AND status='pending'",
            (stamp, row["id"]),
        )
        db.commit()
        result = dict(row)
        result["attempts"] += 1
        return result


def finish(job_id, result):
    with connect() as db:
        db.execute(
            "UPDATE jobs SET status='succeeded', result=?, error=NULL, "
            "updated_at=? WHERE id=?",
            (json.dumps(result, default=str), now(), job_id),
        )


def fail(job, error):
    status = "pending" if job["attempts"] < job["max_attempts"] else "failed"
    with connect() as db:
        db.execute(
            "UPDATE jobs SET status=?, error=?, updated_at=? WHERE id=?",
            (status, str(error)[:4000], now(), job["id"]),
        )


def list_jobs(limit=20):
    with connect() as db:
        rows = db.execute(
            "SELECT id, app_name, status, attempts, created_at, error "
            "FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(row) for row in rows]
