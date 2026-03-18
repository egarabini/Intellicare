import sys, json, urllib.request

with open('token.json', 'r') as f:
    data = json.load(f)
    token = data.get('access_token')

if not token:
    print("Token not found in token.json!")
    sys.exit(1)

req = urllib.request.Request(
    'http://kestra:8080/api/v1/namespaces/intellicare.careplanner/kv/intellicare_jwt_alfa',
    data=json.dumps(token).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='PUT'
)

try:
    res = urllib.request.urlopen(req)
    print("KV provisioned:", res.read().decode('utf-8'))
except Exception as e:
    print("Error:", e)
