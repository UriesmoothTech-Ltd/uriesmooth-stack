import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APPS_DIR = PROJECT_ROOT / "apps"
DATA_DIR = Path(
    os.environ.get("ALPHAURIEL_HOME", str(Path.home() / ".uriesmooth-stack"))
).expanduser()
DB_PATH = DATA_DIR / "jobs.sqlite3"
POLL_SECONDS = max(1, int(os.environ.get("ALPHAURIEL_POLL_SECONDS", "3")))
MAX_ATTEMPTS = max(1, int(os.environ.get("ALPHAURIEL_MAX_ATTEMPTS", "3")))
LEASE_SECONDS = max(30, int(os.environ.get("ALPHAURIEL_LEASE_SECONDS", "600")))
