---
tipo: especificacao-funcional
demanda: DEM-067
titulo: Kestra Flows Condicionais
sprint: 2026-04-18
status: em-execucao
dev: CODEX
criado: 2026-03-21
depende_de: [DEM-039, DEM-047, DEM-048, DEM-049]
habilita: [DEM-068]
tags: [kestra, workflow, careplanner, branching, fallback, retry, urgencia]
---

# DEM-067 — Kestra Flows Condicionais

## Objetivo

Os flows Kestra atuais executam jornadas lineares: disparo → mensagem → timeout. Não há inteligência de roteamento. Quando o WhatsApp falha, nenhum fallback ocorre. Quando o paciente responde "SIM" ou "NÃO", a resposta é descartada. Esta DEM adiciona lógica condicional real aos flows — tornando as jornadas adaptativas ao comportamento do paciente e à disponibilidade dos canais.

---

## Estado Atual vs. Estado Desejado

| Aspecto | Hoje | Após DEM-067 |
|---------|------|--------------|
| WA falha no disparo | Jornada fica presa em FAILED | Fallback automático para Email |
| Paciente responde "SIM" | Resposta ignorada | Consulta confirmada automaticamente |
| Paciente responde "NÃO" | Resposta ignorada | Reagendamento solicitado automaticamente |
| Sem resposta em 2h | Expira sem reenvio | Reenvio em 2h, 6h, 24h antes de expirar |
| Urgência clínica | Sem fluxo especial | Escala para clínico em 1h, gestor em 2h |
| `trigger_flow()` | Flow fixo `jornada_basica` | Flow configurável por template de jornada |

---

## Personas e fluxos

**Gestor dispara jornada de confirmação de consulta:**
1. Seleciona template "Confirmação Consulta" no TriggerModal
2. Kestra executa `jornada_com_fallback`:
   - Tenta WA → se FAILED → Email automático sem intervenção
3. Paciente responde "Sim" via WA → consulta confirmada, clínico notificado
4. Paciente não responde → sistema reenvia após 2h e 6h antes de expirar

**Gestor dispara jornada de urgência:**
1. Seleciona template "Resultado Crítico" (urgency_level: HIGH)
2. Kestra executa `urgencia_clinica`:
   - WA imediato
   - 1h sem leitura → notifica clínico no RocketChat
   - 2h sem resposta → escala para gestor
   - Log de auditoria gravado

---

## Critérios de aceite

1. WA com FAILED → Email disparado automaticamente (sem intervenção humana)
2. Resposta "sim" / "confirmo" / "ok" → normalizada para "SIM" → consulta confirmada
3. Resposta "não" / "cancelar" → reagendamento solicitado via `/appointments/{id}/request-reschedule`
4. `trigger_flow()` aceita parâmetro `flow_id` sem breaking change (default: `jornada_com_fallback`)
5. `seed_flows.py` sobe os 4 flows novos no Kestra sem erros
6. 5/6 testes passando (urgência pode ser mockada)

---

## Fora de escopo

- Interface visual para editar flows (responsabilidade do Dify/Marie futuramente)
- Branching por resultado de exame laboratorial
- Push PWA como canal de fallback (depende de DEM-066 estar estável)
