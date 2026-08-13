from pathlib import Path
p = Path('database.py')
s = p.read_text(encoding='utf-8')
s = s.replace('if DATABASE_URL.startswith("sqlite"):', 'if str(DATABASE_URL).startswith("sqlite"):', 1)
s = s.replace('is_sqlite = DATABASE_URL.startswith("sqlite")', 'is_sqlite = str(DATABASE_URL).startswith("sqlite")', 1)
p.write_text(s, encoding='utf-8')
print('SQLAlchemy URL object compatibility fixed')
