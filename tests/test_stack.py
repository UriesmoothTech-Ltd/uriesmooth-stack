import json
from alphauriel_pascal.registry import list_apps, run_app
from alphauriel_pascal.queue import enqueue, claim, finish, list_jobs


def test_hello_app_is_registered():
    assert any(app["name"] == "hello" for app in list_apps())


def test_hello_app_runs():
    result = run_app("hello", {"message": "Termux test"})
    assert result["message"] == "Termux test"
    assert "timestamp" in result


def test_job_queue_round_trip():
    job_id = enqueue("hello", {"message": "queued test"}, max_attempts=2)
    job = claim()
    assert job is not None
    assert job["id"] == job_id
    assert json.loads(job["payload"])["message"] == "queued test"
    finish(job_id, {"ok": True})
    matching = [item for item in list_jobs() if item["id"] == job_id]
    assert matching[0]["status"] == "succeeded"
