import { Button, Group, Modal, NativeSelect, Stack, Switch, TextInput } from '@mantine/core';
import { useForm } from '@mantine/form';
import type { TriggerJourneyPayload } from '../hooks/useGestor';

interface Props {
  opened: boolean;
  onClose: () => void;
  onSubmit: (payload: TriggerJourneyPayload) => Promise<void>;
  loading: boolean;
}

const TASK_TYPES = [
  { value: 'ADESAO', label: 'Adesão ao Tratamento' },
  { value: 'MONITORAMENTO', label: 'Monitoramento' },
  { value: 'CHECK_IN', label: 'Check-in de Saúde' },
  { value: 'TELECONSULTA', label: 'Teleconsulta' },
];

export function TriggerJourneyModal({ opened, onClose, onSubmit, loading }: Props) {
  const form = useForm<{
    patient_ref: string;
    task_type: string;
    template_code: string;
    contact_phone_e164: string;
    include_video: boolean;
    clinico_ref: string;
  }>({
    initialValues: {
      patient_ref: '',
      task_type: 'CHECK_IN',
      template_code: '',
      contact_phone_e164: '',
      include_video: false,
      clinico_ref: '',
    },
    validate: {
      patient_ref: (v) => (!v.trim() ? 'Referência do paciente obrigatória' : null),
      task_type: (v) => (!v ? 'Tipo de jornada obrigatório' : null),
      clinico_ref: (v, values) =>
        values.include_video && !v.trim()
          ? 'Referência do clínico obrigatória para videoconsulta'
          : null,
    },
  });

  const handleSubmit = form.onSubmit(async (values) => {
    await onSubmit({
      patient_ref: values.patient_ref.trim(),
      task_type: values.task_type,
      template_code: values.template_code.trim() || undefined,
      contact_phone_e164: values.contact_phone_e164.trim() || undefined,
      flow_id: values.include_video ? 'careplanner_jornada_video' : 'careplanner_jornada_basica',
      clinico_ref: values.include_video ? values.clinico_ref.trim() : undefined,
    });
    form.reset();
  });

  return (
    <Modal opened={opened} onClose={onClose} title="Nova Jornada CarePlanner" size="md">
      <form onSubmit={handleSubmit}>
        <Stack>
          <TextInput
            label="Referência do Paciente"
            placeholder="keycloak-uuid-do-paciente"
            required
            data-testid="input-patient-ref"
            {...form.getInputProps('patient_ref')}
          />
          <NativeSelect
            label="Tipo de Jornada"
            data={TASK_TYPES}
            required
            data-testid="select-task-type"
            {...form.getInputProps('task_type')}
          />
          <TextInput
            label="Código do Template"
            placeholder="ex. boas_vindas (opcional)"
            {...form.getInputProps('template_code')}
          />
          <TextInput
            label="Telefone (E.164)"
            placeholder="+5511999999999 (opcional)"
            {...form.getInputProps('contact_phone_e164')}
          />
          <Switch
            label="Incluir videoconsulta após resposta"
            data-testid="switch-video"
            {...form.getInputProps('include_video', { type: 'checkbox' })}
          />
          {form.values.include_video && (
            <TextInput
              label="Referência do Clínico"
              placeholder="keycloak-uuid-do-clinico"
              required
              {...form.getInputProps('clinico_ref')}
            />
          )}
          <Group justify="flex-end" mt="md">
            <Button variant="subtle" onClick={onClose} disabled={loading}>
              Cancelar
            </Button>
            <Button type="submit" loading={loading} data-testid="btn-submit-trigger">
              Iniciar Jornada
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}
