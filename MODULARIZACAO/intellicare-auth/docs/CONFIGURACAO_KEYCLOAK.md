# 🔐 Configuração do Keycloak para IntelliCare

Guia completo para configurar o Keycloak GSI para os módulos IntelliCare.

---

## 📋 INFORMAÇÕES DO AMBIENTE

**Keycloak Server**: `https://keycloak.gsi.srv.br/auth`  
**Realm**: `saudeplanner.com.br`  
**Admin Console**: `https://keycloak.gsi.srv.br/auth/admin/`

**Credenciais Admin**:
- Usuário: `admin@saudeplanner.com.br`
- Senha: `Crazy#57LB`

---

## 🏗️ PASSO 1: Criar Clients

Para cada módulo IntelliCare, criar um client no Keycloak:

### 1.1 Acessar Console Admin

1. Ir para: `https://keycloak.gsi.srv.br/auth/admin/`
2. Login com credenciais admin
3. Selecionar realm: `saudeplanner.com.br`

### 1.2 Criar Client

1. Menu lateral: **Clients** → **Create**
2. Preencher:

```
Client ID: intellicare-donabedian
Name: IntelliCare Donabedian - Quality Assessment Module
Description: Módulo de avaliação de qualidade baseado em Donabedian
Root URL: http://localhost:8003
```

3. Clicar **Save**

### 1.3 Configurar Client

Na aba **Settings**:

```
Access Type: confidential
Standard Flow Enabled: ON
Implicit Flow Enabled: OFF
Direct Access Grants Enabled: ON
Service Accounts Enabled: ON

Valid Redirect URIs:
  http://localhost:8003/*
  https://donabedian.gsi.srv.br/*

Web Origins:
  http://localhost:8003
  https://donabedian.gsi.srv.br
```

4. Clicar **Save**

### 1.4 Obter Client Secret

1. Ir para aba **Credentials**
2. Copiar o **Secret**
3. Armazenar com segurança (será usado no `.env`)

---

## 🎭 PASSO 2: Criar Roles

### 2.1 Realm Roles

Menu lateral: **Roles** → **Add Role**

Criar as seguintes roles:

```
intellicare_admin
  Description: Administrador geral do IntelliCare
  
intellicare_hospital_admin
  Description: Administrador de hospital
  
intellicare_doctor
  Description: Médico
  
intellicare_nurse
  Description: Enfermeiro(a)
  
intellicare_nutritionist
  Description: Nutricionista
  
intellicare_care_coordinator
  Description: Coordenador de cuidado
  
intellicare_patient
  Description: Paciente
```

### 2.2 Composite Roles (Hierarquia)

Configurar `intellicare_admin` como composite role:

1. Editar role `intellicare_admin`
2. Aba **Composite Roles**
3. Adicionar:
   - `intellicare_hospital_admin`
   - `intellicare_doctor`
   - `intellicare_nurse`
   - `intellicare_nutritionist`
   - `intellicare_care_coordinator`

---

## 🗺️ PASSO 3: Protocol Mappers

Para cada client, adicionar mappers customizados:

### 3.1 Acessar Mappers

1. Clients → Selecionar client → Aba **Mappers**
2. Clicar **Create**

### 3.2 Mapper: hospital_id

```
Name: hospital_id
Mapper Type: User Attribute
User Attribute: hospital_id
Token Claim Name: hospital_id
Claim JSON Type: String
Add to ID token: ON
Add to access token: ON
Add to userinfo: ON
```

### 3.3 Mapper: specialty

```
Name: specialty
Mapper Type: User Attribute
User Attribute: specialty
Token Claim Name: specialty
Claim JSON Type: String
Add to ID token: ON
Add to access token: ON
Add to userinfo: ON
```

### 3.4 Mapper: license_number

```
Name: license_number
Mapper Type: User Attribute
User Attribute: license_number
Token Claim Name: license_number
Claim JSON Type: String
Add to ID token: ON
Add to access token: ON
Add to userinfo: ON
```

### 3.5 Mapper: department

```
Name: department
Mapper Type: User Attribute
User Attribute: department
Token Claim Name: department
Claim JSON Type: String
Add to ID token: ON
Add to access token: ON
Add to userinfo: ON
```

---

## 👥 PASSO 4: Criar Usuários de Teste

### 4.1 Usuário Admin

Menu: **Users** → **Add user**

```
Username: admin@saudeplanner.com.br
Email: admin@saudeplanner.com.br
First Name: Admin
Last Name: IntelliCare
Email Verified: ON
Enabled: ON
```

**Credentials**:
- Password: `Crazy#57LB`
- Temporary: OFF

**Role Mappings**:
- Adicionar: `intellicare_admin`

### 4.2 Usuário Médico

```
Username: dr.silva@saudeplanner.com.br
Email: dr.silva@saudeplanner.com.br
First Name: João
Last Name: Silva
```

**Attributes**:
- hospital_id: `HOSP001`
- specialty: `Cardiologia`
- license_number: `CRM-SP-123456`
- department: `Cardiologia`

**Roles**:
- `intellicare_doctor`

---

## 📝 PASSO 5: Testar Configuração

### 5.1 Obter Token

```bash
curl -X POST https://keycloak.gsi.srv.br/auth/realms/saudeplanner.com.br/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=intellicare-donabedian" \
  -d "client_secret=SEU_CLIENT_SECRET_AQUI"
```

### 5.2 Decodificar Token

Usar: https://jwt.io

Verificar:
- ✅ `iss`: `https://keycloak.gsi.srv.br/auth/realms/saudeplanner.com.br`
- ✅ `aud`: `intellicare-donabedian`
- ✅ `realm_access.roles`: contém roles configuradas

---

## ✅ Checklist de Configuração

- [ ] 9 clients criados
- [ ] Client secrets salvos
- [ ] Roles criadas
- [ ] Composite roles configuradas
- [ ] Protocol mappers adicionados
- [ ] Usuários de teste criados
- [ ] Tokens testados

---

**Próximo**: Integrar módulos com `intellicare-auth`

