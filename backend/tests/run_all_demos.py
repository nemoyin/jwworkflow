"""E2E validation: 6 template-instantiated workflows all run successfully."""
import urllib.request, urllib.error, json, time, sys, os

BASE = "http://localhost:8081"
TOKEN = None


def api(method, path, body=None, timeout=120):
    url = f"{BASE}{path}"
    headers = {"Content-Type": "application/json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def login():
    global TOKEN
    status, data = api("POST", "/api/auth/login",
                       {"email": "admin@demo.com", "password": "demo123"})
    assert status == 200, f"Login failed: {data}"
    TOKEN = data["access_token"]
    print("[OK] Auth success\n")


def get_output(result):
    """Extract meaningful output from run response."""
    # Response structure: {id, workflow_id, status, result: {...}, steps: [...]}
    data = result.get("result", result)
    if isinstance(data, dict):
        # Try common output field names
        for key in ("output", "answer", "analysis", "review_result",
                    "conversation_log", "final_answer"):
            val = data.get(key, "")
            if val:
                return str(val)
        # Return first meaningful value
        for k, v in data.items():
            if k not in ("status", "error") and v:
                return str(v)
    return str(data)


def test_ai_qa():
    """Template 4: AI Q&A"""
    wf_id = "8e9efe94-a6a6-4328-ba9e-3c6fd4427de7"
    print("=" * 60)
    print("Test 1/6: AI Q&A")
    print("=" * 60)
    status, result = api("POST", f"/api/workflows/{wf_id}/run", {
        "question": "请解释围串标的概念，100字以内"
    })
    print(f"  HTTP {status}")
    output = get_output(result)
    print(f"  Output: {output[:200]}")
    ok = len(output) > 20 and result.get("status") != "error"
    print(f"  {'[PASS]' if ok else '[FAIL]'}")
    return ok


def test_collusion():
    """Template 2: Collusion Analysis"""
    wf_id = "686b2551-8a26-43c0-bc60-893ecc82735c"
    print("\n" + "=" * 60)
    print("Test 2/6: Collusion Analysis")
    print("=" * 60)
    status, result = api("POST", f"/api/workflows/{wf_id}/run", {
        "bid_files": json.dumps({
            "bidders": [
                {"name": "BidderA", "ip": "192.168.1.100", "price": 980000, "doc_author": "Zhang"},
                {"name": "BidderB", "ip": "192.168.1.100", "price": 985000, "doc_author": "Zhang"},
                {"name": "BidderC", "ip": "10.0.0.50", "price": 1200000, "doc_author": "Li"},
            ]
        }, ensure_ascii=False),
        "threshold": "0.8"
    })
    print(f"  HTTP {status}")
    output = get_output(result)
    print(f"  Output: {output[:250]}")
    ok = len(output) > 10 and result.get("status") != "error"
    print(f"  {'[PASS]' if ok else '[FAIL]'}")
    return ok


def test_compliance():
    """Template 1: Tender Compliance Review"""
    wf_id = "5b37333f-06b0-4c0e-b24b-662d057b41eb"
    print("\n" + "=" * 60)
    print("Test 3/6: Tender Compliance Review")
    print("=" * 60)
    tender_doc = (
        "Project: Smart City Platform\n"
        "Requirements: 1) Registered capital >= 10M RMB. "
        "2) CMMI Level 5. 3) Project manager must have PhD. "
        "Scoring: Technical proposal (30 points) - subjective evaluation. "
        "Delivery: within 30 days."
    )
    status, result = api("POST", f"/api/workflows/{wf_id}/run", {
        "tender_doc": tender_doc,
        "rules": ""
    })
    print(f"  HTTP {status}")
    output = get_output(result)
    print(f"  Output: {output[:300]}")
    ok = len(output) > 10 and result.get("status") != "error"
    print(f"  {'[PASS]' if ok else '[FAIL]'}")
    return ok


def test_excel_qa():
    """Template 5: AI Q&A (Excel)"""
    wf_id = "a196ae45-36b5-45dd-bff8-ef57edbf74fc"
    print("\n" + "=" * 60)
    print("Test 4/6: AI Q&A (Excel)")
    print("=" * 60)
    file_path = "D:/AI/opc/jwworkflow/backend/data/uploads/test/sales_data.xlsx"
    # Upload file first
    upload_result = upload_file(wf_id, file_path)
    print(f"  Upload: {upload_result}")
    status, result = api("POST", f"/api/workflows/{wf_id}/run", {
        "question": "Which product has the highest total sales? What is the overall total?",
        "file_path": file_path
    })
    print(f"  HTTP {status}")
    output = get_output(result)
    print(f"  Output: {output[:300]}")
    ok = len(output) > 10 and result.get("status") != "error"
    print(f"  {'[PASS]' if ok else '[FAIL]'}")
    return ok


def test_codenode():
    """Template 6: AI Data Analysis (CodeNode)"""
    wf_id = "584fa2a2-25e0-4a31-be76-4c2ef941b1d9"
    print("\n" + "=" * 60)
    print("Test 5/6: AI Data Analysis (CodeNode)")
    print("=" * 60)
    file_path = "D:/AI/opc/jwworkflow/backend/data/uploads/test/sales_data.xlsx"
    upload_result = upload_file(wf_id, file_path)
    print(f"  Upload: {upload_result}")
    status, result = api("POST", f"/api/workflows/{wf_id}/run", {
        "question": "Analyze total sales by product and region. Find the best product.",
        "file_path": file_path
    })
    print(f"  HTTP {status}")
    output = get_output(result)
    print(f"  Output: {output[:350]}")
    ok = len(output) > 20 and result.get("status") != "error"
    print(f"  {'[PASS]' if ok else '[FAIL]'}")
    return ok


def test_interview():
    """Template 3: Interview Simulation Agent"""
    wf_id = "7eea11a6-c7a2-4e9f-87fd-937efde1d2ca"
    print("\n" + "=" * 60)
    print("Test 6/6: Interview Simulation Agent")
    print("=" * 60)
    status, result = api("POST", f"/api/workflows/{wf_id}/run", {
        "scenario": "Discipline inspection interview: Official accused of accepting banquets from contractors",
        "subject_info": "Wang, male, 45, Deputy Director, in charge of project approvals"
    })
    print(f"  HTTP {status}")
    output = get_output(result)
    print(f"  Output: {output[:350]}")
    ok = len(output) > 10 and result.get("status") != "error"
    print(f"  {'[PASS]' if ok else '[FAIL]'}")
    return ok


def upload_file(wf_id, file_path):
    """Upload a file to a workflow via multipart/form-data."""
    import http.client
    import mimetypes

    boundary = "----FormBoundary7MA4YWxkTrZu0gW"
    filename = os.path.basename(file_path)
    content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"

    with open(file_path, "rb") as f:
        file_data = f.read()

    body = b""
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode()
    body += f"Content-Type: {content_type}\r\n\r\n".encode()
    body += file_data
    body += f"\r\n--{boundary}--\r\n".encode()

    conn = http.client.HTTPConnection("localhost", 8081, timeout=30)
    conn.request(
        "POST",
        f"/api/workflows/{wf_id}/upload",
        body=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Authorization": f"Bearer {TOKEN}",
        },
    )
    resp = conn.getresponse()
    result = json.loads(resp.read().decode())
    conn.close()
    return f"HTTP {resp.status}"


if __name__ == "__main__":
    print("=" * 60)
    print("jwworkflow 6-Template E2E Validation")
    print("=" * 60 + "\n")

    login()

    results = []
    results.append(("AI Q&A", test_ai_qa()))
    time.sleep(1)
    results.append(("Collusion Analysis", test_collusion()))
    time.sleep(1)
    results.append(("Compliance Review", test_compliance()))
    time.sleep(1)
    results.append(("AI Q&A (Excel)", test_excel_qa()))
    time.sleep(1)
    results.append(("AI Data Analysis (CodeNode)", test_codenode()))
    time.sleep(1)
    results.append(("Interview Simulation", test_interview()))

    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        print(f"  {'[+]' if ok else '[-]'} {name}")
    print(f"\nPassed: {passed}/{len(results)}")
    print("=" * 60)

    sys.exit(0 if passed == len(results) else 1)
