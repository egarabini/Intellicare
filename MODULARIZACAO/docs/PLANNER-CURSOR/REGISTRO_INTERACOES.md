# Registro de Interações — PLANNER-CURSOR

**Papéis:** ARQUITETO (humano) | PLANEJADOR (IA Cursor)

Este documento registra cronologicamente as interações e decisões entre ARQUITETO e PLANEJADOR no projeto IntelliCare MODULARIZACAO.

---

## Formato do Registro

Cada entrada segue o padrão:

```
### [YYYY-MM-DD] — [Título resumido]

**Solicitação:** [o que foi pedido]  
**Ação:** [o que foi feito]  
**Decisões:** [decisões tomadas, se houver]  
**Artefatos gerados:** [arquivos/documentos criados]  
**Próximos passos:** [pendências ou próximas ações]
```

---

## Histórico

### 2026-02-19 — Estudo completo e criação do PLANNER-CURSOR

**Solicitação:**  
Realizar estudo completo do projeto, criar pasta `docs/PLANNER-CURSOR` e registrar toda a interação. Definir papéis: ARQUITETO (humano), PLANEJADOR (IA), fluxo com agentes desenvolvedores (ESPECIFICACAO_FUNCIONAL → ESPECIFICACAO_TECNICA + PLANO_IMPLEMENTACAO → Aprovação/RESSALVAS → Implementação).

**Ação:**  
- Exploração completa da estrutura do projeto via agente de exploração  
- Leitura de documentação existente (PLANO_UNIFICACAO_OPENAPI, API_CATALOG, README_DEMO, docker-compose, migrations, etc.)  
- Criação da pasta `docs/PLANNER-CURSOR`  
- Elaboração dos documentos: README.md, ESTUDO_PROJETO.md, VISAO_PLANEJADOR.md, MODELO_ESPECIFICACAO.md, REGISTRO_INTERACOES.md  

**Decisões:**  
- Estrutura de documentação centralizada em PLANNER-CURSOR  
- Modelo de fluxo: ARQUITETO + PLANEJADOR → ESPECIFICACAO_FUNCIONAL → Agentes → ESPECIFICACAO_TECNICA + PLANO_IMPLEMENTACAO → Aprovação/RESSALVAS → Implementação  
- Proposta de ondas de evolução (Fundação, Segurança, Integração, Escalabilidade)  
- Convenção de nomenclatura para especificações versionadas  

**Artefatos gerados:**  
- `docs/PLANNER-CURSOR/README.md`  
- `docs/PLANNER-CURSOR/ESTUDO_PROJETO.md`  
- `docs/PLANNER-CURSOR/VISAO_PLANEJADOR.md`  
- `docs/PLANNER-CURSOR/MODELO_ESPECIFICACAO.md`  
- `docs/PLANNER-CURSOR/REGISTRO_INTERACOES.md`  

**Próximos passos:**  
1. ARQUITETO validar estudo e visão  
2. Definir primeira ESPECIFICACAO_FUNCIONAL a ser entregue aos agentes  
3. Criar pasta `docs/PLANNER-CURSOR/especificacoes/` quando houver primeira especificação  

---

### 2026-02-19 — Informação sobre Git e Deploy

**Solicitação:**  
Registrar informação importante: o projeto está no Git `eduardo/intellicare`; até o momento não foi feito nenhum deploy nem controle de atualizações do Git.

**Ação:**  
- Atualização do ESTUDO_PROJETO.md com nova seção "10. Controle de Versão e Deploy"  
- Atualização do VISAO_PLANEJADOR.md: inclusão de "Onda 4 — Controle de Versão e Deploy" (estratégia de branches, tags, releases, pipeline CI/CD)  
- Renumeração da antiga Onda 4 para Onda 5 (Escalabilidade e Produção)  

**Decisões:**  
- Tratar controle de versão e deploy como onda prioritária antes de escalabilidade  
- Documentar status atual: repositório em uso, deploy inexistente, controle de atualizações não implementado  

**Artefatos alterados:**  
- `docs/PLANNER-CURSOR/ESTUDO_PROJETO.md`  
- `docs/PLANNER-CURSOR/VISAO_PLANEJADOR.md`  

**Próximos passos:**  
- Quando houver primeira ESPECIFICACAO_FUNCIONAL de deploy/CI, incluir estratégia de branches (main/develop?), tags semânticas, e pipeline básico  

---

### 2026-02-19 — Estratégia de próximos passos e priorização para projeto no ar

**Solicitação:**  
Traçar estratégia de próximos passos, organizar o projeto e priorizar ações para colocar o projeto no ar o mais cedo possível e sem erros. Contexto: evolução rápida, visão avançada, desafio na área da saúde.

**Ação:**  
- Criação do documento `ESTRATEGIA_PROXIMOS_PASSOS.md`  
- Reorganização em 5 fases: Estabilização → Git → Deploy Mínimo → Monitoramento → Produção Ready  
- Priorização: Fases 1 e 2 na primeira semana; Fases 3–4 nas 2–4 semanas seguintes; meta de 4–6 semanas para projeto no ar  
- Princípios: simplicidade, zero erros em saúde, incremental, reversível, documentado  

**Decisões:**  
- Fase 1 (Estabilização) como prioridade máxima — garantir que demo funciona localmente antes de qualquer deploy  
- Deploy mínimo viável via Docker Compose ou plataforma (Railway/Render/Fly.io) antes de Kubernetes  
- Auth e LGPD na Fase 5 (pós-deploy), exceto se houver dados reais antes  

**Artefatos gerados:**  
- `docs/PLANNER-CURSOR/ESTRATEGIA_PROXIMOS_PASSOS.md`  

**Próximos passos:**  
1. ARQUITETO validar estratégia  
2. PLANEJADOR elaborar ESPECIFICACAO_FUNCIONAL da Fase 1 (Estabilização) para agentes desenvolvedores  

---

### 2026-02-19 — Premissa ambiente virtual + Início Fase 1 Estabilização

**Solicitação:**  
Frisar nas especificações que sempre executar em ambiente virtual; havia muitos problemas de compatibilidade de versões de bibliotecas Python. Iniciar conforme sugerido: Fase 1 Estabilização.

**Ação:**  
- Inclusão da premissa "sempre executar em ambiente virtual" no MODELO_ESPECIFICACAO.md (Restrições e Premissas, e nova seção Premissas Obrigatórias para Python)  
- Inclusão da premissa na ESTRATEGIA_PROXIMOS_PASSOS.md (princípios e checklist Fase 1)  
- Criação da ESPECIFICACAO_FUNCIONAL_FASE1_ESTABILIZACAO_v1.0.md para entrega aos agentes desenvolvedores  

**Decisões:**  
- Ambiente virtual (venv, poetry, conda) é obrigatório em todas as especificações Python  
- Fase 1 Estabilização aprovada para início imediato  
- Item 1.7 adicionado ao checklist: garantir que cada módulo Python use ambiente virtual  

**Artefatos gerados/alterados:**  
- `docs/PLANNER-CURSOR/MODELO_ESPECIFICACAO.md`  
- `docs/PLANNER-CURSOR/ESTRATEGIA_PROXIMOS_PASSOS.md`  
- `docs/PLANNER-CURSOR/especificacoes/Fase1/ESPECIFICACAO_FUNCIONAL_FASE1_ESTABILIZACAO_v1.0.md`  

**Próximos passos:**  
1. Agentes desenvolvedores recebem ESPECIFICACAO_FUNCIONAL_FASE1_ESTABILIZACAO_v1.0.md  
2. Agentes produzem ESPECIFICACAO_TECNICA e PLANO_IMPLEMENTACAO no mesmo diretório `especificacoes/Fase1/`  
3. ARQUITETO + PLANEJADOR aprovam ou registram RESSALVAS  

---

### 2026-02-19 — Reestruturação: diretório por fase

**Solicitação:**  
ARQUITETO criou diretório `Fase1` e transferiu a especificação funcional para lá. Dev registrará ESPECIFICACAO_TECNICA e PLANO_IMPLEMENTACAO neste diretório, mantendo controle de cada ação bem documentada.

**Ação:**  
- Atualização do MODELO_ESPECIFICACAO.md com nova estrutura de pastas (um diretório por fase/feature)  
- Atualização do README.md com caminhos corretos  
- Atualização do REGISTRO_INTERACOES com caminho `especificacoes/Fase1/`  

**Decisões:**  
- Estrutura: `especificacoes/Fase1/`, `especificacoes/Fase2/`, etc.  
- Cada fase concentra: ESPECIFICACAO_FUNCIONAL, ESPECIFICACAO_TECNICA, PLANO_IMPLEMENTACAO, RESSALVAS  

**Artefatos alterados:**  
- `docs/PLANNER-CURSOR/MODELO_ESPECIFICACAO.md`  
- `docs/PLANNER-CURSOR/README.md`  
- `docs/PLANNER-CURSOR/REGISTRO_INTERACOES.md`  

---

### 2026-02-19 — Especificação funcional da Fase 2 (Git)

**Solicitação:**  
Escrever a especificação funcional da Fase 2.

**Ação:**  
- Criação do diretório `especificacoes/Fase2/`  
- Elaboração da ESPECIFICACAO_FUNCIONAL_FASE2_GIT_v1.0.md  

**Conteúdo principal:**  
- Escopo: estratégia de branches, .gitignore, CHANGELOG, primeira tag, processo de release  
- RF-001 a RF-008: branches (main, develop), .gitignore, CHANGELOG, tag semântica, documentação  
- CA-001 a CA-006: critérios testáveis para cada entregável  
- Entregáveis: ESTRATEGIA_GIT.md, CHANGELOG.md, PROCESSO_RELEASE.md, .gitignore, primeira tag  

**Artefatos gerados:**  
- `docs/PLANNER-CURSOR/especificacoes/Fase2/ESPECIFICACAO_FUNCIONAL_FASE2_GIT_v1.0.md`  

**Próximos passos:**  
1. ARQUITETO validar especificação  
2. Dev produzir ESPECIFICACAO_TECNICA e PLANO_IMPLEMENTACAO em `especificacoes/Fase2/`  

---

### 2026-02-19 — Especificações funcionais das Fases 3, 4 e 5

**Solicitação:**  
Completar as especificações funcionais para todas as outras fases.

**Ação:**  
- Criação das pastas `especificacoes/Fase3/`, `especificacoes/Fase4/`, `especificacoes/Fase5/`  
- Elaboração das ESPECIFICACAO_FUNCIONAL para:  
  - **Fase 3:** Deploy Mínimo Viável (.env.example, docker-compose.full, GUIA_DEPLOY, smoke tests, URL staging)  
  - **Fase 4:** Monitoramento (Prometheus, Grafana, alertas, dashboard, GUIA_MONITORAMENTO)  
  - **Fase 5:** Produção Ready (Auth/Keycloak, LGPD, backup, retenção, testes integração, CI/CD)  

**Artefatos gerados:**  
- `docs/PLANNER-CURSOR/especificacoes/Fase3/ESPECIFICACAO_FUNCIONAL_FASE3_DEPLOY_v1.0.md`  
- `docs/PLANNER-CURSOR/especificacoes/Fase4/ESPECIFICACAO_FUNCIONAL_FASE4_MONITORAMENTO_v1.0.md`  
- `docs/PLANNER-CURSOR/especificacoes/Fase5/ESPECIFICACAO_FUNCIONAL_FASE5_PRODUCAO_v1.0.md`  

**Próximos passos:**  
- ARQUITETO validar especificações  
- Devs produzirem ESPECIFICACAO_TECNICA e PLANO_IMPLEMENTACAO por fase, conforme prioridade  

---

### 2026-02-20 — Aceite e ressaltas Fase 2 para dev2

**Solicitação:**  
Gerar documento com ressaltas e aceite para orientação do dev2 dentro da Fase 2.

**Ação:**  
- Criação do documento `ACEITE_E_RESSALVAS_FASE2_2026-02-20.md` em `especificacoes/Fase2/`  
- Parecer: APROVADO PARA IMPLEMENTAÇÃO  
- Ressalva R1: Conteúdo do CHANGELOG deve refletir estado real do projeto (evitar itens de template como Keycloak em 9 módulos, Matrix/Synapse)  

**Artefatos gerados:**  
- `docs/PLANNER-CURSOR/especificacoes/Fase2/ACEITE_E_RESSALVAS_FASE2_2026-02-20.md`  

---

### 2026-02-20 — Pasta desenvolvimento V1.0.0-entregas-rapidas-modulares

**Solicitação:**  
Identificar entregável mais rápido (modular, sem interferir em outros módulos). Criar pasta desenvolvimento com subpasta V1.0.0-[abordagem], pastas de cada fase com especificações funcionais, e na raiz: o que estamos desenvolvendo e o que esperamos alcançar.

**Ação:**  
- Criação de `docs/PLANNER-CURSOR/desenvolvimento/V1.0.0-entregas-rapidas-modulares/`  
- README na raiz com: entregas rápidas identificadas (OpenAPI, /health, README, .env.example, lint, /metrics), o que desenvolvemos, o que esperamos alcançar  
- Pastas Fase1 a Fase5, cada uma com README referenciando especificação funcional e entregas rápidas complementares  

**Entregas rápidas identificadas:**  
1. Exportar OpenAPI por módulo (1–2h/módulo)  
2. Padronizar /health e /info (30min/módulo)  
3. README por módulo (1h/módulo)  
4. .env.example por módulo (30min/módulo)  
5. Lint/format Ruff (30min/módulo)  
6. Endpoint /metrics Prometheus (1h/módulo)  

**Artefatos gerados:**  
- `docs/PLANNER-CURSOR/desenvolvimento/V1.0.0-entregas-rapidas-modulares/README.md`  
- `docs/PLANNER-CURSOR/desenvolvimento/V1.0.0-entregas-rapidas-modulares/Fase1/README.md` a Fase5/README.md  

---

### 2026-02-20 — Configuração mínima para staging/homologação

**Solicitação:**  
Qual a configuração mínima para deploy de todos os módulos em homologação (stage), funcional e apresentável — não produção.

**Ação:**  
- Criação do documento `CONFIGURACAO_MINIMA_STAGING.md`  

**Conteúdo:**  
- Recursos: 4 vCPUs, 8 GB RAM, 50 GB (mínimo)  
- Infra: Postgres 15 + Redis 7  
- 6 backends + portal (build estático)  
- Variáveis de ambiente (DATABASE_URL, REDIS_URL, VITE_*)  
- Opções: VPS + Docker Compose, PaaS, híbrido  
- Custo estimado: $20–80/mês  

**Artefatos gerados:**  
- `docs/PLANNER-CURSOR/CONFIGURACAO_MINIMA_STAGING.md`  

---

*[Novas interações serão adicionadas abaixo, em ordem cronológica inversa.]*
