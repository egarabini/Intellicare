/**
 * Tipos FHIR R4 compartilhados pelos componentes clínicos.
 * Subconjunto focado nos recursos mais usados no IntelliCare.
 */

// ── Primitivos ────────────────────────────────────────────────────────────────

export interface Coding {
  system?: string;
  code?: string;
  display?: string;
}

export interface CodeableConcept {
  coding?: Coding[];
  text?: string;
}

export interface Reference {
  reference?: string;
  display?: string;
}

export interface Period {
  start?: string;
  end?: string;
}

export interface Quantity {
  value?: number;
  unit?: string;
  system?: string;
  code?: string;
}

export interface HumanName {
  family?: string;
  given?: string[];
  text?: string;
  use?: string;
}

export interface Address {
  line?: string[];
  city?: string;
  state?: string;
  postalCode?: string;
  country?: string;
}

export interface ContactPoint {
  system?: string; // phone | fax | email | url
  value?: string;
  use?: string;
}

// ── Meta ──────────────────────────────────────────────────────────────────────

export interface Meta {
  versionId?: string;
  lastUpdated?: string;
  profile?: string[];
  tag?: Coding[];
}

// ── Patient ───────────────────────────────────────────────────────────────────

export interface FHIRPatient {
  resourceType: 'Patient';
  id?: string;
  meta?: Meta;
  name?: HumanName[];
  gender?: 'male' | 'female' | 'other' | 'unknown';
  birthDate?: string;
  active?: boolean;
  address?: Address[];
  telecom?: ContactPoint[];
  identifier?: Array<{ system?: string; value?: string }>;
  generalPractitioner?: Reference[];
  managingOrganization?: Reference;
}

// ── Observation ───────────────────────────────────────────────────────────────

export interface FHIRObservation {
  resourceType: 'Observation';
  id?: string;
  meta?: Meta;
  status: 'registered' | 'preliminary' | 'final' | 'amended' | 'corrected' | 'cancelled' | 'entered-in-error' | 'unknown';
  code: CodeableConcept;
  subject?: Reference;
  effectiveDateTime?: string;
  effectivePeriod?: Period;
  valueQuantity?: Quantity;
  valueCodeableConcept?: CodeableConcept;
  valueString?: string;
  valueBoolean?: boolean;
  component?: Array<{
    code: CodeableConcept;
    valueQuantity?: Quantity;
    valueString?: string;
  }>;
  interpretation?: CodeableConcept[];
  referenceRange?: Array<{
    low?: Quantity;
    high?: Quantity;
    text?: string;
  }>;
  note?: Array<{ text: string }>;
}

// ── Condition ─────────────────────────────────────────────────────────────────

export interface FHIRCondition {
  resourceType: 'Condition';
  id?: string;
  meta?: Meta;
  clinicalStatus?: CodeableConcept;
  verificationStatus?: CodeableConcept;
  category?: CodeableConcept[];
  severity?: CodeableConcept;
  code?: CodeableConcept;
  subject?: Reference;
  onsetDateTime?: string;
  onsetPeriod?: Period;
  recordedDate?: string;
  note?: Array<{ text: string }>;
}

// ── Encounter ─────────────────────────────────────────────────────────────────

export interface FHIREncounter {
  resourceType: 'Encounter';
  id?: string;
  meta?: Meta;
  status: 'planned' | 'arrived' | 'triaged' | 'in-progress' | 'onleave' | 'finished' | 'cancelled';
  class?: Coding;
  type?: CodeableConcept[];
  subject?: Reference;
  participant?: Array<{
    type?: CodeableConcept[];
    individual?: Reference;
  }>;
  period?: Period;
  reasonCode?: CodeableConcept[];
  serviceProvider?: Reference;
  diagnosis?: Array<{
    condition: Reference;
    use?: CodeableConcept;
  }>;
}

// ── MedicationRequest ─────────────────────────────────────────────────────────

export interface FHIRMedicationRequest {
  resourceType: 'MedicationRequest';
  id?: string;
  meta?: Meta;
  status: 'active' | 'on-hold' | 'cancelled' | 'completed' | 'entered-in-error' | 'stopped' | 'draft' | 'unknown';
  intent: 'proposal' | 'plan' | 'order' | 'original-order' | 'reflex-order' | 'filler-order' | 'instance-order' | 'option';
  medicationCodeableConcept?: CodeableConcept;
  medicationReference?: Reference;
  subject?: Reference;
  authoredOn?: string;
  requester?: Reference;
  dosageInstruction?: Array<{
    text?: string;
    timing?: { repeat?: { frequency?: number; period?: number; periodUnit?: string } };
    route?: CodeableConcept;
    doseAndRate?: Array<{ doseQuantity?: Quantity }>;
  }>;
  note?: Array<{ text: string }>;
}

// ── DiagnosticReport ──────────────────────────────────────────────────────────

export interface FHIRDiagnosticReport {
  resourceType: 'DiagnosticReport';
  id?: string;
  meta?: Meta;
  status: 'registered' | 'partial' | 'preliminary' | 'final' | 'amended' | 'corrected' | 'appended' | 'cancelled' | 'entered-in-error' | 'unknown';
  category?: CodeableConcept[];
  code: CodeableConcept;
  subject?: Reference;
  effectiveDateTime?: string;
  issued?: string;
  performer?: Reference[];
  result?: Reference[];
  conclusion?: string;
  conclusionCode?: CodeableConcept[];
  presentedForm?: Array<{ contentType?: string; url?: string; title?: string }>;
}

// ── AllergyIntolerance ────────────────────────────────────────────────────────

export interface FHIRAllergyIntolerance {
  resourceType: 'AllergyIntolerance';
  id?: string;
  meta?: Meta;
  clinicalStatus?: CodeableConcept;
  verificationStatus?: CodeableConcept;
  type?: 'allergy' | 'intolerance';
  category?: Array<'food' | 'medication' | 'environment' | 'biologic'>;
  criticality?: 'low' | 'high' | 'unable-to-assess';
  code?: CodeableConcept;
  patient?: Reference;
  onsetDateTime?: string;
  reaction?: Array<{
    substance?: CodeableConcept;
    manifestation?: CodeableConcept[];
    severity?: 'mild' | 'moderate' | 'severe';
  }>;
  note?: Array<{ text: string }>;
}

// ── Questionnaire ─────────────────────────────────────────────────────────────

export interface QuestionnaireItem {
  linkId: string;
  text?: string;
  type: 'group' | 'display' | 'boolean' | 'decimal' | 'integer' | 'date' | 'dateTime' | 'time' | 'string' | 'text' | 'url' | 'choice' | 'open-choice' | 'attachment' | 'reference' | 'quantity';
  required?: boolean;
  repeats?: boolean;
  item?: QuestionnaireItem[];
  answerOption?: Array<{
    valueCoding?: Coding;
    valueString?: string;
    valueInteger?: number;
  }>;
}

export interface FHIRQuestionnaire {
  resourceType: 'Questionnaire';
  id?: string;
  title?: string;
  status: 'draft' | 'active' | 'retired' | 'unknown';
  item?: QuestionnaireItem[];
}

export type QuestionnaireResponseItem = {
  linkId: string;
  answer?: Array<{
    valueBoolean?: boolean;
    valueDecimal?: number;
    valueInteger?: number;
    valueDate?: string;
    valueString?: string;
    valueCoding?: Coding;
  }>;
  item?: QuestionnaireResponseItem[];
};

// ── Generic resource ──────────────────────────────────────────────────────────

export type FHIRResource =
  | FHIRPatient
  | FHIRObservation
  | FHIRCondition
  | FHIREncounter
  | FHIRMedicationRequest
  | FHIRDiagnosticReport
  | FHIRAllergyIntolerance
  | FHIRQuestionnaire
  | ({ resourceType: string; id?: string; meta?: Meta; [key: string]: unknown });

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Extract a display string from a CodeableConcept. */
export function codingDisplay(cc?: CodeableConcept): string {
  if (!cc) return '—';
  if (cc.text) return cc.text;
  const first = cc.coding?.[0];
  return first?.display ?? first?.code ?? '—';
}

/** Format a FHIR date string to pt-BR locale. */
export function fhirDate(dateStr?: string): string {
  if (!dateStr) return '—';
  try {
    return new Date(dateStr).toLocaleDateString('pt-BR');
  } catch {
    return dateStr;
  }
}

/** Format a FHIR dateTime string to pt-BR locale with time. */
export function fhirDateTime(dateStr?: string): string {
  if (!dateStr) return '—';
  try {
    return new Date(dateStr).toLocaleString('pt-BR');
  } catch {
    return dateStr;
  }
}

/** Get the full name from a HumanName array. */
export function patientName(names?: HumanName[]): string {
  if (!names?.length) return 'Paciente sem nome';
  const name = names[0];
  if (name.text) return name.text;
  const given = name.given?.join(' ') ?? '';
  return `${given} ${name.family ?? ''}`.trim() || 'Paciente sem nome';
}

/** Compute age in years from a birth date string. */
export function ageFromBirthDate(birthDate?: string): number | null {
  if (!birthDate) return null;
  const birth = new Date(birthDate);
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const m = today.getMonth() - birth.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;
  return age;
}
