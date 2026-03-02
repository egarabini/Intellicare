# Plano de Implementação — Extensão Odontológica

**Data:** 2026-03-02  
**Status:** Esboço  
**Versão:** 0.1

---

## 1. Objetivo

Definir as fases e ações para estender o IntelliCare à área odontológica, mantendo a arquitetura modular e o padrão FHIR R4.

---

## 2. Fases Propostas

### Fase 0 — Estudo e Validação (Pré-requisito)

| # | Ação | Prioridade | Responsável |
|---|------|------------|-------------|
| 0.1 | Estudar FHIR Dental Data Exchange IG (STU1 e v2.0 ballot) | Alta | Arquiteto |
| 0.2 | Validar proposta com dentistas e gestores de clínicas | Alta | Produto |
| 0.3 | Mapear terminologias: CDT, ICDAS, FDI ↔ FHIR | Média | Técnico |
| 0.4 | Avaliar requisitos regulatórios (CFO, prontuário) | Média | Compliance |

**Entregáveis:** Documento de viabilidade, glossário odontológico-FHIR.

---

### Fase 1 — Fundação FHIR Odontológica

| # | Ação | Prioridade | Dependência |
|---|------|------------|-------------|
| 1.1 | Estender Grahame com value sets odontológicos | Alta | Fase 0 |
| 1.2 | Implementar perfis FHIR Dental no repositório | Alta | 1.1 |
| 1.3 | Criar mapeamento CDT/ICDAS → FHIR CodeableConcept | Média | 0.3 |
| 1.4 | Documentar exemplos de recursos Dental (Bundle, ServiceRequest) | Baixa | 1.2 |

**Entregáveis:** Grahame com suporte a perfis odontológicos, documentação de exemplos.

---

### Fase 2 — Módulo Odontológico Base

| # | Ação | Prioridade | Dependência |
|---|------|------------|-------------|
| 2.1 | Criar `intellicare-odontologia/` com estrutura padrão | Alta | Fase 1 |
| 2.2 | Implementar contrato BaseAgent (health, info, analyze) | Alta | 2.1 |
| 2.3 | Expor endpoints para Dental ServiceRequest, Dental Finding | Alta | 2.2 |
| 2.4 | Integrar com intellicare-core (FHIRClient, TenantResolver) | Alta | 2.1 |
| 2.5 | Adicionar ao docker-compose.full.yml e smoke_test | Média | 2.4 |

**Entregáveis:** Módulo odontológico funcional, health check, integração com Wanda.

---

### Fase 3 — Casos de Uso Prioritários

| # | Ação | Prioridade | Dependência |
|---|------|------------|-------------|
| 3.1 | **Referência médico → dentista:** Dental Referral Note | Alta | Fase 2 |
| 3.2 | **Referência dentista → médico:** Consult Note | Alta | 3.1 |
| 3.3 | Integração IPS com dados odontológicos relevantes | Média | 3.1 |
| 3.4 | Portal: tela de encaminhamento odontológico | Média | 3.1 |

**Entregáveis:** Fluxo de referência médico-dentista funcional, documentação de uso.

---

### Fase 4 — Funcionalidades Avançadas (Backlog)

| # | Ação | Prioridade |
|---|------|------------|
| 4.1 | Odontograma (representação FDI em FHIR) | Média |
| 4.2 | Plano de tratamento odontológico (CarePlan adaptado) | Média |
| 4.3 | **Agendamento odontológico** (Schedule, Slot, Appointment + fila operacional) | **Alta** |
| 4.4 | Faturamento odontológico | Baixa |
| 4.5 | Indicadores Donabedian para odontologia | Baixa |

> **Nota:** O agendamento odontológico é um módulo crítico e requer trabalho aprofundado. Ver [AGENDAMENTO_ODONTOLOGICO.md](./AGENDAMENTO_ODONTOLOGICO.md) para especificação de domínio (horários rígidos, ordem de chegada, pré-recepção por atendentes).

---

## 3. Estrutura do Módulo Proposta

```
intellicare-odontologia/
├── odontologia/
│   ├── api/
│   │   └── app.py           # FastAPI + BaseAgent
│   ├── services/
│   │   ├── referral.py      # Referência médico-dentista
│   │   └── dental_fhir.py    # Mapeamento recursos FHIR odontológicos
│   ├── fhir/
│   │   └── profiles.py      # Perfis Dental (DentalCondition, DentalFinding, etc.)
│   └── config.py
├── tests/
├── pyproject.toml
├── Dockerfile
└── README.md
```

---

## 4. Integrações com Módulos Existentes

| Módulo | Integração Odontológica |
|--------|--------------------------|
| **Grahame** | Value sets odontológicos, perfis Dental |
| **Wanda** | Roteamento para agente odontológico |
| **Geralda** | CarePlan para plano de tratamento |
| **Oswaldo** | Análise clínica com contexto odontológico |
| **Portal** | Telas de encaminhamento, visualização odontograma |
| **Auth** | Mesmos fluxos; roles para dentistas |

---

## 5. Critérios de Aceite — Fase 1 (MVP)

- [ ] Grahame expõe value sets odontológicos (Dental Anatomy, Tooth Identification)
- [ ] Módulo `intellicare-odontologia` responde em `/api/v1/health` e `/api/v1/info`
- [ ] Endpoint `/api/v1/dental/referral` aceita e retorna Dental Referral Note (FHIR)
- [ ] Smoke test inclui módulo odontológico
- [ ] Documentação de exemplos de recursos FHIR odontológicos

---

## 6. Referências

- [HL7 FHIR Dental Data Exchange IG](https://hl7.org/fhir/us/dental-data-exchange/)
- [HL7 Dental Data Exchange STU1](http://hl7.org/fhir/us/dental-data-exchange/STU1/)
- [CLAUDE.md](../../CLAUDE.md) — Arquitetura IntelliCare
