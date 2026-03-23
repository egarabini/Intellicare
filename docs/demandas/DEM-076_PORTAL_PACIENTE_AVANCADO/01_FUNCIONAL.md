---
tipo: especificacao-funcional
demanda: DEM-076
titulo: Portal Paciente Avançado
sprint: 2026-05-02
status: em-execucao
dev: DEV-2
criado: 2026-03-22
depende_de: [DEM-071, DEM-072]
habilita: []
tags: [portal, paciente, timeline, receituario, privacidade]
---

# DEM-076 — Portal Paciente Avançado

## Objetivo

Expor ao paciente as duas funcionalidades entregues no sprint anterior — **Linha do Tempo** e **Receituário Digital** — diretamente no PacienteUI. O paciente passa a ter acesso ao seu próprio histórico clínico consolidado e pode baixar suas prescrições em formato PDF CFM/ANVISA.

---

## Personas

**Paciente:** acessa o PacienteUI e deseja:
- Ver seu histórico clínico completo em ordem cronológica (consultas, notas, prescrições, jornadas)
- Baixar o receituário de uma prescrição específica para apresentar na farmácia
- Não ter acesso a anotações privadas do médico (campo `soap_a` — avaliação clínica interna)

**Clínico:** não é impactado por esta DEM. Nenhum dado novo é criado ou alterado.

---

## Funcionalidades

### F1 — Linha do Tempo no Portal

Nova aba "Meu Histórico" no PacienteUI com a linha do tempo longitudinal do paciente. Reutiliza o endpoint `GET /cuidado/patients/{id}/clinical-timeline` com filtro de privacidade aplicado.

**Regras de privacidade:**
- `encounters` — exibir: data, motivo da consulta, CID (se liberado pelo médico). Ocultar: `soap_a` (avaliação interna)
- `clinical_notes` — exibir: notas tipo `FREE` e resumo `soap_s` (subjetivo). Ocultar: `soap_a`, `soap_p` (plano interno)
- `prescriptions` — exibir: todos os campos (já são dados do paciente)
- `care_tasks` — exibir: tipo e status. Ocultar: notas internas de triagem

### F2 — Download de Receituário

No histórico de prescrições do portal, botão "Baixar Receituário" para cada prescrição. Chama `GET /oswaldo/prescriptions/{id}/receituario.pdf?type=simple` com autenticação do paciente.

**Regra de acesso:** paciente só pode baixar receituários de suas próprias prescrições (`prescription.patient_id == current_user.patient_id`).

---

## Critérios de aceite

1. PacienteUI → "Meu Histórico" exibe linha do tempo com eventos do paciente autenticado
2. Notas com `soap_a` não aparecem no portal (filtro de privacidade no backend)
3. Botão "Baixar Receituário" aparece em cada prescrição da timeline
4. Clique no botão abre PDF em nova aba (não forçar download)
5. Tentativa de acessar receituário de outro paciente retorna 403
6. 4+ testes automatizados cobrindo privacidade e controle de acesso

---

## Fora de escopo

- Assinatura digital ICP-Brasil no receituário (fase futura)
- Paciente enviar mensagem ao médico via portal
- Filtros avançados na timeline do paciente (simplicidade primeiro)
