import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def inspect(wf_id="wf_3a401c167d"):
    url = f"http://127.0.0.1:8000/api/datasets?workflow_id={wf_id}"
    resp = urllib.request.urlopen(url)
    data = json.loads(resp.read().decode())
    records = data.get("records", [])
    print(f"Total records in {wf_id}: {len(records)}\n")
    for idx, r in enumerate(records[:6]):
        d = r.get("data", {})
        print(f"[{idx+1}] TITLE:        {d.get('job_title')}")
        print(f"    COMPANY:      {d.get('company')}")
        print(f"    LOCATION:     {d.get('location')}")
        print(f"    EXPERIENCE:   {d.get('experience_years')}")
        print(f"    REQUIREMENTS: {d.get('requirements')}")
        desc = d.get('description', '') or ''
        print(f"    DESCRIPTION:  {desc[:140]}...")
        print(f"    APPLY LINK:   {d.get('apply_link')}")
        print(f"    SOURCE:       {d.get('platform_source')}")
        print("-" * 50)

if __name__ == "__main__":
    inspect()
