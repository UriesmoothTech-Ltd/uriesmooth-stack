# Uriesmooth Stack

Android-first automation core for Uriesmooth Ltd.

## Setup in Termux

```bash
./scripts/setup.sh
.venv/bin/pytest
.venv/bin/alphauriel list
.venv/bin/alphauriel run hello
```

## Background jobs

```bash
.venv/bin/alphauriel enqueue hello
.venv/bin/alphauriel worker
```

In another Termux session:

```bash
.venv/bin/alphauriel jobs
```

The worker processes persistent SQLite jobs and retries failures up to the configured attempt limit. The scheduler is a simple interval loop; keep Android battery restrictions in mind.
