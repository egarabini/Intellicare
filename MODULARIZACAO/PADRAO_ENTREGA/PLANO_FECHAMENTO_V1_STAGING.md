# PLANO DE FECHAMENTO V1 E TRANSICAO PARA V2

## Objetivo
Fechar a V1 com estabilidade operacional, eliminar divergencias de deploy e preparar a base para V2 com padrao unico `staging`.

## Escopo de Fechamento V1
1. Padronizar nomenclatura `homologacao/HOMOLOGACAO` para `staging/STAGING`.
2. Tornar obrigatorios os 4 controles operacionais:
   - validacao minima antes de push;
   - `git pull --ff-only` no servidor;
   - registro de execucao em diario tecnico;
   - rollback imediato quando health/smoke falhar.
3. Tratar incidente de seguranca por credenciais em `MODULARIZACAO/.env.homologacao`.

## Definicao de Pronto (DoD) da V1
1. Nao existem novos arquivos/pipelines com `homologacao` como termo primario.
2. Fluxo GIT -> STAGING roda com scripts oficiais de `MODULARIZACAO/PADRAO_ENTREGA/`.
3. Todos os deploys de modulo registram diario tecnico.
4. Processo de rollback foi testado ao menos 1 vez por modulo critico.
5. Segredos comprometidos foram rotacionados e removidos de arquivos versionados.

## Plano de Execucao (Passo a Passo)

### Fase 0 - Congelamento Curto (Dia 0)
1. Congelar mudancas de infra/deploy por 24h (somente hotfix critico).
2. Nomear responsaveis:
   - owner de plataforma;
   - owner de seguranca;
   - owner de cada modulo critico (portal, admin, wanda, grahame).
3. Criar branch de governanca: `chore/v1-close-staging-standard`.

### Fase 1 - Inventario e Impacto (Dia 1)
1. Levantar ocorrencias de `homologacao|HOMOLOGACAO` em:
   - docs;
   - scripts;
   - compose/env;
   - workflows CI/CD.
2. Classificar cada ocorrencia:
   - `alias temporario` (manter por compatibilidade);
   - `migrar agora`;
   - `remover`.
3. Publicar matriz de impacto por arquivo com risco de quebra.

Entrega: lista priorizada de arquivos e ordem de mudanca.

### Fase 2 - Padrao STAGING com Compatibilidade (Dia 2-3)
1. Introduzir nomes canonicos:
   - `.env.staging` (novo canonic);
   - variaveis `..._STAGING_...` quando aplicavel.
2. Manter compatibilidade:
   - ler `homologacao` como fallback temporario nos scripts.
3. Atualizar documentacao principal:
   - instrucoes e exemplos passam a usar `staging`.
4. Marcar `homologacao` como `deprecated` com data de remocao.

Entrega: ambiente opera com `staging` sem quebrar legado imediato.

### Fase 3 - Controles Operacionais Obrigatorios (Dia 3-4)
1. Validacao minima antes de push:
   - manter scripts em `PADRAO_ENTREGA/GIT/*.ps1`;
   - bloquear push manual sem validacao no processo oficial.
2. Deploy com `ff-only`:
   - manter `git pull --ff-only` em `PADRAO_ENTREGA/STAGING/deploy-module.ps1`.
3. Diario tecnico obrigatorio:
   - registrar modulo, horario, commit, comando, resultado health/smoke.
4. Rollback imediato:
   - documentar comando padrao e tempo alvo de recuperacao.

Entrega: execucao padronizada e auditavel por modulo.

### Fase 4 - Incidente de Seguranca e Rotacao (Dia 4)
1. Tratar `MODULARIZACAO/.env.homologacao` como credencial exposta.
2. Rotacionar imediatamente:
   - senha Postgres;
   - senha Redis;
   - senha Grafana;
   - segredos SMTP e demais credenciais reais.
3. Remover segredo de arquivo versionado:
   - substituir por placeholders;
   - mover valores reais para cofre/secret manager do ambiente.
4. Revisar historico de vazamento:
   - identificar onde o arquivo foi compartilhado (git, backups, chats).

Entrega: credenciais novas ativas e sem segredo em texto puro no repo.

### Fase 5 - Validacao Final de V1 (Dia 5)
1. Executar ciclo completo em 2 modulos piloto (portal/admin):
   - validacao local;
   - push via script;
   - deploy staging via script;
   - health/smoke;
   - registro no diario.
2. Repetir para modulos criticos restantes (wanda/grahame).
3. Executar teste de rollback controlado em 1 modulo.
4. Publicar relatorio `V1 encerrada` com evidencias.

Entrega: V1 oficialmente fechada e apta para inicio de V2.

## Checklist de Execucao

### Checklist Tecnico
- [ ] Inventario completo de ocorrencias `homologacao`.
- [ ] `.env.staging` criado e documentado.
- [ ] Compatibilidade temporaria validada.
- [ ] Scripts `GIT/STAGING` operacionais para modulos prioritarios.
- [ ] `ff-only` validado em servidor.
- [ ] Diario tecnico com execucoes reais.
- [ ] Procedimento de rollback testado.

### Checklist de Seguranca
- [ ] Credenciais expostas rotacionadas.
- [ ] Arquivos versionados sem segredos reais.
- [ ] Segredos movidos para vault/secret manager.
- [ ] Evidencia de revogacao/rotacao registrada.

### Checklist de Governanca
- [ ] Documento oficial aponta `staging` como padrao.
- [ ] Times informados da deprecacao de `homologacao`.
- [ ] Data de corte para remocao do legado definida.
- [ ] Ata de fechamento V1 publicada.

## Padroes Minimos para V2 (herdados da V1)
1. Nunca deploy de staging a partir de arquivo local sem git.
2. Todo modulo deve ter roteiro de validacao minima reproduzivel.
3. Todo deploy deve ter log no diario tecnico.
4. Toda falha de health/smoke aciona rollback imediato.
5. Segredos somente por mecanismo seguro, nunca em texto puro versionado.

## Registro de Evidencias (modelo)
1. Modulo:
2. Commit:
3. Horario inicio/fim:
4. Comandos executados:
5. Resultado health:
6. Resultado smoke:
7. Rollback necessario? (sim/nao):
8. Responsavel:

## Cronograma Executivo (D0 a D5)
1. D0 (congelamento):
   - abrir branch `chore/v1-close-staging-standard`;
   - travar mudancas de deploy fora de hotfix critico;
   - publicar responsaveis e janela de execucao.
2. D1 (inventario):
   - executar busca de ocorrencias `homologacao|HOMOLOGACAO`;
   - gerar lista priorizada por risco/impacto;
   - validar com owners de modulo.
3. D2-D3 (migracao controlada):
   - aplicar padrao `staging` com fallback temporario;
   - atualizar scripts e documentacao canonica;
   - executar deploy piloto (portal + admin).
4. D4 (seguranca):
   - rotacionar todos os segredos expostos;
   - remover valores reais de arquivos versionados;
   - registrar evidencias de revogacao.
5. D5 (encerramento):
   - executar rodada final em modulos criticos;
   - testar rollback controlado;
   - publicar ata `V1 encerrada`.

## Comandos Operacionais de Referencia
1. Inventario de termos legados:
   - `rg -n "homologacao|HOMOLOGACAO" MODULARIZACAO docs`
2. Validacao minima antes de push:
   - `pwsh -File MODULARIZACAO/PADRAO_ENTREGA/GIT/validacao-minima.ps1`
3. Push padronizado:
   - `pwsh -File MODULARIZACAO/PADRAO_ENTREGA/GIT/push-com-validacao.ps1`
4. Deploy staging com fast-forward only:
   - `pwsh -File MODULARIZACAO/PADRAO_ENTREGA/STAGING/deploy-module.ps1 -Module <modulo>`
5. Verificacao de stack/container:
   - `docker compose --env-file .env.full -f docker-compose.full.yml ps`
   - `docker compose --env-file .env.full -f docker-compose.full.yml logs --tail 120 <servico>`
6. Rollback padrao:
   - `pwsh -File MODULARIZACAO/PADRAO_ENTREGA/STAGING/rollback-module.ps1 -Module <modulo>`

## Gate de Qualidade (Go/No-Go V1)
1. Go:
   - todos os modulos criticos com health/smoke verde;
   - diario tecnico preenchido para cada deploy critico;
   - sem segredos reais em arquivos versionados;
   - rollback testado e tempo de recuperacao dentro da meta.
2. No-Go:
   - qualquer modulo critico sem health estavel;
   - falha de smoke sem rollback executado;
   - evidencia de segredo ativo exposto no repositorio;
   - divergencia entre script oficial e procedimento executado.

## Matriz de Risco de Fechamento
1. Risco: quebra por renomeacao `homologacao -> staging`.
   - mitigacao: fallback temporario + migracao incremental por modulo.
2. Risco: deploy manual fora do fluxo oficial.
   - mitigacao: bloquear processo e exigir scripts em `PADRAO_ENTREGA`.
3. Risco: credenciais antigas seguirem validas apos rotacao.
   - mitigacao: teste imediato de revogacao e troca em todos os consumidores.
4. Risco: rollback nao funcionar sob pressao.
   - mitigacao: teste controlado por modulo critico antes do encerramento.

## Responsabilidades (RACI simplificado)
1. Plataforma (A/R):
   - padronizacao de scripts e pipeline;
   - garantia de `git pull --ff-only` no deploy.
2. Seguranca (A/R):
   - rotacao e revogacao de credenciais expostas;
   - validacao de ausencia de segredos no versionamento.
3. Owners de modulo critico (R):
   - executar validacao minima, health/smoke e registro no diario;
   - acionar rollback imediato quando necessario.
4. Arquitetura/planejamento (C/I):
   - aprovar encerramento da V1;
   - publicar ata e baseline da V2.
