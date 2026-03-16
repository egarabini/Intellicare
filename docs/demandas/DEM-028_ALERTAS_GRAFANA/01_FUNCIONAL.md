# DEM-028 — Alertas Grafana (Alertmanager — E-mail + Slack)

## Objetivo

Configurar alertas automáticos no Grafana para que a equipe de operações seja notificada quando métricas críticas da plataforma ultrapassarem limites definidos, via e-mail e/ou Slack, sem necessidade de monitoramento manual do dashboard.

---

## Contexto

O IntelliCare já possui Prometheus + Grafana operacionais (DEM-025) com 5 targets e 10 painéis. Esta DEM adiciona a camada de alertas: regras de threshold no Grafana/Prometheus e canais de entrega (e-mail SMTP e Slack webhook).

---

## Alertas a configurar

### Categoria: Infraestrutura

| ID | Nome | Condição | Severidade |
|----|------|----------|------------|
| ALT-I01 | Serviço down | `up{job="intellicare-api"} == 0` por 1 min | 🔴 Crítico |
| ALT-I02 | CPU alta | Node CPU > 85% por 5 min | 🟡 Warning |
| ALT-I03 | Memória alta | Node memória usada > 90% por 5 min | 🟡 Warning |
| ALT-I04 | Disco crítico | Espaço livre < 10% por 10 min | 🔴 Crítico |
| ALT-I05 | PostgreSQL down | `pg_up == 0` por 1 min | 🔴 Crítico |
| ALT-I06 | Redis down | `redis_up == 0` por 1 min | 🔴 Crítico |

### Categoria: Aplicação

| ID | Nome | Condição | Severidade |
|----|------|----------|------------|
| ALT-A01 | Taxa de erros HTTP alta | HTTP 5xx > 5% das requests por 2 min | 🟡 Warning |
| ALT-A02 | Latência elevada | p95 latência API > 2s por 5 min | 🟡 Warning |
| ALT-A03 | Keycloak down | `up{job="keycloak"}` ausente por 1 min | 🔴 Crítico |

---

## Canais de notificação

### E-mail (SMTP)
- Destinatário: `egarabini@gmail.com` (configurável via variável de ambiente)
- Remetente: `alertas@intellicare.ia.br`
- Assunto: `[IntelliCare] 🔴 CRÍTICO: <nome do alerta>` ou `[IntelliCare] ⚠️ WARNING: <nome do alerta>`
- Corpo: nome do alerta, condição, valor atual, link para o painel Grafana

### Slack
- Canal: `#intellicare-alertas` (configurável)
- Mensagem: bloco com severidade (cor), nome, condição, valor atual e link para Grafana
- Menção `@channel` apenas para alertas Críticos

---

## Comportamento esperado

| Situação | Comportamento |
|----------|---------------|
| Alerta dispara | Notificação enviada em até 1 minuto para todos os canais configurados |
| Alerta resolvido | Notificação de resolução enviada automaticamente (`[RESOLVED]`) |
| Alerta silenciado | Sem notificação durante o período de silêncio |
| Canal não configurado | Sistema continua funcionando, apenas aquele canal é ignorado |

---

## Critérios de aceitação

1. Todas as 9 regras de alerta aparecem na UI do Grafana (Alerting → Alert rules)
2. Um alerta de teste (`up == 0` forçado manualmente) dispara notificação em até 1 min
3. E-mail recebido com remetente, assunto e corpo corretos
4. Slack recebe mensagem formatada com bloco colorido (vermelho=crítico, amarelo=warning)
5. Alerta resolvido envia notificação de resolução
6. Variáveis de configuração (SMTP, Slack webhook) externalizadas em `.env`
7. Configuração reproduzível via arquivos versionados (sem setup manual no Grafana UI)
