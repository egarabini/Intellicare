# PROPOSTA — Nova Estrutura DOCUMENTACAO

Data: 2026-03-08 (revisada — inclui varredura dos docs dos módulos)
Status: Rascunho para discussão
Objetivo: Substituir `docs/` por uma estrutura clara, separada por abrangência

---

## Diagnóstico completo — o que existe hoje

### Camada 1 — docs/ central do projeto (levantamento anterior)

300+ documentos em 17+ pastas:
- `docs/NORMAS_E_PADROES/`, `docs/GOVERNANCA/`, `docs/RELATORIOS_E_ANDAMENTO/`
- `docs/V2.0.0-KEYCLOAK/`, `docs/V2.0.1 - ADMIN/`, `docs/V2.0.2 - ADMIN - GESTOR/`
- `docs/INFRAESTRUTURA/` (16 arquivos sobre deploy e portas)
- `docs/PLANNER-ANTIGRAVITY/` (210+ arquivos — ondas 1-11)
- `docs/PLANNER-CURSOR/` (processo de trabalho com Cursor AI)
- `PADRAO_ENTREGA/` (scripts + histórico V1)
- 15 arquivos .md/.txt soltos na raiz do projeto

### Camada 2 — docs/ DENTRO de cada módulo (NOVO)

Levantamento completo dos 18 módulos revelou **~295 arquivos adicionais**
distribuídos entre pastas `docs/` locais e raízes de módulo.

#### Volume por módulo:

| Módulo | Arquivos docs/ | Arquivos raiz (md) | Total | Status |
|---|---|---|---|---|
| intellicare-comunicacao | 42 | 16 | 58 | ✅ Bem documentado |
| intellicare-florence | 20 | 22 | 42 | ✅ Bem documentado |
| intellicare-donabedian | 22 | 13 | 35 | ✅ Bem documentado |
| intellicare-oswaldo | 15 | 17 | 32 | ✅ Bem documentado |
| intellicare-nise | 7 | 15 | 22 | ✅ Guias excelentes |
| intellicare-wanda | 17 | 6 | 23 | ✅ Bem documentado |
| intellicare-geralda | 20 | 0 | 20 | ✅ Limpo |
| intellicare-grahame | 13 | 5 | 18 | ✅ Focado em segurança |
| intellicare-auth | 6 | 5 | 11 | ✅ Bons guias |
| intellicare-zilda | 11 | 0 | 11 | ✅ Limpo |
| intellicare-portal | 3 | 1 | 4 | ⚠️ Básico |
| intellicare-minerva | 3 | 0 | 3 | ⚠️ Mínimo |
| intellicare-pierre | 3 | 0 | 3 | ⚠️ Mínimo |
| intellicare-core | 2 | 0 | 2 | ⚠️ Mínimo |
| intellicare-conhecimento | 2 | 0 | 2 | ⚠️ Mínimo* |
| intellicare-admin | 0 | 0 | 0 | ❌ SEM documentação |
| intellicare-gestor | 0 | 0 | 0 | ❌ SEM documentação |
| intellicare-apresentacao | 0 | 0 | 0 | — Fora do escopo |

*O módulo `intellicare-conhecimento` tem apenas 2 arquivos de spec locais, mas o dev
registrou uma implementação completa (AI-GED / Knowledge Engine) que Eduardo moveu para
`docs/20260308_AIGED_KNOWLEDGE_ENGINE_IMPLEMENTATION.md`.

---

### Problemas identificados nos docs dos módulos

**1. Relatórios de desenvolvimento misturados com documentação ativa**
Módulos como Florence (22 arquivos na raiz), Oswaldo (17), Comunicacao (16)
têm registros diários de desenvolvimento (`DIA_N_RESULTADO_FINAL.md`,
`FASE_N_CONCLUIDA.md`, `DAY5_SUBTASK_5_2_COMPLETO.md`) misturados com specs
e guias. São histórico de execução, não documentação de produto.

**2. Logs de teste poluindo raízes de módulos**
Gestor: `gestor_pytest_output.txt`, `pytest_output.txt`
Grahame: `err.txt`, `grahame_err.txt`, `smart_test_result.txt`
Core: `pytest_e2e.txt`, `pytest_e2e_2.txt`
Estes não são documentação — são artefatos temporários de desenvolvimento.

**3. Guias operacionais de módulo que pertencem ao central**
Nise: `GUIA_DEPLOYMENT_PRODUCAO.md` (1555 linhas!) — guia de deploy de produção
deveria estar em `05_INFRAESTRUTURA/` do central, não soterrado no módulo.
Oswaldo: `RUNBOOK.md` e `TROUBLESHOOTING.md` — idem.
Donabedian: `DEPLOYMENT.md` — idem.

**4. Documentação de implementação sem lar definido**
O caso AI-GED é o exemplo: o dev implementou algo significativo no módulo
`intellicare-conhecimento`, registrou o andamento, mas não sabia onde colocar.
Resultado: foi parar no docs local do módulo em vez do docs central.
Este tipo de registro — o que foi feito, como, próximos passos — é um
ANDAMENTO_DEMANDA e pertence ao `06_ANDAMENTO/` do central.

**5. Módulos críticos sem documentação**
`intellicare-admin` e `intellicare-gestor` — zero documentação técnica.
São módulos em produção sem especificação, guia de uso ou runbook.

---

## A regra de dois mundos

Antes de propor a estrutura, é preciso definir o que fica onde:

```
DENTRO DO MÓDULO (docs/ local)          DOCUMENTACAO/ CENTRAL
────────────────────────────────        ──────────────────────────────────
Spec funcional do módulo                Governança e fluxo de trabalho
Spec técnica do módulo                  Normas e templates
Contratos de API do módulo              Arquitetura integrada (todos os módulos)
Guia de configuração do módulo          Specs de versões (cross-módulo)
Algoritmos específicos do módulo        Guias de infra (deploy, servidores)
                                        ANDAMENTO_DEMANDA (registro de demandas)
                                        Relatórios de progresso
                                        Histórico e retrospectivas
```

**Regra prática:**
- Se explica *o que o módulo faz* → fica no módulo
- Se explica *como o time trabalha* ou *o que foi entregue* → vai para o central
- Guias de deploy de produção → sempre no central (são infra, não módulo)

---

## Proposta: pasta `DOCUMENTACAO/`

Criar `DOCUMENTACAO/` na raiz do projeto com **7 áreas numeradas**.

```
INTELLICARE/
├── DOCUMENTACAO/           ← NOVA — substitui docs/
│   ├── 01_GOVERNANCA/
│   ├── 02_NORMAS_E_PADROES/
│   ├── 03_ARQUITETURA/
│   ├── 04_VERSOES/
│   ├── 05_INFRAESTRUTURA/
│   ├── 06_ANDAMENTO/
│   └── 07_HISTORICO/
├── docs/                   ← vai para 07_HISTORICO/ após migração
├── PADRAO_ENTREGA/         ← scripts executáveis ficam aqui
├── intellicare-florence/
│   └── docs/               ← docs LOCAL — permanece no módulo ✅
├── intellicare-oswaldo/
│   └── docs/               ← docs LOCAL — permanece no módulo ✅
├── [demais módulos com seus docs/ locais]
├── README.md               ← fica na raiz
├── CLAUDE.md               ← fica na raiz
└── CHANGELOG.md            ← fica na raiz
```

**Os docs/ locais dos módulos NÃO são migrados para o central.**
Ficam onde estão. O que muda é:
1. Os relatórios de execução/histórico saem dos módulos e vão para `07_HISTORICO/`
2. Os guias de deploy de produção saem dos módulos e vão para `05_INFRAESTRUTURA/`
3. Os ANDAMENTO_DEMANDA vão direto para `06_ANDAMENTO/`
4. Os logs de teste (.txt) são excluídos

---

## As 7 áreas

---

### 01_GOVERNANCA — Como trabalhamos

**Pergunta que responde:** *Como o time funciona? Quais são os papéis? Como uma demanda nasce e morre?*

Escopo: papéis, ciclo de vida de demanda, fluxo de aprovação, CODEOWNERS,
branch protection, regras inegociáveis.

Arquivos que vêm de:
- `docs/GOVERNANCA/20260307-1703_GOVERNANCA_DESENVOLVIMENTO.md` ✅
- `docs/PROPOSTA-CICD-E-GOVERNANCA.md` → resumir e incorporar
- `PLANNER-CURSOR/VISAO_PLANEJADOR.md` → avaliar o que é relevante
- `PLANNER-CURSOR/FLUXO_DE_TRABALHO.md` → incorporar o que ainda vale

---

### 02_NORMAS_E_PADROES — As regras

**Pergunta que responde:** *Como nomeio arquivos? Como faço commit? Qual padrão de branch? Como estruturo uma spec?*

Escopo: nomenclatura de documentos (`YYYYMMDD-HHMM_TITULO.md`), branches,
commits, templates de ANDAMENTO_DEMANDA, Spec Funcional, Spec Técnica,
Plano de Implementação, configuração SSH e Git.

Arquivos que vêm de:
- `docs/NORMAS_E_PADROES/` (4 arquivos) ✅
- `CHAVE_SSH_GITHUB.md` (raiz) → aqui
- `SOLUCAO_GIT.md` (raiz) → aqui
- `PLANNER-CURSOR/ESTRATEGIA_GIT.md` → avaliar
- `PLANNER-CURSOR/MODELO_ESPECIFICACAO.md` → avaliar e incorporar
- `PLANNER-CURSOR/PROCESSO_RELEASE.md` → avaliar

---

### 03_ARQUITETURA — O que construímos

**Pergunta que responde:** *Como o sistema está estruturado? Quais módulos existem? Como os dados fluem?*

Escopo: visão geral integrada de todos os módulos, arquitetura de dados,
mapeamento de domínios e roteamento Traefik, contratos de API (FHIR R4,
BaseAgent), dependências entre módulos.

Esta área contém a **visão integrada** — não duplica os docs dos módulos,
mas referencia-os e mostra como se conectam.

Arquivos que vêm de:
- `docs/ARQUITETURA_E_DADOS/` (7 arquivos) → consolidar em 3-4 docs
- `docs/API_OPENAPI/` (3 arquivos) → aqui
- `docs/INFRAESTRUTURA/MAPEAMENTO_PORTAS_COMPLETO.md` → aqui
- `docs/INFRAESTRUTURA/ROTEAMENTO_DOMINIOS.md` → aqui
- `PLANNER-CURSOR/ESTUDO_PROJETO.md` → avaliar

Índice de docs locais por módulo (não copia — aponta):
```
03_ARQUITETURA/
├── VISAO_GERAL_SISTEMA.md          ← mapa integrado de todos os módulos
├── ARQUITETURA_DADOS.md             ← schemas, multi-tenancy, OLTP/OLAP
├── DOMINIOS_E_ROTEAMENTO.md         ← Traefik, subdomínios, portas
├── CONTRATOS_API.md                 ← FHIR R4, BaseAgent, HealthCheck
└── INDICE_DOCS_MODULOS.md           ← links para docs/ de cada módulo
```

---

### 04_VERSOES — O que estamos construindo

**Pergunta que responde:** *O que está planejado para a versão X? Qual é a spec? O dev precisa implementar o quê?*

Cada subpasta = uma versão = uma branch no GitHub.

```
04_VERSOES/
├── V2.0.0_KEYCLOAK/
│   ├── README.md
│   ├── 01_ESPECIFICACAO_FUNCIONAL.md
│   ├── 02_ESPECIFICACAO_TECNICA.md
│   ├── 03_PLANO_IMPLEMENTACAO.md
│   └── 04_OPERACAO_PRODUCAO.md
├── V2.0.1_ADMIN/
├── V2.0.2_ADMIN_GESTOR/
├── V2.1.0_AIGED_CONHECIMENTO/      ← NOVO — implementação AI-GED
│   ├── README.md
│   └── 01_IMPLEMENTACAO.md         ← base: doc movido pelo Eduardo
├── V2.1.x_MULTITENANCY/
│   ├── F0_TENANT_CONTEXT/
│   └── F1_INTELLICARE_ADMIN/
└── V3.0.0_MEDPLUS_ON/
    ├── ONDA_1_FHIR_OPERATIONS/
    └── ...
```

**Destino do doc AI-GED:**
`docs/20260308_AIGED_KNOWLEDGE_ENGINE_IMPLEMENTATION.md` → `04_VERSOES/V2.1.0_AIGED_CONHECIMENTO/`
É uma spec de versão em andamento, não histórico nem ANDAMENTO.

Arquivos que vêm de:
- `docs/V2.0.0-KEYCLOAK/` → aqui ✅
- `docs/V2.0.1 - ADMIN/` → aqui ✅
- `docs/V2.0.2 - ADMIN - GESTOR/` → aqui ✅
- `docs/PLANNER-ANTIGRAVITY/MULTI_TENANCY/` → V2.1.x_MULTITENANCY
- `docs/PLANNER-ANTIGRAVITY/MEDPLUS_ON/ONDA_*` → V3.0.0_MEDPLUS_ON
- `docs/EXTENSAO_ODONTOLOGIA/` → versão futura a definir
- `docs/CARGA_DADOS/` → versão a definir ou ARQUITETURA

---

### 05_INFRAESTRUTURA — Como fazemos deploy

**Pergunta que responde:** *Como subo o sistema? Como configuro o servidor? O que fazer quando dá erro?*

Esta área **consolida guias de módulos também**. Os guias de deploy que
estão dentro de módulos (Nise, Donabedian, Oswaldo) devem ter uma versão
aqui, já que deploy é responsabilidade de infra, não do módulo.

```
05_INFRAESTRUTURA/
├── GUIA_DEPLOY_COMPLETO.md          ← consolidação de 22 docs
├── CONFIGURACAO_SERVIDORES.md       ← IPs, SSH, paths
├── DOCKER_E_COMPOSE.md              ← docker compose configs
├── TRAEFIK_CONFIGURACAO.md          ← roteamento e certificados
├── TROUBLESHOOTING.md               ← problemas conhecidos + soluções
├── COMANDOS_PRONTOS.md              ← comandos SSH para o servidor
└── SCRIPTS/                         ← smoke tests, health checks
```

Arquivos que vêm de:
- `GUIA_DEPLOY.md` (raiz) → base do guia consolidado
- `DEPLOYMENT.md` (raiz) → incorporar
- `COMANDOS_SERVIDOR.txt` + `SERVER_COMMANDS.txt` → consolidar
- `EXECUTE_AQUI.md`, `NETWORK_TROUBLESHOOTING.md`, `TROUBLESHOOT_UNHEALTHY.md`
- `docs/INFRAESTRUTURA/` (16 arquivos) → 22 docs viram ~6
- `docs/SERVIDORES/` → aqui
- `PADRAO_ENTREGA/FASE5_GUIA_EXECUCAO_REMOTA.md` e `COMANDOS_SSH_PRONTOS.md`
- **Dos módulos:**
  - `intellicare-nise/GUIA_DEPLOYMENT_PRODUCAO.md` (1555 linhas!) → aqui
  - `intellicare-donabedian/docs/DEPLOYMENT.md` → incorporar
  - `intellicare-oswaldo/RUNBOOK.md` + `TROUBLESHOOTING.md` → aqui

---

### 06_ANDAMENTO — O que está acontecendo agora

**Pergunta que responde:** *Qual demanda está em andamento? Quem está fazendo o quê?*

```
06_ANDAMENTO/
├── README.md              ← índice: tabela com todas as demandas e status
├── DEMANDAS/
│   ├── 20260307-1703_DEM-001_INFRA_FIX_SUBDOMINIOS.md    ✅
│   ├── 20260308-XXXX_DEM-002_CONHECIMENTO_AIGED.md       ← criar
│   └── ...
└── RELATORIOS/
    └── [relatórios de progresso recentes]
```

**Sobre o AI-GED:** o doc movido pelo Eduardo
(`20260308_AIGED_KNOWLEDGE_ENGINE_IMPLEMENTATION.md`) é um registro de
implementação — exatamente o que um ANDAMENTO_DEMANDA registra.
Recomendo criar `DEM-002_CONHECIMENTO_AIGED.md` no padrão do template,
incorporando o conteúdo desse doc como seção "Log de Execução".
A spec técnica vai para `04_VERSOES/V2.1.0_AIGED_CONHECIMENTO/`.

Regra: demandas concluídas há mais de 30 dias vão para `07_HISTORICO/`.

---

### 07_HISTORICO — O que já aconteceu

**Pergunta que responde:** *Como chegamos até aqui? O que aprendemos?*

Incluindo agora os relatórios de desenvolvimento dos módulos:

Arquivos que vêm de:
- `docs/HISTORICO/` → aqui
- `CHANGELOG.md` → cópia (original fica na raiz)
- `PADRAO_ENTREGA/ATA_V1_ENCERRADA.md`, `DIARIO_TECNICO.md`, `RELATORIO_FINAL_V1_V2.md`
- `docs/PLANNER-ANTIGRAVITY/` → histórico (exceto o que vai para 04_VERSOES)
- `docs/PLANNER-CURSOR/` → histórico (trabalho com Cursor AI)
- `INSTALLATION_REPORT.md` (raiz) → aqui
- **Dos módulos** (histórico de desenvolvimento):
  - `intellicare-florence/` — `DIA_N_*.md`, `SEMANA_N_*.md`, `FASE_N_*.md` (22 arquivos)
  - `intellicare-oswaldo/` — `DAY5_SUBTASK_*.md`, `DAY6_*.md`, `DAY7_*.md` (14 arquivos)
  - `intellicare-donabedian/` — `FASE_*.md`, `RESUMO_*.md`, `SESSION_*.md` (9 arquivos)
  - `intellicare-comunicacao/` — `D2_*.md`, `D7_*.md`, `FASE_*_RESUMO_FINAL.md`
  - `intellicare-nise/` — `IMPLEMENTACAO_DIA_*.md` (7 arquivos)
  - `intellicare-wanda/` — `DEVLOG.md`, `RELATORIO_FINAL_INTEGRACAO.md`
  - `intellicare-grahame/docs/` — `COMPLETE_IMPLEMENTATION_SUMMARY.md`, `FINAL_IMPLEMENTATION_SUMMARY.md`, `SESSION_*.md`

---

## Documentos da raiz — destino de cada um

| Arquivo | Destino |
|---|---|
| `README.md` | Fica na raiz ✅ |
| `CLAUDE.md` | Fica na raiz ✅ |
| `CHANGELOG.md` | Fica na raiz ✅ (cópia em 07_HISTORICO) |
| `DEPLOYMENT.md` | → 05_INFRAESTRUTURA |
| `GUIA_DEPLOY.md` | → 05_INFRAESTRUTURA (base do guia consolidado) |
| `COMANDOS_SERVIDOR.txt` | → 05_INFRAESTRUTURA |
| `SERVER_COMMANDS.txt` | → 05_INFRAESTRUTURA |
| `NETWORK_TROUBLESHOOTING.md` | → 05_INFRAESTRUTURA |
| `TROUBLESHOOT_UNHEALTHY.md` | → 05_INFRAESTRUTURA |
| `CHAVE_SSH_GITHUB.md` | → 02_NORMAS_E_PADROES |
| `SOLUCAO_GIT.md` | → 02_NORMAS_E_PADROES |
| `EXECUTE_AQUI.md` | → 05_INFRAESTRUTURA |
| `README_DEMO.md` | → 05_INFRAESTRUTURA |
| `INSTALLATION_REPORT.md` | → 07_HISTORICO |
| `DOCUMENTACAO.md` | → descartar (substituído pela pasta DOCUMENTACAO/) |
| `kc_logs.txt` | → descartar (log de produção) |
| `parsed_kc_logs.txt` | → descartar |
| `docs_w2b_spec.txt` | → descartar (arquivo temporário) |
| `docs/20260308_AIGED_KNOWLEDGE_ENGINE_IMPLEMENTATION.md` | → 04_VERSOES/V2.1.0_AIGED_CONHECIMENTO/ |

---

## Limpeza nos módulos (ações paralelas)

Além da migração do docs/ central, estas ações nos módulos são recomendadas:

**Excluir (não é documentação):**
- `intellicare-gestor/gestor_pytest_output.txt` e `pytest_output.txt`
- `intellicare-grahame/err.txt`, `grahame_err.txt`, `smart_test.txt`, `smart_test_result.txt`
- `intellicare-core/pytest_e2e.txt`, `pytest_e2e_2.txt`, `pytest_sandbox.txt`
- `intellicare-wanda/wanda_test_errors.txt`
- `intellicare-auth/pytest_resolver_err.txt`

**Mover para DOCUMENTACAO/ central:**
- `intellicare-nise/GUIA_DEPLOYMENT_PRODUCAO.md` → 05_INFRAESTRUTURA/
- `intellicare-nise/DOCUMENTACAO_COMPLETA_PROJETO_06.md` → 04_VERSOES/ ou 07_HISTORICO
- `intellicare-oswaldo/RUNBOOK.md` + `TROUBLESHOOTING.md` → 05_INFRAESTRUTURA/
- `intellicare-donabedian/docs/DEPLOYMENT.md` → 05_INFRAESTRUTURA/
- Todos os `DIA_N_*.md`, `FASE_N_*.md`, `DAY*_*.md` → 07_HISTORICO/

**Criar documentação urgente:**
- `intellicare-admin/docs/` — especificação funcional e técnica
- `intellicare-gestor/docs/` — especificação funcional e técnica

---

## Relação entre versões e branches

```
Branch no GitHub               Pasta em DOCUMENTACAO/
─────────────────────          ──────────────────────────────────
feat/v2.0.0-keycloak     ←→   04_VERSOES/V2.0.0_KEYCLOAK/
feat/v2.0.2-admin-gestor ←→   04_VERSOES/V2.0.2_ADMIN_GESTOR/
feat/v2.1.0-aiged        ←→   04_VERSOES/V2.1.0_AIGED_CONHECIMENTO/
feat/v2.1.x-multitenancy ←→   04_VERSOES/V2.1.x_MULTITENANCY/
feat/v3.0.0-medplus-on   ←→   04_VERSOES/V3.0.0_MEDPLUS_ON/
```

---

## Plano de execução

**Etapa 1 — Criar estrutura vazia** (Claude executa)
Criar todas as pastas de `DOCUMENTACAO/` sem mover nada ainda.

**Etapa 2 — Migrar docs/ central** (Claude executa, Eduardo valida)
Mover e consolidar os arquivos de `docs/`, raiz e `PADRAO_ENTREGA/`.
Os 22 docs de deploy viram ~6 documentos consolidados.

**Etapa 3 — Limpar módulos** (Claude executa)
Excluir logs de teste, mover guias de infra e relatórios históricos
dos módulos para DOCUMENTACAO/. Os docs/ locais de spec permanecem.

**Etapa 4 — Arquivar docs/ antiga** (Eduardo executa)
Eduardo faz backup, move `docs/` para `07_HISTORICO/docs_antigo/`
e retira ela do projeto ativo.

---

## Pontos para discussão

1. **PLANNER-ANTIGRAVITY** — ondas 1-11 do MEDPLUS_ON: planejamento ativo ou histórico?
   Define se vão para `04_VERSOES/V3.0.0_MEDPLUS_ON/` ou `07_HISTORICO/`.

2. **CARGA_DADOS** (7 documentos) — ficam em `03_ARQUITETURA/` ou `04_VERSOES/`?

3. **EXTENSAO_ODONTOLOGIA** — feature futura (`04_VERSOES/`) ou estudo (`07_HISTORICO/`)?

4. **PADRAO_ENTREGA/ .md files** — os relevantes migram para `02_NORMAS_E_PADROES/`
   ou `05_INFRAESTRUTURA/` dependendo do conteúdo. Os scripts `.ps1` ficam onde estão.

5. **intellicare-admin e intellicare-gestor** — criar specs do zero é urgente?
   Se sim, posso criar os templates de spec funcional + técnica para ambos.

---

*Proposta revisada em 2026-03-08 — inclui varredura completa de 18 módulos (295 arquivos adicionais identificados).*
