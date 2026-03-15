import { Badge } from '@mantine/core'

const colorMap: Record<string, string> = {
  active: 'green',
  suspended: 'orange',
  terminated: 'gray',
  trial: 'yellow',
  inactive: 'gray',
  maintenance: 'yellow',
  dev: 'violet',
  overdue: 'red',
  pending: 'yellow',
  cancelled: 'gray',
  paid: 'green',
  infrastructure: 'blue',
  license: 'grape',
  personnel: 'teal',
  other: 'gray',
}

export function StatusBadge({ status }: { status: string }) {
  return (
    <Badge color={colorMap[status] ?? 'gray'} variant="light">
      {status}
    </Badge>
  )
}
