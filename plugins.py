from __future__ import annotations
from pathlib import Path
import importlib.util

def load_plugins(folder: Path):
    plugins = []
    folder.mkdir(parents=True, exist_ok=True)
    for py in folder.glob("*.py"):
        try:
            spec = importlib.util.spec_from_file_location(py.stem, py)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore
            if hasattr(mod, "register"):
                plugins.append(mod.register())
        except Exception:
            pass
    return plugins
