# DELTA Documentação — Sprint 2026-04-18 (Addendum — fechamento DEM-068)

> Complemento ao `DELTA_SPRINT_2026_04_18.md` (já aplicado).
> DEV-4: aplicar estas atualizações adicionais referentes ao fechamento da DEM-068 e fixes do staging.
> **Status: ⏳ PENDENTE**

---

## Contexto

O DELTA anterior cobriu DEM-065, DEM-066 e DEM-067. Este addendum cobre:
- DEM-068 (Staging Full Sync) — conclusão e smoke final
- Fix portal de agentes (`0807431`) — rename de imagens
- Sprint 2026-04-18 totalmente concluída

---

## Arquivos a atualizar

### `UTILIZACAO/README.md`

Atualizar a linha de escopo:
```
DE: "cobertura funcional: entregas concluídas até DEM-067 (sprint 2026-04-18)"
PARA: "cobertura funcional: sprint 2026-04-18 concluída — DEMs 065 a 068 validadas em staging"
```

---

### `UTILIZACAO/01_VISAO_GERAL_INTELLICARE.md`

Adicionar nota no rodapé ou seção "Estado da plataforma":

```
## Estado atual da plataforma (sprint 2026-04-18 — concluída)

Todos os módulos abaixo foram validados em staging em 2026-03-21:

| Módulo | Smoke staging | Observação |
|--------|-------------|------------|
| Florence (notas IA) | ✅ 200 | |
| Oswaldo (prescrições IA) | ✅ 200 | |
| CarePlanner (jornadas) | ✅ trigger 202 | Kestra com flows condicionais ativos |
| Push PWA (notificações) | ✅ subscribe 201 | ClinicoUI + GestorUI |
| Multi-tenant (provisioning) | ✅ provision 201 | Suspend/reactivate funcionais |
| WhatsApp Evolution | ✅ state: open | |
| Health adapters | ✅ 200 | |
```

---

### `UTILIZACAO/02_GUIA_ADMINISTRADOR_PLATAFORMA.md`

**Seção 2.2 — acrescentar observação sobre o Portal de Agentes:**

As imagens dos agentes disponíveis na plataforma foram renomeadas — o sufixo `_ia` foi removido dos arquivos. Isso não afeta a experiência do usuário (nomes visíveis na interface não mudaram), mas equipes de suporte ou documentação que referenciem arquivos de imagem pelo nome devem usar o novo padrão:

```
agente_florence.png   (antes: agente_florence_ia.png)
agente_oswaldo.png    (antes: agente_oswaldo_ia.png)
agente_marie.png      (antes: agente_marie_ia.png)
agente_pierre.png     (antes: agente_pierre_ia.png)
... (padrão: agente_{nome}.png para todos)
```

---

### `UTILIZACAO/03_GUIA_GESTOR_TENANT.md`

**Seção sobre CarePlanner — acrescentar nota sobre flows condicionais validados em staging:**

```
Nota operacional (validado em staging 2026-03-21):
Os flows condicionais estão ativos no ambiente de staging:
- Fallback automático de canal (WA → Email) funcionando
- Confirmação "Sim"/"Não" via WhatsApp processa automaticamente
- Retry com backoff ativo (2h → 6h → 24h)
```

---

### `UTILIZACAO/MANUAL_USUARIO_INTELLICARE_COMPLETO.md` e `PRONTO_PARA_IMPRESSAO.md/.html`

- Atualizar cabeçalho/rodapé: versão `Sprint 2026-04-18 — Concluída (DEMs 065–068)`
- Aplicar as mesmas adições dos arquivos individuais acima no manual consolidado
- Regenerar versão HTML após atualizar o `.md`

---

## Não impactado neste addendum

| Arquivo | Motivo |
|---------|--------|
| `04_GUIA_CLINICO.md` | Já atualizado no DELTA anterior (push toggle) |
| `05_GUIA_PACIENTE.md` | Sem mudanças neste fechamento |
| `06_DASHBOARDS_E_RELATORIOS.md` | Sem novos painéis |
| `07_CHECKLIST_IMPLANTACAO_E_TREINAMENTO.md` | Sem mudanças |
| `08`, `09`, `10` | Prints de agentes: usar nomes sem `_ia` se capturar telas do Portal |

---

## Referência — commits deste sprint

| Commit | O que entrou |
|--------|-------------|
| `683c0f9` | DEM-065 Multi-tenant Avançado |
| `98d0310f` | DEM-066 Push PWA |
| `5b7e1a42` | DEM-067 Kestra Flows Condicionais |
| `0807431` | Fix: rename imagens agentes Portal |
| `d7cc7cc8` | Fix: Dockerfile, push_subscriptions, Kestra multipart |
| `772a1dd` | DEM-068 evidência staging sync — sprint fechado |

---

*Gerado automaticamente ao encerrar sprint 2026-04-18 (fechamento final) — IntelliCare ARQUITETO*
