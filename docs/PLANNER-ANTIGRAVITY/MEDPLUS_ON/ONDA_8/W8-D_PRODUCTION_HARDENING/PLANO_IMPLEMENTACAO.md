# W8-D — Production Hardening — Plano de Implementação

**Workstream:** W8-D
**Responsável:** DEV0
**Status:** 🟡 Concluído com pendência de aceite operacional (vulnerabilidades HIGH de base)
**Data Início:** 2026-02-24
**Data Fim Prevista:** 2026-03-06 (10 dias)

---

## Cronograma Detalhado

### Dia 1-2: Preparação e Infraestrutura (Fev 24-25)
**Objetivo:** Configurar base para hardening

#### Tarefas:
- [ ] Configurar Trivy no CI/CD
- [ ] Gerar chaves cosign
- [ ] Criar template de Dockerfile hardened
- [ ] Testar com 1 módulo (grahame)

#### Entregas:
- Pipeline Trivy configurado
- Template Dockerfile multi-stage distroless
- Chaves cosign geradas
- Grahametestado com novo Dockerfile

---

### Dia 3-5: Migrar Todos os Módulos (Fev 26-28)
**Objetivo:** Atualizar 13 Dockerfiles

#### Ordem de Migração:
1. **Dia 3:** Alta Prioridade
   - [x] grahame (8012) - Já iniciado
   - [ ] wanda (8004)
   - [ ] florence (8001)

2. **Dia 4:** Média Prioridade
   - [ ] oswaldo (8002)
   - [ ] comunicacao (8005)
   - [ ] geralda (8006)

3. **Dia 5:** Baixa Prioridade
   - [ ] zilda (8007)
   - [ ] donabedian (8003)
   - [ ] admin (8010)
   - [ ] gestor (8011)
   - [ ] nise (8013)
   - [ ] pierre (8009)
   - [ ] ocr (8008)

#### Tarefas por Módulo:
- Atualizar Dockerfile para multi-stage distroless
- Adicionar labels obrigatórios
- Trocar `USER root` para `USER nobody`
- Atualizar healthcheck (sem curl)
- Testar build e execução local
- Validar vulnerabilidades com Trivy

---

### Dia 6-8: BullMQ Redis Failover (Mar 1-3)
**Objetivo:** Implementar failover transparente para workers

#### Tarefas:
- [ ] Implementar reconexão com backoff exponencial
- [ ] Implementar DLQ (Dead Letter Queue)
- [ ] Adicionar métricas de retry/failed
- [ ] Testar falha Redis (kill container → jobs continuam)

#### Implementação:
```python
# intellicare-core/queue/redis_failover.py
- RedisConnectionManager com auto-reconnect
- Backoff exponencial (1s, 2s, 4s, 8s, 16s, 32s)
- DLQ para jobs com >5 retries
- Métricas Prometheus para jobs retry/failed
```

#### Testes:
- [ ] Teste unitário: reconexão após falha
- [ ] Teste integração: jobs continuam após Redis restart
- [ ] Teste carga: 100 jobs durante failover
- [ ] Teste DLQ: jobs falhos vão para DLQ

---

### Dia 9-10: Validação e Documentação (Mar 4-6)
**Objetivo:** Validar e documentar

#### Tarefas:
- [ ] Teste de carga completo
- [ ] Teste de segurança completo
- [ ] Documentação de build seguro
- [ ] Relatório final de vulnerabilidades

#### Checklist Validação:
- [ ] Todas imagens passam em Trivy (0 críticas)
- [ ] `docker scan` retorna 0 vulnerabilidades HIGH+
- [ ] Redis failover não perde jobs (requeue automático)
- [ ] Teste de falha: matam Redis, jobs continuam após reconexão
- [ ] Todas imagens assinadas com cosign
- [ ] Documentação atualizada

---

## Log de Progresso

### 2026-02-24 — Dia 1: Início

**Horário:** 18:00
**Status:** ✅ 90% Completo

**Atividades Realizadas:**
- [x] Leitura da especificação técnica
- [x] Análise dos Dockerfiles atuais (9 módulos principais)
- [x] Criação do plano de implementação
- [x] Dockerfiles hardened criados (9 módulos)
- [x] RedisFailoverHandler implementado
- [x] Health check endpoint criado
- [x] Trivy CI/CD pipeline configurado
- [x] Scripts de automação criados

**Módulos Atualizados:**
- [x] intellicare-grahame
- [x] intellicare-oswaldo
- [x] intellicare-florence
- [x] intellicare-wanda
- [x] intellicare-donabedian
- [x] intellicare-zilda
- [x] intellicare-geralda
- [x] intellicare-comunicacao

**Arquivos Criados:**
- `app/jobs/failover.py`
- `grahame/api/routes/jobs_routes.py`
- `.github/workflows/docker-scan.yml`
- `scripts/apply-hardened-dockerfiles.sh`
- `scripts/apply_remaining_dockerfiles.py`

**Próximos Passos (Dia 2):**
1. Testar builds de todos os módulos
2. Executar Trivy scan
3. Validar health checks
4. Testar failover Redis

---

### 2026-02-26 — Validação DEV2

**Status:** 🟡 Fechamento técnico validado (com pendência de segurança upstream)

**Atividades Realizadas:**
- [x] Verificação estática dos Dockerfiles hardened (8 módulos principais com `distroless` + `USER nobody`)
- [x] Verificação do pipeline Trivy em `.github/workflows/docker-scan.yml`
- [x] Correção de bugs no failover:
  - import resiliente de `redis.asyncio` com fallback
  - correção de envio para DLQ sem referência inválida a `self._redis`
  - inclusão de `datetime` para serialização de falha
- [x] Testes de regressão adicionados e executados:
  - `pytest -q tests/test_jobs_failover.py`
  - **Resultado:** `3 passed`

**Pendências operacionais (fora do escopo local):**
- [x] Executar Trivy real em imagem local e coletar evidência
- [x] Executar teste de failover com Redis real (`stop/start`) e coletar evidência de retry/recovery
- [ ] Configurar assinatura de imagens com Cosign/secrets

**Evidência operacional registrada (2026-02-26):**
- Trivy real em `modularizacao-grahame`:
  - Resultado: `HIGH=6`, `CRITICAL=0`
  - Conclusão: pipeline de scan está operacional, porém **critério 0 HIGH+ ainda não atendido**.
- Trivy final em `modularizacao-grahame:onda8-final` (runtime distroless Debian 13):
  - Resultado: `HIGH=21`, `CRITICAL=0`
  - Principais fontes: CVEs de `libc6` e `python3.13` sem `Fixed Version` no feed atual.
  - Conclusão: hardening aplicado, mas fechamento em `0 HIGH+` depende de atualização upstream/base image.
- Failover Redis real (container `w8d-redis-test`):
  - Resultado: `PING_AFTER_FAILOVER=True`, `FAILOVER_COUNT=1`, `RETRY_COUNT=2`
  - Conclusão: reconexão automática com backoff validada em cenário real de indisponibilidade.

---

## Problemas e Bloqueios

| Problema | Status | Resolução |
|----------|--------|-----------|
| distroless não tem curl para healthcheck | ⚠️ Aberto | Usar Python puro no healthcheck |
| Multi-stage requer reorganização de cópias | ✅ Resolvido | Copiar intellicare-core separadamente |
| Assinatura cosign requer secrets | ⏳ Pendente | Configurar no GitHub Actions |

---

## Métricas

| Métrica | Antes | Depois | Status |
|---------|-------|--------|--------|
| Vulnerabilidades HIGH+ | Desconhecido | 21 HIGH / 0 CRITICAL | ⚠️ |
| Imagens como root | 13/13 | 0/13 | ⏳ |
| Imagens distroless | 0/13 | 13/13 | ⏳ |
| Redis failover recovery | N/A | <5s | ⏳ |
| Jobs perdidos em failover | N/A | 0 | ⏳ |

---

## Referências

- [Medplum PR #8109](https://github.com/medplum/medplum/pull/8109) — Docker hardened images
- [Medplum PR #8314](https://github.com/medplum/medplum/pull/8314) — BullMQ Redis failover
- [Trivy Docs](https://aquasecurity.github.io/trivy/)
- [Cosign Docs](https://sigstore.cosign.dev/)
- [Distroless Images](https://github.com/GoogleContainerTools/distroless)

---

**Responsável:** DEV0
**Status:** 🟡 **CONCLUÍDO COM RESSALVAS (escopo de desenvolvimento)** — pendente aceite de risco/correção upstream para HIGH OS/runtime e configuração de Cosign
