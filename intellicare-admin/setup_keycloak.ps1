$ErrorActionPreference = "Stop"

echo "Authenticating kcadm.sh inside Keycloak docker..."
docker exec keycloak-intellicare /opt/keycloak/bin/kcadm.sh config credentials --server http://localhost:8080 --realm master --user admin --password changeme

echo "Checking if intellicare-admin client exists..."
$clientID = docker exec keycloak-intellicare /opt/keycloak/bin/kcadm.sh get clients -r bemcuidar -q clientId=intellicare-admin | Select-String -Pattern '"id" : "(.*)"'
if (-not $clientID) {
    echo "Creating intellicare-admin client..."
    docker exec keycloak-intellicare /opt/keycloak/bin/kcadm.sh create clients -r bemcuidar -s clientId=intellicare-admin -s enabled=true -s publicClient=false -s serviceAccountsEnabled=true -s standardFlowEnabled=false -s 'redirectUris=["http://localhost:8010/*"]'
} else {
    echo "Client intellicare-admin already exists."
}

echo "Ensuring PLATFORM_ADMIN role exists..."
$roleAdmin = docker exec keycloak-intellicare /opt/keycloak/bin/kcadm.sh get roles/PLATFORM_ADMIN -r bemcuidar 2>$null
if (-not $roleAdmin) {
    docker exec keycloak-intellicare /opt/keycloak/bin/kcadm.sh create roles -r bemcuidar -s name=PLATFORM_ADMIN
}

echo "Ensuring PLATFORM_SUPPORT role exists..."
$roleSupport = docker exec keycloak-intellicare /opt/keycloak/bin/kcadm.sh get roles/PLATFORM_SUPPORT -r bemcuidar 2>$null
if (-not $roleSupport) {
    docker exec keycloak-intellicare /opt/keycloak/bin/kcadm.sh create roles -r bemcuidar -s name=PLATFORM_SUPPORT
}

echo "Getting client secret..."
$cid = docker exec keycloak-intellicare /opt/keycloak/bin/kcadm.sh get clients -r bemcuidar -q clientId=intellicare-admin
# Process json output to extract ID
$cidJson = $cid | ConvertFrom-Json
$id = $cidJson[0].id

$secretJson = docker exec keycloak-intellicare /opt/keycloak/bin/kcadm.sh get clients/$id/client-secret -r bemcuidar
$secretObj = $secretJson | ConvertFrom-Json
$secret = $secretObj.value

echo "CLIENT_SECRET=$secret"

echo "Keycloak setup complete."
