# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Added
- (mudanças ainda não lançadas)

### Changed
- (mudanças ainda não lançadas)

### Fixed
- (mudanças ainda não lançadas)

## [0.1.0-demo] - 2026-02-20

### Added
- Estrutura modular com 15 módulos (core, wanda, florence, oswaldo, nise, geralda, grahame, zilda, donabedian, superz, ocr, conhecimento, comunicacao, auth, portal)
- Demo local funcional com 6 backends Python + portal React
- Ambientes virtuais Python por módulo (.venv ou venv)
- Scripts de automação:
  - `start_demo.bat` - Iniciar demo completa
  - `kill_demo.bat` - Encerrar todos os serviços
  - `check_demo_health.ps1` - Smoke test de health checks
  - `setup_demo_venvs.ps1` - Configurar ambientes virtuais
- Infraestrutura Docker:
  - PostgreSQL (porta 5432)
  - Redis (porta 6379)
  - Prometheus (porta 9090)
  - Grafana (porta 3000)
- Módulo intellicare-comunicacao:
  - D1 - Engine de Roteamento (35+ arquivos, 100+ testes, 21 endpoints)
  - D2 - Integração Rocket.Chat (20 arquivos, 30+ testes, 6 endpoints)
  - D3 - Teleconsulta/Vídeo com Jitsi (15 arquivos, 50+ testes, 11 endpoints)
  - D4 - Notificações Externas (65 arquivos, 71 testes, 16 endpoints)
    - Push Notifications (VAPID/FCM)
    - WhatsApp Business API (Meta Graph API)
    - SMS (Twilio/Zenvia/SNS)
    - Email (SMTP com templates Jinja2)
  - D6 - LGPD/Auditoria (22 arquivos, 39 testes, 15 endpoints)
  - D7 - Dashboard/Monitoramento (20 arquivos, 8 dashboards Grafana, 14 alertas)
- Documentação técnica:
  - README_DEMO.md - Guia completo da demo
  - docs/PLANNER-CURSOR/ - Governança e especificações
  - Fase 1 (Estabilização) - Especificações e relatórios
  - Fase 2 (Organização Git) - Especificações técnicas e plano
- Controle de versão:
  - .gitignore completo (Python, venv, .env, Node.js, IDEs)
  - Estratégia de branches documentada
  - Processo de release documentado

### Changed
- Migração de Matrix/Synapse (legacy) para Rocket.Chat + Jitsi (V5 oficial)
- Padronização de health checks em todos os módulos
- Isolamento de dependências Python por módulo

### Fixed
- Estabilização da demo local (Fase 1)
- Correção de scripts de inicialização e encerramento
- Ajustes em endpoints de health check

### Security
- Proteção de credenciais via .env (não versionado)
- .gitignore configurado para evitar vazamento de dados sensíveis
- LGPD compliance no módulo comunicacao (hash chain audit trail)

---

## Notas de Release

### v0.1.0-demo (2026-02-20)

Esta é a primeira release oficial da demo do IntelliCare MODULARIZACAO. O projeto está funcional em ambiente local e pronto para evolução governada através do fluxo ARQUITETO → PLANEJADOR → Agentes Desenvolvedores.

**Pré-requisitos para executar a demo:**
- Docker Desktop instalado e rodando
- Python 3.11+ instalado
- Node.js 18+ instalado (para o portal)
- Git instalado

**Como executar:**
1. Iniciar infraestrutura: `.\start-infrastructure.ps1`
2. Aguardar serviços subirem (~30 segundos)
3. Iniciar demo: `.\start_demo.bat`
4. Verificar saúde: `.\check_demo_health.ps1`

**Endpoints principais:**
- Portal: http://localhost:3000
- Wanda (Triagem): http://localhost:8001
- Florence (Exames): http://localhost:8002
- Oswaldo (Condições Crônicas): http://localhost:8003
- Nise (Medicamentos): http://localhost:8004
- Comunicacao: http://localhost:8005
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

**Próximos passos:**
- Fase 3: Deploy Mínimo (CI/CD, ambientes)
- Fase 4: Monitoramento (alertas avançados)
- Fase 5: Produção Ready (auth Keycloak, hardening)

