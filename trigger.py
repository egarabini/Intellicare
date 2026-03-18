import json, urllib.request

try:
    with open("token.json") as f:
        token = json.load(f)["access_token"]
except Exception as e:
    print("Could not read token:", e)
    exit(1)

req = urllib.request.Request(
    "http://localhost:9000/careplanner/journeys/trigger",
    data=json.dumps({
        "patient_ref": "paciente-teste-001",
        "task_type": "CHECK_IN",
        "template_code": "boas_vindas",
        "tenant_slug": "alfa"
    }).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
)

try:
    res = urllib.request.urlopen(req)
    print("API Response:", res.read().decode())
except Exception as e:
    if hasattr(e, 'read'):
        print("API Error:", e.read().decode())
    else:
        print("Error:", e)
