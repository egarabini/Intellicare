---
tipo: especificacao-funcional
demanda: DEM-041
titulo: Templates CarePlanner — CRUD + integração TriggerModal
sprint: "4.2"
status: pronto-para-dev
planejador: Claude (PLANEJADOR)
criado: 2026-03-18
depende_de: [DEM-038, DEM-040]
habilita: [DEM-042]
tags: [careplanner, templates, backend, frontend, gestorui, p1]
---

# DEM-041 — Templates CarePlanner (CRUD + integração TriggerModal)

## Objetivo

Dar ao gestor controle total sobre os templates de mensagem que o CarePlanner
envia aos pacientes. Hoje o campo `template_code` no modal "Nova Jornada" é
texto livre — o gestor precisa memorizar os códigos e o sistema falha silenciosamente
se o código não existir. Esta DEM expõe a tabela `care_templates` (já criada
pela DEM-038) via API e GestorUI, e transforma o campo de texto em um Select
dinâmico com os templates ativos do tenant.

---

## Estado Atual vs. Estado Desejado

| Item | Hoje | DEM-041 |
|------|------|---------|
| Tabela `care_templates` | ✅ existe, multi-tenant, UNIQUE por code+channel+tenant | mantida |
| `create_template` no repositório | ✅ | mantido |
| `list_templates` no repositório | ✅ | mantido |
| `update_template` no repositório | ❌ | ✅ UPDATE por id |
| `get_template` (por id) | ❌ | ✅ SELECT por id |
| Endpoints REST | ❌ nenhum exposto | ✅ 4 endpoints |
| Página de gestão no GestorUI | ❌ | ✅ `/careplanner/templates` |
| `template_code` no TriggerModal | TextInput livre | ✅ Select com templates ativos |
| Templates de exemplo (seed) | ❌ | ✅ 4 templates default por tenant |

---

## Critérios de Aceite

1. `GET /careplanner/templates` retorna lista de templates do tenant com status 200.
2. `POST /careplanner/templates` cria template; código duplicado (mesmo code+channel)
   retorna 409 com `code: "template_already_exists"`.
3. `PUT /careplanner/templates/{id}` atualiza `content`, `variables` e `active`;
   retorna o template atualizado.
4. `PATCH /careplanner/templates/{id}/toggle` inverte o campo `active`; retorna
   `{ id, active }`.
5. A página `/careplanner/templates` lista todos os templates do tenant numa tabela
   com código, canal, prévia do conteúdo (60 chars), badge ativo/inativo e botões
   editar e toggle.
6. O modal "Novo Template" valida campos obrigatórios (code, content) e exibe
   o erro 409 como mensagem inline (não toast).
7. O formulário de edição pré-popula com os valores atuais do template.
8. No `TriggerJourneyModal` (DEM-040), o campo `template_code` é substituído por
   um Select que carrega templates ativos via `GET /careplanner/templates?active=true`.
   O Select mostra `template_code — primeiros 40 chars do content`.
9. Seed de 4 templates default: `boas_vindas`, `check_in`, `lembrete_medicacao`,
   `teleconsulta_confirmacao` — criados na inicialização se não existirem.
10. 3 testes Python e 2 testes Playwright passando sem regressão.

---

## O que NÃO está incluído

- Versionamento de templates (histórico de edições)
- Templates para outros canais além de Rocket.Chat
- Variáveis dinâmicas com preview renderizado
- Permissão granular por tipo de template (qualquer GESTOR pode editar qualquer template)
- Import/export de templates em CSV ou JSON

---

## Notas para o Agente Desenvolvedor

- A tabela tem `UNIQUE (template_code, channel, tenant_slug)` — capturar
  `IntegrityError` do SQLAlchemy e converter em `api_error(409, "template_already_exists", ...)`.
- `variables` é `JSONB DEFAULT '[]'` que armazena `list[str]` — nomes das
  variáveis usadas no template, ex. `["nome_paciente", "data_consulta"]`. No
  frontend, exibir como chips/tags separados por vírgula.
- `get_template_by_code` (já existe) é usado pelo dispatcher; não alterar.
- O seed de templates deve usar `INSERT ... ON CONFLICT DO NOTHING` para ser idempotente.
- Adicionar `?active=true` como query param em `list_templates` do repositório
  e repassar na rota de listagem — assim o TriggerModal só carrega ativos.
- A página `/careplanner/templates` é acessível por GESTOR. Adicionar ao NavLink
  do AppShell como sub-item do "CarePlanner" usando `MantineNavLink` com `childrenOffset`.
