import json
from pathlib import Path
from .config import APPS_DIR


def list_apps():
    found = []
    if not APPS_DIR.exists():
        return found
    for folder in sorted(APPS_DIR.iterdir()):
        manifest = folder / "app.json"
        if folder.is_dir() and not folder.name.startswith("_") and manifest.is_file():
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
                if data.get("name") and (folder / "app.py").is_file():
                    found.append({
                        "name": data["name"],
                        "description": data.get("description", ""),
                        "path": folder,
                    })
            except (ValueError, OSError):
                continue
    return found


def get_app(name):
    for app in list_apps():
        if app["name"] == name:
            return app
    raise ValueError(f"App not found: {name}")


def run_app(name, payload=None):
    import importlib.util
    app = get_app(name)
    module_path = app["path"] / "app.py"
    spec = importlib.util.spec_from_file_location(
        f"uriesmooth_app_{name}", module_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load app: {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, "run", None)):
        raise RuntimeError(f"App {name} must define run(payload)")
    return module.run(payload or {})
