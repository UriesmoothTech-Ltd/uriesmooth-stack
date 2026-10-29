import logging
import time
from .config import MAX_ATTEMPTS, POLL_SECONDS
from .queue import claim, fail, finish
from .registry import run_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def process_one():
    job = claim()
    if job is None:
        return False
    try:
        result = run_app(job["app_name"], __import__("json").loads(job["payload"]))
        finish(job["id"], result)
        logging.info("Job %s completed (%s)", job["id"], job["app_name"])
    except Exception as exc:
        fail(job, exc)
        logging.exception("Job %s failed", job["id"])
    return True


def run_worker(once=False, poll_seconds=None):
    delay = max(1, poll_seconds or POLL_SECONDS)
    logging.info("Alphauriel worker started")
    while True:
        worked = process_one()
        if once:
            return
        if not worked:
            time.sleep(delay)
