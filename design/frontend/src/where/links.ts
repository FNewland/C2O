/**
 * External reading links (configs/worksheets/where_map.yaml `links`), rendered only when
 * they are safe: https, no credentials, and on this allow-list of open-access hosts
 * (docs/plan_2026-11/EXTERNAL_LINKS_DESIGN.md). tests/test_logbook/test_where_map.py checks
 * that every link in the map passes. Opened in a new window with rel="noopener noreferrer".
 */

/** host, or host + path prefix ("storage.googleapis.com/rideshare-static/") */
export const ALLOWED_LINK_HOSTS: readonly string[] = [
  'ntrs.nasa.gov',
  'www.nasa.gov',
  'standards.nasa.gov',
  'www.esa.int',
  'cubesat.org',
  'ecss.nl',
  'celestrak.org',
  'asc-csa.gc.ca',
  'www.asc-csa.gc.ca',
  'laws-lois.justice.gc.ca',
  'international.gc.ca',
  'www.international.gc.ca',
  'ised-isde.canada.ca',
  'www.itu.int',
  'www.fcc.gov',
  'www.unoosa.org',
  'ccsds.org',
  'storage.googleapis.com/rideshare-static/',
]

export interface ExternalLink { id: string; title: string; url: string; lang?: string }

/** The URL if it may be rendered as a link, else null. */
export function safeExternalUrl(raw: string): string | null {
  let u: URL
  try { u = new URL(raw) } catch { return null }
  if (u.protocol !== 'https:' || u.username || u.password || u.port) return null
  const host = u.hostname.toLowerCase()
  const ok = ALLOWED_LINK_HOSTS.some(entry => {
    const slash = entry.indexOf('/')
    if (slash < 0) return host === entry
    return host === entry.slice(0, slash) && u.pathname.startsWith(entry.slice(slash))
  })
  return ok ? u.toString() : null
}
