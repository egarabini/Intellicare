# IntelliCare V3 — Roteiro de Demonstração

> **Duração estimada:** 25–30 minutos  
> **Pré-requisitos:** `docker compose up -d` rodando, seed executado (`seed_demo.py`), `setup_keycloak.py` executado  
> **URL base:** `http://localhost:8000`

---

## Antes de começar (5 min antes)

```bash
# Verificar stack
docker compose ps                          # todos healthy
curl http://localhost:8000/health          # {"status":"healthy"}
curl http://localhost:8080/health/ready    # Keycloak pronto
```

Abrir 3 abas no browser:
- Aba 1: `http://localhost:8000/` (Portal)
- Aba 2: `http://localhost:8000/admin-ui/`
- Aba 3: `http://localhost:8000/clinico-ui/`

---

## Bloco 1 — Portal e Roteamento por Role (3 min)

**Mensagem:** *"Um único endereço para todos os perfis. O sistema sabe para onde enviar cada um."*

1. Abrir `http://localhost:8000/` em aba anônima
2. Mostrar redirecionamento automático para o Keycloak
3. Logar com `platform-admin` / *(senha do .env)*
   → Portal lê role `PLATFORM_ADMIN` → redireciona para `/admin-ui/`
4. Logout → logar com `dr.silva` / `Demo@1234`
   → Portal lê role `CLINICO` → redireciona para `/clinico-ui/`
5. Logout → logar com `gestor.alfa` / `Demo@1234`
   → Portal lê role `TENANT_GESTOR` → redireciona para `/gestor-ui/`

**Ponto de destaque:** token apenas em memória — fechar e reabrir a aba exige novo login.

---

## Bloco 2 — Administração de Tenants (5 min)

**Mensagem:** *"O PLATFORM_ADMIN provisiona novos clientes em segundos — schema isolado, grupo no Keycloak, tudo automático."*

**Login:** `platform-admin` → AdminUI

### 2.1 Ver tenants existentes
- Mostrar lista: `Clínica Alfa Saúde` (active/pro), `Hospital Beta` (active/enterprise), `Consultório Gamma` (suspended/basic)
- Destacar badge de status colorido

### 2.2 Criar novo tenant ao vivo
- Clicar em **Novo Tenant**
- Digitar nome: `Demo Ao Vivo`
- Mostrar slug gerado automaticamente: `demo-ao-vivo`
- Selecionar plano: Pro → **Criar**

### 2.3 Verificar provisionamento
```bash
# Em terminal separado — mostrar ao vivo
psql $DATABASE_URL -c "\dn" | grep demo
# deve aparecer: tenant_demo_ao_vivo
```

### 2.4 Suspender tenant
- Clicar no ícone de suspender em `Consultório Gamma`
- Badge muda para **suspended** instantaneamente
- Tentar logar com `gestor.gamma` → 403 (tenant suspenso)

---

## Bloco 3 — Gestor: Base de Conhecimento RAG (5 min)

**Mensagem:** *"O gestor carrega os protocolos clínicos da unidade. A IA aprende com eles — sem enviar dados para fora."*

**Login:** `gestor.alfa` / `Demo@1234` → GestorUI

### 3.1 Ver documentos já ingeridos
- Mostrar lista: 5 protocolos clínicos com contagem de chunks
- Destacar: `protocolo_hipertensao.txt — 12 chunks`

### 3.2 Upload de novo documento ao vivo
- Arrastar um PDF ou TXT para o Dropzone
- Mostrar barra de progresso
- Documento aparece na lista com chunks gerados

### 3.3 Relatório de uso
- Navegar para **Relatórios**
- Mostrar: total de consultas, usuários únicos, tempo médio de resposta

---

## Bloco 4 — Clínico: Consulta + Assistente IA (10 min)

**Mensagem:** *"O clínico foca no paciente. A IA está no painel ao lado — responde em PT-BR, cita as fontes, nunca inventa."*

**Login:** `dr.silva` / `Demo@1234` → ClinicoUI

### 4.1 Buscar paciente
- Digitar 3 letras no campo de busca (ex: `car`)
- Mostrar debounce 400ms → lista aparece
- Selecionar um paciente

### 4.2 Abrir encontro
- Clicar em **Abrir Novo Encontro**
- Encontro criado com status `Aberto`

### 4.3 Escrever nota SOAP
No painel esquerdo, digitar:
```
S: Paciente hipertenso, relata cefaleia occipital há 2 dias.
   Nega febre. Em uso de Losartana 50mg.
O: PA 158/96 mmHg, FC 78 bpm, peso 82 kg.
   Ausculta sem alterações.
A: HAS descompensada
P: Ajuste de dose — Losartana 100mg. Retorno em 15 dias.
```

### 4.4 Acionar assistente IA (ponto alto da demo)
No painel direito, digitar:
> *"Paciente com HAS descompensada e cefaleia. Quais as condutas recomendadas pelo protocolo da unidade?"*

- Clicar em **Perguntar**
- **Mostrar os tokens chegando em tempo real via SSE**
- Resposta em PT-BR com referência ao protocolo carregado pelo gestor
- Destacar: inferência local, sem API externa, sem LGPD

### 4.5 Fechar encontro
- Clicar em **Fechar Encontro**
- Histórico atualiza com o encontro encerrado

---

## Bloco 5 — Isolamento Multi-tenant (2 min)

**Mensagem:** *"Clínica Alfa e Hospital Beta usam o mesmo sistema — e nunca veem os dados um do outro."*

```bash
# Obter token de dr.silva (clinica-alfa)
TOKEN=$(curl -s -X POST http://localhost:8080/realms/intellicare/protocol/openid-connect/token \
  -d "client_id=clinico-ui&grant_type=password&username=dr.silva&password=Demo@1234" \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Tentar acessar dados do hospital-beta com token da clinica-alfa
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/cuidado/patients \
  | python -m json.tool

# Retorna pacientes da CLINICA-ALFA apenas — never hospital-beta
```

---

## Bloco 6 — Billing e Inadimplência (2 min)

**Mensagem:** *"O ciclo financeiro é automático. Venceu → suspende. Pagou → reativa."*

```bash
# Ver faturas da clinica-alfa
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
     http://localhost:8000/financeiro/reports/billing \
  | python -m json.tool

# Mostra: 4 pagas, 1 pendente, 1 vencida

# Job de inadimplência (roda automaticamente às 03h — forçar aqui)
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
     http://localhost:8000/financeiro/jobs/overdue

# Tenant com fatura vencida → status 'suspended'
```

---

## Perguntas Frequentes

**"Os dados do paciente saem para a nuvem?"**
→ Não. OLLAMA roda localmente. Embeddings e inferência são feitos no próprio servidor. O pgvector armazena tudo no PostgreSQL local.

**"Como adiciono um novo módulo?"**
→ Implementar `class Module(BaseModule)` com `get_router()` e `health()`, registrar no loader. O serviço carrega dinamicamente sem rebuild.

**"Como escala para múltiplas unidades?"**
→ Cada tenant tem schema isolado no mesmo PostgreSQL. Para escala horizontal, basta adicionar replicas do `intellicare-service` com o mesmo banco.

**"E a LGPD?"**
→ Dados nunca saem da infraestrutura do cliente. SLM local, sem telemetria, schema por tenant facilita exclusão seletiva de dados.

---

## Encerramento

| Módulo | Status |
|--------|--------|
| Portal unificado | ✅ |
| Admin multi-tenant | ✅ |
| Financeiro + billing | ✅ |
| RAG pipeline | ✅ |
| SLM local (OLLAMA) | ✅ |
| Gestor UI | ✅ |
| Clínico UI + streaming | ✅ |
| Programas de saúde | ✅ |
| E2E testado | ✅ |
| Isolamento multi-tenant | ✅ |

> IntelliCare V3 — de 10+ containers independentes para 1 serviço modular,  
> com IA clínica local, multi-tenancy nativo e frontends unificados.
