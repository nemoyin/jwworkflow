"""Run workflow test inside Docker container"""
import urllib.request, json, sys

# Login
login_req = urllib.request.Request(
    'http://localhost:8000/api/auth/login',
    data=json.dumps({"email": "admin@demo.com", "password": "demo123"}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)
login_resp = urllib.request.urlopen(login_req, timeout=10)
token = json.loads(login_resp.read())["access_token"]
print(f"Logged in: {token[:20]}...")

# Run workflow
data = json.dumps({
    "file_path": "/tmp/test.xlsx",
    "question": "哪个城市销售额最高？数据分析一下"
}).encode()
req = urllib.request.Request(
    "http://localhost:8000/api/workflows/25aad827-bc0b-4e02-8089-8bd45a55df7f/run",
    data=data,
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
    method="POST"
)
resp = urllib.request.urlopen(req, timeout=120)
result = json.loads(resp.read())
print(f"Status: {result.get('status')}")
if result.get("status") == "success":
    output = result.get("result", {})
    analysis = output.get("analysis", "")
    print(f"Analysis ({len(analysis)} chars):")
    print(analysis[:500])
else:
    print(f"Error: {result.get('error', 'unknown')}")
