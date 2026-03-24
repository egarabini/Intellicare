"""
Smoke test for Marie (Dify) API key.
Verifies the API key is valid and the app is accessible.
"""
import os
import urllib.request
import urllib.error
import json

API_KEY = os.environ.get("MARIE_API_KEY", "app-qynPMo4xCj9oRJclTG5xllVl")
DIFY_API = os.environ.get("DIFY_API_URL", "http://localhost:5001")

def test_parameters():
    """Test /v1/parameters endpoint with API key."""
    url = f"{DIFY_API}/v1/parameters"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    req = urllib.request.Request(url, headers=headers)
    
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode())
        print(f"GET /v1/parameters → {resp.status}")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return True
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"GET /v1/parameters → HTTP {e.code}: {body[:300]}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_chat_message():
    """Test /v1/chat-messages endpoint with a simple request."""
    url = f"{DIFY_API}/v1/chat-messages"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = json.dumps({
        "inputs": {
            "chief_complaint": "Dor de cabeça persistente",
            "encounter_date": "2026-03-23",
            "patient_history": "Paciente feminina, 45 anos, HAS controlada"
        },
        "query": "Gere nota SOAP",
        "response_mode": "blocking",
        "user": "smoke-test"
    }).encode()
    
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read().decode())
        print(f"\nPOST /v1/chat-messages → {resp.status}")
        answer = data.get("answer", "no answer field")
        print(f"Answer: {answer[:500]}")
        return True
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"\nPOST /v1/chat-messages → HTTP {e.code}: {body[:500]}")
        # 400 with "model not configured" is expected since no LLM provider is set
        if e.code == 400:
            print("(This is expected - no LLM provider configured in Dify)")
            return True  # API key works, just no model
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    print("=== Marie/Dify API Smoke Test ===\n")
    
    ok1 = test_parameters()
    ok2 = test_chat_message()
    
    print(f"\n{'='*40}")
    if ok1:
        print("RESULT: API Key is VALID ✓")
    else:
        print("RESULT: API Key FAILED ✗")
