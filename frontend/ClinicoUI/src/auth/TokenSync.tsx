import { useEffect } from 'react'
import { useAuth } from 'react-oidc-context'

export function TokenSync() {
  const auth = useAuth()
  useEffect(() => {
    if (auth.user?.access_token) {
      sessionStorage.setItem('oidc.access_token', auth.user.access_token)
    } else {
      sessionStorage.removeItem('oidc.access_token')
    }
  }, [auth.user?.access_token])
  return null
}
