# ESPECIFICACAO_FUNCIONAL — Fase 3: Deploy Mínimo Viável

**Versão:** 1.0  
**Data:** 2026-02-19  
**Status:** Rascunho — aguardando aprovação  
**Referência:** `docs/PLANNER-CURSOR/ESTRATEGIA_PROXIMOS_PASSOS.md`  
**Pré-requisitos:** Fase 1 e Fase 2 concluídas

---

## 1. Contexto e Objetivo

O IntelliCare está estável localmente e com controle de versão Git. O próximo passo é tornar o projeto acessível via URL pública, permitindo demonstrações remotas e preparando o terreno para uso real.

**Objetivo:** Colocar o projeto no ar — acessível via URL pública com HTTPS — com todos os serviços da demo (6 backends + portal), de forma reproduzível e documentada.

---

## 2. Escopo

### 2.1 Dentro do escopo

- Criação de `.env.example` com todas as variáveis necessárias para deploy
- Orquestração unificada (docker-compose ou script) que levanta toda a stack
- Configuração do frontend para apontar aos backends via variáveis de ambiente
- Ambiente de staging/homologação acessível via URL
- HTTPS configurado (Let's Encrypt ou provedor)
- Smoke tests automatizados (health de cada serviço)
- Documentação do processo de deploy

### 2.2 Fora do escopo

- Múltiplos ambientes (dev/staging/prod) — apenas staging nesta fase
- Kubernetes ou orquestração complexa
- CI/CD automatizado (deploy por pipeline)
- Domínio customizado (pode usar subdomínio do provedor)
- Escalabilidade horizontal

---

## 3. Requisitos Funcionais

| ID | Requisito | Prioridade |
|----|-----------|------------|
| RF-001 | `.env.example` deve listar todas as variáveis necessárias para deploy em máquina limpa | Obrigatório |
| RF-002 | Um único comando ou script deve subir toda a stack (infra + 6 backends + portal) | Obrigatório |
| RF-003 | Frontend deve obter URLs dos backends via variáveis de ambiente (VITE_* ou equivalente) | Obrigatório |
| RF-004 | Projeto deve ser acessível via URL pública com HTTPS | Obrigatório |
| RF-005 | Smoke tests devem validar health de cada serviço (script executável) | Obrigatório |
| RF-006 | Documentação de deploy deve permitir que um dev reproduza o deploy em ambiente limpo | Obrigatório |
| RF-007 | Infraestrutura (Postgres, Redis) deve estar disponível no ambiente de deploy | Obrigatório |

---

## 4. Requisitos Não Funcionais

| ID | Requisito | Prioridade |
|----|-----------|------------|
| RNF-001 | Credenciais e secrets não devem estar em repositório; usar variáveis de ambiente ou secrets do provedor | Obrigatório |
| RNF-002 | Deploy deve ser reversível (rollback possível) | Obrigatório |
| RNF-003 | Módulos Python devem rodar em ambiente virtual ou em containers isolados | Obrigatório |
| RNF-004 | Documentação deve ser clara para um dev sem conhecimento prévio do projeto | Obrigatório |

---

## 5. Critérios de Aceite

| ID | Critério |
|----|----------|
| CA-001 | Dado `.env.example`, quando configurar variáveis em máquina limpa, então o deploy funciona |
| CA-002 | Dado o comando/script de deploy, quando executar, então toda a stack sobe (infra + 6 backends + portal) |
| CA-003 | Dado o portal em produção, quando acessar, então carrega e os módulos respondem aos backends corretos |
| CA-004 | Dado o ambiente de staging, quando acessar via URL, então conexão é HTTPS |
| CA-005 | Dado o script de smoke tests, quando executar, então valida health de cada serviço e reporta OK/FALHA |
| CA-006 | Dado um dev novo, quando seguir GUIA_DEPLOY.md, então consegue fazer deploy sem ambiguidade |

---

## 6. Cenários de Uso

### Cenário 1: Deploy em VPS com Docker Compose

1. Provisiona servidor (VPS)
2. Instala Docker e Docker Compose
3. Clona repositório na tag de release
4. Copia `.env.example` para `.env` e preenche valores
5. Executa `docker-compose -f docker-compose.full.yml up -d`
6. Configura HTTPS (Let's Encrypt ou nginx reverse proxy)
7. Executa smoke tests
8. Resultado esperado: URL acessível com demo funcional

### Cenário 2: Deploy em plataforma (Railway/Render/Fly.io)

1. Conecta repositório à plataforma
2. Configura variáveis de ambiente via painel
3. Define comando de build e start
4. Plataforma faz deploy automático
5. Obtém URL gerada
6. Executa smoke tests na URL
7. Resultado esperado: demo funcional

### Cenário 3: Validação pós-deploy

1. Executa script de smoke tests
2. Script verifica /health de cada backend
3. Script verifica se portal carrega
4. Resultado esperado: relatório OK ou lista de falhas

---

## 7. Restrições e Premissas

### 7.1 Restrições

- **Python:** Sempre em ambiente virtual ou em container com dependências isoladas
- **Opções de deploy:** Docker Compose em VPS ou plataforma PaaS (Railway, Render, Fly.io); Kubernetes fora do escopo

### 7.2 Premissas

- Fases 1 e 2 concluídas
- Servidor ou conta em plataforma de deploy disponível
- Domínio ou subdomínio configurável (ou URL gerada pelo provedor)
- Portas 80/443 disponíveis no ambiente de deploy

---

## 8. Entregáveis

| # | Entregável | Descrição |
|---|------------|-----------|
| 1 | .env.example | Arquivo na raiz com todas as variáveis necessárias (valores de exemplo, sem credenciais) |
| 2 | docker-compose.full.yml | Ou equivalente que sobe infra + backends + portal |
| 3 | GUIA_DEPLOY.md | Documento em docs/PLANNER-CURSOR/ com passos para deploy |
| 4 | Script de smoke tests | Script que valida health de cada serviço |
| 5 | URL de staging funcional | Projeto acessível via HTTPS |

**Artefatos do fluxo (neste diretório):** O dev deve registrar aqui a ESPECIFICACAO_TECNICA e o PLANO_IMPLEMENTACAO antes da implementação.

---

## 9. Referências

- `docs/PLANNER-CURSOR/ESTRATEGIA_PROXIMOS_PASSOS.md` — estratégia completa
- `docker-compose.yml` — infraestrutura existente
- `README_DEMO.md` — módulos da demo

---

## 10. Histórico de Alterações

| Versão | Data | Alteração |
|--------|------|-----------|
| 1.0 | 2026-02-19 | Versão inicial |
