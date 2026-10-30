
import json
from datetime import datetime, timedelta, timezone

import alphauriel_pascal.queue as queue

from alphauriel_pascal.registry import list_apps, run_app
from alphauriel_pascal.queue import (
    enqueue,
    claim,
    finish,
    list_jobs,
)


def test_hello_app_is_registered():
    assert any(
        app["name"] == "hello"
        for app in list_apps()
    )


def test_hello_app_runs():
    result = run_app(
        "hello",
        {"message": "Termux test"},
    )

    assert result["message"] == "Termux test"
    assert "timestamp" in result


def test_job_queue_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(queue, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        queue,
        "DB_PATH",
        tmp_path / "jobs.sqlite3",
    )

    job_id = enqueue(
        "hello",
        {"message": "queued test"},
        max_attempts=2,
    )

    job = claim()

    assert job is not None
    assert job["id"] == job_id

    assert (
        json.loads(job["payload"])["message"]
        == "queued test"
    )

    assert finish(
        job_id,
        {"ok": True},
        job["lease_token"],
    ) is True

    matching = [
        item
        for item in list_jobs()
        if item["id"] == job_id
    ]

    assert matching[0]["status"] == "succeeded"


def test_expired_job_is_recovered_and_reclaimed(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(queue, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        queue,
        "DB_PATH",
        tmp_path / "jobs.sqlite3",
    )

    job_id = queue.enqueue(
        "hello",
        {"message": "recovery test"},
        2,
    )

    first = queue.claim(lease_seconds=30)

    assert first["id"] == job_id

    old_token = first["lease_token"]

    stale_time = (
        datetime.now(timezone.utc)
        - timedelta(minutes=5)
    ).isoformat()

    with queue.connect() as db:
        db.execute(
            "UPDATE jobs SET updated_at=? WHERE id=?",
            (stale_time, job_id),
        )

    assert queue.recover_stale_jobs(30) == 1

    second = queue.claim(lease_seconds=30)

    assert second["id"] == job_id
    assert second["attempts"] == 2
    assert second["lease_token"] != old_token

    assert queue.finish(
        job_id,
        {"wrong": True},
        old_token,
    ) is False

    assert queue.finish(
        job_id,
        {"ok": True},
        second["lease_token"],
    ) is True


def test_expired_job_exhausts_attempts(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(queue, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        queue,
        "DB_PATH",
        tmp_path / "jobs.sqlite3",
    )

    job_id = queue.enqueue(
        "hello",
        {},
        1,
    )

    job = queue.claim(lease_seconds=30)

    assert job["id"] == job_id

    stale_time = (
        datetime.now(timezone.utc)
        - timedelta(minutes=5)
    ).isoformat()

    with queue.connect() as db:
        db.execute(
            "UPDATE jobs SET updated_at=? WHERE id=?",
            (stale_time, job_id),
        )

    assert queue.recover_stale_jobs(30) == 1

    matching = [
        item
        for item in queue.list_jobs()
        if item["id"] == job_id
    ]

    assert matching[0]["status"] == "failed"
