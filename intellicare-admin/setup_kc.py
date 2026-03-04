import asyncio
import sys
from keycloak import KeycloakAdmin

async def main():
    try:
        server_url = "http://167.86.97.142:8080/"
        username = "admin"
        password = "Soeuso410863"

        print(f"Connecting to Keycloak {server_url} as {username}...")
        
        admin = KeycloakAdmin(
            server_url=server_url,
            username=username,
            password=password,
            realm_name="master",
            user_realm_name="master",
            verify=False
        )

        realms = admin.get_realms()
        realm_names = [r["realm"] for r in realms]
        print(f"Available realms: {realm_names}")
        
        target_realm = "bemcuidar"
        if "bemcuidar" not in realm_names:
            if "intellicare" in realm_names:
                target_realm = "intellicare"
            else:
                print("Target realm not found. Creating 'bemcuidar'...")
                admin.create_realm(payload={"realm": "bemcuidar", "enabled": True})
                target_realm = "bemcuidar"
        
        admin.realm_name = target_realm
        print(f"Using realm: {target_realm}")

        roles = admin.get_realm_roles()
        role_names = [r["name"] for r in roles]
        if "PLATFORM_ADMIN" not in role_names:
            print("Creating PLATFORM_ADMIN role...")
            admin.create_realm_role(payload={"name": "PLATFORM_ADMIN"})
        if "PLATFORM_SUPPORT" not in role_names:
            print("Creating PLATFORM_SUPPORT role...")
            admin.create_realm_role(payload={"name": "PLATFORM_SUPPORT"})

        clients = admin.get_clients()
        client_exists = next((c for c in clients if c.get("clientId") == "intellicare-admin"), None)
        
        if not client_exists:
            print("Creating client 'intellicare-admin'...")
            client_payload = {
                "clientId": "intellicare-admin",
                "enabled": True,
                "publicClient": False,
                "serviceAccountsEnabled": True,
                "standardFlowEnabled": False,
                "redirectUris": ["http://localhost:8010/*"],
                "protocol": "openid-connect"
            }
            client_id_uuid = admin.create_client(payload=client_payload)
            print(f"Client created with UUID: {client_id_uuid}")
        else:
            print("Client 'intellicare-admin' already exists.")
            client_id_uuid = client_exists["id"]
        
        secret = admin.get_client_secrets(client_id_uuid)
        print(f"\n=========================================")
        print(f"CLIENT_SECRET={secret.get('value')}")
        print(f"=========================================\n")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
