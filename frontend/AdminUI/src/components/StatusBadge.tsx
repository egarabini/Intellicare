import { Badge } from '@mantine/core'

const colorMap: Record<string, string> = {
  active: 'green',
  suspended: 'orange',
  terminated: 'gray',
  trial: 'yellow',
}

export function StatusBadge({ status }: { status: string }) {
  return (
    <Badge color={colorMap[status] ?? 'gray'} variant="light">
      {status}
    </Badge>
  )
}
