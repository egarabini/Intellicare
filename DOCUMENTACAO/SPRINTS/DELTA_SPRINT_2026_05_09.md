# DELTA Sprint 2026-05-09 — Atualizações UTILIZACAO

> Para: DEV-4
> Sprint: 2026-05-09 | Status: ⏳ Pendente
> DEMs entregues: DEM-079, DEM-080, DEM-081, DEM-082

---

## O que mudou para o usuário final

### DEM-079 — Florence com IA contextualizada (ClinicoUI)

Florence agora usa o histórico clínico do paciente ao sugerir o SOAP. O botão "Sugestão IA" em `EncounterView` continua o mesmo — o resultado é mais personalizado quando há encontros anteriores registrados.

**Atualizar em** `UTILIZACAO/05_CLINICO_GUIA.md`:
- Na seção do Florence: adicionar parágrafo explicando que a sugestão IA agora considera o histórico longitudinal do paciente (últimos encontros, notas, prescrições)
- Nota: quando MARIE_ENABLED está ativo em produção, a sugestão pode levar 2–5s a mais — comportamento esperado

---

### DEM-080 — Assinatura Digital no Receituário (ClinicoUI)

Médicos podem agora fazer upload do seu certificado digital A1 (.pfx) e os receituários gerados serão assinados digitalmente.

**Atualizar em** `UTILIZACAO/12_RECEITUARIO_DIGITAL.md` (ou criar se não existir):
- Nova seção: **Certificado Digital**
  - Para ativar a assinatura: ir em Perfil → seção "Certificado Digital" → enviar arquivo `.pfx` + senha
  - Após upload, todos os receituários gerados terão assinatura digital embutida
  - Para remover o certificado: botão "Remover" na mesma seção
  - Nota importante: o receituário é gerado mesmo sem certificado — a assinatura é opcional
  - Nota para produção: para assinatura com validade jurídica, o certificado deve ser emitido por AC credenciada ICP-Brasil. Certificados autoassinados (testes) mostram aviso no Adobe Reader

---

### DEM-081 — KPIs Clínicos (GestorUI)

Nova página `/indicadores` no GestorUI com dashboard de indicadores clínicos.

**Criar** `UTILIZACAO/16_GESTORUI_INDICADORES.md` com:
- Como acessar: GestorUI → menu lateral → "Indicadores"
- Filtros disponíveis: período (data início/fim), profissional (opcional)
- KPIs exibidos:
  - Total de encontros no período
  - Total de notas Florence geradas
  - Total de prescrições emitidas
  - Total de interações medicamentosas detectadas
  - Jornadas CarePlanner por status (ativa, concluída, expirada)
  - Top profissionais por prescrições
  - Gráfico de interações detectadas por dia (linha temporal)
- **Nota importante**: o contador de interações (`interaction_warnings_count`) não é retroativo — prescrições geradas antes da DEM-077 aparecem como 0 interações, mesmo que existissem
- Filtro por profissional não afeta o KPI de interações por dia (limitação conhecida)

---

## Configuração de produção (para DEV-3/4 no deploy)

Antes de ativar `MARIE_ENABLED=true` em produção:
1. Configurar LLM provider no console Dify (`/settings/model-provider`) — sem isso, Florence usa fallback rule-based
2. `SERVER_ENCRYPTION_KEY` deve ser gerada uma única vez e nunca rotacionada enquanto houver certificados armazenados
3. Migrations 019 e 020 aplicadas em todos os schemas de tenant ativos

---

## O que NÃO precisa ser documentado pelo DEV-4

- Internos do `call_marie()`, `sign_pdf()`, `get_clinical_kpis()` — são implementação
- Workflow Dify — interno da plataforma
- `dify_setup.py` — ferramenta de operações, não de usuário
