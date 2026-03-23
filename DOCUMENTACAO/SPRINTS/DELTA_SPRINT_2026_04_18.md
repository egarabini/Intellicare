# DELTA Documentação — Sprint 2026-04-18

> Resumo das mudanças que impactam a documentação de usuário.
> **Status: ✅ APLICADO** — DEV-4 executou todas as correções em 2026-03-21.
> DEV-4: aplique este delta nos arquivos indicados antes do próximo sprint.

---

## Arquivos a atualizar

### `README.md`
- Linha de escopo: alterar de `"cobertura funcional: entregas concluídas até DEM-063"` para `"cobertura funcional: entregas concluídas até DEM-067 (sprint 2026-04-18)"`.
- Remover nota sobre DEM-064 em andamento — está concluída (`af3e66bb`).

---

### `01_VISAO_GERAL_INTELLICARE.md`
- Seção "O que está fora de escopo": remover referência a DEM-064 em progresso.
- Adicionar linha no mapa funcional:
  - `notificacoes-push`: alertas nativos do browser mesmo com app fechado (ClinicoUI + GestorUI).

---

### `02_GUIA_ADMINISTRADOR_PLATAFORMA.md` ← **maior impacto (DEM-065)**

**Seção 2.2 — Criação de tenant: REESCREVER**

O fluxo mudou completamente. Agora é automático via `TenantsManager`:

```
Campos do modal "Novo Tenant":
- Slug (obrigatório — lowercase, sem espaços, imutável após criação)
- Nome de exibição (obrigatório)
- Plano: standard | premium | enterprise

O que acontece automaticamente ao clicar "Criar":
1. Schema PostgreSQL criado para o tenant
2. Migrations aplicadas no novo schema
3. Realm e client criados no Keycloak
4. Seed básico (módulos padrão, roles, usuário gestor inicial)

Resultado esperado:
- Badge "provisioning" (amarelo) durante criação
- Badge "active" (verde) ao concluir
- Tenant aparece na lista com data de criação e plano
```

**Seção 2.3 — Edição de tenant: ATUALIZAR**

Adicionar que agora existe `TenantConfigPage` para editar:
- Plano (standard / premium / enterprise)
- `max_users` (limite de usuários)
- Módulos ativos (Florence, Oswaldo, CarePlanner — toggle por módulo)

**Seção nova 2.5 — Suspensão e reativação de tenant**

```
Suspender:
- Clicar no botão "Suspender" na linha do tenant
- Badge muda para "suspended" (vermelho)
- Todos os usuários do tenant recebem 403 na próxima requisição
- Dados permanecem intactos

Reativar:
- Clicar em "Reativar"
- Acesso restaurado imediatamente
- Badge volta para "active" (verde)

Uso operacional: suspensão por inadimplência, manutenção emergencial, violação de termos.
```

---

### `03_GUIA_GESTOR_TENANT.md` ← **impacto DEM-067 (flows condicionais)**

**Seção sobre CarePlanner / TriggerModal — adicionar:**

```
Seleção de fluxo ao disparar jornada:
- O sistema agora oferece seleção de fluxo no modal de disparo.
- Fluxo padrão: "Jornada com Fallback de Canal"
  → Tenta WhatsApp primeiro; se falhar, dispara Email automaticamente.
- Outros fluxos disponíveis:
  → "Retry com Backoff": reenvia após 2h, 6h e 24h sem resposta.
  → "Urgência Clínica": escala para o clínico se paciente não responder em 1h.

Confirmação automática de consulta:
- Se o paciente responder "Sim" / "Confirmo" / "Ok" via WhatsApp,
  a consulta é confirmada automaticamente — sem ação manual do gestor.
- Se responder "Não" / "Cancelar", sistema solicita reagendamento automaticamente.
```

**Adicionar seção: Notificações Push (DEM-066)**

```
Ativar notificações push (GestorUI):
1. Clicar no ícone de sino no canto superior direito.
2. Clicar no toggle "Receber notificações mesmo com app fechado".
3. Browser solicita permissão → clicar "Permitir".
4. A partir deste momento, alertas chegam mesmo com o browser fechado.

Desativar: repetir o processo — toggle desliga e remove a inscrição.
```

---

### `04_GUIA_CLINICO.md` ← **impacto DEM-066**

**Adicionar seção 4.7 — Notificações Push:**

```
Ativar notificações push (ClinicoUI):
1. Clicar no sino no canto superior direito.
2. Ativar o toggle "Receber notificações mesmo com app fechado".
3. Autorizar quando o browser solicitar permissão.

Casos em que o push chega com o app fechado:
- Nova mensagem de paciente no CarePlanner (WhatsApp / RocketChat).
- Jornada expirada sem resposta.

Observação: em iOS, o recurso exige que o ClinicoUI esteja
instalado na tela inicial ("Adicionar à tela inicial" no Safari).
```

---

### `MANUAL_USUARIO_INTELLICARE_COMPLETO.md` e `MANUAL_USUARIO_INTELLICARE_PRONTO_PARA_IMPRESSAO.md`

- Atualizar capa/cabeçalho: versão de `DEM-063` para `DEM-067 | Sprint 2026-04-18`.
- Aplicar os mesmos deltas das seções acima nos capítulos correspondentes do manual consolidado.
- Atualizar versão HTML (`PRONTO_PARA_IMPRESSAO.html`) após o .md estar revisado.

---

## Não impactado neste sprint

| Arquivo | Motivo |
|---------|--------|
| `05_GUIA_PACIENTE.md` | Nenhuma mudança de interface no PacienteUI neste sprint |
| `06_DASHBOARDS_E_RELATORIOS.md` | Sem novos painéis neste sprint |
| `07_CHECKLIST_IMPLANTACAO_E_TREINAMENTO.md` | Adicionar item: "Ativar push no ClinicoUI e GestorUI" na seção Clínico e Gestor |
| `08`, `09`, `10` | Adicionar prints: TenantsManager, TenantConfigPage, toggle push |

---

## Prints novos necessários (para os guias visuais)

| Tela | Arquivo de destino |
|------|--------------------|
| AdminUI → TenantsManager (lista com badges) | `02_GUIA_ADMINISTRADOR_PLATAFORMA.md` |
| AdminUI → Modal "Novo Tenant" preenchido | `02_GUIA_ADMINISTRADOR_PLATAFORMA.md` |
| AdminUI → TenantConfigPage (plano + módulos) | `02_GUIA_ADMINISTRADOR_PLATAFORMA.md` |
| AdminUI → Tenant suspenso (badge vermelho) | `02_GUIA_ADMINISTRADOR_PLATAFORMA.md` |
| ClinicoUI → NotificationBell toggle push | `04_GUIA_CLINICO.md` |
| GestorUI → TriggerModal com seleção de fluxo | `03_GUIA_GESTOR_TENANT.md` |

---

*Gerado automaticamente ao encerrar sprint 2026-04-18 — IntelliCare ARQUITETO*
