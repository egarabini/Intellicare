/**
 * Referência síncrona ao access token.
 * Usada pelo axios interceptor para evitar race condition com useEffect.
 * setToken() é chamado diretamente no corpo do componente App (não em useEffect),
 * garantindo que o token esteja disponível antes de qualquer query disparar.
 */
let _token: string | null = null

export function getToken(): string | null {
  return _token
}

export function setToken(token: string | null): void {
  _token = token
}

