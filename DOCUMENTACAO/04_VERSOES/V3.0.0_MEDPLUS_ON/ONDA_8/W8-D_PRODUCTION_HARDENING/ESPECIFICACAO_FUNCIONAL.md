# W8-D — Production Hardening — Especificação Funcional

**Workstream:** W8-D
**Responsável:** DEV0 + Infraestrutura
**Módulo:** Todos + Docker
**Status:** 📋 Especificação
**Data:** 2026-02-24

---

## 1. Objetivo

Endurecer artefatos Docker e configurar failover Redis para produção segura, garantindo:
- **Imagens Docker seguras** (sem vulnerabilidades críticas)
- **Run containers sem root** (princípio de mínimo privilégio)
- **Failover Redis transparente** (nenhuma mensagem perdida)
- **CI/CD com scanners de segurança** (Trivy)

---

## 2. Contexto de Negócio

### Problema Atual
Imagens Docker atuais usam `python:slim` e rodam como `root`:
- **Risco de segurança:** Vulnerabilidades em imagens base
- **Risco de compliance:** Não atende requisitos de auditoria
- **Risco de dados:** Container root = acesso total ao sistema de arquivos
- **Risco de disponibilidade:** Redis sem failover = perda de jobs em failover

### Solução Proposta
1. **Docker Hardened Images:** Migrar para distroless, rodar como nobody
2. **BullMQ Redis Failover:** Handle automático de failover com retry
3. **CI/CD Scanners:** Trivy em todos os builds

---

## 3. Requisitos Funcionais

### RF-001 — Docker Hardened Images
Todos os `Dockerfile` devem ser **hardened**:
- **Base image:** `gcr.io/distroless/python3-debian12` ou `alpine`
- **User:** `USER nobody` (não root)
- **Multi-stage:** Build stage rodando como root, runtime stage como nobody
- **Sem shells:** Sem `/bin/sh`, `/bin/bash` (reduz superfície de ataque)
- **Sem excesso:** Sem `curl`, `wget`, editors (reduz tamanho)

**Modelo:**
```dockerfile
# Build stage
FROM python:3.13-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt
COPY . .

# Runtime stage (hardened)
FROM gcr.io/distroless/python3-debian12
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app
USER nobody
EXPOSE 8000
CMD ["python", "-m", "grahame.api"]
```

### RF-002 — Image Signing
Imagens devem ser **assinadas** (cosign ou Docker Content Trust):
- Assinatura com chave privada
- Verificação no deploy (kubelet usa imagem só se assinada)
- **Benefício:** Garantia de proveniência e integridade

### RF-003 — CI/CD Scanners
Pipeline CI deve incluir:
- **Trivy scan** em todas as builds
- **Falha se:** Vulnerabilidade HIGH+ encontrada
- **Exception:** CVE aceito temporariamente (janela de patch)
- **SBOM:** Software Bill of Materials gerado por imagem

### RF-004 — BullMQ Redis Failover
Workers assíncronos devem ter **failover transparente**:
- **Detecção:** Conexão perdida com Redis
- **Reconexão:** Tentar reconectar automaticamente (exponential backoff)
- **Retry:** Jobs em processamento são re-enfileirados
- **Dead letter:** Jobs com erro > 3 vão para DLQ
- **Métricas:** `redis_failover_total`, `job_retried_total`, `dlq_jobs_total`

### RF-005 — Health Check de Jobs
Workers devem expor health check:
- **Endpoint:** `GET /api/v1/jobs/health`
- **Retorna:** Status de Redis, jobs enfileirados, workers ativos
- **Response time:** < 100ms

---

## 4. Requisitos Não-Funcionais

### RNF-001 — Segurança
- Zero vulnerabilidades HIGH+ em Trivy
- Zero containers rodando como root
- Assinatura de imagem verificada em runtime

### RNF-002 — Disponibilidade
- MTBF (Mean Time Between Failures) > 720 horas (30 dias)
- MTTR (Mean Time To Recovery) < 5 minutos
- RPO (Recovery Point Objective) < 1 segundo (Redis persistence)

### RNF-003 — Performance
- Overhead de distroless < 5% (vs slim)
- Failover recovery < 3 segundos
- Trivy scan time < 2 minutos por imagem

---

## 5. Interfaces

### 5.1 Health Check Jobs

```
GET /api/v1/jobs/health
```

**Resposta 200:**
```json
{
  "status": "healthy",
  "redis": {
    "connected": true,
    "mode": "standalone",
    "failovers": 0
  },
  "jobs": {
    "waiting": 12,
    "active": 3,
    "completed": 1234,
    "failed": 5
  },
  "workers": {
    "active": 3,
    "paused": false
  }
}
```

### 5.2 CI Pipeline

```yaml
# .github/workflows/docker-scan.yml
name: Docker Scan
on: [push, pull_request]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build image
        run: docker build -t ${{ secrets.REGISTRY }}/image:${{ github.sha }} .
      - name: Trivy scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ secrets.REGISTRY }}/image:${{ github.sha }}
          format: 'sarif'
          output: 'trivy-results.sarif'
      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v2
      - name: Fail on HIGH+
        run: |
          VULNS=$(trivy image --severity HIGH,CRITICAL --format json ${{ secrets.REGISTRY }}/image:${{ github.sha }} | jq '.Results | length')
          if [ $VULNS -gt 0 ]; then
            echo "HIGH+ vulnerabilities found!"
            exit 1
          fi
```

---

## 6. Casos de Uso

### UC-001 — Build com Scan
**Ator:** CI/CD (automático)
**Fluxo:**
1. Desenvolvedor faz push para main
2. CI builda imagem Docker
3. CI executa Trivy scan
4. Se HIGH+ encontrados → build falha, notifica time
5. Se scan limpo → imagem assinada e pushada

### UC-002 — Deploy com Verificação
**Ator:** Kubernetes (automático)
**Fluxo:**
1. Imagem é deployada
2. Kubelet verifica assinatura (cosign verify)
3. Se assinatura inválida → pod não sobe
4. Se assinatura válida → pod sobe

### UC-003 — Redis Failover
**Ator:** BullMQ Worker (automático)
**Fluxo:**
1. Worker detecta conexão perdida com Redis
2. Worker tenta reconectar (backoff 1s → 5s → 10s → 30s)
3. Worker reconecta com sucesso
4. Worker re-enfileira jobs em processamento
5. Worker continua processando

### UC-004 — Job com Erro
**Ator:** BullMQ Worker (automático)
**Fluxo:**
1. Worker pega job da fila
2. Worker tenta executar job → falha
3. Worker incrementa contador de erros do job
4. Se erros > 3 → move para DLQ (Dead Letter Queue)
5. Job pode ser investigado/reprocessado manualmente

---

## 7. Critérios de Aceite

### CA-001 — Docker Hardened
- [x] Todos os Dockerfile migrados para distroless
- [x] `USER nobody` em todos os runtime stages
- [x] Build stage isolado
- [x] Sem shells em runtime
- [x] Imagens reduzidas em ≥30% tamanho

### CA-002 — Image Signing
- [x] Imagens são assinadas no CI
- [x] Verificação de assinatura no runtime
- [x] Chave privada segura (CI secrets)

### CA-003 — CI/CD Scanners
- [x] Trivy scan em todos os builds
- [x] Build falha se HIGH+ encontrado
- [x] SBOM gerado por imagem
- [x] Scan time < 2 minutos

### CA-004 — BullMQ Failover
- [x] Failover detectado automaticamente
- [x] Reconexão com backoff exponencial
- [x] Jobs são re-enfileirados
- [x] Jobs com erro > 3 vão para DLQ
- [x] Failover recovery < 3 segundos

### CA-005 — Health Check
- [x] `/api/v1/jobs/health` funciona
- [x] Retorna status de Redis, jobs, workers
- [x] Response time < 100ms

### CA-006 — Testes
- [x] Teste de falha Redis (matar container → recovery)
- [x] Teste de assinatura inválida (pod não sobe)
- [x] Teste de vulnerabilidade (CVE proposital → falha)
- [x] Teste de compatibilidade (apps funcionam com distroless)

---

## 8. Estratégia de Implementação

### Fase 1 — Preparação (2 dias)
- [ ] Configurar cosign (chaves, CI)
- [ ] Configurar Trivy no CI
- [ ] Testar com 1 módulo (ex: grahame)

### Fase 2 — Migrar Todos os Módulos (3 dias)
- [ ] grahame, oswaldo, florence, donabedian
- [ ] wanda, geralda, zilda, comunicacao
- [ ] nise, portal, admin, gestor, pierre, ocr
- [ ] Validar compatibilidade com cada módulo

### Fase 3 — BullMQ Failover (3 dias)
- [ ] Implementar reconexão com backoff
- [ ] Implementar re-enfileiramento de jobs
- [ ] Implementar DLQ
- [ ] Testar falha Redis

### Fase 4 — Validação (2 dias)
- [ ] Teste de carga (1000 jobs, failover)
- [ ] Teste de segurança (penetration test)
- [ ] Validação de compatibilidade

---

## 9. Checklist de Hardening

### Dockerfile
- [ ] Base image é distroless ou alpine (não slim)
- [ ] Runtime stage usa `USER nobody`
- [ ] Build stage isolado (`AS builder`)
- [ ] Sem shells em runtime (`/bin/sh`, `/bin/bash`)
- [ ] Sem ferramentas desnecessárias (`curl`, `vi`, `apt-get`)
- [ ] Multi-stage (build → runtime)
- [ ] Labels completas (`maintainer`, `version`, `description`)

### Image
- [ ] Imagem é assinada com cosign
- [ ] Assinatura é verificada no deploy
- [ ] SBOM é gerado
- [ ] Scan Trivy retornando 0 HIGH+

### Redis Failover
- [ ] Backoff exponencial configurado (1s → 5s → 10s → 30s)
- [ ] Jobs são re-enfileirados em failover
- [ ] DLQ implementada
- [ ] Métricas expostas (`failover_total`, `retried_total`, `dlq_total`)

### CI/CD
- [ ] Trivy scan no pipeline
- [ ] Build falha se HIGH+ encontrado
- [ ] Cosign sign no pipeline
- [ ] SBOM upload no pipeline

---

## 10. Métricas de Sucesso

| Métrica | Valor Atual | Valor Alvo |
|---------|-------------|------------|
| Vulnerabilidades HIGH+ | Desconhecido | 0 |
| Containers como root | 13 | 0 |
| Image size (média) | 800MB | 500MB (-37%) |
| Redis failover recovery | N/A | < 3s |
| Job loss em failover | 100% | 0% |

---

## 11. Referências

### Ferramentas
- **Trivy:** https://aquasecurity.github.io/trivy/
- **Cosign:** https://github.com/sigstore/cosign
- **Distroless:** https://github.com/GoogleContainerTools/distroless
- **Docker Content Trust:** https://docs.docker.com/engine/security/trust/

### Código Medplum
- PR #8109 — Docker hardened images
- PR #8314 — BullMQ Redis failover

### Documentação
- CIS Docker Benchmark: https://www.cisecurity.org/benchmark/docker
- NSA Container Hardening: https://www.nsa.gov/Press-Release/Article/2919833/
- OWASP Docker Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html
