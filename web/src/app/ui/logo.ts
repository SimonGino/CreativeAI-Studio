const LOGO_VERSION = '20260223'

function normalizeBaseUrl(baseUrl: string): string {
  if (!baseUrl) return '/'
  return baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`
}

export function providerLogoSrc(providerId: string): string {
  const baseUrl = normalizeBaseUrl(import.meta.env.BASE_URL || '/')
  return `${baseUrl}logos/${encodeURIComponent(providerId)}.svg?v=${LOGO_VERSION}`
}

