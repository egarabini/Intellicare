/**
 * Tests for FHIR React components — 25 scenarios.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import {
  StatusBadge,
  PatientSummary,
  PatientTimeline,
  ResourceTable,
  DiagnosticReportDisplay,
  ProblemList,
  AllergyList,
  VitalSignsGrid,
  EncounterCard,
  ResourceDiff,
  MedicationCard,
  codingDisplay,
  fhirDate,
  fhirDateTime,
  patientName,
  ageFromBirthDate,
  type FHIRPatient,
  type FHIRObservation,
  type FHIRCondition,
  type FHIREncounter,
  type FHIRMedicationRequest,
  type FHIRDiagnosticReport,
  type FHIRAllergyIntolerance,
} from '@components/fhir';

// ── Fixtures ──────────────────────────────────────────────────────────────────

const PATIENT: FHIRPatient = {
  resourceType: 'Patient',
  id: 'p-001',
  name: [{ family: 'Silva', given: ['Maria'] }],
  gender: 'female',
  birthDate: '1985-03-15',
  active: true,
  telecom: [{ system: 'phone', value: '(11) 99999-0000' }],
  identifier: [{ system: 'http://cpf.gov.br', value: '123.456.789-00' }],
};

const OBS_ACTIVE: FHIRObservation = {
  resourceType: 'Observation',
  id: 'obs-1',
  status: 'final',
  code: { coding: [{ system: 'http://loinc.org', code: '8867-4', display: 'FC' }] },
  effectiveDateTime: '2024-06-01T10:00:00Z',
  valueQuantity: { value: 72, unit: 'bpm' },
};

const CONDITION_ACTIVE: FHIRCondition = {
  resourceType: 'Condition',
  id: 'cond-1',
  code: { coding: [{ system: 'http://hl7.org/fhir/sid/icd-10', code: 'I10', display: 'Hipertensão Arterial' }] },
  clinicalStatus: { coding: [{ code: 'active' }] },
  onsetDateTime: '2020-01-10',
};

const ENCOUNTER: FHIREncounter = {
  resourceType: 'Encounter',
  id: 'enc-1',
  status: 'finished',
  type: [{ coding: [{ code: 'AMB', display: 'Consulta Ambulatorial' }] }],
  period: { start: '2024-05-10T09:00:00Z', end: '2024-05-10T09:30:00Z' },
  reasonCode: [{ coding: [{ display: 'Controle de hipertensão' }] }],
};

const MED: FHIRMedicationRequest = {
  resourceType: 'MedicationRequest',
  id: 'med-1',
  status: 'active',
  intent: 'order',
  medicationCodeableConcept: { coding: [{ display: 'Losartana 50mg' }] },
  dosageInstruction: [{ text: 'Tomar 1 comprimido por dia', doseAndRate: [{ doseQuantity: { value: 50, unit: 'mg' } }] }],
  authoredOn: '2024-06-01',
};

const REPORT: FHIRDiagnosticReport = {
  resourceType: 'DiagnosticReport',
  id: 'dr-1',
  status: 'final',
  code: { coding: [{ display: 'Hemograma Completo' }] },
  effectiveDateTime: '2024-06-01T10:00:00Z',
  conclusion: 'Sem alterações significativas.',
};

const ALLERGY: FHIRAllergyIntolerance = {
  resourceType: 'AllergyIntolerance',
  id: 'allergy-1',
  code: { coding: [{ display: 'Penicilina' }] },
  criticality: 'high',
  category: ['medication'],
  reaction: [{
    manifestation: [{ coding: [{ display: 'Anafilaxia' }] }],
    severity: 'severe',
  }],
};

// ── Utility functions ─────────────────────────────────────────────────────────

describe('FHIR utility functions', () => {
  it('codingDisplay returns text when present', () => {
    expect(codingDisplay({ text: 'Hipertensão' })).toBe('Hipertensão');
  });

  it('codingDisplay returns coding display when no text', () => {
    expect(codingDisplay({ coding: [{ display: 'FC' }] })).toBe('FC');
  });

  it('codingDisplay returns dash for empty', () => {
    expect(codingDisplay(undefined)).toBe('—');
  });

  it('patientName builds full name', () => {
    expect(patientName([{ family: 'Silva', given: ['Maria'] }])).toBe('Maria Silva');
  });

  it('patientName returns fallback when empty', () => {
    expect(patientName([])).toBe('Paciente sem nome');
  });

  it('ageFromBirthDate computes correct age', () => {
    const year = new Date().getFullYear() - 30;
    expect(ageFromBirthDate(`${year}-01-01`)).toBeGreaterThanOrEqual(29);
    expect(ageFromBirthDate(`${year}-01-01`)).toBeLessThanOrEqual(31);
  });

  it('ageFromBirthDate returns null for undefined', () => {
    expect(ageFromBirthDate(undefined)).toBeNull();
  });
});

// ── StatusBadge ───────────────────────────────────────────────────────────────

describe('StatusBadge', () => {
  it('renders known status', () => {
    render(<StatusBadge status="final" />);
    expect(screen.getByText('Final')).toBeDefined();
  });

  it('renders custom label', () => {
    render(<StatusBadge status="active" label="Ativo customizado" />);
    expect(screen.getByText('Ativo customizado')).toBeDefined();
  });

  it('renders unknown status as raw string', () => {
    render(<StatusBadge status="my-custom-status" />);
    expect(screen.getByText('my-custom-status')).toBeDefined();
  });
});

// ── PatientSummary ────────────────────────────────────────────────────────────

describe('PatientSummary', () => {
  it('renders patient name', () => {
    render(<PatientSummary patient={PATIENT} />);
    expect(screen.getByText('Maria Silva')).toBeDefined();
  });

  it('renders gender', () => {
    render(<PatientSummary patient={PATIENT} />);
    expect(screen.getByText('Feminino')).toBeDefined();
  });

  it('renders CPF identifier', () => {
    render(<PatientSummary patient={PATIENT} />);
    expect(screen.getByText(/123\.456\.789-00/)).toBeDefined();
  });

  it('renders active status badge', () => {
    render(<PatientSummary patient={PATIENT} />);
    expect(screen.getByText('Ativo')).toBeDefined();
  });
});

// ── PatientTimeline ───────────────────────────────────────────────────────────

describe('PatientTimeline', () => {
  it('renders observation in timeline', () => {
    render(<PatientTimeline resources={[OBS_ACTIVE]} />);
    expect(screen.getByText('FC')).toBeDefined();
  });

  it('shows empty state when no resources', () => {
    render(<PatientTimeline resources={[]} />);
    expect(screen.getByText(/Nenhum evento/i)).toBeDefined();
  });

  it('calls onSelect when row clicked', () => {
    const onSelect = vi.fn();
    render(<PatientTimeline resources={[OBS_ACTIVE]} onSelect={onSelect} />);
    fireEvent.click(screen.getByText('FC'));
    expect(onSelect).toHaveBeenCalledWith(OBS_ACTIVE);
  });
});

// ── ProblemList ───────────────────────────────────────────────────────────────

describe('ProblemList', () => {
  it('renders condition name', () => {
    render(<ProblemList conditions={[CONDITION_ACTIVE]} />);
    expect(screen.getByText('Hipertensão Arterial')).toBeDefined();
  });

  it('shows empty state', () => {
    render(<ProblemList conditions={[]} />);
    expect(screen.getByText(/Nenhum problema/i)).toBeDefined();
  });
});

// ── AllergyList ───────────────────────────────────────────────────────────────

describe('AllergyList', () => {
  it('renders allergy name', () => {
    render(<AllergyList allergies={[ALLERGY]} />);
    expect(screen.getByText('Penicilina')).toBeDefined();
  });

  it('shows criticality badge', () => {
    render(<AllergyList allergies={[ALLERGY]} />);
    expect(screen.getByText('Alto risco')).toBeDefined();
  });
});

// ── EncounterCard ─────────────────────────────────────────────────────────────

describe('EncounterCard', () => {
  it('renders encounter type', () => {
    render(<EncounterCard encounter={ENCOUNTER} />);
    expect(screen.getByText('Consulta Ambulatorial')).toBeDefined();
  });

  it('renders finished status', () => {
    render(<EncounterCard encounter={ENCOUNTER} />);
    expect(screen.getByText('Finalizado')).toBeDefined();
  });
});

// ── MedicationCard ────────────────────────────────────────────────────────────

describe('MedicationCard', () => {
  it('renders medication name', () => {
    render(<MedicationCard medication={MED} />);
    expect(screen.getByText('Losartana 50mg')).toBeDefined();
  });

  it('renders dosage instructions', () => {
    render(<MedicationCard medication={MED} />);
    expect(screen.getByText('Tomar 1 comprimido por dia')).toBeDefined();
  });
});

// ── DiagnosticReportDisplay ───────────────────────────────────────────────────

describe('DiagnosticReportDisplay', () => {
  it('renders report title', () => {
    render(<DiagnosticReportDisplay report={REPORT} />);
    expect(screen.getByText('Hemograma Completo')).toBeDefined();
  });

  it('renders conclusion', () => {
    render(<DiagnosticReportDisplay report={REPORT} />);
    expect(screen.getByText('Sem alterações significativas.')).toBeDefined();
  });
});

// ── ResourceDiff ──────────────────────────────────────────────────────────────

describe('ResourceDiff', () => {
  it('detects changed field', () => {
    const v1 = { ...PATIENT, active: true } as any;
    const v2 = { ...PATIENT, active: false } as any;
    render(<ResourceDiff oldResource={v1} newResource={v2} />);
    expect(screen.getByText('active')).toBeDefined();
  });

  it('shows no changes when identical', () => {
    render(<ResourceDiff oldResource={PATIENT} newResource={PATIENT} />);
    expect(screen.getByText(/Nenhuma diferença/i)).toBeDefined();
  });
});
