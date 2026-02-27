# FASE 1 - INVENTÁRIO E MATRIZ DE IMPACTO
**Data:** 2026-02-27
**Status:** COMPLETO
**Arquivos identificados:** 27

## Resumo Executivo

Inventário completo de ocorrências de `homologacao|HOMOLOGACAO` no repositório. Identificado **1 incidente de segurança crítico** (`.env.homologacao` com credenciais expostas) e 5 scripts operacionais que requerem migração imediata.

## Classificação por Tipo

### 🔴 CRÍTICO - Incidente de Segurança (1 arquivo)

| Arquivo | Problema | Ação Imediata | Prioridade |
|---------|----------|---------------|------------|
| `.env.homologacao` | Credenciais reais expostas no Git (PostgreSQL, Redis, Grafana, Rocket.Chat, Jitsi, Flowise, Keycloak) | 1. Rotacionar TODAS as senhas<br>2. Criar `.env.staging` com placeholders<br>3. Remover valores reais do histórico | URGENTE |

**Credenciais Expostas:**
- PostgreSQL: `IntelliCare@Homolog2026!Pg`
- Redis: `IntelliCare@Homolog2026!Redis`
- Grafana: `IntelliCare@Homolog2026!Grafana`
- Rocket.Chat Admin: `IntelliCare@Homolog2026!RocketChat`
- Rocket.Chat Bot: `IntelliCare@Homolog2026!Bot`
- Jitsi: `IntelliCare@Homolog2026!Jitsi`
- Flowise: `IntelliCare@Homolog2026!Flowise`
- Keycloak: `IntelliCare@Homolog2026!Keycloak`

### 🟡 MIGRAR AGORA - Scripts Operacionais (5 arquivos)

| Arquivo | Linhas Afetadas | Ação | Risco de Quebra |
|---------|-----------------|------|-----------------|
| `scripts/setup_servidor_homologacao.sh` | 134-136 | Renomear → `setup_staging.sh` + ajustar refs | MÉDIO |
| `scripts/setup_servidor_direto.sh` | 115-117 | Ajustar refs `.env.homologacao` → `.env.staging` | MÉDIO |
| `scripts/execute_remote_setup.ps1` | 102 | Ajustar refs `.env.homologacao` → `.env.staging` | MÉDIO |
| `scripts/deploy_homologacao.sh` | 7, 53-54 | Renomear → `deploy_staging.sh` + ajustar refs | MÉDIO |
| `DOCUMENTACAO.md` | 40, 41, 74, 86, 114, 115 | Atualizar refs para `staging` | BAIXO |
| `EXECUTE_AQUI.md` | 50, 125 | Atualizar refs para `staging` | BAIXO |

### 🟢 MANTER HISTÓRICO - Documentação (21 arquivos)

| Localização | Arquivos | Ação |
|-------------|----------|------|
| `docs/SERVIDORES/HOMOLOGACAO/*` | ~10 arquivos | Renomear pasta → `STAGING` (preservar histórico V1) |
| `docs/PLANNER-CURSOR/*` | ~8 arquivos | Manter (documentação fase V1) |
| `intellicare-*/docs/*` | ~3 arquivos | Manter (documentação específica módulo) |

## Plano de Ação - Ordem de Execução

### Passo 1: Segurança (FASE 4 - antecipada)
1. ✅ Criar branch `chore/v1-close-staging-standard`
2. ⏳ Rotacionar credenciais expostas (servidor Contabo)
3. ⏳ Criar `.env.staging` com placeholders seguros
4. ⏳ Remover `.env.homologacao` com credenciais reais

### Passo 2: Scripts Operacionais (FASE 2)
1. Renomear scripts:
   - `setup_servidor_homologacao.sh` → `setup_staging.sh`
   - `deploy_homologacao.sh` → `deploy_staging.sh`
2. Ajustar referências em todos os scripts
3. Atualizar DOCUMENTACAO.md e EXECUTE_AQUI.md

### Passo 3: Documentação Histórica
1. Renomear pasta: `docs/SERVIDORES/HOMOLOGACAO` → `docs/SERVIDORES/STAGING`
2. Adicionar cabeçalho de preservação histórica

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Quebra de scripts de deploy existentes | ALTA | ALTO | Manter compatibilidade temporária (fallback) |
| Credenciais antigas ainda válidas após rotação | MÉDIA | CRÍTICO | Testar revogação imediatamente |
| Links quebrados em documentação | MÉDIA | BAIXO | Atualizar refs de forma sistemática |

## Checklist de Validação

- [x] Inventário completo executado
- [x] Classificação por criticidade definida
- [x] Matriz de impacto publicada
- [ ] Credenciais rotacionadas
- [ ] `.env.staging` criado
- [ ] Scripts migrados
- [ ] Documentação atualizada
- [ ] Pasta `HOMOLOGACAO` renomeada para `STAGING`

## Próximos Passos

1. **FASE 2:** Criar `.env.staging` com placeholders
2. **FASE 3:** Criar scripts `validacao-minima.ps1` e `rollback-module.ps1`
3. **FASE 4:** Executar rotação de credenciais (servidor Contabo)
4. **FASE 5:** Validar ciclo completo em modulos piloto

---

**Relatório gerado:** 2026-02-27
**Responsável:** DEV0 (Claude Code)
**Branch:** `chore/v1-close-staging-standard`
