# 🧪 GUIA DE TESTES - INTEGRAÇÃO KEYCLOAK

**Módulo**: intellicare-donabedian  
**Data**: 2026-02-12  
**Objetivo**: Validar integração completa com Keycloak

---

## 🚀 OPÇÃO 1: TESTES AUTOMATIZADOS (Recomendado)

### Passo 1: Iniciar o Servidor

Abra um terminal e execute:

```bash
cd .\intellicare-donabedian
start_server.bat
```

Ou manualmente:

```bash
cd .\intellicare-donabedian
venv\Scripts\activate
python -m uvicorn src.donabedian.api.main:app --reload --port 8003
```

**Aguarde até ver**: `Application startup complete`

### Passo 2: Executar Testes

Em **outro terminal**, execute:

```bash
cd .\intellicare-donabedian
run_tests.bat
```

Ou manualmente:

```bash
cd .\intellicare-donabedian
venv\Scripts\activate
python test_keycloak_integration.py
```

### Resultados Esperados

```
✅ TESTE 1: Endpoint público acessível
✅ TESTE 2: Endpoint protegido bloqueia sem token
✅ TESTE 3: Endpoint protegido permite com token válido
✅ TESTE 4: Endpoint admin bloqueia sem role admin
```

---

## 🔧 OPÇÃO 2: TESTES MANUAIS COM CURL

### 1. Testar Endpoint Público

```bash
curl http://localhost:8003/api/v1/health
```

**Esperado**: `{"status": "healthy"}` (200 OK)

### 2. Testar Endpoint Protegido SEM Token

```bash
curl http://localhost:8003/api/v1/pillars
```

**Esperado**: `403 Forbidden` (sem token)

### 3. Obter Token do Keycloak

```bash
curl -X POST https://keycloak.gsi.srv.br/realms/bemcuidar/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=intellicare-donabedian" \
  -d "client_secret=3w0l6qxYnNwm2jPDozu1x2LVyzjv4Cs" \
  -d "username=dr.silva@saudeplanner.com.br" \
  -d "password=Test@123"
```

**Copie o `access_token` retornado**

### 4. Testar Endpoint Protegido COM Token

```bash
export TOKEN="<seu_access_token_aqui>"

curl -H "Authorization: Bearer $TOKEN" http://localhost:8003/api/v1/pillars
```

**Esperado**: Lista de pillars (200 OK)

### 5. Testar Endpoint Admin SEM Role Admin

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"test","description":"test","display_order":99}' \
  http://localhost:8003/api/v1/pillars
```

**Esperado**: `403 Forbidden` (usuário não é admin)

---

## 🌐 OPÇÃO 3: TESTES VIA SWAGGER UI

### 1. Acessar Swagger

Abra no navegador: http://localhost:8003/docs

### 2. Obter Token

Use o script Python ou curl para obter um token.

### 3. Autorizar no Swagger

1. Clique no botão **"Authorize"** (cadeado verde)
2. No campo **"Value"**, digite: `Bearer <seu_token>`
3. Clique em **"Authorize"**
4. Clique em **"Close"**

### 4. Testar Endpoints

Agora você pode testar qualquer endpoint diretamente no Swagger!

**Endpoints para testar**:
- ✅ GET /health (público - sem token)
- ✅ GET /pillars (protegido - com token)
- ✅ POST /pillars (admin - deve retornar 403)

---

## 📊 CHECKLIST DE VALIDAÇÃO

### Funcionalidades Básicas
- [ ] Servidor inicia sem erros
- [ ] Log do Keycloak aparece no startup
- [ ] Endpoint /health acessível sem token
- [ ] Swagger UI carrega corretamente

### Autenticação
- [ ] Endpoint protegido bloqueia sem token (403)
- [ ] Token obtido com sucesso do Keycloak
- [ ] Endpoint protegido permite com token válido (200)
- [ ] Token inválido retorna 401

### Autorização
- [ ] Usuário não-admin bloqueado em endpoint admin (403)
- [ ] GET endpoints permitem qualquer usuário autenticado
- [ ] POST/PUT/DELETE endpoints requerem role admin

---

## 🐛 TROUBLESHOOTING

### Erro: "Connection refused"
**Solução**: Certifique-se de que o servidor está rodando na porta 8003

### Erro: "401 Unauthorized"
**Solução**: Token expirado ou inválido. Obtenha um novo token.

### Erro: "403 Forbidden" em GET endpoint
**Solução**: Token não foi enviado ou é inválido. Verifique o header Authorization.

### Erro: "Keycloak authentication not configured"
**Solução**: Verifique se o arquivo `.env.keycloak` existe e está correto.

### Erro: SSL Certificate
**Solução**: Adicione `verify=False` nas chamadas httpx (apenas para testes)

---

## 📝 USUÁRIOS DE TESTE DISPONÍVEIS

Todos com senha `Test@123`:

| Email | Role | Pode Ler? | Pode Criar/Editar? |
|-------|------|-----------|-------------------|
| dr.silva@saudeplanner.com.br | intellicare_doctor | ✅ Sim | ❌ Não |
| enf.maria@saudeplanner.com.br | intellicare_nurse | ✅ Sim | ❌ Não |
| nutri.ana@saudeplanner.com.br | intellicare_nutritionist | ✅ Sim | ❌ Não |
| coord.pedro@saudeplanner.com.br | intellicare_care_coordinator | ✅ Sim | ❌ Não |
| paciente.jose@saudeplanner.com.br | intellicare_patient | ✅ Sim | ❌ Não |

**Nota**: Nenhum usuário tem role `intellicare_admin`, então todos devem receber 403 ao tentar criar/editar/deletar.

---

## ✅ CRITÉRIOS DE SUCESSO

A integração está funcionando corretamente se:

1. ✅ Servidor inicia e mostra log do Keycloak
2. ✅ Endpoint /health acessível sem autenticação
3. ✅ Endpoints protegidos bloqueiam sem token
4. ✅ Endpoints protegidos permitem com token válido
5. ✅ Endpoints admin bloqueiam usuários sem role admin
6. ✅ Nenhum erro no console do servidor

---

**Boa sorte com os testes!** 🚀

