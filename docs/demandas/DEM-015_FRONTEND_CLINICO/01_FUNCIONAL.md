# DEM-015 — Frontend Clínico (React + Vite + Mantine UI)

## 1. Contexto e Motivação

O módulo de cuidado ao paciente (DEM-013) e o assistente SLM (DEM-010) existem como APIs, mas ainda não possuem interface de usuário para o profissional de saúde (CLINICO). Esta demanda entrega o **ClinicoUI**: uma SPA (Single Page Application) React leve, integrada ao Keycloak via OIDC, que permite ao clínico gerenciar encontros e consultar o assistente IA em tempo real.

---

## 2. Escopo

### Incluído

| Funcionalidade | Detalhe |
|---|---|
| Login OIDC | SSO via Keycloak realm `intellicare` |
| Lista de pacientes | Busca full-text, paginação |
| Abrir / Fechar encontro | Integração com `/cuidado/encounters` |
| Registro de nota SOAP | Textarea com rótulos S/O/A/P |
| Assistente SLM | Streaming SSE em painel lateral |
| Upload de documento | Reusa endpoint `/gestor/documents/upload` |
| Build integrado | Saída copiada para `intellicare_core/static/clinico-ui/` |

### Fora do Escopo

- Prescrições eletrônicas (demanda futura)
- Módulo financeiro/faturamento
- App mobile

---

## 3. Personas e Jornada

**Persona principal**: Dr. Ana — clínica de atenção primária, acessa pelo navegador durante consultas.

**Jornada típica**:
1. Login via SSO → redireciona para `/clinico-ui/`
2. Busca paciente pelo nome → seleciona na lista
3. Abre novo encontro
4. Preenche nota SOAP no painel esquerdo
5. Aciona assistente IA no painel direito ("Sugestão de CID para HAS com complicação renal")
6. Tokens chegam via SSE em menos de 5 s (first token)
7. Fecha encontro → retorna à lista

---

## 4. Requisitos Funcionais

| ID | Requisito |
|---|---|
| RF-01 | Usuário deve logar via OIDC; token JWT armazenado apenas em memória |
| RF-02 | Lista de pacientes com busca por nome (mín. 3 chars) |
| RF-03 | Criar encontro vinculado ao paciente |
| RF-04 | Adicionar nota ao encontro aberto |
| RF-05 | Fechar encontro (status → closed) |
| RF-06 | Enviar pergunta ao assistente SLM com contexto do encontro atual |
| RF-07 | Resposta SLM exibida em streaming (token a token) |
| RF-08 | Upload de PDF/DOCX para base de conhecimento do tenant |

---

## 5. Requisitos Não Funcionais

| ID | Requisito |
|---|---|
| RNF-01 | First Contentful Paint < 2 s em conexão de 10 Mbps |
| RNF-02 | First token SLM < 5 s |
| RNF-03 | Sem uso de localStorage (segurança HIPAA-like) |
| RNF-04 | Build estático < 500 KB gzip |
| RNF-05 | Responsivo — funciona em tela 1280×800 mínimo |

---

## 6. Stack Técnica

| Camada | Tecnologia |
|---|---|
| Framework | React 18 + TypeScript |
| Bundler | Vite 5 |
| UI Components | Mantine 7 |
| State / Cache | TanStack Query v5 |
| Auth | `react-oidc-context` + `oidc-client-ts` |
| HTTP | Axios |
| SSE Streaming | Fetch API + `ReadableStream` |
| Build output | `intellicare_core/static/clinico-ui/` |

---

## 7. Critérios de Aceite

- [ ] Login/logout OIDC funciona com usuário `dr.ana` no Keycloak
- [ ] Token não persiste após fechar aba (sem localStorage)
- [ ] Busca de pacientes retorna resultados após 3 caracteres
- [ ] Criar e fechar encontro refletem na listagem
- [ ] Streaming SSE exibe tokens progressivamente sem reload
- [ ] Upload de documento retorna confirmação de ingestão
- [ ] Build gera arquivos em `intellicare_core/static/clinico-ui/`
- [ ] FastAPI serve `/clinico-ui/` estaticamente

---

## 8. Dependências

| DEM | Razão |
|---|---|
| DEM-004 | Keycloak realm e usuário CLINICO configurados |
| DEM-010 | Endpoint `/slm/ask` com streaming |
| DEM-013 | Endpoints `/cuidado/patients` e `/cuidado/encounters` |
| DEM-011 | Endpoint `/gestor/documents/upload` (upload de docs) |
