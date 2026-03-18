import { Button, Group, Modal, NativeSelect, Stack, Switch, TextInput, Select } from '@mantine/core';
import { useForm } from '@mantine/form';
import { useTemplates, type TriggerJourneyPayload } from '../hooks/useGestor';

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
  const { data: templates } = useTemplates(true);

  const form = useForm<{
    patient_ref: string;
    task_type: string;
    channel: string;
    template_code: string;
    contact_phone_e164: string;
    contact_email: string;
    include_video: boolean;
    clinico_ref: string;
  }>({
    initialValues: {
      patient_ref: '',
      task_type: 'CHECK_IN',
      channel: 'rocketchat',
      template_code: '',
      contact_phone_e164: '',
      contact_email: '',
      include_video: false,
      clinico_ref: '',
    },
    validate: {
      patient_ref: (v) => (!v.trim() ? 'Referência do paciente obrigatória' : null),
      task_type: (v) => (!v ? 'Tipo de jornada obrigatório' : null),
      contact_phone_e164: (v, values) => ((values.channel === 'whatsapp' || values.channel === 'sms') && !v.trim() ? 'Telefone obrigatório para WhatsApp/SMS' : null),
      contact_email: (v, values) => (values.channel === 'email' && !v.trim() ? 'E-mail obrigatório para o canal selecionado' : null),
      clinico_ref: (v, values) =>
        values.include_video && !v.trim()
          ? 'Referência do clínico obrigatória para videoconsulta'
          : null,
    },
  });

  const templateOptions = (templates ?? [])
    .filter((t) => t.channel === form.values.channel)
    .map((t) => ({
      value: t.template_code,
      label: `${t.template_code} — ${t.content.slice(0, 40)}${t.content.length > 40 ? '…' : ''}`,
    }));


  const handleSubmit = form.onSubmit(async (values) => {
    let flow = 'careplanner_jornada_basica';
    if (values.channel === 'whatsapp') {
      flow = 'careplanner_jornada_whatsapp';
    } else if (values.channel === 'email') {
      flow = 'careplanner_jornada_email';
    } else if (values.channel === 'sms') {
      flow = 'careplanner_jornada_sms';
    } else if (values.include_video) {
      flow = 'careplanner_jornada_video';
    }

    await onSubmit({
      patient_ref: values.patient_ref.trim(),
      task_type: values.task_type,
      channel: values.channel,
      template_code: values.template_code.trim() || undefined,
      contact_phone_e164: values.contact_phone_e164.trim() || undefined,
      contact_email: values.contact_email.trim() || undefined,
      flow_id: flow,
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
          <NativeSelect
            label="Canal de Comunicação"
            data={[
              { value: 'rocketchat', label: 'Rocket.Chat Público' },
              { value: 'whatsapp', label: 'WhatsApp via Evolution' },
              { value: 'sms', label: 'SMS via Jasmin' },
              { value: 'email', label: 'E-mail via Listmonk' },
            ]}
            required
            data-testid="select-channel"
            {...form.getInputProps('channel')}
          />
          <Select
            label="Template de Mensagem"
            placeholder="Selecione um template (opcional)"
            data={templateOptions}
            clearable
            searchable
            data-testid="select-template-code"
            {...form.getInputProps('template_code')}
          />
          {(form.values.channel === 'whatsapp' || form.values.channel === 'sms') && (
            <TextInput
              label="Telefone (E.164)"
              placeholder="+5511999999999"
              required
              {...form.getInputProps('contact_phone_e164')}
            />
          )}
          {form.values.channel === 'email' && (
            <TextInput
              label="E-mail do paciente"
              placeholder="paciente@email.com"
              required
              {...form.getInputProps('contact_email')}
            />
          )}
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
