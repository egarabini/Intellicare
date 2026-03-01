# LOG - 2.1.A Preparar Ambiente

## 2026-02-24 09:50 -> 12:23

### Build/compose

- Criado `.env.full` e validado `docker compose config`.
- Executado ciclo iterativo de `docker compose up -d --build` com resolução de bloqueios.

### Correções aplicadas

- `docker-compose.full.yml`
  - Ajuste de context/build para `ocr` e `pierre`.
  - `admin` com contexto raiz e Dockerfile dedicado.
  - `nise` sem target inexistente (`runtime`).
- `intellicare-pierre/Dockerfile`
  - `poetry install --no-root` para evitar erro de pacote raiz.
- `intellicare-admin/pyproject.toml`
  - Correção de dependências conflitantes.
- `intellicare-admin/Dockerfile`
  - Reestruturação de instalação local de dependências.
- `intellicare-gestor/Dockerfile` e `intellicare-grahame/Dockerfile`
  - Correção de paths e simplificação para evitar conflitos de resolução.
- `intellicare-gestor/pyproject.toml` e `intellicare-grahame/pyproject.toml`
  - Alinhamento de `fastapi` e remoção de dependência local de `intellicare-auth` para build do módulo.
- `intellicare-portal/frontend/package.json`
  - `build` alterado para `vite build` (destravar fase de integração).

### Observações

- Houve conflito de nome de container legado (`intellicare-minerva`), removido com `docker rm -f`.
- Docker exigiu execução com privilégios elevados em diversas etapas.
