# DEM-027 — Finalização

## Resumo da Entrega
Foi implementada com sucesso a arquitetura para exportação nativa de PDFs (HTML + CSS) baseada em Python WeasyPrint, sem requerer Chromium ou WebKit.

O core de geração (`pdf/renderer.py`) utiliza Jinja2 para contextualização de variávies de um HTML A4 unificado.
Foi criado um botão "Exportar" em UIs do React implementando fetch do Blob via Token Bearer do Oauth2, e forçando download do PDF (Client-side) nomeado especificamente.

## Módulos & Relatórios
1. **Admin**: Receita Mensal (`/receita`), Lista de Tenants Ativos (`/tenants`)
2. **Gestor**: Consultas Agendadas por Período (`/consultas`), Profissionais da Unidade (`/profissionais/{unit_id}`)
3. **Clínico**: Resumo Clínico do Paciente (`/prontuario/{patient_id}`), Agenda do Profissional (`/agenda`)

## Detalhes Técnicos e Lições Aprendidas
- **Docker**: Houveram falhas de integração TypeScript/Vite ocorrendo isoladamente nos ambientes da Docker por conta de versões cruzadas da biblioteca '@mantine/*'. A inclusão de `--legacy-peer-deps` no Stage 1 da pipeline contornou essa barreira.
- **Tipagem GestorUI**: O `@mantine/dates` requisita tipos fechados como `Date`. Uma range não funcionou de acordo e causou conflito TS. Passou-se a usar Data Inicial e Data Final isoladas para evitar que o hook da Mantine quebrasse o frontend de GestorUI.
- **WeasyPrint**: Instalar dependências nativas (pango, harfbuzz) no stage 2 Python do Docker garantiu uma exibição fluida das Fontes no layout paginado PDF, não requerendo ferramentas pesadas no container.

## Próximos Passos
Toda codificação está concluída e integrada nas 3 views da plataforma (Admin, Gestor e Clinico). A estrutura React já se encontra em produção, dependendo puramente da inicialização bem-sucedida do compose intellicare-service.
