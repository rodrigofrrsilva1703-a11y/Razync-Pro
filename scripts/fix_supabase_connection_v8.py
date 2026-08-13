from pathlib import Path

p = Path('database.py')
s = p.read_text(encoding='utf-8')

s = s.replace('from sqlalchemy.exc import IntegrityError\n', 'from sqlalchemy.exc import IntegrityError\nfrom sqlalchemy.engine import URL\n', 1)

start = s.index('def _resolve_database_url() -> str:')
end = s.index('\n\nDATABASE_URL = _resolve_database_url()', start)
new = '''def _secret(name: str) -> str:\n    value = os.getenv(name, "").strip()\n    if value:\n        return value\n    try:\n        import streamlit as st\n        return str(st.secrets.get(name, "")).strip()\n    except Exception:\n        return ""\n\n\ndef _resolve_database_url():\n    # Preferred production path: keep only the password in Streamlit Secrets.\n    # URL.create safely escapes special characters such as @, #, %, / and :.\n    password = _secret("SUPABASE_DB_PASSWORD")\n    if password:\n        return URL.create(\n            drivername="postgresql+psycopg",\n            username="postgres.etimfgenlludorrftapb",\n            password=password,\n            host="aws-0-sa-east-1.pooler.supabase.com",\n            port=5432,\n            database="postgres",\n            query={"sslmode": "require"},\n        )\n\n    configured = _secret("DATABASE_URL")\n    if configured:\n        if configured.startswith("postgres://"):\n            configured = "postgresql+psycopg://" + configured[len("postgres://"):]\n        elif configured.startswith("postgresql://") and "+psycopg" not in configured:\n            configured = "postgresql+psycopg://" + configured[len("postgresql://"):]\n        return configured\n\n    fallback = Path(tempfile.gettempdir()) / "razync_pro.db"\n    return f"sqlite:///{fallback.as_posix()}"'''

s = s[:start] + new + s[end:]
p.write_text(s, encoding='utf-8')
print('Supabase connection hardened')
