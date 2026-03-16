# DEM-027 — Diário de Desenvolvimento

## 1. Planejamento
Nesta fase, recebemos os requisitos do DEM-027 e configuramos o `03_PLANO.md`. Realizamos a leitura e abstração dos requisitos de WeasyPrint. Aguardando a liberação para seguir para a Codificação.

## 2. Execução (Backend & Infra)
- Modificado `deploy/Dockerfile` para adicionar os pacotes do `weasyprint` (libpango, libharfbuzz, libfontconfig) no stage 2 do Python.
- Incluído `weasyprint` e `jinja2` no `pyproject.toml` do pacote `intellicare-core`.
- Criado o core PDF `renderer.py` em `packages/intellicare-core/intellicare_core/pdf` junto aos templates HTML `base.html`.
- Criados os templates de todos os 6 relatórios exigidos: `admin_receita`, `admin_tenants`, `gestor_consultas`, `gestor_profissionais`, `clinico_prontuario`, `clinico_agenda`.
- Rotas `/relatorios/*` criadas para os três módulos correspondentes (Admin, Gestor, Cuidado) devolvendo PDF compilado em bytes.

## 3. Integração Frontend
- Desenvolvido um Hook padronizado `useDownloadPdf` em React que anexa o JWT nas requisições via Blob e força o navegador a salvar o documento na máquina local. O Hook foi propagado para os módulos Admin, Gestor e Clinico.
- Export Buttons adicionados e vinculados nos Dashboards correspondentes.
- Ajustado o Typescript do DatePicker no `RelatoriosPage` do GestorUI para satisfazer a interface da `@mantine/dates`. Diferente da AdminUI, Gestor utilizava uma UI Range conflitante.
- Inserido `--legacy-peer-deps` à esteira de Node Packages (`Dockerfile`) devido ao Vite no Node:20 reclamar sobre disparidades nos sub-pacotes de interface de outros frameworks.
