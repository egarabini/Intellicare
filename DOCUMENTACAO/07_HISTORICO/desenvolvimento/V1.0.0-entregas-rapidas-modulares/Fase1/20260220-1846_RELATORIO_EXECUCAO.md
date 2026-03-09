# RELATORIO_EXECUCAO_FASE1 — 2026-02-19

## 1. Escopo executado nesta rodada

- Atualizacao do launcher da demo para considerar ambiente virtual por modulo.
- Harden do launcher para fallback automatico por import check do entrypoint do modulo.
- Correcao do script de encerramento de servicos.
- Atualizacao do guia de demo com fluxo de execucao e troubleshooting.
- Criacao de templates de operacao da fase:
  - `CHECKLIST_ESTABILIZACAO.md`
  - `ISSUES_CONHECIDOS.md`
- Criacao de script de smoke test:
  - `check_demo_health.ps1`
- Criacao de script de setup de venvs:
  - `setup_demo_venvs.ps1`
- Instalacao de runtime minimo nos venvs dos modulos da demo.

## 2. Evidencias coletadas

### 2.1 Ambientes virtuais detectados (demo)

- Oswaldo: `.venv` criado
- Florence: `venv` detectado
- Geralda: `.venv` criado
- Nise: `.venv` criado
- Zilda: `.venv` criado
- Grahame: `.venv` criado

Automacao adicionada:
- `setup_demo_venvs.ps1` para criar/verificar ambientes virtuais da demo.

Validacao de imports de runtime (venv):
- Oswaldo (`.venv39`): OK
- Florence (`venv`): OK
- Geralda (`.venv`): OK
- Nise (`.venv`): OK
- Zilda (`.venv`): OK
- Grahame (`.venv`): OK

Dependencias instaladas nesta rodada:
- Geralda/Nise/Zilda/Grahame: `fastapi`, `uvicorn` (venv local).
- Florence: bootstrap de `pip` no `venv` + `fastapi`, `uvicorn`.
- Oswaldo (`.venv39`): requirements instalados + `psycopg2-binary`.
- Zilda: `pip install -e ../intellicare-core` no venv para resolver dependencia local.

### 2.2 Infraestrutura Docker

- `docker compose -f ./docker-compose.yml ps` executado
- Resultado: sem servicos ativos no compose no momento da verificacao

### 2.3 Health check integrado

Comando:
- `powershell -ExecutionPolicy Bypass -File ./check_demo_health.ps1`

Resultado:
- Nise: 200
- Florence: 200
- Oswaldo: 200
- Zilda: 200
- Grahame: 200
- Geralda: 200
- Portal: 200
- Sumario: `OK=7 FAIL=0`

## 3. Situacao atual

- Demo funcional no momento da verificacao (todos os endpoints alvo responderam 200).
- Ambientes virtuais presentes nos 6 modulos Python da demo (`.venv` ou `venv`).
- Fase 1 em andamento com foco nos requisitos RF-005 e RNF-002/RNF-003.
- Issue conhecida aberta: ausencia de Python 3.11 no host (apenas 3.14 e 3.9).

## 4. Proximas acoes tecnicas

1. Validar instalacao de dependencias por modulo dentro do venv.
2. Executar rodada limpa:
   - parar processos;
   - subir infra;
   - subir via `start_demo.bat`;
   - validar via `check_demo_health.ps1`.
3. Preencher checklist final e registrar issues (se houver).
