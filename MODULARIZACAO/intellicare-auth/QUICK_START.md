# 🚀 QUICK START - IntelliCare Auth

Guia rápido para configurar Keycloak e começar a usar `intellicare-auth` em **30 minutos**.

---

## ⚡ SETUP RÁPIDO (3 Passos)

### PASSO 1: Instalar Dependências (2 min)

```bash
cd MODULARIZACAO/intellicare-auth

# Instalar biblioteca
pip install -e .

# Instalar dependências de scripts
pip install python-keycloak
```

---

### PASSO 2: Configurar Keycloak Automaticamente (10 min)

#### 2.1 Executar Script de Setup

```bash
# Configurar senha de admin (se diferente)
export KEYCLOAK_ADMIN_PASSWORD="Crazy#57LB"

# Executar setup automático
python scripts/setup_keycloak.py
```

**O que o script faz**:
- ✅ Cria 9 clients (1 por módulo IntelliCare)
- ✅ Cria 7 roles (admin, doctor, nurse, etc.)
- ✅ Adiciona 4 protocol mappers (hospital_id, specialty, etc.)
- ✅ Salva client secrets em `keycloak_client_secrets.json`
- ✅ Gera arquivo `.env.example`

**Saída esperada**:
```
🔐 SETUP KEYCLOAK INTELLICARE
============================================================

📡 Conectando ao Keycloak: https://keycloak.gsi.srv.br/auth/
   Realm: saudeplanner.com.br
✅ Conectado com sucesso!

🎭 Criando Roles...
------------------------------------------------------------
✅ Role criada: intellicare_admin
✅ Role criada: intellicare_doctor
...

🔧 Criando Clients...
------------------------------------------------------------

📦 Configurando: intellicare-core
   ✅ Client criado
   🔑 Secret: h6AmFgY4S9MwJFMEXX...
   ✅ Mapper adicionado: hospital_id
...

✅ SETUP CONCLUÍDO COM SUCESSO!
```

#### 2.2 Criar Usuários de Teste

```bash
python scripts/create_test_users.py
```

**Usuários criados**:
- `dr.silva@saudeplanner.com.br` (doctor)
- `enf.maria@saudeplanner.com.br` (nurse)
- `nutri.ana@saudeplanner.com.br` (nutritionist)
- `coord.pedro@saudeplanner.com.br` (care_coordinator)
- `paciente.jose@saudeplanner.com.br` (patient)

**Senha padrão**: `Test@123`

---

### PASSO 3: Testar Conexão (5 min)

#### 3.1 Configurar .env

```bash
# Copiar exemplo
cp .env.example .env

# Editar .env (usar secret do intellicare-core)
nano .env
```

**Conteúdo do `.env`**:
```bash
KEYCLOAK_SERVER_URL=https://keycloak.gsi.srv.br/auth
KEYCLOAK_REALM=saudeplanner.com.br
KEYCLOAK_CLIENT_ID=intellicare-core
KEYCLOAK_CLIENT_SECRET=<copiar_de_keycloak_client_secrets.json>
```

#### 3.2 Executar Teste

```bash
python examples/test_connection.py
```

**Saída esperada**:
```
🔐 TESTE DE CONEXÃO KEYCLOAK GSI
============================================================

📋 Configuração:
   Server: https://keycloak.gsi.srv.br/auth
   Realm: saudeplanner.com.br
   Client ID: intellicare-core

🔑 Teste 1: Obter Token (Client Credentials)
------------------------------------------------------------
✅ Token obtido com sucesso!
   Token Type: Bearer
   Expires In: 300s

✅ Teste 2: Validar Token (JWT Local)
------------------------------------------------------------
✅ Token validado com sucesso!
   Subject (sub): ...
   Roles: intellicare_admin, ...

✅ TODOS OS TESTES PASSARAM!
```

---

## 🎯 PRÓXIMO PASSO: Integrar Primeiro Módulo

### Opção A: Módulo Piloto (intellicare-donabedian)

```bash
cd MODULARIZACAO/intellicare-donabedian

# 1. Instalar biblioteca
pip install -e ../intellicare-auth

# 2. Criar .env
cat > .env << EOF
KEYCLOAK_SERVER_URL=https://keycloak.gsi.srv.br/auth
KEYCLOAK_REALM=saudeplanner.com.br
KEYCLOAK_CLIENT_ID=intellicare-donabedian
KEYCLOAK_CLIENT_SECRET=<copiar_secret_do_json>
EOF

# 3. Modificar main.py (ver GUIA_INTEGRACAO.md)
```

### Opção B: Criar Módulo de Teste

```bash
# Executar exemplo FastAPI
cd MODULARIZACAO/intellicare-auth
python examples/fastapi_example.py
```

Acessar: http://localhost:8000/docs

---

## 📚 DOCUMENTAÇÃO COMPLETA

| Documento | Quando Usar |
|-----------|-------------|
| [GUIA_INTEGRACAO.md](docs/GUIA_INTEGRACAO.md) | Integrar módulo existente |
| [CONFIGURACAO_KEYCLOAK.md](docs/CONFIGURACAO_KEYCLOAK.md) | Configuração manual do Keycloak |
| [PLANO_EXECUCAO.md](docs/PLANO_EXECUCAO.md) | Ver cronograma completo |
| [README.md](README.md) | Referência da API |

---

## 🧪 TESTAR AUTENTICAÇÃO

### Obter Token (Client Credentials)

```bash
curl -X POST https://keycloak.gsi.srv.br/auth/realms/saudeplanner.com.br/protocol/openid-connect/token \
  -d "grant_type=client_credentials" \
  -d "client_id=intellicare-core" \
  -d "client_secret=SEU_SECRET_AQUI"
```

### Obter Token (Password - Usuário)

```bash
curl -X POST https://keycloak.gsi.srv.br/auth/realms/saudeplanner.com.br/protocol/openid-connect/token \
  -d "grant_type=password" \
  -d "client_id=intellicare-core" \
  -d "username=dr.silva@saudeplanner.com.br" \
  -d "password=Test@123"
```

### Testar Endpoint Protegido

```bash
# Salvar token
export TOKEN="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."

# Testar
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/profile
```

---

## ⚠️ TROUBLESHOOTING

### Erro: "Connection refused"
- Verificar se Keycloak está acessível: `curl https://keycloak.gsi.srv.br/auth/`
- Verificar VPN/rede

### Erro: "Invalid credentials"
- Verificar senha de admin
- Tentar login manual: https://keycloak.gsi.srv.br/auth/admin/

### Erro: "Client already exists"
- Normal se executar script múltiplas vezes
- Secrets serão obtidos dos clients existentes

### Erro: "Role not found"
- Executar `setup_keycloak.py` novamente
- Verificar roles no admin console

---

## ✅ CHECKLIST

- [ ] Biblioteca instalada (`pip install -e .`)
- [ ] Script `setup_keycloak.py` executado
- [ ] Arquivo `keycloak_client_secrets.json` criado
- [ ] Usuários de teste criados
- [ ] Arquivo `.env` configurado
- [ ] Teste de conexão passou
- [ ] Pronto para integrar módulos!

---

## 🆘 SUPORTE

**Problemas?** Ver documentação completa em `docs/`

**Dúvidas?** Consultar:
- `README.md` - API reference
- `GUIA_INTEGRACAO.md` - Integração passo a passo
- `CONFIGURACAO_KEYCLOAK.md` - Setup manual

---

**Tempo total**: ~30 minutos ⏱️  
**Próximo passo**: Integrar primeiro módulo 🚀

