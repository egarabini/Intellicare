---
tipo: especificacao-funcional
demanda: DEM-077
titulo: Oswaldo — Interação Medicamentosa
sprint: 2026-05-02
status: em-execucao
dev: DEV-1
criado: 2026-03-22
depende_de: [DEM-058, DEM-072]
habilita: []
tags: [oswaldo, prescricao, seguranca-clinica, interacao, medicamento]
---

# DEM-077 — Oswaldo Interação Medicamentosa

## Objetivo

Adicionar verificação de interações medicamentosas ao editor de prescrições do Oswaldo. Quando o clínico adiciona ou edita um medicamento, o sistema verifica automaticamente se há conflito com outros medicamentos já na prescrição e exibe um **alerta visual** não bloqueante — o clínico pode ignorar e prescrever mesmo assim, mas está ciente do risco.

---

## Personas

**Clínico (Oswaldo):** ao adicionar um medicamento em uma prescrição, vê um aviso amarelo/vermelho se há interação conhecida com outro medicamento já na lista. O aviso não impede a prescrição — é informativo.

**Paciente:** não impactado diretamente. Beneficiado indiretamente pela maior segurança da prescrição.

---

## Mecanismo de verificação — dois níveis

**Nível 1 — Checker estático (tabela local):**
Base de dados de ~150 pares de interações graves/moderadas curada a partir de fontes abertas (Bulário Eletrônico ANVISA + interações clássicas da literatura). Verificação instantânea, sem LLM, sem internet.

**Nível 2 — LLM fallback (se par não encontrado na tabela):**
Se os medicamentos não estão na tabela estática, uma chamada ao LLM local (`shared/llm`) verifica a interação. Usado apenas quando necessário — não substitui a tabela para pares conhecidos.

---

## Exemplos de interações cobertas na tabela estática

| Medicamento A | Medicamento B | Nível | Efeito |
|--------------|--------------|-------|--------|
| Varfarina | AAS | GRAVE | Risco hemorrágico aumentado |
| Metformina | Álcool | MODERADO | Risco de acidose lática |
| IECA | Espironolactona | MODERADO | Hipercalemia |
| Digoxina | Amiodarona | GRAVE | Toxicidade digitálica |
| Fluoxetina | Tramadol | GRAVE | Síndrome serotoninérgica |
| Sildenafil | Nitrato | GRAVE | Hipotensão grave |

---

## Interface — warning no editor

```
┌─ Prescrição ───────────────────────────────────────────────────┐
│  Atenolol 50mg  1x/dia  via oral                    [remover]  │
│  Varfarina 5mg  1x/dia  via oral                    [remover]  │
│  AAS 100mg      1x/dia  via oral                    [remover]  │
│                                                                  │
│  ⚠️  Interação detectada: Varfarina + AAS                       │
│     Nível: GRAVE — Risco hemorrágico aumentado                  │
│     [Entendido — manter prescrição]                             │
│                                                                  │
│  [+ Adicionar medicamento]   [Sugerir via IA]                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Critérios de aceite

1. Ao adicionar medicamento com interação grave, banner vermelho aparece no editor
2. Ao adicionar medicamento com interação moderada, banner amarelo aparece
3. Botão "Entendido — manter prescrição" fecha o banner e permite salvar
4. Se não há interação, nenhum banner é exibido
5. `POST /oswaldo/check-interactions` retorna lista de `InteractionWarning`
6. 5+ testes automatizados cobrindo: par grave, par moderado, sem interação, LLM fallback, múltiplos pares

---

## Fora de escopo

- Integração com base RxNorm online (sem dependência de internet)
- Interações com alimentos ou condições clínicas (foco em fármaco-fármaco)
- Bloqueio automático da prescrição (é sempre decisão do médico)
