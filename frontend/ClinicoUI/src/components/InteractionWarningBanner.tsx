import { Alert, Button, Group, Stack, Text } from '@mantine/core'
import { IconAlertTriangle, IconInfoCircle, IconShieldCheck } from '@tabler/icons-react'

export interface InteractionWarning {
  drug_a: string
  drug_b: string
  severity: "GRAVE" | "MODERADO" | "LEVE"
  effect: string
  recommendation: string
  source: "static" | "llm"
}

interface Props {
  warnings: InteractionWarning[]
  onDismiss: () => void
}

export function InteractionWarningBanner({ warnings, onDismiss }: Props) {
  if (!warnings || warnings.length === 0) return null

  const getSeverityProps = (severity: "GRAVE" | "MODERADO" | "LEVE") => {
    switch (severity) {
      case "GRAVE":
        return { color: "red", icon: <IconAlertTriangle size={18} />, label: "Grave" }
      case "MODERADO":
        return { color: "orange", icon: <IconAlertTriangle size={18} />, label: "Moderado" }
      case "LEVE":
        return { color: "blue", icon: <IconInfoCircle size={18} />, label: "Leve" }
    }
  }

  return (
    <Stack gap="xs" mb="sm">
      {warnings.map((w, idx) => {
        const style = getSeverityProps(w.severity)
        return (
          <Alert
            key={idx}
            color={style.color}
            icon={style.icon}
            title={`Interação ${style.label}: ${w.drug_a} + ${w.drug_b}`}
            variant="light"
          >
            <Stack gap="xs">
              <Text size="sm"><strong>Efeito:</strong> {w.effect}</Text>
              <Text size="sm"><strong>Recomendação:</strong> {w.recommendation}</Text>
              {w.source === 'llm' && (
                <Text size="xs" c="dimmed" mt={4} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <IconShieldCheck size={14} />
                  Verificação por IA IntelliCare — Confirmar com fontes clínicas.
                </Text>
              )}
            </Stack>
          </Alert>
        )
      })}
      <Group justify="flex-end" mt="xs">
        <Button variant="outline" color="gray" size="xs" onClick={onDismiss}>
          Entendido — Manter prescrição
        </Button>
      </Group>
    </Stack>
  )
}
