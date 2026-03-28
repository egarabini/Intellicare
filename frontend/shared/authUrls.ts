export function getPortalUrl() {
  if (typeof window === 'undefined') {
    return '/'
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
