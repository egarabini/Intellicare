# WAHA — Integração como Ferramenta Auxiliar

**EF:** EF-COM-034  
**Domínio:** D4 — Notificações e Canais Externos  
**Status:** Planejado  
**Data:** 19 de Fevereiro de 2026

---

## Visão Geral

O **WAHA** (WhatsApp HTTP API) é uma ferramenta open-source (Apache 2.0) que complementa a Meta WhatsApp Business API no módulo intellicare-comunicacao. Integrado como **canal auxiliar**, não substituto.

| Documento | Descrição |
|----------|-----------|
| [ESPECIFICACAO_FUNCIONAL.md](ESPECIFICACAO_FUNCIONAL.md) | Requisitos funcionais detalhados |
| [ESPECIFICACAO_TECNICA.md](ESPECIFICACAO_TECNICA.md) | Arquitetura, contratos, modelos |
| [PLANO_IMPLEMENTACAO.md](PLANO_IMPLEMENTACAO.md) | Passo a passo para o desenvolvedor |
| [20260223_STATUS_IMPLEMENTACAO.md](20260223_STATUS_IMPLEMENTACAO.md) | Status da implementação: feito x pendente |
| [../../04_notificacoes_canais_externos/GUIA_CONFIGURACAO.md](../../04_notificacoes_canais_externos/GUIA_CONFIGURACAO.md) | Configuração de ambiente (Meta + WAHA) |

---

## Uso do WAHA no IntelliCare

| Cenário | Descrição |
|---------|-----------|
| **Homologação/Dev** | Testes sem custo por mensagem (Meta API cobra) |
| **Fallback** | Canal alternativo quando Meta API indisponível |
| **Geralda** | Validação de fluxos paciente-equipe via WhatsApp |

**Produção:** Meta API permanece como canal principal. WAHA é complementar.
