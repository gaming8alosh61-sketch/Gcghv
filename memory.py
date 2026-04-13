from __future__ import annotations
import json, math, sqlite3, time
from pathlib import Path
from .config import DB_PATH, INDEX_DIR
from .utils import safe_read_text, sha1_text

class SQLiteMemory:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _init(self):
        with self._conn() as con:
            con.execute("CREATE TABLE IF NOT EXISTS memories (id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT, key TEXT, value TEXT, ts REAL)")
            con.commit()

    def put(self, kind: str, key: str, value):
        payload = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        with self._conn() as con:
            con.execute("INSERT INTO memories(kind, key, value, ts) VALUES(?,?,?,?)", (kind, key, payload, time.time()))
            con.commit()

    def recent(self, kind: str | None = None, limit: int = 20):
        q = "SELECT kind, key, value, ts FROM memories"
        args = []
        if kind:
            q += " WHERE kind=?"
            args.append(kind)
        q += " ORDER BY id DESC LIMIT ?"
        args.append(limit)
        with self._conn() as con:
            rows = con.execute(q, args).fetchall()
        return [{"kind": r[0], "key": r[1], "value": r[2], "ts": r[3]} for r in rows]

class SimpleIndex:
    def __init__(self, name: str = "projects", dim: int = 256):
        self.path = INDEX_DIR / f"{name}.json"
        self.dim = dim
        self.items = []
        if self.path.exists():
            try:
                self.items = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self.items = []

    def _vec(self, text: str):
        v = [0.0] * self.dim
        for tok in text.lower().split():
            h = int(sha1_text(tok), 16) % self.dim
            v[h] += 1.0
        n = math.sqrt(sum(x*x for x in v)) or 1.0
        return [x / n for x in v]

    def add(self, text: str, meta: dict):
        self.items.append({"text": text, "meta": meta, "vec": self._vec(text)})
        self.path.write_text(json.dumps(self.items, ensure_ascii=False), encoding="utf-8")

    def search(self, query: str, k: int = 5):
        q = self._vec(query)
        scored = []
        for item in self.items:
            s = sum(a*b for a, b in zip(q, item["vec"]))
            scored.append((s, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"score": s, "text": i["text"], "meta": i["meta"]} for s, i in scored[:k]]

def index_project(root: Path, index: SimpleIndex):
    exts = {".py",".cpp",".c",".h",".hpp",".txt",".md",".json",".yaml",".yml",".toml",".ini",".js",".ts",".cs"}
    count = 0
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in exts:
            continue
        txt = safe_read_text(p)
        if not txt.strip():
            continue
        chunk_size, overlap = 1200, 200
        step = max(1, chunk_size - overlap)
        for start in range(0, len(txt), step):
            chunk = txt[start:start+chunk_size]
            if not chunk.strip():
                continue
            index.add(chunk, {"path": str(p), "start": start, "sha1": sha1_text(chunk)})
            count += 1
    return count
