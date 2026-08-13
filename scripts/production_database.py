from pathlib import Path

p = Path("database.py")
s = p.read_text(encoding="utf-8")

if "import tempfile" not in s:
    s = s.replace("import os\n", "import os\nimport tempfile\nfrom pathlib import Path\n", 1)

old = 'DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///razync_pro.db")\n\nengine_kwargs: dict[str, Any] = {"pool_pre_ping": True}\n'
new = '''def _resolve_database_url() -> str:\n    configured = os.getenv("DATABASE_URL", "").strip()\n    if not configured:\n        try:\n            import streamlit as st\n            configured = str(st.secrets.get("DATABASE_URL", "")).strip()\n        except Exception:\n            configured = ""\n    if configured:\n        if configured.startswith("postgres://"):\n            configured = "postgresql+psycopg://" + configured[len("postgres://"):]\n        elif configured.startswith("postgresql://") and "+psycopg" not in configured:\n            configured = "postgresql+psycopg://" + configured[len("postgresql://"):]\n        return configured\n    fallback = Path(tempfile.gettempdir()) / "razync_pro.db"\n    return f"sqlite:///{fallback.as_posix()}"\n\n\nDATABASE_URL = _resolve_database_url()\n\nengine_kwargs: dict[str, Any] = {"pool_pre_ping": True}\n'''
if old in s:
    s = s.replace(old, new, 1)

if "def database_runtime_info" not in s:
    marker = "metadata = MetaData()\n"
    addition = '''metadata = MetaData()\n\n\ndef database_runtime_info() -> dict[str, Any]:\n    is_sqlite = DATABASE_URL.startswith("sqlite")\n    return {\n        "backend": "SQLite temporário" if is_sqlite else "PostgreSQL",\n        "persistent": not is_sqlite,\n        "production_ready": not is_sqlite,\n    }\n'''
    s = s.replace(marker, addition, 1)

p.write_text(s, encoding="utf-8")
print("database production configuration applied")

# trigger production database workflow
