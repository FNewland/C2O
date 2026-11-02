/**
 * EscalationBanner — Warns when a lower level breaks a higher level's budget.
 *
 * Walks up the breadcrumb checking each ancestor's budget.
 * If any ancestor has actuals exceeding allocation, shows a red banner
 * with a link to navigate back to the broken level.
 */
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useUIStore } from '../stores/uiStore'
import { StatusBadge } from '../components/ui/StatusBadge'
import { displayElementName } from './BlocksPanel'

const API = '/api'
// English text is the i18n key (budget type shown as t(type); the value itself is an API path segment).
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
  const { t } = useTranslation()
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
    enabled: !!studyId, structuralSharing: false,
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

  // Inline in the context bar: alarm glyph + text per broken ancestor; a click goes to that level.
  return (
    <div className="c2o-escalation" role="alert" aria-label={t('Budget escalation')}>
      {violations.map((v) => (
        <button
          key={`${v.elementId}-${v.budgetType}`}
          type="button"
          className="c2o-escalation__item"
          onClick={() => drillUp(v.breadcrumbIndex)}
          title={t('Go to the level where {{name}} is allocated', { name: displayElementName(v.elementName, t) })}
        >
          <StatusBadge status="alarm">
            {t('{{name}} {{budget}} over allocation', { name: displayElementName(v.elementName, t), budget: t(v.budgetType) })}
          </StatusBadge>
          <span className="mono t-12 c-1">{v.actual.toFixed(2)} / {v.allocation.toFixed(2)} {v.unit}</span>
        </button>
      ))}
    </div>
  )
}
