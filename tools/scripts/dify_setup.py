"""
Dify setup + florence_soap_rag workflow creation + API key generation.
Run: python tools/scripts/dify_setup.py
"""
import os
import urllib.request
import urllib.error
import json
import sys

DIFY_API = os.environ.get("DIFY_API_URL", "http://localhost:5001")
DIFY_ADMIN_EMAIL = os.environ.get("DIFY_ADMIN_EMAIL", "admin@intellicare.local")
DIFY_ADMIN_PASSWORD = os.environ.get("DIFY_ADMIN_PASSWORD", "Admin2026!Dify")
DIFY_ADMIN_NAME = os.environ.get("DIFY_ADMIN_NAME", "IntelliCare Admin")

def api_call(method, path, data=None, token=None):
    """Make an API call to Dify console API."""
    url = f"{DIFY_API}/console/api{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        raw = resp.read().decode()
        return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  HTTP {e.code}: {body[:500]}")
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None


def check_setup():
    """Check if Dify is already set up."""
    print("1. Checking Dify setup status...")
    result = api_call("GET", "/setup")
    if result is None:
        print("  Could not reach Dify API")
        return None
    print(f"  Setup status: {result}")
    return result


def init_setup(email=None, name=None, password=None):
    """Initialize Dify with admin account."""
    email = email or DIFY_ADMIN_EMAIL
    name = name or DIFY_ADMIN_NAME
    password = password or DIFY_ADMIN_PASSWORD
    print("2. Initializing Dify setup...")
    result = api_call("POST", "/setup", {
        "email": email,
        "name": name,
        "password": password
    })
    if result:
        print(f"  Setup complete: {list(result.keys())}")
    return result


def login(email=None, password=None):
    """Login to get access token."""
    email = email or DIFY_ADMIN_EMAIL
    password = password or DIFY_ADMIN_PASSWORD
    print("3. Logging in...")
    result = api_call("POST", "/login", {
        "email": email,
        "password": password
    })
    if result and "data" in result:
        token = result["data"]
        print(f"  Login OK, token: {token[:20]}...")
        return token
    elif result and "access_token" in result:
        token = result["access_token"]
        print(f"  Login OK, token: {token[:20]}...")
        return token
    else:
        print(f"  Login result: {result}")
        return None


def create_chat_app(token):
    """Create a chat app for florence_soap_rag."""
    print("4. Creating florence_soap_rag app...")
    result = api_call("POST", "/apps", {
        "name": "florence_soap_rag",
        "mode": "chat",
        "icon": "🏥",
        "icon_background": "#E8F5E9",
        "description": "Florence SOAP note generation via RAG"
    }, token)
    if result and "id" in result:
        app_id = result["id"]
        print(f"  App created: {app_id}")
        return app_id
    else:
        print(f"  Create result: {result}")
        return None


def configure_app_prompt(token, app_id):
    """Set the SOAP prompt for the app."""
    print("5. Configuring app prompt...")
    prompt = (
        "Você é Florence, assistente clínica especializada em documentação médica.\n"
        "Gere uma nota SOAP para a consulta descrita abaixo.\n\n"
        "Consulta: {{chief_complaint}}\n"
        "Data: {{encounter_date}}\n"
        "Histórico do paciente: {{patient_history}}\n\n"
        "Retorne APENAS um JSON válido com as chaves:\n"
        '{"soap_s": "...", "soap_o": "...", "soap_a": "...", "soap_p": "..."}\n\n'
        "Onde:\n"
        "- soap_s: Subjetivo (queixa do paciente)\n"
        "- soap_o: Objetivo (achados de exame)\n"
        "- soap_a: Avaliação (diagnóstico/hipótese)\n"
        "- soap_p: Plano (conduta terapêutica)"
    )
    
    model_config = {
        "pre_prompt": prompt,
        "model": {
            "provider": "openai",
            "name": "gpt-3.5-turbo",
            "completion_params": {
                "temperature": 0.3,
                "max_tokens": 1000
            }
        },
        "user_input_form": [
            {"text-input": {"label": "Chief Complaint", "variable": "chief_complaint", "required": True}},
            {"text-input": {"label": "Encounter Date", "variable": "encounter_date", "required": True}},
            {"paragraph": {"label": "Patient History", "variable": "patient_history", "required": True}}
        ]
    }
    
    result = api_call("POST", f"/apps/{app_id}/model-config", model_config, token)
    print(f"  Config result: {result}")
    return result


def create_api_key(token, app_id):
    """Generate an API key for the app."""
    print("6. Generating API key...")
    result = api_call("POST", f"/apps/{app_id}/api-keys", {}, token)
    if result and "id" in result:
        api_key = result.get("token", result.get("api_key", ""))
        print(f"  API Key: {api_key}")
        return api_key
    elif result and "result" in result:
        print(f"  Result: {result}")
        # Maybe list existing keys
        keys = api_call("GET", f"/apps/{app_id}/api-keys", token=token)
        if keys and "data" in keys:
            for k in keys["data"]:
                print(f"  Existing key: {k.get('token', k.get('api_key', 'unknown'))}")
                return k.get("token", k.get("api_key"))
    else:
        print(f"  Key result: {result}")
    return None


def list_apps(token):
    """List existing apps."""
    print("  Listing existing apps...")
    result = api_call("GET", "/apps?page=1&limit=30", token=token)
    if result and "data" in result:
        for app in result["data"]:
            print(f"  - {app['name']} (id={app['id']}, mode={app.get('mode', '?')})")
        return result["data"]
    return []


def main():
    # Step 1: Check setup
    setup = check_setup()
    if setup is None:
        print("FATAL: Cannot reach Dify API at", DIFY_API)
        sys.exit(1)
    
    # Step 2: Initialize if needed
    step = setup.get("step", "")
    if step == "finished":
        print("  Already set up, skipping init.")
    else:
        print(f"  Setup step: {step}")
        init_result = init_setup()
        if init_result is None:
            print("  Setup might already be done, trying login...")
    
    # Step 3: Login 
    token = login()
    if not token:
        print("FATAL: Cannot login to Dify")
        sys.exit(1)
    
    # Step 4: Check for existing app
    apps = list_apps(token)
    app_id = None
    for app in apps:
        if app["name"] == "florence_soap_rag":
            app_id = app["id"]
            print(f"  Found existing app: {app_id}")
            break
    
    if not app_id:
        app_id = create_chat_app(token)
        if not app_id:
            print("FATAL: Cannot create app")
            sys.exit(1)
        
        # Configure prompt
        configure_app_prompt(token, app_id)
    
    # Step 6: Create or get API key
    api_key = create_api_key(token, app_id)
    if api_key:
        print(f"\n{'='*60}")
        print(f"MARIE_API_KEY={api_key}")
        print(f"{'='*60}")
        print(f"\nAdd this to infra/.env and restart intellicare-service")
    else:
        # Try listing keys
        print("  Trying to list existing keys...")
        keys = api_call("GET", f"/apps/{app_id}/api-keys", token=token)
        print(f"  Keys: {keys}")


if __name__ == "__main__":
    main()
