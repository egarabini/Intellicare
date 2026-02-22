# Análise Comparativa — Fase 1 vs. Relatório do DEV e Próximos Passos

**Data:** 2026-02-22  
**Objetivo:** Comparar o que foi planejado, o que foi executado, o que falta e avaliar a próxima etapa

---

## 1. O que o Plano Original Determinava (Fase 1 — Preparação do Sistema)

O **PLANO_IMPLEMENTACAO** define a Fase 1 como parte do fluxo A→E. A pasta `Fase1_Preparacao_Sistema` corresponde ao **escopo de preparação do servidor**:

| Item | Plano Original | Escopo |
|------|----------------|--------|
| **A1–A4** | Atualizar SO, instalar Docker, Docker Compose, UFW | Preparação do servidor |
| **A5** | Segurança (senha root, SSH chave) | Fase 4 (Segurança) |
| **B1–B3** | Clone do repo, configurar .env | Fase 2 (Clone/Config) |
| **C1–C3** | Postgres, Redis, schemas | Fase 3 (Infraestrutura) |

**Fase 1 (pasta) = A1–A4** — preparação do sistema (Docker, firewall, ferramentas).

---

## 2. O que o DEV Executou (conforme relatório)

O relatório do DEV foca em **correções de código e configuração** após o deploy falhar:

| Ação | Planejado na Fase 1? | Observação |
|------|----------------------|------------|
| Corrigir erros Docker (Oswaldo, Donabedian, Comunicacao) | ❌ Não | Problemas surgiram ao rodar o deploy |
| Alterar Dockerfile donabedian (intellicare-auth) | ✅ Sim (no relatório de análise) | Correção prevista |
| Tornar intellicare_auth **opcional** em 7 arquivos | ❌ Não | Solução alternativa ao invés de só instalar o pacote |
| Adicionar psycopg ao pyproject.toml (oswaldo, comunicacao) | ⚠️ Implícito | Consequência da troca asyncpg→psycopg |
| URL encoding no .env | ❌ Não | Problema novo descoberto em execução |
| Script fix_url_encoding.sh | ❌ Não | Automação criada pelo DEV |
| Rebuild de imagens Docker | ⚠️ Implícito | Necessário após alterações |

---

## 3. O que Foi Feito a Mais

1. **Imports opcionais de intellicare_auth**  
   O relatório de análise sugeria instalar `intellicare-auth` no Dockerfile. O DEV fez isso **e** tornou os imports opcionais (try/except) em 7 arquivos. Isso reduz o acoplamento, mas altera o comportamento: em staging, o auth fica desabilitado (usuário anônimo).

2. **URL encoding**  
   Não estava no plano nem na análise inicial. O DEV identificou e corrigiu durante a execução.

3. **Scripts e documentação extra**  
   `fix_url_encoding.sh`, `INSTRUCOES_FINAIS_OSWALDO.md` — úteis, mas fora do escopo original.

---

## 4. O que Não Foi Explicitamente Validado

O relatório **não confirma** de forma explícita:

| Item | Status | Observação |
|------|--------|------------|
| A1–A4 (Docker, UFW, etc.) | ⚠️ Assumido | Servidor já em uso; provavelmente feito antes |
| B1–B3 (Clone, .env) | ⚠️ Assumido | .env foi alterado (encoding); clone já existia |
| C1–C3 (Postgres, Redis, schemas) | ⚠️ Assumido | Containers rodando; schemas não validados |
| A5 / Fase 4 (Segurança) | ❌ Não feito | Senha root, SSH, Fail2Ban não citados |
| Fase E (Backup, Fail2Ban) | ❌ Não feito | Pós-configuração pendente |

---

## 5. O que Falta Fazer

### 5.1. Pendências da Fase 1 (se quiser fechar formalmente)

- [ ] Confirmar que A1–A4 foram executados (ou documentar que o servidor já estava pronto)
- [ ] Validar criação dos schemas no Postgres (C3)
- [ ] Remover senha em texto de `docs/SERVIDORES/HOMOLOGACAO/README.md` (A5)

### 5.2. Pendências do Relatório do DEV (próxima fase sugerida)

| Item | Impacto nos módulos | Esforço |
|------|---------------------|---------|
| Ajustar healthchecks | docker-compose + possivelmente 6+ módulos | Médio |
| Testar endpoints REST | Manual ou smoke tests | Baixo |
| Configurar dependências opcionais | Por módulo | Variável |
| Monitoramento e alertas | Infra + config | Médio |
| Backup | Script + cron | Baixo |

### 5.3. Fases 2, 3 e 4 da Inicialização

- **Fase 2 (Clone/Config):** Provavelmente concluída (repo e .env em uso)
- **Fase 3 (Infra):** Provavelmente concluída (Postgres, Redis rodando)
- **Fase 4 (Segurança):** **Não feita** — senha root, SSH, Fail2Ban, remoção de credenciais em docs

---

## 6. Avaliação: Vale a Pena Executar a Próxima Etapa?

### 6.1. Próxima etapa segundo o DEV

1. Ajustar healthchecks  
2. Testar endpoints  
3. Configurar dependências opcionais  
4. Monitoramento  
5. Backup  

### 6.2. Impacto em “mexer em todos os módulos”

| Ação | Módulos afetados | Tipo de alteração |
|------|------------------|-------------------|
| **Healthchecks** | 6+ backends + portal | `docker-compose.full.yml` + possivelmente endpoint `/health` em cada módulo |
| **Dependências opcionais** | Donabedian (e outros que usem auth) | Código (imports, config) |
| **Monitoramento** | Todos | Config (Prometheus, Grafana) |
| **Backup** | Nenhum módulo | Script + cron no servidor |

O maior impacto vem de **healthchecks** e **dependências opcionais**:

- **Healthchecks:** Hoje Donabedian e Comunicacao aparecem como "unhealthy" porque o healthcheck chama endpoints que podem falhar. Ajustar isso pode exigir:
  - Padronizar `/health` em todos os módulos, ou
  - Trocar o healthcheck no docker-compose para um endpoint que sempre exista.

- **Dependências opcionais:** Donabedian já usa auth opcional. Outros módulos (Florence, Wanda, Geralda) podem ter imports de `intellicare_auth` e precisar do mesmo padrão.

### 6.3. Recomendações

| Cenário | Recomendação |
|---------|--------------|
| **Prioridade: estabilidade mínima** | Fazer só **backup** e **Fase 4 (Segurança)**. Pouco impacto em código. |
| **Prioridade: healthchecks verdes** | Ajustar healthchecks no docker-compose para um endpoint que exista em todos (ex.: `/health` ou `/api/v1/health`). Pode exigir checagem em cada módulo. |
| **Prioridade: adiar mudanças grandes** | Deixar healthchecks "unhealthy" por enquanto. Containers estão rodando; o problema é cosmético. Focar em backup e segurança. |
| **Prioridade: preparar produção** | Executar Fase 4 (Segurança), backup, e depois healthchecks + testes de integração. |

---

## 7. Resumo para Decisão

| Pergunta | Resposta |
|----------|----------|
| O DEV fez mais do que o plano? | Sim. Corrigiu erros de deploy, criou imports opcionais, URL encoding e scripts extras. |
| O que falta da Fase 1? | Validação explícita de A1–C3 e itens de segurança (A5, Fase 4). |
| A próxima etapa mexe em todos os módulos? | Healthchecks e dependências opcionais podem exigir alterações em vários módulos. Backup e segurança não. |
| Vale a pena executar agora? | **Backup + Fase 4 (Segurança):** sim, baixo risco. **Healthchecks + dependências:** avaliar custo/benefício; os containers já estão funcionando. |

---

## 8. Checklist de Decisão

- [ ] Confirmar se A1–C3 foram executados (ou documentar estado atual)
- [ ] Executar Fase 4 (Segurança) — senha root, SSH, Fail2Ban, remover credenciais em docs
- [ ] Configurar backup automático (script + cron)
- [ ] Decidir: ajustar healthchecks agora ou depois
- [ ] Decidir: padronizar auth opcional em outros módulos agora ou depois
