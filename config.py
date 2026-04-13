from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPOS_DIR = DATA_DIR / "repos"
INDEX_DIR = DATA_DIR / "indexes"
PLUGINS_DIR = BASE_DIR / "plugins"
DB_PATH = DATA_DIR / "memory.sqlite3"

for p in [DATA_DIR, REPOS_DIR, INDEX_DIR, PLUGINS_DIR]:
    p.mkdir(parents=True, exist_ok=True)
