export function getPortalUrl() {
  if (typeof window === 'undefined') {
    return '/'
  }

  const configuredPortalUrl = import.meta.env.VITE_PORTAL_URL?.trim()
  if (configuredPortalUrl) {
    return configuredPortalUrl.endsWith('/') ? configuredPortalUrl : `${configuredPortalUrl}/`
  }

  const { hostname, origin } = window.location

  if (hostname === 'localhost' || hostname.startsWith('127.')) {
    return `http://${hostname}:5176/`
  }

  if (hostname === 'intellicare.ia.br' || hostname.endsWith('.intellicare.ia.br')) {
    return 'https://intellicare.ia.br/'
  }

  return `${origin}/`
}
