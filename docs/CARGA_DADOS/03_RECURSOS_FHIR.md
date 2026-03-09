# Recursos FHIR Gerados

Demonstra todo o potencial do IntelliCare.

| Recurso | Módulo | Descrição |
|---------|--------|-----------|
| **Organization** | GRAHAME, Zilda | 7 organizações (secretarias, hospitais, UBS) |
| **Location** | GRAHAME | 7 unidades físicas |
| **Patient** | Todos | Pacientes (REG Brasília/Montes Claros) |
| **Practitioner** | Comunicação, Gestor | 10 profissionais (médicos, enfermeiros) |
| **PractitionerRole** | Encounters | Vínculo profissional–organização–unidade |
| **Condition** | Oswaldo, IPS | DRC, DM2, HAS (associação aleatória) |
| **Observation** | AlertHub, IPS | Creatinina, eGFR, PA (incl. valores críticos) |
| **Encounter** | Donabedian | Atendimentos (ambulatório, emergência, internação) |
| **MedicationRequest** | IPS, Geralda | Prescrições |
| **AllergyIntolerance** | IPS, CDS Hooks | Alergias (segurança clínica) |
| **CarePlan** | Geralda | Planos de cuidado DRC/DM2/HAS |
| **Goal** | Geralda | Metas dos planos |
| **Procedure** | IPS | Diálise, consultas |
| **DiagnosticReport** | Bulk Export | Relatórios agregando Observations |
| **RelatedPerson** | Comunicação | Contatos de emergência |

## Observações críticas (AlertHub)

- ~15% dos pacientes com eGFR baixo (12–35 mL/min)
- ~10% com pressão arterial elevada
- Permitem testar disparo de alertas
