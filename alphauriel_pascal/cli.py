import argparse
import json
import time

from .config import MAX_ATTEMPTS
from .registry import list_apps, run_app
from .queue import enqueue, list_jobs, queue_stats
from .worker import run_worker


def main():
    parser = argparse.ArgumentParser(prog="alphauriel")
    commands = parser.add_subparsers(
        dest="command",
        required=True,
    )

    commands.add_parser(
        "list",
        help="List registered apps",
    )

    run_cmd = commands.add_parser(
        "run",
        help="Run an app immediately",
    )
    run_cmd.add_argument("name")
    run_cmd.add_argument("--payload", default="{}")

    job_cmd = commands.add_parser(
        "enqueue",
        help="Queue an app for background work",
    )
    job_cmd.add_argument("name")
    job_cmd.add_argument("--payload", default="{}")

    worker_cmd = commands.add_parser(
        "worker",
        help="Start background worker",
    )
    worker_cmd.add_argument("--once", action="store_true")
    worker_cmd.add_argument("--poll", type=int, default=None)
    worker_cmd.add_argument("--workers", type=int, default=1)

    commands.add_parser(
        "jobs",
        help="Show recent jobs",
    )

    commands.add_parser(
        "stats",
        help="Show queue statistics",
    )

    schedule_cmd = commands.add_parser(
        "schedule",
        help="Enqueue an app repeatedly",
    )
    schedule_cmd.add_argument("name")
    schedule_cmd.add_argument(
        "--every",
        type=int,
        required=True,
        help="Interval in seconds",
    )
    schedule_cmd.add_argument("--payload", default="{}")

    args = parser.parse_args()

    try:
        if args.command == "list":
            for app in list_apps():
                print(
                    f'{app["name"]}: {app["description"]}'
                )

        elif args.command == "run":
            result = run_app(
                args.name,
                json.loads(args.payload),
            )
            print(json.dumps(result, indent=2))

        elif args.command == "enqueue":
            job_id = enqueue(
                args.name,
                json.loads(args.payload),
                MAX_ATTEMPTS,
            )
            print(f"Queued job: {job_id}")

        elif args.command == "worker":
            if args.poll is not None and args.poll < 1:
                parser.error("--poll must be at least 1 second")

            if args.workers < 1:
                parser.error("--workers must be at least 1")

            run_worker(args.once, args.poll, args.workers)

        elif args.command == "jobs":
            for job in list_jobs():
                print(json.dumps(job, default=str))

        elif args.command == "stats":
            stats = queue_stats()
            print("ALPHAURIEL QUEUE STATISTICS")
            print("==========================")
            for status, total in stats.items():
                print(f"{status.capitalize():12} {total}")

        elif args.command == "schedule":
            if args.every < 1:
                parser.error("--every must be at least 1 second")

            payload = json.loads(args.payload)

            while True:
                job_id = enqueue(
                    args.name,
                    payload,
                    MAX_ATTEMPTS,
                )
                print(job_id, flush=True)
                time.sleep(args.every)

    except (ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
