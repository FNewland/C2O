/**
 * The drill-down path a "Where in SpaceCDF" link follows to reach a product-tree level
 * (pure; runs under plain Node in tests): mission root → space segment → first spacecraft →
 * the subsystem of the asked domain (else the first).
 */
export interface El { id: string; name: string; parent_id?: string | null; element_type?: string | null; segment?: string | null; subsystem_domain?: string | null; deleted_at?: string | null }

/** The drill-down path (root → … ) to a product-tree level in this study, or null. */
export function pathToLevel(elements: El[], level: 0 | 1 | 2 | 3, domain?: string): El[] | null {
  const live = elements.filter(e => !e.deleted_at)
  const kids = (id: string | null) => live.filter(e => (e.parent_id ?? null) === id)
  const root = live.find(e => !e.parent_id && e.element_type === 'mission')
  const top = root ? kids(root.id) : kids(null)
  const path: El[] = root ? [root] : []
  if (level === 0) return path
  const seg = top.find(e => e.element_type === 'segment' && e.segment === 'space')
    ?? top.find(e => e.element_type === 'segment')
  if (!seg) return null
  path.push(seg)
  if (level === 1) return path
  const sc = kids(seg.id).find(e => e.element_type === 'system')
  if (!sc) return null
  path.push(sc)
  if (level === 2) return path
  const subs = kids(sc.id).filter(e => e.element_type === 'subsystem')
  const sub = (domain && subs.find(e => e.subsystem_domain === domain)) || subs[0]
  if (!sub) return null
  path.push(sub)
  return path
}

