# DEM-004 — Module Test Console: Especificação Funcional

**Demanda:** DEM-004
**Módulo:** intellicare-admin
**Dev:** dev2
**Referência completa:** `DOCUMENTACAO/06_ANDAMENTO/DEMANDAS/20260308-1600_DEM-004_ADMIN_MODULE_TEST_CONSOLE.md`

---

## O que é

Uma seção no frontend do admin chamada **"Diagnóstico de Módulos"** que dá ao
administrador da plataforma visibilidade e controle real sobre cada um dos
11 módulos do IntelliCare — indo além do simples "está de pé ou não" para
"está funcionando corretamente ou não".

---

## Problema que resolve

Um módulo pode responder `200 OK` no `/health` e ainda assim estar quebrado
funcionalmente (ex: banco de dados conectado mas queries falhando, LLM
configurado mas sem credenciais válidas, RAG indexado mas sem retornar
resultados). O administrador hoje não tem como detectar isso sem abrir um
terminal.

---

## Três níveis de diagnóstico

### Nível 1 — Probe Dashboard
*"Todos os módulos estão de pé e saudáveis?"*

O administrador vê um **grid de cards**, um por módulo. Cada card mostra:
- Nome e descrição do módulo
- Indicador visual de status:
  - 🟢 **healthy** — respondeu em < 500ms
  - 🟡 **degraded** — respondeu mas com latência ≥ 500ms
  - 🔴 **unhealthy** — respondeu com erro (não-2xx)
  - ⚫ **unreachable** — timeout ou conexão recusada
- Latência em ms
- Versão do módulo
- Uptime
- Dependências internas (ex: postgres: ok, redis: ok)

Funcionalidades do grid:
- Botão **"Atualizar tudo"** — re-probe de todos em paralelo
- **Auto-refresh** configurável: desligado / 30s / 60s / 5 min
- Filtro por status (ex: mostrar só os degraded/unhealthy)

### Nível 2 — Teste Funcional
*"Este módulo está processando análises corretamente?"*

Ao expandir o card de qualquer módulo, aparece a aba **"Teste Funcional"**:
- **Dropdown** com payloads pré-configurados (ex: para OSWALDO: "Paciente fictício João Silva, 65 anos, HAS + DRC")
- **Editor JSON** editável para o administrador customizar o payload se quiser
- Botão **"Executar Teste"**
- Painel de resultado mostrando: status HTTP, latência, resposta JSON formatada com syntax highlight, badge success/fail
- Link para o **histórico** daquele módulo

Cada módulo tem pelo menos um payload pré-configurado que representa um
caso de uso real típico (ver lista completa na spec técnica).

### Nível 3 — Testes de Integração
*"Os módulos estão funcionando juntos corretamente?"*

Página separada **"Testes de Integração"** com flows multi-módulo:

| Flow | Módulos envolvidos | O que valida |
|---|---|---|
| `basic_patient_flow` | WANDA → OSWALDO → DONABEDIAN | análise clínica completa |
| `rag_protocol_search` | FLORENCE + PIERRE | busca RAG + literatura científica |
| `full_health_sweep` | todos em paralelo | saúde geral da plataforma |

Para cada flow, o administrador vê:
- Lista de passos com status individual (✅ ❌ ⏳)
- Latência por passo
- Resposta de cada módulo (colapsável)
- Linha do tempo visual simplificada

---

## Histórico de testes

Todas as execuções (probe, funcional e integração) ficam registradas e
acessíveis em uma tela de histórico paginada. O administrador consegue ver
se um módulo que está verde hoje estava vermelho ontem — identificando
regressões e padrões de instabilidade.

---

## O que NÃO faz

- Não executa ações destrutivas nos módulos (apenas leitura/análise)
- Não expõe dados reais de pacientes — os payloads de teste são sempre fictícios
- Não substitui o Grafana para métricas de longo prazo — é diagnóstico pontual
- Não configura nem reinicia módulos — é diagnóstico, não gerenciamento

---

## Módulos cobertos

| Módulo | Porta interna | Agente |
|---|---|---|
| florence | 8001 | FLORENCE — RAG + Protocolos |
| oswaldo | 8002 | OSWALDO — Análise Clínica FHIR |
| donabedian | 8003 | DONABEDIAN — Qualidade + Indicadores |
| wanda | 8004 | WANDA — Orquestrador IA |
| comunicacao | 8005 | — Comunicação (WhatsApp/Email/SMS) |
| geralda | 8006 | GERALDA — Suporte ao Paciente |
| zilda | 8007 | ZILDA — CNES + DATASUS |
| minerva | 8008 | MINERVA — Extração de Documentos |
| pierre | 8009 | PIERRE — Busca Científica |
| grahame | 8012 | GRAHAME — FHIR R4 + CDS Hooks |
| nise | 8013 | NISE — Chatbot + Treinamento |

---

## Fluxo de uso típico do administrador

1. Abre a tela "Diagnóstico de Módulos"
2. Vê o grid — todos verdes ✅
3. Nota que FLORENCE está 🟡 amarelo (latência 1200ms)
4. Clica no card do FLORENCE → aba "Teste Funcional"
5. Executa o teste com payload padrão
6. Resultado volta com erro: "pgvector index não encontrado"
7. Administrador identifica o problema e aciona o responsável

Ou:
1. Após um deploy, administrador clica em "Atualizar tudo"
2. Todos voltam verde — confirma que o deploy não quebrou nada
3. Executa "Teste de Integração: basic_patient_flow" para confirmar fluxo E2E
