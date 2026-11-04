/**
 * Which study this browser tab is in, kept across reloads (WP0, Nov 2026: a refresh used
 * to drop the study and send everyone back to Home). Pure: storage is passed in, so this
 * runs under plain Node in tests.
 *
 *   ?study=<id> in the URL wins (a shareable link), then the stored id. The breadcrumb
 *   (drill-down) is stored with the study it belongs to and dropped for any other study.
 */
export interface KV { getItem(k: string): string | null; setItem(k: string, v: string): void; removeItem(k: string): void }
export interface Crumb { id: string; name: string; type?: string | null }

export const STUDY_KEY = 'scdf.study'
export const CRUMBS_KEY = 'scdf.breadcrumb'

function safe<T>(f: () => T, fallback: T): T {
  try { return f() } catch { return fallback }
}

export function loadStudyId(storage: KV | null, search: string): string | null {
  const fromUrl = safe(() => new URLSearchParams(search).get('study'), null)
  if (fromUrl && /^[A-Za-z0-9_-]{1,64}$/.test(fromUrl)) return fromUrl
  const stored = storage ? safe(() => storage.getItem(STUDY_KEY), null) : null
  return stored && /^[A-Za-z0-9_-]{1,64}$/.test(stored) ? stored : null
}

export function saveStudyId(storage: KV | null, id: string | null): void {
  if (!storage) return
  safe(() => {
    if (id) storage.setItem(STUDY_KEY, id)
    else { storage.removeItem(STUDY_KEY); storage.removeItem(CRUMBS_KEY) }
    return null
  }, null)
}

export function loadBreadcrumb(storage: KV | null, studyId: string | null): Crumb[] {
  if (!storage || !studyId) return []
  const raw = safe(() => storage.getItem(CRUMBS_KEY), null)
  if (!raw) return []
  const data = safe(() => JSON.parse(raw) as { study?: string; crumbs?: Crumb[] }, null)
  if (!data || data.study !== studyId || !Array.isArray(data.crumbs)) return []
  return data.crumbs.filter(c => c && typeof c.id === 'string' && typeof c.name === 'string').slice(0, 8)
}

export function saveBreadcrumb(storage: KV | null, studyId: string | null, crumbs: Crumb[]): void {
  if (!storage || !studyId) return
  safe(() => { storage.setItem(CRUMBS_KEY, JSON.stringify({ study: studyId, crumbs })); return null }, null)
}
