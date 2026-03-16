import { useEffect, useRef, useState, useCallback } from 'react'
import { useAuth } from 'react-oidc-context'
import api from '../api/client'

export interface AppNotification {
  id: string
  title: string
  message: string
  is_read: boolean
  created_at: string
  category?: string
}

export function useNotifications() {
  const auth = useAuth()
  const [notifications, setNotifications] = useState<AppNotification[]>([])
  const [available, setAvailable] = useState(true)
  const retryRef = useRef(0)
  const esRef = useRef<EventSource | null>(null)

  const unreadCount = notifications.filter(n => !n.is_read).length

  const fetchNotifications = useCallback(async () => {
    try {
      const { data } = await api.get<AppNotification[]>('/notifications/?limit=20')
      setNotifications(data)
    } catch (err: any) {
      if (err?.response?.status === 404) setAvailable(false)
    }
  }, [])

  const markRead = useCallback(async (id: string) => {
    try {
      await api.patch(`/notifications/${id}/read`)
      setNotifications(prev =>
        prev.map(n => (n.id === id ? { ...n, is_read: true } : n))
      )
    } catch {
      // silencioso
    }
  }, [])

  useEffect(() => {
    if (!available) return
    const token = auth.user?.access_token
    if (!token) return

    function connect() {
      const es = new EventSource(`/notifications/stream?token=${token}`)
      esRef.current = es

      es.onmessage = (event) => {
        try {
          const incoming: AppNotification = JSON.parse(event.data)
          setNotifications(prev => [incoming, ...prev].slice(0, 20))
          retryRef.current = 0
        } catch {
          // ignore parse errors
        }
      }

      es.onerror = () => {
        es.close()
        if (retryRef.current < 3) {
          retryRef.current++
          setTimeout(connect, 5_000)
        }
      }
    }

    void fetchNotifications()
    connect()

    return () => {
      esRef.current?.close()
    }
  }, [auth.user?.access_token, available, fetchNotifications])

  return { notifications, unreadCount, markRead, available }
}
