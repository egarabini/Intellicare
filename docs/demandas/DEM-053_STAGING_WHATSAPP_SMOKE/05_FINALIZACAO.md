# DEM-053 — Staging WhatsApp Smoke — Finalização

## Status: ✅ CONCLUÍDA

- **Commit:** `06a0b1e` (`06a0b1e94bb84bd2f7dcb3bb18b6a9b03ff3ec5e`)
- **Mensagem:** `infra: evolution-api bump atendai/v2.3.7 -> evoapicloud/v2.3.7 (QR fix)`
- **Responsáveis:** DEV-3/4 + Eduardo (escaneio do QR)
- **Data:** 2026-03-21

---

## O que foi resolvido

### Diagnóstico — Evolution API QR broken (v2.2.x)

| Tentativa | Imagem | Resultado |
|---|---|---|
| 1 | `atendai/evolution-api:v2.2.0` | `count:0`, QR nunca gerado |
| 2 | `atendai/evolution-api:v2.1.1` | idem |
| 3 | `atendai/evolution-api:v2.2.2` | idem — Baileys v6 morre silenciosamente |
| 4 | Reset completo banco + Redis | Problema persiste — não era corrupção de estado |
| 5 | `evoapicloud/evolution-api:v2.3.7` | ✅ QR gerado, `state: open` |

**Causa raiz:** Baileys v6 nas imagens `atendai/v2.2.x` tem race condition no WebSocket
que causa morte silenciosa do worker sem emitir o evento `qr`. As imagens do registry
`evoapicloud/` com v2.3.x corrigem esse comportamento.

### Validação final

- `GET /instance/connectionState/intellicare` → `{"state":"open"}` ✅
- Mensagem "Hello World" entregue no celular +5527988358449 ✅
- Evolution retornou status `PENDING` (confirmação Baileys) ✅
- `infra/evolution_secrets_STAGING.txt` deletado do VPS ✅
- `infra/docker-compose.yml` atualizado e commitado ✅

---

## Itens não executados nesta DEM

O smoke test completo de Email e SMS (Fases B e C do BRIEFING) não foi executado
formalmente — o foco foi resolver o bloqueio do QR que estava pendente desde
DEM-INF_STAGING_EVOLUTION. Email e SMS podem ser validados em próxima janela de
staging sem bloqueio arquitetural.

---

## Gotcha registrada

Entrada adicionada em `docs/gotchas/staging-deploy.md`:
**"Evolution API v2.2.x não gera QR Code — usar evoapicloud/v2.3.7"**

---

## Critérios de aceite — verificação final

- [x] `connectionState` retorna `state: open`
- [x] Mensagem WhatsApp real entregue no celular do chip staging
- [x] `infra/evolution_secrets_STAGING.txt` deletado após `open`
- [x] `docker-compose.yml` atualizado com imagem correta e commitado
- [x] Gotcha documentada em `docs/gotchas/staging-deploy.md`
