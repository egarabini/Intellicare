# ESPECIFICACAO_FUNCIONAL — Fase 5: Produção Ready

**Versão:** 1.0  
**Data:** 2026-02-19  
**Status:** Rascunho — aguardando aprovação  
**Referência:** `docs/PLANNER-CURSOR/ESTRATEGIA_PROXIMOS_PASSOS.md`  
**Pré-requisitos:** Fases 1, 2, 3 e 4 concluídas

---

## 1. Contexto e Objetivo

O IntelliCare está no ar com monitoramento ativo. Para uso real com usuários e dados sensíveis de saúde, é necessário implementar autenticação, conformidade LGPD, backup e hardening. Esta fase prepara o sistema para produção com dados reais.

**Objetivo:** Preparar o IntelliCare para uso em produção — autenticação, conformidade LGPD, backup automatizado, testes de integração e CI/CD — garantindo segurança e rastreabilidade em domínio de saúde.

---

## 2. Escopo

### 2.1 Dentro do escopo

- Implementação de intellicare-auth (integração Keycloak)
- Revisão e adequação LGPD (consentimento, anonimização, auditoria)
- Backup automatizado do banco de dados
- Política de retenção de dados documentada
- Testes de integração automatizados
- CI/CD básico (GitHub Actions ou similar)

### 2.2 Fora do escopo

- Migração de dados legados
- Certificação formal (ISO 27001, SOC2)
- Multi-tenancy
- Alta disponibilidade (HA) e disaster recovery avançado

---

## 3. Requisitos Funcionais

| ID | Requisito | Prioridade |
|----|-----------|------------|
| RF-001 | Sistema deve integrar autenticação via Keycloak (SSO) | Obrigatório |
| RF-002 | Portal e backends devem validar token JWT nas rotas protegidas | Obrigatório |
| RF-003 | Mecanismo de consentimento do titular (LGPD) deve estar documentado e implementado onde aplicável | Obrigatório |
| RF-004 | Processo de anonimização de dados para fins de auditoria/analítica deve estar documentado | Obrigatório |
| RF-005 | Auditoria de acesso a dados sensíveis deve ser registrada | Obrigatório |
| RF-006 | Backup do banco PostgreSQL deve ser executado automaticamente (agendado) | Obrigatório |
| RF-007 | Política de retenção de dados deve estar documentada | Obrigatório |
| RF-008 | Testes de integração devem cobrir fluxos críticos (health, auth, módulos principais) | Obrigatório |
| RF-009 | Pipeline CI deve executar lint, testes e build em cada PR/push | Obrigatório |
| RF-010 | Pipeline CD (opcional) deve permitir deploy em staging a partir de tag ou branch | Desejável |

---

## 4. Requisitos Não Funcionais

| ID | Requisito | Prioridade |
|----|-----------|------------|
| RNF-001 | Dados de saúde devem ser tratados conforme LGPD (base legal, consentimento, minimização) | Obrigatório |
| RNF-002 | Backup deve ser armazenado em local seguro e testado (restore) | Obrigatório |
| RNF-003 | Credenciais e secrets em CI/CD devem usar mecanismo seguro (secrets do provedor) | Obrigatório |
| RNF-004 | Testes de integração devem ser executáveis localmente e no CI | Obrigatório |

---

## 5. Critérios de Aceite

| ID | Critério |
|----|----------|
| CA-001 | Dado usuário não autenticado, quando acessar rota protegida, então é redirecionado para login Keycloak |
| CA-002 | Dado usuário autenticado, quando acessar rota protegida com token válido, então acesso é permitido |
| CA-003 | Dado documento de consentimento LGPD, quando consultar, então descreve fluxo de consentimento e direitos do titular |
| CA-004 | Dado processo de backup, quando executar, então gera backup do PostgreSQL e armazena em local configurado |
| CA-005 | Dado backup gerado, quando executar restore de teste, então banco é restaurado com sucesso |
| CA-006 | Dado política de retenção, quando consultar documentação, então descreve prazos por tipo de dado |
| CA-007 | Dado push/PR, quando pipeline CI executar, então lint e testes passam (ou falha é reportada) |
| CA-008 | Dado testes de integração, quando executar localmente, então cobrem fluxos críticos e passam |

---

## 6. Cenários de Uso

### Cenário 1: Usuário acessa o portal

1. Acessa URL do portal
2. É redirecionado para Keycloak (login)
3. Autentica com credenciais
4. É redirecionado de volta ao portal com sessão ativa
5. Navega nos módulos
6. Resultado esperado: acesso controlado por autenticação

### Cenário 2: Backup automatizado

1. Cron/scheduler dispara job de backup
2. Script conecta ao PostgreSQL e gera dump
3. Dump é armazenado em storage configurado (S3, volume, etc.)
4. Log de sucesso/falha é registrado
5. Resultado esperado: backup disponível para restore

### Cenário 3: Desenvolvedor faz PR

1. Abre PR com alterações
2. Pipeline CI é disparado
3. Executa lint (Ruff, ESLint)
4. Executa testes unitários e de integração
5. Executa build do frontend
6. Resultado esperado: PR com status de CI (pass/fail)

### Cenário 4: Titular solicita exclusão de dados (LGPD)

1. Titular solicita exclusão/anonimização
2. Processo documentado é executado
3. Dados são anonimizados ou removidos
4. Auditoria registra a ação
5. Resultado esperado: conformidade com direito à exclusão

---

## 7. Restrições e Premissas

### 7.1 Restrições

- **Python:** Sempre em ambiente virtual
- **Keycloak:** Infraestrutura já planejada em intellicare-auth; implementação Python pendente
- **LGPD:** Adequação conforme orientação jurídica; esta especificação define requisitos técnicos

### 7.2 Premissas

- Fases 1 a 4 concluídas
- Keycloak disponível (self-hosted ou serviço)
- Ambiente de staging para testes de integração
- Repositório em GitHub/GitLab com suporte a Actions/Pipelines

---

## 8. Entregáveis

| # | Entregável | Descrição |
|---|------------|-----------|
| 1 | intellicare-auth integrado | Keycloak configurado, portal e backends validando JWT |
| 2 | Documento de consentimento LGPD | Fluxo, direitos do titular, base legal |
| 3 | Processo de anonimização | Documentado e implementado onde aplicável |
| 4 | Script de backup automatizado | Agendado, com armazenamento seguro |
| 5 | Teste de restore | Procedimento documentado e validado |
| 6 | Política de retenção | Documento com prazos por tipo de dado |
| 7 | Testes de integração | Suite executável localmente e no CI |
| 8 | Pipeline CI | Lint, testes, build em PR/push |
| 9 | Pipeline CD (opcional) | Deploy em staging por tag/branch |

**Artefatos do fluxo (neste diretório):** O dev deve registrar aqui a ESPECIFICACAO_TECNICA e o PLANO_IMPLEMENTACAO antes da implementação.

---

## 9. Referências

- `intellicare-auth/docs/PLANO_EXECUCAO.md` — integração Keycloak
- Lei Geral de Proteção de Dados (LGPD) — Lei 13.709/2018
- `docs/PLANNER-CURSOR/ESTRATEGIA_PROXIMOS_PASSOS.md`
- `intellicare-comunicacao/docs/` — especificações LGPD existentes

---

## 10. Histórico de Alterações

| Versão | Data | Alteração |
|--------|------|-----------|
| 1.0 | 2026-02-19 | Versão inicial |
