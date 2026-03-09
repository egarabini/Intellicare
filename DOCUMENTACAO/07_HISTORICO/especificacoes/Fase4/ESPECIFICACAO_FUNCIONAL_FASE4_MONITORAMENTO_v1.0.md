# ESPECIFICACAO_FUNCIONAL — Fase 4: Monitoramento e Observabilidade

**Versão:** 1.0  
**Data:** 2026-02-19  
**Status:** Rascunho — aguardando aprovação  
**Referência:** `docs/PLANNER-CURSOR/ESTRATEGIA_PROXIMOS_PASSOS.md`  
**Pré-requisitos:** Fase 3 concluída (projeto no ar)

---

## 1. Contexto e Objetivo

O projeto está no ar (Fase 3). Para reagir a falhas e garantir visibilidade operacional, é essencial que Prometheus e Grafana — já presentes na infraestrutura — estejam configurados e funcionais, com alertas básicos e dashboard mínimo.

**Objetivo:** Garantir visibilidade operacional do sistema — métricas coletadas, alertas configurados, dashboard único — permitindo identificar e reagir a falhas de forma proativa.

---

## 2. Escopo

### 2.1 Dentro do escopo

- Validação de que Prometheus coleta métricas dos serviços
- Configuração de alertas básicos (serviço down, alta latência)
- Criação de dashboard Grafana mínimo (status dos 6 módulos + portal)
- Documentação de como acessar e interpretar métricas e alertas
- Integração dos backends com Prometheus (endpoint /metrics)

### 2.2 Fora do escopo

- APM (Application Performance Monitoring) completo
- Log aggregation centralizada (ELK, Loki)
- Tracing distribuído
- SLO/SLI avançados
- Integração com PagerDuty, Slack ou similares (pode ser fase posterior)

---

## 3. Requisitos Funcionais

| ID | Requisito | Prioridade |
|----|-----------|------------|
| RF-001 | Prometheus deve coletar métricas dos serviços da demo (backends + infra) | Obrigatório |
| RF-002 | Cada backend deve expor endpoint `/metrics` compatível com Prometheus | Obrigatório |
| RF-003 | Alertas devem ser configurados em `alerts.yml` (ou equivalente) | Obrigatório |
| RF-004 | Deve existir alerta para serviço down (health check falhou) | Obrigatório |
| RF-005 | Deve existir alerta para alta latência (quando aplicável) | Desejável |
| RF-006 | Dashboard Grafana deve exibir status dos 6 módulos + portal | Obrigatório |
| RF-007 | Documentação deve explicar como acessar Prometheus e Grafana e interpretar dados | Obrigatório |

---

## 4. Requisitos Não Funcionais

| ID | Requisito | Prioridade |
|----|-----------|------------|
| RNF-001 | Prometheus e Grafana devem estar acessíveis no ambiente de deploy | Obrigatório |
| RNF-002 | Retenção de métricas mínima de 7 dias | Obrigatório |
| RNF-003 | Dashboard deve carregar em tempo aceitável (< 10s) | Desejável |

---

## 5. Critérios de Aceite

| ID | Critério |
|----|----------|
| CA-001 | Dado Prometheus em execução, quando acessar targets, então todos os serviços da demo aparecem como UP |
| CA-002 | Dado um backend parado, quando configurado, então alerta de serviço down é disparado |
| CA-003 | Dado Grafana, quando acessar dashboard, então exibe status dos 6 módulos + portal |
| CA-004 | Dado GUIA_MONITORAMENTO.md, quando seguir, então consegue acessar Prometheus e Grafana e interpretar métricas |
| CA-005 | Dado `alerts.yml`, quando validar, então regras estão sintaticamente corretas e ativas |

---

## 6. Cenários de Uso

### Cenário 1: Operador verifica saúde do sistema

1. Acessa Grafana (ex.: http://staging:3000)
2. Abre dashboard "IntelliCare - Status"
3. Visualiza status de cada módulo (verde/vermelho)
4. Identifica módulo com problema
5. Resultado esperado: visão única do sistema

### Cenário 2: Alerta de serviço down

1. Um backend para (crash ou reinício)
2. Prometheus detecta falha no health check
3. Alerta é disparado (estado: firing)
4. Operador é notificado (conforme canal configurado)
5. Resultado esperado: reação proativa à falha

### Cenário 3: Novo dev entende o monitoramento

1. Lê GUIA_MONITORAMENTO.md
2. Acessa Prometheus e executa query básica
3. Acessa Grafana e navega no dashboard
4. Resultado esperado: entende como verificar saúde do sistema

---

## 7. Restrições e Premissas

### 7.1 Restrições

- Prometheus e Grafana já existem no `docker-compose.yml`; esta fase configura e valida, não cria do zero
- Backends devem expor `/metrics` — verificar se já existe (prometheus-client)

### 7.2 Premissas

- Fase 3 concluída (projeto no ar)
- Prometheus e Grafana rodando no ambiente de deploy
- Backends compatíveis com formato Prometheus (prometheus_client em Python)

---

## 8. Entregáveis

| # | Entregável | Descrição |
|---|------------|-----------|
| 1 | prometheus.yml validado | Configuração com targets dos 6 backends + infra |
| 2 | alerts.yml funcional | Regras de alerta (serviço down, latência) |
| 3 | Dashboard Grafana | Painel com status dos 6 módulos + portal |
| 4 | GUIA_MONITORAMENTO.md | Documento em docs/PLANNER-CURSOR/ com acesso e interpretação |

**Artefatos do fluxo (neste diretório):** O dev deve registrar aqui a ESPECIFICACAO_TECNICA e o PLANO_IMPLEMENTACAO antes da implementação.

---

## 9. Referências

- `prometheus.yml` — configuração existente
- `alerts.yml` — regras existentes
- `grafana-datasources.yml`, `grafana-dashboards.yml` — provisionamento existente
- `docs/PLANNER-CURSOR/ESTRATEGIA_PROXIMOS_PASSOS.md`

---

## 10. Histórico de Alterações

| Versão | Data | Alteração |
|--------|------|-----------|
| 1.0 | 2026-02-19 | Versão inicial |
