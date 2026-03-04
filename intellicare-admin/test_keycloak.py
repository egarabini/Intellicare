import os
from dotenv import load_dotenv
from keycloak import KeycloakOpenID

load_dotenv()

keycloak_url = os.getenv("KEYCLOAK_URL")
if keycloak_url and not keycloak_url.endswith("/"):
    keycloak_url += "/"

print(f"Testing connection to: {keycloak_url}")
print(f"Realm: {os.getenv('KEYCLOAK_REALM')}")
print(f"Client ID: {os.getenv('KEYCLOAK_CLIENT_ID')}")

try:
    keycloak_openid = KeycloakOpenID(
        server_url=keycloak_url,
        client_id=os.getenv("KEYCLOAK_CLIENT_ID"),
        realm_name=os.getenv("KEYCLOAK_REALM"),
        client_secret_key=os.getenv("KEYCLOAK_CLIENT_SECRET"),
    )

    print("Checking well-known configuration...")
    config = keycloak_openid.well_known()
    if config:
        print("Successfully connected to Keycloak OpenID configuration!")
        print("Integration test passed.")
    else:
        print("Failed to get well-known config.")
except Exception as e:
    print(f"Keycloak Connection Error: {e}")
