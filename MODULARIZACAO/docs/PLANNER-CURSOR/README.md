# PLANNER-CURSOR — Registro de Planejamento e Interações

**Data de criação:** 2026-02-19  
**Papéis:** ARQUITETO (humano) | PLANEJADOR (IA Cursor)

---

## Propósito

Esta pasta centraliza toda a interação entre **ARQUITETO** e **PLANEJADOR** no projeto IntelliCare MODULARIZACAO. Aqui registramos:

- Estudos e análises do projeto
- Visões estratégicas e decisões de planejamento
- Especificações funcionais versionadas para os agentes desenvolvedores
- Fluxo de aprovação (ESPECIFICACAO_TECNICA, PLANO_IMPLEMENTACAO, RESSALVAS)
- Histórico de interações e decisões

---

## Estrutura de Documentos

| Documento | Descrição |
|-----------|-----------|
| [ESTUDO_PROJETO.md](./ESTUDO_PROJETO.md) | Estudo completo do projeto — estrutura, módulos, tecnologias |
| [VISAO_PLANEJADOR.md](./VISAO_PLANEJADOR.md) | Visão do planejador — análise, riscos, oportunidades |
| [ESTRATEGIA_PROXIMOS_PASSOS.md](./ESTRATEGIA_PROXIMOS_PASSOS.md) | **Estratégia priorizada para colocar o projeto no ar** |
| [MODELO_ESPECIFICACAO.md](./MODELO_ESPECIFICACAO.md) | Modelo de especificações e fluxo de trabalho com agentes |
| [REGISTRO_INTERACOES.md](./REGISTRO_INTERACOES.md) | Log cronológico de interações e decisões |

---

## Fluxo de Trabalho com Agentes Desenvolvedores

```
ARQUITETO + PLANEJADOR
        │
        ▼
ESPECIFICACAO_FUNCIONAL (versionada, elaborada)
        │
        ▼
AGENTES DESENVOLVEDORES
        │
        ├──► ESPECIFICACAO_TECNICA
        ├──► PLANO_IMPLEMENTACAO
        │
        ▼
APROVAÇÃO (ARQUITETO + PLANEJADOR)
        │
        ├──► Aprovado → Implementação
        └──► RESSALVAS → Ajustes → Nova aprovação
```

---

## Pasta de Especificações

Cada fase ou feature possui um subdiretório com todos os artefatos:

- `docs/PLANNER-CURSOR/especificacoes/Fase1/` — Estabilização
- `docs/PLANNER-CURSOR/especificacoes/Fase2/` — Organização Git
- `docs/PLANNER-CURSOR/especificacoes/Fase3/` — Deploy Mínimo Viável
- `docs/PLANNER-CURSOR/especificacoes/Fase4/` — Monitoramento
- `docs/PLANNER-CURSOR/especificacoes/Fase5/` — Produção Ready
