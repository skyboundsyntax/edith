"""
Comprehensive test script for EDITH Job Intelligence Platform.
Validates:
1. Health endpoint (/api/health)
2. Sources Health Matrix (/api/sources/health)
3. AI Query Planning (/api/workflows/plan)
4. User Profile (/api/profile)
5. Live Workflow Execution with parallel source connectors
"""
import urllib.request
import json
import time

def test_api():
    base_url = "http://127.0.0.1:8000/api"
    print("========================================")
    print("1. Testing /api/health...")
    req = urllib.request.urlopen(f"{base_url}/health")
    health = json.loads(req.read().decode())
    print("Health response:", json.dumps(health, indent=2))

    print("\n========================================")
    print("2. Testing /api/sources/health...")
    req = urllib.request.urlopen(f"{base_url}/sources/health")
    sources = json.loads(req.read().decode())
    print(f"Total Sources: {sources['total_sources']} | Online: {sources['online_sources']} | Link-Out: {sources['linkout_sources']}")
    for s in sources["sources"]:
        print(f" - {s['name']:12} | Status: {s['status']:14} | Method: {s['access_method']:18} | Latency: {s['latency_ms']}ms")

    print("\n========================================")
    print("3. Testing AI Query Planning /api/workflows/plan...")
    user_prompt = "I am a second-year CSE student looking for internships or entry-level AI/ML or Python roles in India. I prefer Pune, Bangalore or remote. I know Python, React, JavaScript, SQL and basic ML. I want startups or product companies. I don't want jobs requiring more than 1 year experience. Minimum salary 6 LPA."
    
    plan_data = json.dumps({"prompt": user_prompt}).encode('utf-8')
    plan_req = urllib.request.Request(
        f"{base_url}/workflows/plan",
        data=plan_data,
        headers={"Content-Type": "application/json"}
    )
    plan_res = json.loads(urllib.request.urlopen(plan_req).read().decode())
    print("Interpreted Specification:")
    print(json.dumps(plan_res["spec"], indent=2))

    print("\n========================================")
    print("4. Testing User Profile /api/profile...")
    profile_data = json.dumps({
        "name": "CSE Student Candidate",
        "skills": ["Python", "React", "SQL", "Machine Learning"],
        "experience_years": 0.5,
        "education": "B.Tech Computer Science (2026)",
        "preferred_roles": ["AI/ML Intern", "Python Developer"],
        "preferred_locations": ["Pune", "Bangalore"],
        "remote_preference": True,
        "salary_expectation": 600000.0
    }).encode('utf-8')
    prof_req = urllib.request.Request(
        f"{base_url}/profile",
        data=profile_data,
        headers={"Content-Type": "application/json"}
    )
    prof_res = json.loads(urllib.request.urlopen(prof_req).read().decode())
    print("Profile save result:", prof_res)

    print("\n========================================")
    print("5. Launching Live Ingestion Pipeline /api/workflows...")
    wf_data = json.dumps({
        "prompt": "Find entry-level Python & AI/ML engineer roles in Pune or Bangalore or Remote",
        "confidence_threshold": 75.0,
        "query_spec": plan_res["spec"]
    }).encode('utf-8')
    wf_req = urllib.request.Request(
        f"{base_url}/workflows",
        data=wf_data,
        headers={"Content-Type": "application/json"}
    )
    wf_res = json.loads(urllib.request.urlopen(wf_req).read().decode())
    wf_id = wf_res["id"]
    print(f"Launched Workflow ID: {wf_id}. Waiting for parallel sources to finish...")

    for i in range(12):
        time.sleep(2)
        check_req = urllib.request.urlopen(f"{base_url}/workflows/{wf_id}")
        check_res = json.loads(check_req.read().decode())
        wf_info = check_res["workflow"]
        print(f" [T+{2*(i+1)}s] Status: {wf_info['status']} | Extracted: {wf_info['total_extracted']} | Deduplicated: {wf_info['total_deduplicated']}")
        if wf_info["status"] in ["completed", "failed"]:
            break

    print("\n========================================")
    print(f"6. Checking Datasets for Workflow {wf_id}...")
    ds_req = urllib.request.urlopen(f"{base_url}/datasets?workflow_id={wf_id}")
    ds_res = json.loads(ds_req.read().decode())
    records = ds_res.get("records", [])
    print(f"Verified Records Returned: {len(records)}")
    if records:
        for r in records[:5]:
            d = r.get("data", {})
            print(f" -> [{r.get('confidence_score')}% Score] {d.get('job_title')} at {d.get('company')} ({d.get('location')}) | Source: {d.get('platform_source')}")
            print(f"    Apply: {d.get('apply_link')}")
            why_str = str(d.get('why_it_matches')).encode('ascii', errors='replace').decode()
            gaps_str = str(d.get('potential_gaps')).encode('ascii', errors='replace').decode()
            print(f"    Why: {why_str}")
            print(f"    Gaps: {gaps_str}")

if __name__ == "__main__":
    test_api()
