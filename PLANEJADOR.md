# PLANEJADOR.md — Padrão de Planejamento IntelliCare V3

> Documento de regras do papel PLANEJADOR (Claude — ARQUITETO).
> Criado após incidente: dev aguardou 30+ min sem spec, risco de desvio de objetivo.

---

## Papel do PLANEJADOR

O PLANEJADOR é responsável por garantir que **nenhum desenvolvedor inicie uma DEM sem especificação completa**. Antes de qualquer linha de código, a spec deve estar commitada, revisada e disponível no repositório.

---

## Regra 1 — NUNCA registrar DEM na fila sem spec completa

**Proibido:**
```
## 📋 Fila
| DEM-028 | Alertas Grafana | (spec a criar) |   ← ERRADO
```

**Obrigatório:**
```
## 📋 Fila
| DEM-028 | Alertas Grafana | docs/demandas/DEM-028_.../02_TECNICA.md |   ← CORRETO
```

Uma DEM só entra na fila do _dashboard.md **depois** que `01_FUNCIONAL.md` e `02_TECNICA.md` estiverem commitados em `origin/main`.

---

## Regra 2 — O que uma spec completa exige

### `01_FUNCIONAL.md` — O QUÊ e o PORQUÊ

- [ ] Objetivo em 2–3 frases diretas
- [ ] Contexto (por que isso precisa ser feito agora)
- [ ] Lista de comportamentos esperados com exemplos concretos
- [ ] Critérios de aceitação enumerados e verificáveis (não subjetivos)

### `02_TECNICA.md` — COMO implementar

- [ ] Biblioteca/tecnologia escolhida com justificativa
- [ ] Todos os arquivos a criar ou modificar com caminho exato
- [ ] Assinaturas de funções ou contratos de API (métodos, parâmetros, retornos)
- [ ] SQL de migration se houver (completo, não esquemático)
- [ ] Novos endpoints: método, path, roles, request/response
- [ ] Alterações no `docker-compose.yml`, `Dockerfile`, `.env` se necessário
- [ ] Checklist de entrega (`- [ ] item`) que o dev marca ao concluir

**Critério:** o dev deve conseguir implementar a DEM **sem nenhuma pergunta**, usando apenas `01_FUNCIONAL.md` + `02_TECNICA.md` + o código existente no repositório.

---

## Regra 3 — Ordem obrigatória de trabalho

```
1. PLANEJADOR escreve 01_FUNCIONAL.md
2. PLANEJADOR escreve 02_TECNICA.md
3. PLANEJADOR commita ambos em origin/main
4. PLANEJADOR adiciona DEM à fila no _dashboard.md
5. PLANEJADOR distribui a DEM para o dev disponível
6. DEV lê os dois documentos, cria 03_PLANO.md e começa
```

Pular qualquer passo é proibido. Em especial: **os passos 4 e 5 dependem dos passos 1–3**.

---

## Regra 4 — Disciplina do _dashboard.md

| Coluna | Quando mover para lá |
|--------|----------------------|
| ✅ Concluídas | Somente após receber o commit hash do dev e confirmar entrega |
| 🔄 Em execução | Quando o dev confirmar que leu a spec e começou |
| 📋 Fila | Somente após spec 01+02 commitada |
| 🗓️ Planejadas | DEM ainda sem spec — não distribuir, não mencionar para dev |

---

## Regra 5 — Spec deve refletir o projeto real

Antes de escrever a spec, o PLANEJADOR deve:

1. Ler os arquivos relevantes existentes (service.py, router.py, docker-compose.yml, etc.)
2. Confirmar nomes de tabelas, colunas, funções e paths que já existem
3. Identificar dependências entre DEMs (ex: DEM-032 depende de migration 005 do DEM-031)
4. Nunca inventar estruturas que não existem no código sem especificar que devem ser criadas

---

## Regra 6 — Comunicação com o dev

Quando distribuir uma DEM, passar exatamente:

```
DEM-NNN — [Título]
Spec em: docs/demandas/DEM-NNN_NOME/01_FUNCIONAL.md
         docs/demandas/DEM-NNN_NOME/02_TECNICA.md
Dependências: [DEM-XXX migration/tabela específica já aplicada / nenhuma]
Atenção especial: [qualquer desvio conhecido ou ponto de cuidado]
```

Nunca enviar "faça DEM-028" sem o link para a spec.

---

## Anti-padrões documentados

| Anti-padrão | Consequência | Regra violada |
|-------------|--------------|---------------|
| Colocar DEM na fila sem spec | Dev para 30+ min tentando entender o escopo | Regra 1 |
| Spec com "faça algo parecido com X" | Dev implementa algo diferente do esperado | Regra 2 |
| Inventar nomes de tabelas/campos | Dev quebra o banco ou cria duplicatas | Regra 5 |
| Marcar DEM como concluída sem hash | Dashboard desatualizado, rastreabilidade perdida | Regra 4 |
| Distribuir 2 DEMs para 1 dev sem spec da segunda | Dev paralisa na segunda, perde foco | Regra 3 |
