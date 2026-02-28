/**
 * @module @components/fhir
 * Componentes React clínicos para visualização e interação com recursos FHIR R4.
 * Inspirados nos componentes Medplum — re-implementados para IntelliCare.
 *
 * Uso:
 *   import { PatientSummary, PatientTimeline, StatusBadge } from '@components/fhir';
 */

// Tipos FHIR compartilhados
export * from './types';

// Componentes
export { StatusBadge } from './StatusBadge';
export type { default as StatusBadgeType } from './StatusBadge';

export { PatientSummary } from './PatientSummary';
export { PatientTimeline } from './PatientTimeline';

export { ResourceTable } from './ResourceTable';
export type { ResourceColumn } from './ResourceTable';

export { SearchControl } from './SearchControl';
export type { SearchFilter as FHIRSearchFilter, SearchParams } from './SearchControl';

export { DiagnosticReportDisplay } from './DiagnosticReportDisplay';
export { CodeableConceptInput } from './CodeableConceptInput';
export type { CodeOption } from './CodeableConceptInput';

export { ObservationChart } from './ObservationChart';
export { MedicationCard } from './MedicationCard';
export { ProblemList } from './ProblemList';
export { AllergyList } from './AllergyList';
export { VitalSignsGrid } from './VitalSignsGrid';
export { EncounterCard } from './EncounterCard';
export { ResourceDiff } from './ResourceDiff';
export { QuestionnaireForm } from './QuestionnaireForm';
