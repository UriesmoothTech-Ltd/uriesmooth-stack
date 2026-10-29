from datetime import datetime, timezone


def run(payload):
    return {
        "message": payload.get("message", "Hello from Uriesmooth Stack"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
