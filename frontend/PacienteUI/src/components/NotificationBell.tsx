import { useState } from 'react'
import {
  ActionIcon, Badge, Group, Indicator, Popover,
  ScrollArea, Stack, Text,
} from '@mantine/core'
import { IconBell } from '@tabler/icons-react'
import { useNotifications, AppNotification } from '../hooks/useNotifications'

function timeAgo(iso: string): string {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (diff < 60) return 'agora'
  if (diff < 3600) return `há ${Math.floor(diff / 60)} min`
  if (diff < 86400) return `há ${Math.floor(diff / 3600)} h`
  return `há ${Math.floor(diff / 86400)} d`
}

function NotificationItem({
  notification,
  onRead,
}: {
  notification: AppNotification
  onRead: (id: string) => void
}) {
  return (
    <Stack
      gap={2}
      p="xs"
      style={{
        cursor: notification.is_read ? 'default' : 'pointer',
        borderRadius: 6,
        background: notification.is_read ? 'transparent' : 'var(--mantine-color-blue-0)',
        borderBottom: '1px solid var(--mantine-color-gray-2)',
      }}
      onClick={() => !notification.is_read && onRead(notification.id)}
    >
      <Group justify="space-between" gap={4}>
        <Text size="sm" fw={notification.is_read ? 400 : 600} lineClamp={1}>
          {notification.title}
        </Text>
        <Text size="xs" c="dimmed">{timeAgo(notification.created_at)}</Text>
      </Group>
      <Text size="xs" c="dimmed" lineClamp={2}>
        {notification.message}
      </Text>
    </Stack>
  )
}

export function NotificationBell() {
  const { notifications, unreadCount, markRead, available } = useNotifications()
  const [opened, setOpened] = useState(false)

  if (!available) return null

  const label = unreadCount >= 10 ? '9+' : String(unreadCount)

  return (
    <Popover
      opened={opened}
      onClose={() => setOpened(false)}
      position="bottom-end"
      shadow="md"
      width={320}
    >
      <Popover.Target>
        <Indicator
          label={label}
          size={16}
          color="red"
          disabled={unreadCount === 0}
          processing={unreadCount > 0}
        >
          <ActionIcon
            variant="subtle"
            color="gray"
            onClick={() => setOpened(o => !o)}
            aria-label="Notificações"
          >
            <IconBell size={20} />
          </ActionIcon>
        </Indicator>
      </Popover.Target>

      <Popover.Dropdown p={0}>
        <Group px="sm" py="xs" justify="space-between"
          style={{ borderBottom: '1px solid var(--mantine-color-gray-2)' }}>
          <Text size="sm" fw={600}>Notificações</Text>
          {unreadCount > 0 && (
            <Badge size="xs" color="blue">{unreadCount} não lidas</Badge>
          )}
        </Group>
        <ScrollArea.Autosize mah={360}>
          {notifications.length === 0 ? (
            <Text size="sm" c="dimmed" ta="center" py="md">
              Nenhuma notificação
            </Text>
          ) : (
            notifications.map(n => (
              <NotificationItem key={n.id} notification={n} onRead={markRead} />
            ))
          )}
        </ScrollArea.Autosize>
      </Popover.Dropdown>
    </Popover>
  )
}
