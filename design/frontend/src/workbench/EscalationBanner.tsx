/**
 * EscalationBanner — Warns when a lower level breaks a higher level's budget.
 *
 * Walks up the breadcrumb checking each ancestor's budget.
 * If any ancestor has actuals exceeding allocation, shows a red banner
 * with a link to navigate back to the broken level.
 */
import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useUIStore } from '../stores/uiStore'

const API = '/api'
const BUDGET_TYPES = ['mass', 'power', 'cost'] as const

interface Violation {
  elementId: string
  elementName: string
  budgetType: string
  allocation: number
  actual: number
  unit: string
  breadcrumbIndex: number
}

export function EscalationBanner() {
  const studyId = useUIStore(s => s.studyId)
  const breadcrumb = useUIStore(s => s.breadcrumb)
  const currentLevel = useUIStore(s => s.currentLevel)
  const drillUp = useUIStore(s => s.drillUp)

  // Only check when we're at level 1+ (there's an ancestor to check)
  const ancestorIds = breadcrumb.map(b => b.id)

  // Fetch budget for each ancestor across all budget types
  // We batch all queries together
  const { data: allElements = [] } = useQuery({
    queryKey: ['elements', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/elements`).then(r => r.json()),
    enabled: !!studyId,
  })

  // Find mission root as well
  const missionRoot = allElements.find((e: any) => !e.parent_id)
  const checkIds = missionRoot ? [missionRoot.id, ...ancestorIds] : ancestorIds

  // Fetch budgets for ancestors
  const budgetQueries = checkIds.flatMap(id =>
    BUDGET_TYPES.map(type => ({ id, type }))
  )

  // We'll use a single query that fetches all ancestor budgets
  const { data: violations = [] } = useQuery({
    queryKey: ['escalation', studyId, checkIds.join(',')],
    queryFn: async () => {
      const results: Violation[] = []
      for (const { id, type } of budgetQueries) {
        try {
          const res = await fetch(`${API}/elements/${id}/budget/${type}`)
          if (!res.ok) continue
          const budget = await res.json()
          if (budget.allocation != null && budget.sum_with_margin > budget.allocation) {
            const unit = type === 'mass' ? 'kg' : type === 'power' ? 'W' : 'kEUR'
            const bcIdx = ancestorIds.indexOf(id)
            results.push({
              elementId: id,
              elementName: budget.element_name,
              budgetType: type,
              allocation: budget.allocation,
              actual: budget.sum_with_margin,
              unit,
              breadcrumbIndex: bcIdx,
            })
          }
        } catch { /* skip */ }
      }
      return results
    },
    enabled: !!studyId && checkIds.length > 0 && currentLevel > 0,
    refetchInterval: 5000, // Re-check every 5s while user is working
  })

  if (violations.length === 0) return null

  return (
    <div style={{
      padding: '0.4rem 1rem', fontSize: '0.72rem',
      background: 'rgba(239,68,68,0.12)', borderBottom: '1px solid var(--danger)',
      display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap',
    }}>
      <span style={{ fontWeight: 700, color: 'var(--danger)' }}>ESCALATION</span>
      {violations.map((v, i) => (
        <button
          key={`${v.elementId}-${v.budgetType}`}
          onClick={() => drillUp(v.breadcrumbIndex)}
          style={{
            display: 'flex', alignItems: 'center', gap: '0.3rem',
            padding: '0.2rem 0.5rem', borderRadius: '3px',
            background: 'rgba(239,68,68,0.15)', border: '1px solid var(--danger)',
            color: 'var(--text-primary)', cursor: 'pointer', fontSize: '0.68rem',
          }}
        >
          <span style={{ fontWeight: 600 }}>{v.elementName}</span>
          <span style={{ color: 'var(--danger)' }}>
            {v.budgetType}: {v.actual.toFixed(1)}/{v.allocation.toFixed(1)} {v.unit}
          </span>
          <span style={{ color: 'var(--text-secondary)' }}>— click to fix</span>
        </button>
      ))}
    </div>
  )
}
