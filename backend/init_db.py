# Optional: SQLite DB init for future expansion
# Run: python init_db.py
import sqlite3

DB_PATH = 'fortune.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Example: create a table for requests (not used in v1.1 MVP)
    c.execute('''
    CREATE TABLE IF NOT EXISTS analysis_requests (
        id TEXT PRIMARY KEY,
        name TEXT,
        gender TEXT,
        calendar_type TEXT,
        birth_date TEXT,
        birth_time TEXT,
        has_birth_time INTEGER,
        precision_mode TEXT,
        start_date TEXT,
        end_date TEXT,
        timezone TEXT,
        created_at TEXT
    )
    ''')
    conn.commit()
    conn.close()
    print('DB initialized.')

if __name__ == '__main__':
    init_db()
