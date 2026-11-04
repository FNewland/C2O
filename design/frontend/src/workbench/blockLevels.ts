/**
 * Product-tree levels and what the Blocks panel creates at the current drill-down position
 * (pure; runs under plain Node in tests).
 *
 * The product tree follows ECSS-M-ST-10C (product tree) and the NASA SE Handbook (product
 * breakdown); the server holds the same rules (services/product_tree.py):
 *   level 0  mission
 *   level 1  segment (space, ground, launch, user, operations)
 *   level 2  system / element: a spacecraft, a constellation member, a ground station
 *   level 3  subsystem (EPS, AOCS, TT&C, OBDH, thermal, structure, propulsion, payload)
 *   level 4  equipment / unit (element_type 'component')
 * A space segment is not a spacecraft: its children are spacecraft, never subsystems.
 *
 * The level is read from the TYPE of the element in focus, not from the breadcrumb depth.
 * The mission wizard adds a mission root above the segments, so the depth is one more than
 * the product-tree level; keyed on depth, presets, the "+ Add Element" types, Quick Start and
 * the level tabs were all one level off (WP0 #6, Nov 2026 product-tree fix):
 *   mission root (or top level with a mission root) → segments
 *   segment → systems   ·   system → subsystems   ·   subsystem → components
 */
export type ChildType = 'mission' | 'segment' | 'system' | 'subsystem' | 'component' | null

export interface ElLike {
  id: string; element_type?: string | null; parent_id?: string | null; deleted_at?: string | null
  segment?: string | null; name?: string | null
}

const CHILD_OF: Record<string, ChildType> = {
  mission: 'segment', segment: 'system', system: 'subsystem', subsystem: 'component', component: null,
}

/** ECSS / NASA product-tree level of an element type (null: not a tree type). */
export const TREE_LEVEL: Record<string, 0 | 1 | 2 | 3 | 4> = {
  mission: 0, segment: 1, system: 2, subsystem: 3, component: 4, equipment: 4,
}

export function treeLevel(type: string | null | undefined): 0 | 1 | 2 | 3 | 4 | null {
  return type && type in TREE_LEVEL ? TREE_LEVEL[type] : null
}

export interface Crumb { id: string; name: string; type?: string | null }

/**
 * Workbench level (the level tabs, readiness, decisions, link proposals) of a drill-down:
 * the product-tree level of the element in focus — 0 at the top or inside the mission,
 * 1 inside a segment, 2 inside a system (spacecraft), 3 inside a subsystem (its equipment).
 * Crumbs saved before the fix carry no type: their depth stands in (old behaviour).
 */
export function workbenchLevel(crumbs: Crumb[]): 0 | 1 | 2 | 3 {
  if (!crumbs.length) return 0
  const last = crumbs[crumbs.length - 1]
  const lv = treeLevel(last.type)
  if (lv != null) return Math.min(lv, 3) as 0 | 1 | 2 | 3
  return Math.min(crumbs.length, 3) as 0 | 1 | 2 | 3
}

/** Index of the crumb to go back to for level ``level`` (-1: the top). */
export function crumbIndexForLevel(crumbs: Crumb[], level: number): number {
  let idx = -1
  for (let i = 0; i < crumbs.length; i++) {
    const lv = treeLevel(crumbs[i].type) ?? (i + 1)
    if (Math.min(lv, 3) <= level) idx = i
    else break
  }
  return idx
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

/** Index into the Blocks panel's per-level tables of the blocks being created:
 *  segment 0, system 1, subsystem 2, component 3 (= product-tree level − 1). */
export function structuralLevel(childType: ChildType): 0 | 1 | 2 | 3 | 4 {
  switch (childType) {
    case 'segment': return 0
    case 'system': return 1
    case 'subsystem': return 2
    case 'component': return 3
    default: return 4
  }
}

function effectiveSegment(el: ElLike | undefined, elements: ElLike[]): string {
  let cur = el
  let n = 0
  while (cur && n < 50) {
    if (cur.segment && cur.segment !== 'space') return cur.segment
    if (cur.element_type === 'segment' && /^ground/i.test(cur.name ?? '')) return 'ground'
    cur = cur.parent_id ? elements.find(e => e.id === cur!.parent_id) : undefined
    n++
  }
  return 'space'
}

/** A segment of the space segment kind (its systems are spacecraft). */
export function isSpaceSegment(elements: ElLike[], focusId: string | null): boolean {
  const focus = focusId ? elements.find(e => e.id === focusId) : undefined
  return !!focus && focus.element_type === 'segment' && effectiveSegment(focus, elements) === 'space'
}

/** The segment kind (space, ground, launch, user, operations) of the element in focus. */
export function segmentOf(elements: ElLike[], focusId: string | null): string | null {
  const focus = focusId ? elements.find(e => e.id === focusId) : undefined
  return focus ? effectiveSegment(focus, elements) : null
}

/**
 * Quick Start ("Populate Subsystems + Equipment"): on a segment with no system yet (it
 * creates the spacecraft and its subsystems), or on a system with no subsystem yet (it
 * gives that spacecraft its subsystems).
 */
export function showQuickStart(elements: ElLike[], focusId: string | null): boolean {
  if (!focusId) return false
  const focus = elements.find(e => e.id === focusId)
  const kids = elements.filter(e => e.parent_id === focusId && !e.deleted_at)
  if (focus?.element_type === 'segment') return !kids.some(e => e.element_type === 'system')
  if (focus?.element_type === 'system') return !kids.some(e => e.element_type === 'subsystem')
  return false
}

/** "+ Add Spacecraft" belongs on a space segment (one or several spacecraft, level 2). */
export function canAddSpacecraft(elements: ElLike[], focusId: string | null): boolean {
  return isSpaceSegment(elements, focusId)
}
