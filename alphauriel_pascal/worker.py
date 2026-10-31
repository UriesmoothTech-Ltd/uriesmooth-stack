
import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from .config import POLL_SECONDS, LEASE_SECONDS
from .queue import claim, fail, finish, heartbeat
from .registry import run_app


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def process_one():
    job = claim(LEASE_SECONDS)

    if job is None:
        return False

    stop_event = threading.Event()
    lease_lost = threading.Event()
    heartbeat_interval = max(5, LEASE_SECONDS // 3)

    def maintain_lease():
        while not stop_event.wait(heartbeat_interval):
            try:
                if not heartbeat(job["id"], job["lease_token"]):
                    lease_lost.set()
                    logging.error(
                        "Lease lost for job %s",
                        job["id"],
                    )
                    return
            except Exception:
                logging.exception(
                    "Heartbeat failed for job %s",
                    job["id"],
                )

    heartbeat_thread = threading.Thread(
        target=maintain_lease,
        daemon=True,
    )
    heartbeat_thread.start()

    try:
        payload = json.loads(job["payload"])
        result = run_app(job["app_name"], payload)

        if lease_lost.is_set():
            logging.error(
                "Job %s finished after losing its lease; "
                "result not committed",
                job["id"],
            )

        elif finish(
            job["id"],
            result,
            job["lease_token"],
        ):
            logging.info(
                "Job %s completed (%s)",
                job["id"],
                job["app_name"],
            )

        else:
            logging.warning(
                "Job %s could not be marked complete",
                job["id"],
            )

    except Exception as exc:
        if not lease_lost.is_set():
            if not fail(job, exc):
                logging.warning(
                    "Job %s could not be marked failed",
                    job["id"],
                )

        logging.exception(
            "Job %s failed",
            job["id"],
        )

    finally:
        stop_event.set()
        heartbeat_thread.join(timeout=2)

    return True


def worker_loop(stop_event, poll_seconds, once=False):
    while not stop_event.is_set():
        worked = process_one()

        if once:
            return

        if not worked:
            stop_event.wait(poll_seconds)


def run_worker(once=False, poll_seconds=None, workers=1):
    workers = max(1, int(workers))
    delay = max(1, poll_seconds or POLL_SECONDS)

    stop_event = threading.Event()

    logging.info(
        "Alphauriel worker started with %s worker(s)",
        workers,
    )

    executor = ThreadPoolExecutor(
        max_workers=workers,
        thread_name_prefix="alphauriel",
    )

    futures = []

    try:
        for number in range(workers):
            futures.append(
                executor.submit(
                    worker_loop,
                    stop_event,
                    delay,
                    once,
                )
            )

        for future in futures:
            future.result()

    except KeyboardInterrupt:
        logging.info("Shutdown requested")

    finally:
        stop_event.set()
        executor.shutdown(wait=True, cancel_futures=True)
        logging.info("Alphauriel worker stopped")
