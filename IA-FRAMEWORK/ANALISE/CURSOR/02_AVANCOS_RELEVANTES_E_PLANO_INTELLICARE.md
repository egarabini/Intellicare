# Avanços Relevantes para o IntelliCare e Plano Resumido de Implementação

## 1) O que traria avanço significativo para o IntelliCare

Com base na arquitetura atual do IntelliCare (módulos Python, contratos por camada, multi-tenant, FHIR R4, RAG/SLM/pgvector), os maiores ganhos viriam de cinco blocos:

### A. Pipeline clínico orientado por evidência (inspirado no Deep Research)

**Ganho:** aumentar robustez analítica e reduzir variabilidade nas recomendações clínicas.  
**Aplicação:** criar fluxo padrão para perguntas clínicas complexas:

1. formulação da pergunta clínica;
2. busca e seleção de evidências;
3. síntese estruturada;
4. auditoria de viés/confiabilidade;
5. recomendação final com nível de confiança.

### B. Matriz de executor (Worker/Agent/Hybrid/Human) por tarefa clínica

**Ganho:** menor custo, mais previsibilidade e melhor gestão de risco assistencial.  
**Aplicação:** classificar cada etapa de cada módulo (`cuidado`, `florence`, `oswaldo`) por tipo de executor:

- **Worker** para transformações determinísticas (FHIR mapping, validações, ETL);
- **Agent** para análise semântica;
- **Hybrid** para saídas que exigem revisão humana;
- **Human** para decisões clínicas críticas.

### C. Quality gates clínicos e de integração

**Ganho:** padronizar o “definition of done” entre módulos e evitar regressão silenciosa.  
**Aplicação:** instituir gates objetivos antes de publicação de novas capacidades:

- integridade estrutural de artefatos;
- aderência a contratos e rotas obrigatórias;
- validação semântica mínima por tipo de análise;
- segurança e rastreabilidade clínica;
- score de aprovação por dimensão.

### D. Handoffs explícitos e protocolo de governança

**Ganho:** reduzir perda de contexto entre times/módulos e melhorar auditabilidade.  
**Aplicação:** adotar handshake `Existing -> Gap -> Decision` e contrato de evidência em demandas e entregas técnicas.

### E. Execução paralela controlada (DAG/waves) para pipelines analíticos

**Ganho:** reduzir latência para fluxos complexos sem inflar custo de modelo.  
**Aplicação:** paralelizar etapas independentes (ex.: extrações e validações paralelas), mantendo checkpoints de segurança para junção de resultados.

---

## 2) Plano resumido de implementação (prático e incremental)

## Fase 0 (1-2 semanas) — Arquitetura de adoção e baseline

- Definir 1 fluxo-alvo por módulo (`cuidado`, `florence`, `oswaldo`) para piloto.
- Criar matriz inicial de executor por etapa desses fluxos.
- Definir 6-8 quality gates mínimos do IntelliCare (incluindo segurança clínica/FHIR).
- Padronizar template de handoff técnico com evidência e status (`implemented/partial/concept`).

**Entregáveis:**
- `docs/design-docs/intellicare-executor-matrix.md`
- `docs/design-docs/intellicare-quality-gates.md`
- `docs/design-docs/intellicare-handoff-governance.md`

## Fase 1 (2-4 semanas) — Piloto no módulo `cuidado`

- Implementar pipeline “evidência -> síntese -> recomendação” com checkpoints.
- Mover tarefas determinísticas para workers/scripts sempre que possível.
- Inserir revisão Hybrid em saídas clínicas de maior risco.
- Medir baseline vs pós-piloto (tempo, custo, taxa de retrabalho, qualidade da saída).

**Entregáveis:**
- workflow clínico piloto em `modules/cuidado`;
- relatório de métricas comparativas (antes/depois);
- catálogo inicial de falhas e critérios de veto.

## Fase 2 (2-3 semanas) — Expansão para `florence` e `oswaldo`

- Replicar padrões validados do piloto, ajustando por domínio de cada módulo.
- Introduzir scorecard único de qualidade para os três módulos.
- Integrar checkpoints de compliance técnica e rastreabilidade em produção.

**Entregáveis:**
- padrão comum de validação inter-módulos;
- dashboards operacionais de qualidade e custo;
- playbook de operação para incidentes de pipeline.

## Fase 3 (contínua) — Otimização e escala

- Identificar tarefas Agent com alta repetibilidade e migrar para Worker.
- Ajustar thresholds de gates por criticidade clínica.
- Evoluir biblioteca de templates/checklists por tipo de caso clínico.
- Criar rotina de revisão trimestral dos padrões de qualidade.

---

## 3) Priorização objetiva (o que fazer primeiro)

1. **Executor Matrix + gates mínimos** (melhor relação impacto/esforço);
2. **Piloto clínico em `cuidado` com HITL por risco**;
3. **Governança de handoff/evidência entre módulos**;
4. **Paralelização DAG em etapas já estabilizadas**.

---

## 4) Resultado esperado para a plataforma

Se implementado em ondas curtas, o IntelliCare tende a ganhar:

- mais consistência clínica e técnica entre módulos;
- menor custo operacional de IA por melhor alocação de executor;
- maior velocidade de entrega com menos retrabalho;
- melhor auditabilidade para contexto regulado de saúde.

