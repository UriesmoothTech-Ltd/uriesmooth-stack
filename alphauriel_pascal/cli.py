import argparse
import json
import time
from .config import MAX_ATTEMPTS
from .registry import list_apps, run_app
from .queue import enqueue, list_jobs
from .worker import run_worker


def main():
    parser = argparse.ArgumentParser(prog="alphauriel")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("list", help="List registered apps")

    run_cmd = commands.add_parser("run", help="Run an app immediately")
    run_cmd.add_argument("name")
    run_cmd.add_argument("--payload", default="{}")

    job_cmd = commands.add_parser("enqueue", help="Queue an app for background work")
    job_cmd.add_argument("name")
    job_cmd.add_argument("--payload", default="{}")

    worker_cmd = commands.add_parser("worker", help="Start background worker")
    worker_cmd.add_argument("--once", action="store_true")
    worker_cmd.add_argument("--poll", type=int, default=None)

    commands.add_parser("jobs", help="Show recent jobs")

    schedule_cmd = commands.add_parser("schedule", help="Enqueue an app repeatedly")
    schedule_cmd.add_argument("name")
    schedule_cmd.add_argument("--every", type=int, required=True,
                              help="Interval in seconds")
    schedule_cmd.add_argument("--payload", default="{}")

    args = parser.parse_args()

    try:
        if args.command == "list":
            for app in list_apps():
                print(f'{app["name"]}: {app["description"]}')
        elif args.command == "run":
            print(json.dumps(run_app(args.name, json.loads(args.payload)), indent=2))
        elif args.command == "enqueue":
            job_id = enqueue(args.name, json.loads(args.payload), MAX_ATTEMPTS)
            print(f"Queued job: {job_id}")
        elif args.command == "worker":
            run_worker(args.once, args.poll)
        elif args.command == "jobs":
            for job in list_jobs():
                print(json.dumps(job, default=str))
        elif args.command == "schedule":
            if args.every < 1:
                parser.error("--every must be at least 1 second")
            while True:
                print(enqueue(args.name, json.loads(args.payload), MAX_ATTEMPTS),
                      flush=True)
                time.sleep(args.every)
    except (ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
