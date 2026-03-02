# Módulo de Agendamento Odontológico — Especificação de Domínio

**Data:** 2026-03-02  
**Status:** Esboço / Levantamento de requisitos  
**Prioridade:** Módulo crítico — requer trabalho aprofundado

---

## 1. Contexto

O agendamento em clínicas odontológicas **não é um simples calendário de reservas**. O fluxo real combina:

- **Horários rígidos** (dentistas, consultórios)
- **Compromissos prefixados** (pacientes com horário marcado)
- **Ordem de chegada** (quem chega primeiro)
- **Pré-recepção** (triagem por um pequeno grupo de atendentes)

O módulo de agendamento deve modelar essa realidade operacional para ser útil no dia a dia da clínica.

---

## 2. Entidades e Restrições

### 2.1 Dentistas

| Aspecto | Descrição |
|--------|-----------|
| **Disponibilidade** | Horários fixos por dia da semana (ex.: seg–sex 8h–18h) |
| **Consultório** | Um ou mais dentistas por consultório; consultório pode ter múltiplas cadeiras |
| **Especialidade** | Pode afetar duração e tipo de slot (ex.: endodontia vs. limpeza) |
| **Ausências** | Férias, licenças, eventos — blocos indisponíveis |

### 2.2 Pacientes

| Aspecto | Descrição |
|--------|-----------|
| **Horário prefixado** | Tem um slot reservado (ex.: 14h com Dr. X) |
| **Ordem de chegada** | Chega na clínica em momento real; pode ser antes ou depois do horário |
| **Prioridade** | Emergência, idoso, criança — pode alterar ordem de chamada |

### 2.3 Atendentes / Recepção

| Aspecto | Descrição |
|--------|-----------|
| **Grupo pequeno** | Poucos atendentes para toda a clínica |
| **Pré-recepção** | Confirmação de dados, triagem, encaminhamento ao consultório |
| **Orquestração** | Decidem quem chama primeiro quando há conflito (chegou antes do horário vs. quem já estava esperando) |
| **Flexibilidade** | Ajustam a fila em tempo real conforme imprevistos |

---

## 3. Fluxo Real vs. Fluxo Idealizado

```
IDEALIZADO (agenda simples):
  Paciente marca 14h → Chega 14h → Entra 14h

REAL (clínica odontológica):
  Paciente marca 14h
       ↓
  Chega 13h45 (antes) ou 14h20 (atrasado)
       ↓
  Pré-recepção (atendente: confirma, triagem, atualiza status)
       ↓
  Fila de espera (ordem de chegada + prioridades + horário original)
       ↓
  Chamada para consultório (atendente decide momento)
       ↓
  Atendimento pelo dentista
```

O **horário marcado** é uma âncora, mas a **ordem efetiva de atendimento** depende da interação entre chegada, pré-recepção e decisão dos atendentes.

---

## 4. Requisitos Funcionais do Módulo

### 4.1 Agenda (camada de restrições)

- [ ] Cadastro de disponibilidade por dentista (blocos de tempo, dias da semana)
- [ ] Cadastro de consultórios e vínculo dentista ↔ consultório
- [ ] Bloqueio de horários (ausências, manutenção)
- [ ] Slots por tipo de procedimento (duração variável)

### 4.2 Reservas (camada de compromissos)

- [ ] Reserva de slot para paciente em horário específico
- [ ] Notificação/lembrete de compromisso
- [ ] Reagendamento e cancelamento

### 4.3 Fila de atendimento (camada operacional)

- [ ] **Check-in** na chegada (registro de ordem de chegada)
- [ ] **Pré-recepção** — status: aguardando triagem | em triagem | pronto para chamar
- [ ] **Fila unificada** por consultório ou por dentista (configurável)
- [ ] Regras de priorização: horário original, ordem de chegada, prioridade clínica
- [ ] **Chamada** — atendente indica "próximo" para consultório X
- [ ] Histórico de fluxo (chegou, triagem, chamado, em atendimento, saiu)

### 4.4 Integração

- [ ] FHIR `Schedule` e `Slot` (disponibilidade)
- [ ] FHIR `Appointment` (compromisso)
- [ ] Recurso customizado ou extensão para **fila/check-in** (não padronizado em FHIR R4)
- [ ] Integração com módulo Comunicacao (lembretes, confirmações)

---

## 5. Modelo de Dados Sugerido (conceitual)

```
Schedule (dentista + período)
    └── Slot[] (janelas disponíveis)

Appointment (paciente + slot + dentista)
    └── status: booked | arrived | in-reception | ready | in-progress | fulfilled | cancelled

AttendanceQueue (fila por consultório/dentista)
    └── QueueEntry (appointment + arrived_at + priority + current_status)
```

---

## 6. Desafios de Implementação

| Desafio | Abordagem |
|---------|-----------|
| **FHIR não modela fila de espera** | Extensão ou recurso customizado; documentar no IG |
| **Conflito horário vs. chegada** | Regras de negócio configuráveis por clínica |
| **Poucos atendentes, muitos pacientes** | UI enxuta; suporte a tablets/celular na recepção |
| **Multi-tenant** | Cada clínica com suas regras (prioridade, tolerância a atraso) |

---

## 7. Priorização no Roadmap

O agendamento odontológico deve ser **bem trabalhado** antes de ir para produção. Sugestão:

| Fase | Escopo |
|------|--------|
| **Fase 4.3 (revisada)** | Agendamento: agenda + reservas (Schedule, Slot, Appointment) |
| **Fase 5 (nova)** | Fila operacional: check-in, pré-recepção, chamada |

Ou tratar como **módulo dedicado** `intellicare-agendamento` (ou `intellicare-agenda`) reutilizável para saúde geral e odontologia, com perfis específicos por domínio.

---

## 8. Referências FHIR

- [Schedule](https://hl7.org/fhir/R4/schedule.html) — Recurso que representa a disponibilidade
- [Slot](https://hl7.org/fhir/R4/slot.html) — Intervalos de tempo disponíveis
- [Appointment](https://hl7.org/fhir/R4/appointment.html) — Compromisso entre paciente e provedor

*Nota: FHIR R4 não possui recurso nativo para "fila de espera" ou "check-in". Será necessário extensão ou recurso customizado.*
