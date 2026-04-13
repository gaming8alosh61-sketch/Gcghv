from __future__ import annotations
import json, subprocess, urllib.request
from pathlib import Path
from .utils import which, run_cpp, run_python

def run_ollama(prompt: str, model: str = "codellama:7b-instruct") -> str | None:
    url = "http://localhost:11434/api/generate"
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response")
    except Exception:
        return None

def git_status(path: str) -> str:
    if not which("git"):
        return "git not installed"
    try:
        out = subprocess.run(["git", "-C", path, "status", "--short"], capture_output=True, text=True, timeout=20)
        return out.stdout.strip() or "clean"
    except Exception as e:
        return str(e)

def git_commits(path: str, n: int = 10):
    if not which("git"):
        return []
    try:
        out = subprocess.run(["git", "-C", path, "log", f"-n{n}", "--pretty=format:%h|%an|%ad|%s", "--date=iso"],
                             capture_output=True, text=True, timeout=20)
        return [ln.strip() for ln in out.stdout.splitlines() if ln.strip()]
    except Exception:
        return []

def clone_repo(url: str, target_dir: str) -> str:
    if not which("git"):
        raise RuntimeError("git not installed")
    target = Path(target_dir)
    target.mkdir(parents=True, exist_ok=True)
    repo_name = url.rstrip("/").split("/")[-1].replace(".git", "") or "repo"
    path = target / repo_name
    if path.exists() and any(path.iterdir()):
        return str(path)
    subprocess.run(["git", "clone", url, str(path)], check=True)
    return str(path)
