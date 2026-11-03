/**
 * What the Blocks panel creates at the current drill-down position (pure; runs under
 * plain Node in tests).
 *
 * The level is read from the TYPE of the element in focus, not from the breadcrumb
 * depth. The mission wizard adds a mission root above the segments, so the depth is one
 * more than the product-tree level; keyed on depth, presets, the "+ Add Element" types
 * and Quick Start were all one level off (WP0, walkthrough top problem 4):
 *   mission root (or top level with a mission root) → segments
 *   segment → systems   ·   system → subsystems   ·   subsystem → components
 */
export type ChildType = 'mission' | 'segment' | 'system' | 'subsystem' | 'component' | null

export interface ElLike { id: string; element_type?: string | null; parent_id?: string | null; deleted_at?: string | null }

const CHILD_OF: Record<string, ChildType> = {
  mission: 'segment', segment: 'system', system: 'subsystem', subsystem: 'component', component: null,
}

/** The single mission root of a study, if it has one (wizard-created studies do). */
export function missionRoot(elements: ElLike[]): ElLike | null {
  const roots = elements.filter(e => !e.parent_id && !e.deleted_at && e.element_type === 'mission')
  return roots.length === 1 ? roots[0] : null
}

/**
 * Where a new block goes and of what type. At the top level of a study with a mission
 * root, new blocks are segments UNDER the mission root (never a second mission root).
 */
export function placement(elements: ElLike[], focusId: string | null): { parentId: string | null; childType: ChildType } {
  if (!focusId) {
    const root = missionRoot(elements)
    return root ? { parentId: root.id, childType: 'segment' } : { parentId: null, childType: 'segment' }
  }
  const focus = elements.find(e => e.id === focusId)
  const type = focus?.element_type || 'system'
  return { parentId: focusId, childType: type in CHILD_OF ? CHILD_OF[type] : 'subsystem' }
}

/** Product-tree level of the blocks being created: segment 0, system 1, subsystem 2, component 3. */
export function structuralLevel(childType: ChildType): 0 | 1 | 2 | 3 | 4 {
  switch (childType) {
    case 'segment': return 0
    case 'system': return 1
    case 'subsystem': return 2
    case 'component': return 3
    default: return 4
  }
}

/** Quick Start ("Populate Subsystems + Equipment") belongs on a segment with no system yet. */
export function showQuickStart(elements: ElLike[], focusId: string | null): boolean {
  if (!focusId) return false
  const focus = elements.find(e => e.id === focusId)
  if (focus?.element_type !== 'segment') return false
  return !elements.some(e => e.parent_id === focusId && !e.deleted_at && e.element_type === 'system')
}
