from __future__ import annotations
import hashlib, math, os, shutil, subprocess, tempfile
from pathlib import Path

def sha1_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()

def safe_read_text(path: Path, max_bytes: int = 300_000) -> str:
    try:
        data = path.read_bytes()
        if len(data) > max_bytes:
            data = data[:max_bytes]
        return data.decode("utf-8", errors="ignore")
    except Exception:
        return ""

def which(cmd: str):
    return shutil.which(cmd)

def run_python(code: str, timeout: int = 12) -> dict:
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "snippet.py"
        p.write_text(code, encoding="utf-8")
        try:
            proc = subprocess.run(["python", str(p)], capture_output=True, text=True, timeout=timeout)
            return {"success": proc.returncode == 0, "stdout": proc.stdout, "stderr": proc.stderr, "returncode": proc.returncode}
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}

def run_cpp(code: str, timeout: int = 20) -> dict:
    compiler = which("g++") or which("clang++")
    if not compiler:
        return {"success": False, "stdout": "", "stderr": "No C++ compiler found", "returncode": -1}
    with tempfile.TemporaryDirectory() as td:
        cpp = Path(td) / "snippet.cpp"
        exe = Path(td) / ("snippet.exe" if os.name == "nt" else "snippet.out")
        cpp.write_text(code, encoding="utf-8")
        try:
            comp = subprocess.run([compiler, str(cpp), "-std=c++17", "-O2", "-o", str(exe)],
                                  capture_output=True, text=True, timeout=timeout)
            if comp.returncode != 0:
                return {"success": False, "stdout": comp.stdout, "stderr": comp.stderr, "returncode": comp.returncode}
            run = subprocess.run([str(exe)], capture_output=True, text=True, timeout=timeout)
            return {"success": run.returncode == 0, "stdout": run.stdout, "stderr": run.stderr, "returncode": run.returncode}
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}
