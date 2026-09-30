import sqlite3
import json

conn = sqlite3.connect("backend/data_intelligence.db")
c = conn.cursor()
c.execute("SELECT id, data_json, source_title FROM data_records ORDER BY extracted_timestamp DESC LIMIT 5")
rows = c.fetchall()
print(f"Total rows fetched: {len(rows)}")
for r in rows:
    rec_id, data_str, s_title = r
    data = json.loads(data_str) if isinstance(data_str, str) else data_str
    print("ID:", rec_id)
    print("Source Title:", s_title)
    print("job_title:", data.get("job_title"))
    print("company:", data.get("company"))
    print("location:", data.get("location"))
    print("experience_years:", data.get("experience_years"))
    print("skills:", data.get("skills"))
    print("---")
