import urllib.request
import json
import time
import sys

# Ensure UTF-8 output on Windows terminal
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_URL = "http://127.0.0.1:8000/api"

def test_workflow_execution(prompt):
    print(f"\n==========================================")
    print(f"Executing workflow for: '{prompt}'")
    print(f"==========================================")
    req_data = json.dumps({
        "prompt": prompt,
        "confidence_threshold": 50.0
    }).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/workflows",
        data=req_data,
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req)
    wf = json.loads(resp.read().decode())
    wf_id = wf["id"]
    print(f"Created workflow: {wf_id}, status: {wf.get('status')}")

    # Wait for completion
    for _ in range(20):
        time.sleep(2)
        status_req = urllib.request.urlopen(f"{BASE_URL}/workflows/{wf_id}")
        wf_status = json.loads(status_req.read().decode())
        if wf_status.get("status") in ["completed", "failed"]:
            print(f"Workflow finished with status: {wf_status.get('status')}")
            break

    # Fetch records
    records_req = urllib.request.urlopen(f"{BASE_URL}/datasets?workflow_id={wf_id}")
    records_data = json.loads(records_req.read().decode())
    records = records_data.get("records", [])
    print(f"Retrieved {len(records)} extracted job records for '{prompt}':")
    for r in records[:4]:
        d = r.get("data", {})
        title = d.get('job_title', '').encode('ascii', errors='replace').decode('ascii')
        company = d.get('company', '').encode('ascii', errors='replace').decode('ascii')
        loc = d.get('location', '').encode('ascii', errors='replace').decode('ascii')
        print(f"  • Title:        {title}")
        print(f"    Company:      {company}")
        print(f"    Location:     {loc}")
        print(f"    Experience:   {d.get('experience_years')}")
        print(f"    Requirements: {d.get('requirements')[:3]}")
        print(f"    Description:  {(d.get('description') or '')[:100]}...")
        print(f"    Source:       {d.get('platform_source')}")
        print(f"    Apply Link:   {d.get('apply_link')}")
        print()
    return len(records)

if __name__ == "__main__":
    test_workflow_execution("receptionist in orissa")
    test_workflow_execution("copywriting job online")
    test_workflow_execution("project manager in pune")
