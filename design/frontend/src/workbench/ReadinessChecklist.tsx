/**
 * ReadinessChecklist — Shows what's needed to freeze the current level and move on.
 *
 * Checks:
 * - All elements at this level exist (at least 1)
 * - All in-scope elements have budget allocations
 * - All in-scope elements have at least 1 requirement
 * - All in-scope elements have defined interfaces (if >1 sibling)
 * - All checks green → can freeze
 */
import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useUIStore } from '../stores/uiStore'

const API = '/api'

interface Check {
  label: string
  passed: boolean
  detail: string
}

export function ReadinessChecklist() {
  const studyId = useUIStore(s => s.studyId)
  const focusElementId = useUIStore(s => s.focusElementId)
  const currentLevel = useUIStore(s => s.currentLevel)

  const { data: allElements = [] } = useQuery({
    queryKey: ['elements', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/elements`).then(r => r.json()),
    enabled: !!studyId,
  })

  const { data: allRequirements = [] } = useQuery({
    queryKey: ['requirements', studyId],
    queryFn: () => fetch(`${API}/requirements/tree?study_id=${studyId}`).then(r => r.json()),
    enabled: !!studyId,
  })

  const { data: allInterfaces = [] } = useQuery({
    queryKey: ['interfaces', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/interfaces`).then(r => r.json()),
    enabled: !!studyId,
  })

  const checks = useMemo<Check[]>(() => {
    const children = allElements.filter((el: any) =>
      focusElementId ? el.parent_id === focusElementId : !el.parent_id
    )
    const inScopeChildren = children.filter((el: any) => el.in_scope !== false)
    const childIds = new Set(children.map((c: any) => c.id))

    const result: Check[] = []

    // 1. Has elements
    const hasElements = children.length > 0
    result.push({
      label: 'Elements defined',
      passed: hasElements,
      detail: hasElements ? `${children.length} elements at this level` : 'Add at least one element',
    })

    // 2. In-scope elements have requirements
    if (inScopeChildren.length > 0) {
      const elementsWithReqs = new Set<string>()
      for (const req of allRequirements) {
        if (req.element_id && childIds.has(req.element_id)) {
          elementsWithReqs.add(req.element_id)
        }
      }
      // Also count requirements on the focus element itself
      const focusReqs = allRequirements.filter((r: any) => r.element_id === focusElementId)
      const hasParentReqs = focusReqs.length > 0
      const missingReqs = inScopeChildren.filter((el: any) => !elementsWithReqs.has(el.id))

      result.push({
        label: 'Requirements defined',
        passed: hasParentReqs || elementsWithReqs.size > 0,
        detail: missingReqs.length > 0
          ? `Missing requirements: ${missingReqs.map((e: any) => e.name).join(', ')}`
          : `${elementsWithReqs.size} elements have requirements`,
      })
    }

    // 3. Interfaces defined (if more than 1 in-scope sibling)
    if (inScopeChildren.length > 1) {
      const connectedElements = new Set<string>()
      for (const iface of allInterfaces) {
        if (childIds.has(iface.from_element_id)) connectedElements.add(iface.from_element_id)
        if (childIds.has(iface.to_element_id)) connectedElements.add(iface.to_element_id)
      }
      const unconnected = inScopeChildren.filter((el: any) => !connectedElements.has(el.id))
      result.push({
        label: 'Interfaces defined',
        passed: unconnected.length === 0,
        detail: unconnected.length > 0
          ? `No interfaces: ${unconnected.map((e: any) => e.name).join(', ')}`
          : `${connectedElements.size} elements connected`,
      })
    }

    // 4. All in-scope elements frozen
    if (inScopeChildren.length > 0) {
      const unfrozen = inScopeChildren.filter((el: any) => !el.frozen)
      result.push({
        label: 'All elements frozen',
        passed: unfrozen.length === 0,
        detail: unfrozen.length > 0
          ? `Unfrozen: ${unfrozen.map((e: any) => e.name).join(', ')}`
          : 'All elements frozen — ready for next level',
      })
    }

    return result
  }, [allElements, allRequirements, allInterfaces, focusElementId])

  const allPassed = checks.every(c => c.passed)
  const passedCount = checks.filter(c => c.passed).length

  return (
    <div style={{
      padding: '0.4rem 1rem', fontSize: '0.72rem',
      background: allPassed ? 'rgba(16,185,129,0.08)' : 'rgba(245,158,11,0.08)',
      borderBottom: `1px solid ${allPassed ? 'var(--success)' : 'var(--warning)'}`,
      display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap',
    }}>
      <span style={{ fontWeight: 600, color: allPassed ? 'var(--success)' : 'var(--warning)' }}>
        Level {currentLevel} Readiness: {passedCount}/{checks.length}
      </span>
      {checks.map(c => (
        <span key={c.label} style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }} title={c.detail}>
          <span style={{
            display: 'inline-block', width: 7, height: 7, borderRadius: '50%',
            background: c.passed ? 'var(--success)' : 'var(--danger)',
          }} />
          <span style={{ color: c.passed ? 'var(--text-secondary)' : 'var(--text-primary)' }}>
            {c.label}
          </span>
          {!c.passed && (
            <span style={{ color: 'var(--danger)', fontSize: '0.6rem', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              — {c.detail}
            </span>
          )}
        </span>
      ))}
    </div>
  )
}
