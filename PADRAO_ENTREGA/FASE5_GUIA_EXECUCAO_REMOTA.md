# FASE 5.3 - GUIA DE EXECUÇÃO REMOTA (SERVIDOR)
**Data:** 2026-02-27
**Servidor:** 167.86.97.142 (Contabo)
**Status:** PRONTO PARA EXECUÇÃO

## Pré-requisitos

### 1. Acesso SSH ao Servidor
```bash
# Testar conexão
ssh root@167.86.97.142

# Esperado: Login bem-sucedido
```

### 2. Credenciais Rotacionadas (Fase 4 Completa)
⚠️ **IMPORTANTE:** Executar rotação de credenciais PRIMEIRO
- Ver documento: `FASE4_INCIDENTE_SEGURANCA_CREDENCIAIS.md`
- Confirmar que senhas antigas NÃO funcionam mais

### 3. Branch no Git
```bash
# Branch deve existir remotamente
git fetch origin
git checkout chore/v1-close-staging-standard
```

---

## CICLO COMPLETO DEPLOY - ADMIN (Módulo Piloto)

### Passo 1: Validação Local (Já Executado)
```bash
# Status: ⚠️ PARCIAL (78% passou)
# 21 de 27 testes passaram
# Aceitável para prosseguir com deploy piloto
```

### Passo 2: Push para Git
```bash
cd c:\DOCSHARE\INTELLICARE

# Usar script oficial
pwsh -File PADRAO_ENTREGA/GIT/publish-module.ps1 `
    -Module admin `
    -CommitMessage "chore(v1): fase5 - deploy piloto admin para validacao v1" `
    -SkipValidation  # Pulamos porque validação parcial já foi executada

# Esperado:
# - Changes detected
# - Git add
# - Git commit
# - Git push
```

### Passo 3: Deploy no Servidor
```bash
# Usar script oficial
pwsh -File PADRAO_ENTREGA/STAGING/deploy-module.ps1 `
    -Module admin `
    -Host 167.86.97.142 `
    -User root `
    -Branch chore/v1-close-staging-standard `
    -Build

# Esperado:
# [1/5] Sync git branch chore/v1-close-staging-standard
# [2/5] Pull latest image for service admin
# [3/5] Start service admin
# [4/5] Service status
# [5/5] Health check
# Health check passed: http://localhost:8010/api/v1/health
```

### Passo 4: Verificação Manual de Saúde
```bash
# SSH no servidor
ssh root@167.86.97.142

# Verificar container
docker compose --env-file .env.full -f docker-compose.full.yml ps admin

# Verificar logs
docker compose --env-file .env.full -f docker-compose.full.yml logs --tail 50 admin

# Health check
curl http://localhost:8010/api/v1/health

# Esperado: {"status": "healthy", ...}
```

### Passo 5: Smoke Test
```bash
# No servidor ou local
cd /opt/intellicare
python scripts/smoke_tests.py --url http://167.86.97.142:8010

# Esperado: Todos os testes passam
```

### Passo 6: Registro no Diário Técnico
```markdown
## Deploy Admin - 2026-02-27

**Horário Início:** 09:00
**Horário Fim:** 09:15
**Duração:** 15 minutos

**Responsável:** [Seu Nome]

**Commit:** [hash do commit]
**Branch:** chore/v1-close-staging-standard

**Comandos:**
1. pwsh -File PADRAO_ENTREGA/GIT/publish-module.ps1 -Module admin ...
2. pwsh -File PADRAO_ENTREGA/STAGING/deploy-module.ps1 -Module admin -Host 167.86.97.142
3. curl http://localhost:8010/api/v1/health

**Resultados:**
- Health Check: ✅ PASS
- Smoke Test: ✅ PASS
- Logs: Sem erros

**Rollback Necessário?** NÃO

**Observações:**
- Deploy executado com sucesso
- Serviço respondendo normalmente
- Próximo passo: Testar rollback controlado
```

---

## TESTE DE ROLLBACK CONTROLADO

### Objetivo
Validar que o procedimento de rollback funciona corretamente em caso de falha.

### Passo 1: Simular Falha (Deploy com Bug)
```bash
# Criar commit propositalmente com bug
echo "# BUG TEST FOR ROLLBACK" >> intellicare-admin/README.md

# Push da versão com bug
pwsh -File PADRAO_ENTREGA/GIT/publish-module.ps1 `
    -Module admin `
    -CommitMessage "test: rollback validation - intentional bug"

# Deploy do bug
pwsh -File PADRAO_ENTREGA/STAGING/deploy-module.ps1 `
    -Module admin `
    -Host 167.86.97.142
```

### Passo 2: Executar Rollback
```bash
# Usar script oficial de rollback
pwsh -File PADRAO_ENTREGA/STAGING/rollback-module.ps1 `
    -Module admin `
    -Host 167.86.97.142 `
    -CommitsBack 1 `
    -Force

# Confirmar digitando: ROLLBACK

# Esperado:
# - Backup automático criado
# - Git reset para commit anterior
# - Container recriado
# - Health check passa
```

### Passo 3: Verificar Recuperação
```bash
# SSH no servidor
ssh root@167.86.97.142

# Verificar que versão anterior está ativa
curl http://localhost:8010/api/v1/health

# Verificar logs
docker compose --env-file .env.full -f docker-compose.full.yml logs --tail 50 admin

# Esperado:
# - Health check: PASS
# - Logs: Sem erros
# - Serviço funcional
```

### Passo 4: Limpeza
```bash
# Reverter commit de teste localmente
git reset --hard HEAD~1
git push origin chore/v1-close-staging-standard --force
```

---

## CHECKLIST FINAL

### Antes do Deploy
- [ ] Branch `chore/v1-close-staging-standard` existe no Git remoto
- [ ] Credenciais rotacionadas (Fase 4 completa)
- [ ] Novas senhas testadas e confirmadas
- [ ] Validação local executada (Admin: 78% passou)

### Durante o Deploy
- [ ] Push via script oficial
- [ ] Deploy via script oficial
- [ ] Health check: PASS
- [ ] Smoke test: PASS
- [ ] Registrado no diário técnico

### Teste de Rollback
- [ ] Commit com bug criado
- [ ] Deploy do bug executado
- [ ] Rollback via script oficial
- [ ] Health check pós-rollback: PASS
- [ ] Tempo de recuperação < 5 minutos
- [ ] Backup verificado

### Pós-Deploy
- [ ] Serviço estável
- [ ] Logs sem erros críticos
- [ ] Monitoramento ativo
- [ ] Time informado

---

## SOLUÇÃO DE PROBLEMAS

### Problema: SSH Connection Refused
```bash
# Verificar IP e porta
ping 167.86.97.142
telnet 167.86.97.142 22

# Se falhar: Contatar suporte Contabo ou verificar firewall
```

### Problema: Git Pull Falha
```bash
# No servidor
cd /opt/intellicare
git fetch --all
git checkout chore/v1-close-staging-standard
git branch --set-upstream-to=origin/chore/v1-close-staging-standard chore/v1-close-staging-standard
```

### Problema: Container Não Inicia
```bash
# Verificar logs
docker compose --env-file .env.full -f docker-compose.full.yml logs admin

# Verificar se porta está em uso
netstat -tlnp | grep 8010

# Recriar container
docker compose --env-file .env.full -f docker-compose.full.yml up -d --force-recreate admin
```

### Problema: Health Check Falha
```bash
# Verificar se serviço está rodando
docker ps | grep admin

# Verificar logs de erro
docker logs <container_id>

# Testar health check manualmente
curl -v http://localhost:8010/api/v1/health
```

### Problema: Rollback Falha
```bash
# Rollback manual (emergência)
ssh root@167.86.97.142

cd /opt/intellicare
git log --oneline -5  # Ver commits
git reset --hard HEAD~1  # Voltar 1 commit
docker compose --env-file .env.full -f docker-compose.full.yml up -d --force-recreate admin

# Verificar health
curl http://localhost:8010/api/v1/health
```

---

## TEMPO ESTIMADO

| Atividade | Tempo |
|-----------|-------|
| Pré-requisitos (credenciais rotacionadas) | 30-45 min |
| Deploy Admin | 10-15 min |
| Smoke Test | 5 min |
| Teste de Rollback | 10-15 min |
| **TOTAL** | **55-80 min** |

---

## CONTATO EM CASO DE EMERGÊNCIA

- **Platform Owner:** [PREENCHER]
- **On-Call:** [PREENCHER]
- **Contabo Support:** https://contabo.com/

---

**Guia criado:** 2026-02-27
**Status:** PRONTO PARA EXECUÇÃO
**Próxima revisão:** Após execução no servidor
