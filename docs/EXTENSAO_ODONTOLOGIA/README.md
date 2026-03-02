# Extensão IntelliCare para Área Odontológica

**Data:** 2026-03-02  
**Status:** Esboço / Proposta  
**Versão:** 0.1

---

## 1. Visão Geral

Este documento descreve a proposta de **extensão do IntelliCare** para a área odontológica, aproveitando a arquitetura modular existente e o padrão FHIR R4 como linguagem franca de interoperabilidade.

O IntelliCare foi concebido para saúde geral (cuidado crônico, atenção primária, análise laboratorial, etc.). A extensão odontológica visa ampliar a abrangência da plataforma sem alterar a base técnica, adicionando módulos especializados e perfis FHIR odontológicos.

---

## 2. Viabilidade Técnica

### 2.1 Suporte FHIR à Odontologia

O **HL7** publicou o **Dental Data Exchange Implementation Guide** (US Realm) para FHIR R4, com suporte padronizado:

| Recurso FHIR | Descrição |
|--------------|-----------|
| **Dental Bundle** | Pacote de dados odontológicos |
| **Dental Referral Note** | Encaminhamento médico ↔ dentista |
| **Dental Service Request** | Solicitação de procedimento |
| **Dental Consult Note** | Consulta/retorno |
| **Dental Condition** | Condições odontológicas |
| **Dental Finding** | Achados clínicos |
| **Dental Communication** | Comunicação entre profissionais |

**Value Sets e Code Systems:**
- Dental Anatomy
- Tooth Identification (FDI)
- Oral Cavity Area
- Dental Observation Codes
- Dental Reason For Referral
- Dental Category

**Referência:** [HL7 FHIR Dental Data Exchange IG](https://hl7.org/fhir/us/dental-data-exchange/)

### 2.2 Compatibilidade com a Arquitetura Atual

| Componente IntelliCare | Compatibilidade Odontológica |
|------------------------|------------------------------|
| **FHIR R4 (Grahame)** | Perfis odontológicos são extensões do R4 |
| **Multi-tenancy** | Clínicas odontológicas como tenants |
| **Keycloak / Auth** | Mesmos fluxos de autenticação |
| **Patient, Procedure, Observation** | Recursos base reutilizáveis |
| **CarePlan (Geralda)** | Planos de tratamento odontológico |
| **IPS (Patient Summary)** | Visão integrada saúde + odontologia |

---

## 3. Benefícios da Extensão

1. **Visão integrada do paciente** — Histórico médico e odontológico unificado (medicamentos, alergias, condições crônicas relevantes para procedimentos)
2. **Referências padronizadas** — Fluxos médico → dentista e dentista → médico via FHIR
3. **Economia de escala** — Mesma infraestrutura (PostgreSQL, Redis, Keycloak, portal)
4. **Interoperabilidade** — Integração com sistemas odontológicos que adotem FHIR
5. **Qualidade assistencial** — Donabedian e indicadores adaptáveis à odontologia

---

## 4. Pontos de Atenção

| Aspecto | Consideração |
|---------|--------------|
| **Terminologia** | Integrar CDT, ICDAS, FDI além do FHIR Dental IG |
| **Workflows** | Odontograma, plano de tratamento por arcada, agendamento |
| **Regulamentação** | CFO, prontuário odontológico, LGPD no contexto odontológico |
| **Escopo inicial** | Priorizar casos de uso de maior valor (ex.: referência médico-dentista) |

---

## 5. Documentos Relacionados

- [PLANO_IMPLEMENTACAO.md](./PLANO_IMPLEMENTACAO.md) — Fases, módulos e recomendações práticas
- [AGENDAMENTO_ODONTOLOGICO.md](./AGENDAMENTO_ODONTOLOGICO.md) — Especificação de domínio do agendamento (horários rígidos, ordem de chegada, pré-recepção)
- [CLAUDE.md](../../CLAUDE.md) — Visão geral do repositório IntelliCare

---

## 6. Próximos Passos

1. Validar proposta com stakeholders (dentistas, gestores de clínicas)
2. Estudar em profundidade o FHIR Dental Data Exchange IG
3. Definir escopo da Fase 1 (MVP odontológico)
4. Criar especificação do módulo `intellicare-odontologia`
