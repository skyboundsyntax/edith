"""
Utility script to inspect records stored in backend/data_intelligence.db.
"""
import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data_intelligence.db"

def inspect():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT count(*) FROM data_records")
    total = c.fetchone()[0]
    print(f"Total data_records in database: {total}")
    c.execute("SELECT id, data_json, source_title FROM data_records ORDER BY extracted_timestamp DESC LIMIT 5")
    rows = c.fetchall()
    for r in rows:
        rec_id, data_str, s_title = r
        data = json.loads(data_str) if isinstance(data_str, str) else data_str
        print("ID:", rec_id)
        print("Source Title:", s_title)
        print("job_title:", data.get("job_title"))
        print("company:", data.get("company"))
        print("location:", str(data.get("location", "")).encode("ascii", errors="replace").decode())
        print("experience_years:", data.get("experience_years"))
        print("skills:", data.get("skills"))
        print("---")

if __name__ == "__main__":
    inspect()
