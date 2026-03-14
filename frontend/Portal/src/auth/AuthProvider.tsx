import React from 'react'
import { AuthProvider as OidcAuthProvider, AuthProviderProps } from 'react-oidc-context'

const oidcConfig: AuthProviderProps = {
  authority:    import.meta.env.VITE_KEYCLOAK_URL + '/realms/intellicare',
  client_id:    'portal',
  redirect_uri: window.location.origin + '/',
  post_logout_redirect_uri: window.location.origin + '/',
  scope:        'openid profile email',
  userStore:    undefined,   // tokens apenas em memória
  onSigninCallback: () => {
    // limpa os parâmetros OIDC da URL após callback
    window.history.replaceState({}, document.title, '/')
  },
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  return <OidcAuthProvider {...oidcConfig}>{children}</OidcAuthProvider>
}
