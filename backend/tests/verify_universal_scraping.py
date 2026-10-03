import urllib.request
import json
import time

BASE_URL = "http://127.0.0.1:8000/api"

def test_health():
    resp = urllib.request.urlopen(f"{BASE_URL}/health")
    data = json.loads(resp.read().decode())
    print("Health:", data)
    assert data.get("status") == "healthy"

def test_plan(prompt):
    req_data = json.dumps({"prompt": prompt}).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/workflows/plan",
        data=req_data,
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read().decode())
    spec = data.get("spec", {})
    print(f"\n--- Planning prompt: '{prompt}' ---")
    print(f"Roles:     {spec.get('roles')}")
    print(f"Keywords:  {spec.get('keywords')}")
    print(f"Skills:    {spec.get('skills')}")
    print(f"Locations: {spec.get('locations')}")
    print(f"Remote:    {spec.get('remote')}")
    print(f"Salary:    {spec.get('salary_min')} - {spec.get('salary_max')}")
    return spec

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
    for _ in range(15):
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
    print(f"Retrieved {len(records)} extracted job records:")
    for r in records[:5]:
        d = r.get("data", {})
        print(f"  • Title:    {d.get('job_title')}")
        print(f"    Company:  {d.get('company')}")
        print(f"    Location: {d.get('location')}")
        print(f"    Source:   {d.get('platform_source')}")
        print(f"    Skills:   {d.get('skills')}")
        print(f"    Apply:    {d.get('apply_link')}")
        print()

if __name__ == "__main__":
    test_health()
    test_plan("game developer")
    test_plan("15k per day copywriting job online")
    test_plan("project manager in pune")
    test_plan("receptionist in orissa")
    test_workflow_execution("game developer")
