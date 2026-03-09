# =============================================================================
# Atribui a role HIS_ADAPTER ao service account intellicare-bridge-dev
# =============================================================================
# Uso: .\assign-his-adapter-role.ps1
#      .\assign-his-adapter-role.ps1 -KeycloakUrl "http://localhost:8080"
#
# Pré-requisitos: Keycloak rodando, realm bemcuidar importado
# =============================================================================

param(
    [string]$KeycloakUrl = $env:KEYCLOAK_URL ?? "http://localhost:8080",
    [string]$AdminUser = $env:KEYCLOAK_ADMIN ?? "admin",
    [string]$AdminPassword = $env:KEYCLOAK_ADMIN_PASSWORD ?? "changeme",
    [string]$Realm = "bemcuidar",
    [string]$ClientId = "intellicare-bridge-dev",
    [string]$RoleName = "HIS_ADAPTER"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Atribuindo role $RoleName ao service account $ClientId ===" -ForegroundColor Cyan
Write-Host "Keycloak: $KeycloakUrl | Realm: $Realm" -ForegroundColor Gray

# 1. Obter token admin
Write-Host "`n[1/4] Obtendo token admin..." -ForegroundColor Yellow
$tokenBody = @{
    grant_type = "password"
    client_id = "admin-cli"
    username = $AdminUser
    password = $AdminPassword
}
try {
    $tokenResp = Invoke-RestMethod -Uri "$KeycloakUrl/realms/master/protocol/openid-connect/token" `
        -Method Post -Body $tokenBody -ContentType "application/x-www-form-urlencoded"
} catch {
    Write-Host "ERRO: Falha ao obter token. Verifique Keycloak em $KeycloakUrl e credenciais admin." -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}
$token = $tokenResp.access_token
Write-Host "   Token obtido." -ForegroundColor Green

# 2. Obter client UUID
Write-Host "`n[2/4] Buscando client $ClientId..." -ForegroundColor Yellow
$headers = @{ Authorization = "Bearer $token" }
try {
    $clients = Invoke-RestMethod -Uri "$KeycloakUrl/admin/realms/$Realm/clients?clientId=$ClientId" `
        -Headers $headers -Method Get
} catch {
    Write-Host "ERRO: Falha ao listar clients." -ForegroundColor Red
    exit 1
}
if ($clients.Count -eq 0) {
    Write-Host "ERRO: Client '$ClientId' nao encontrado. Importe o realm bemcuidar primeiro." -ForegroundColor Red
    exit 1
}
$clientUuid = $clients[0].id
Write-Host "   Client UUID: $clientUuid" -ForegroundColor Green

# 3. Obter service account user
Write-Host "`n[3/4] Obtendo service account user..." -ForegroundColor Yellow
try {
    $saUser = Invoke-RestMethod -Uri "$KeycloakUrl/admin/realms/$Realm/clients/$clientUuid/service-account-user" `
        -Headers $headers -Method Get
} catch {
    Write-Host "ERRO: Service account nao encontrado. Verifique se o client tem serviceAccountsEnabled=true." -ForegroundColor Red
    exit 1
}
$userId = $saUser.id
Write-Host "   User ID: $userId" -ForegroundColor Green

# 4. Obter role e atribuir
Write-Host "`n[4/4] Atribuindo role $RoleName..." -ForegroundColor Yellow
try {
    $role = Invoke-RestMethod -Uri "$KeycloakUrl/admin/realms/$Realm/roles/$RoleName" `
        -Headers $headers -Method Get
} catch {
    Write-Host "ERRO: Role '$RoleName' nao encontrada no realm." -ForegroundColor Red
    exit 1
}
$rolePayload = @(@{ id = $role.id; name = $role.name }) | ConvertTo-Json
try {
    $resp = Invoke-WebRequest -Uri "$KeycloakUrl/admin/realms/$Realm/users/$userId/role-mappings/realm" `
        -Headers $headers -Method Post -Body $rolePayload -ContentType "application/json" -UseBasicParsing -ErrorAction Stop
    Write-Host "   Role atribuida com sucesso." -ForegroundColor Green
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 204) {
        Write-Host "   Role atribuida com sucesso." -ForegroundColor Green
    } else {
        # Verificar se já tem a role (pode ter retornado erro por outro motivo)
        try {
            $currentRoles = Invoke-RestMethod -Uri "$KeycloakUrl/admin/realms/$Realm/users/$userId/role-mappings/realm" `
                -Headers $headers -Method Get
            if ($currentRoles.name -contains $RoleName) {
                Write-Host "   Role ja estava atribuida." -ForegroundColor Green
            } else {
                throw
            }
        } catch {
            Write-Host "ERRO ao atribuir role (HTTP $statusCode):" -ForegroundColor Red
            Write-Host $_.Exception.Message
            exit 1
        }
    }
}

Write-Host "`n=== Concluido ===" -ForegroundColor Cyan
Write-Host "O service account $ClientId agora tem a role $RoleName." -ForegroundColor Green
Write-Host "`nTeste o token:" -ForegroundColor Gray
Write-Host "  `$body = @{ grant_type='client_credentials'; client_id='$ClientId'; client_secret='bridge-dev-secret-change-in-production' }" -ForegroundColor Gray
Write-Host "  Invoke-RestMethod -Uri '$KeycloakUrl/realms/$Realm/protocol/openid-connect/token' -Method Post -Body `$body -ContentType 'application/x-www-form-urlencoded'" -ForegroundColor Gray
