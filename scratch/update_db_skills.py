import sqlite3
import json
import re

db_path = "data_intelligence.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT id, data_json FROM data_records")
rows = c.fetchall()
updated_count = 0

for rec_id, data_str in rows:
    if not data_str:
        continue
    try:
        data = json.loads(data_str) if isinstance(data_str, str) else data_str
        skills = data.get("skills")
        if skills:
            new_skills = []
            changed = False
            for s in skills:
                s_str = str(s).strip()
                if s_str.lower() == "ai":
                    new_skills.append("AI")
                    if s_str != "AI":
                        changed = True
                elif s_str.lower() == "ml":
                    new_skills.append("ML")
                    if s_str != "ML":
                        changed = True
                elif s_str.lower() == "llm":
                    new_skills.append("LLM")
                    if s_str != "LLM":
                        changed = True
                else:
                    fixed = re.sub(r'\bAi\b', 'AI', s_str, flags=re.IGNORECASE)
                    if fixed != s_str:
                        changed = True
                    new_skills.append(fixed)
            if changed:
                data["skills"] = new_skills
                c.execute("UPDATE data_records SET data_json = ? WHERE id = ?", (json.dumps(data), rec_id))
                updated_count += 1
    except Exception as e:
        print(f"Error updating {rec_id}: {e}")

conn.commit()
conn.close()
print(f"Updated {updated_count} records in database to use 'AI'!")
