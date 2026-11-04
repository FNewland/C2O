/**
 * ReadinessChecklist — Shows what's needed to freeze the current level and move on.
 *
 * Checks:
 * - All elements at this level exist (at least 1)
 * - All in-scope elements have budget allocations
 * - All in-scope elements have at least 1 requirement
 * - All in-scope elements have defined interfaces (if >1 sibling)
 * - No suggested links left to review
 * - All checks green → can freeze
 *
 * The server checklist (GET /api/studies/{sid}/readiness?level=) is the
 * source of truth: its "Interfaces defined" item applies the coverage rules
 * (power, data, mount and thermal path per unit), so the panel and the gate
 * agree. The local checks below are only the fallback for servers without it.
 */
import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useUIStore } from '../stores/uiStore'
import { StatusBadge } from '../components/ui/StatusBadge'
import { Chevron } from '../components/ui/Disclosure'
import { normaliseInterface, pickLang } from '../types/interfaces'
import { useServerReadiness } from './interfaceApi'

const API = '/api'

interface Check {
  id: string
  label: string
  passed: boolean
  detail: string
}

export function ReadinessChecklist({ hideNext = false }: { hideNext?: boolean } = {}) {
  const { t, i18n } = useTranslation()
  const [open, setOpen] = useState(false)
  const studyId = useUIStore(s => s.studyId)
  const focusElementId = useUIStore(s => s.focusElementId)
  const currentLevel = useUIStore(s => s.currentLevel)

  const { data: allElements = [] } = useQuery({
    queryKey: ['elements', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/elements`).then(r => r.json()),
    enabled: !!studyId, structuralSharing: false,
  })

  const { data: allRequirements = [] } = useQuery({
    queryKey: ['requirements', studyId],
    queryFn: () => fetch(`${API}/requirements/tree?study_id=${studyId}`).then(r => r.json()),
    enabled: !!studyId, structuralSharing: false,
  })

  const { data: allInterfaces = [] } = useQuery({
    queryKey: ['interfaces', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/interfaces`).then(r => r.json()),
    enabled: !!studyId, structuralSharing: false,
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
      id: 'elements',
      label: t('Elements defined'),
      passed: hasElements,
      detail: hasElements
        ? t('{{count}} elements at this level', { count: children.length })
        : t('Add at least one element'),
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
        id: 'requirements',
        label: t('Requirements defined'),
        passed: hasParentReqs || elementsWithReqs.size > 0,
        detail: missingReqs.length > 0
          ? t('Missing requirements: {{names}}', { names: missingReqs.map((e: any) => e.name).join(', ') })
          : t('{{count}} elements have requirements', { count: elementsWithReqs.size }),
      })
    }

    // 3. Interfaces defined (if more than 1 in-scope sibling)
    if (inScopeChildren.length > 1) {
      const connectedElements = new Set<string>()
      const live = allInterfaces.map(normaliseInterface).filter((i: any) => i.status !== 'rejected')
      for (const iface of live) {
        if (childIds.has(iface.from_element_id)) connectedElements.add(iface.from_element_id)
        if (childIds.has(iface.to_element_id)) connectedElements.add(iface.to_element_id)
      }
      const unconnected = inScopeChildren.filter((el: any) => !connectedElements.has(el.id))
      result.push({
        id: 'interfaces',
        label: t('Interfaces defined'),
        passed: unconnected.length === 0,
        detail: unconnected.length > 0
          ? t('No interfaces: {{names}}', { names: unconnected.map((e: any) => e.name).join(', ') })
          : t('{{count}} elements connected', { count: connectedElements.size }),
      })
    }

    // 3b. Suggested links reviewed
    if (inScopeChildren.length > 1) {
      const pending = allInterfaces.map(normaliseInterface).filter((i: any) =>
        i.status === 'suggested' && childIds.has(i.from_element_id) && childIds.has(i.to_element_id))
      result.push({
        id: 'suggested_reviewed',
        label: t('Suggested links reviewed'),
        passed: pending.length === 0,
        detail: pending.length > 0
          ? t('{{count}} suggested links to accept, edit or reject', { count: pending.length })
          : t('No suggested links left'),
      })
    }

    // 4. All in-scope elements frozen
    if (inScopeChildren.length > 0) {
      const unfrozen = inScopeChildren.filter((el: any) => !el.frozen)
      result.push({
        id: 'frozen',
        label: t('All elements frozen'),
        passed: unfrozen.length === 0,
        detail: unfrozen.length > 0
          ? t('Unfrozen: {{names}}', { names: unfrozen.map((e: any) => e.name).join(', ') })
          : t('All elements frozen — ready for next level'),
      })
    }

    return result
  }, [allElements, allRequirements, allInterfaces, focusElementId, t])

  // Server checklist when available (items keep the server's order); local checks otherwise.
  const server = useServerReadiness(studyId, currentLevel, focusElementId)
  const served = server.data?.served && (server.data.items.length > 0)
  const shown: Check[] = served
    ? server.data!.items.map(it => ({ id: it.id, label: pickLang(it.label, i18n.language), passed: it.ok, detail: pickLang(it.detail, i18n.language) }))
    : checks
  return <ReadinessView checks={shown} open={open} setOpen={setOpen} level={currentLevel} source={served ? 'server' : 'local'} hideNext={hideNext} />
}

function ReadinessView({ checks, open, setOpen, level, source, hideNext }: {
  checks: Check[]; open: boolean; setOpen: (f: (o: boolean) => boolean) => void; level: number; source: 'server' | 'local'; hideNext?: boolean
}) {
  const { t } = useTranslation()
  const currentLevel = level
  const allPassed = checks.every(c => c.passed)
  const passedCount = checks.filter(c => c.passed).length
  const firstOpen = checks.find(c => !c.passed)

  // Compact summary in the context bar; the full checklist is one click deeper.
  // Unmet readiness is "not yet", not an alarm: caution glyph + text; check for met (P6).
  return (
    <div className="c2o-readiness" data-where="readiness">
      <button type="button" className="c2o-readiness__btn" aria-expanded={open} aria-controls="c2o-readiness-list"
        onClick={() => setOpen(o => !o)}>
        <StatusBadge status={allPassed ? 'ok' : 'caution'}>
          {/* Level 4 is the V&V view, not a design level (screen review §11). */}
          {currentLevel === 4
            ? t('V&V readiness {{passed}}/{{total}}', { passed: passedCount, total: checks.length })
            : t('Level {{level}} readiness {{passed}}/{{total}}', { level: currentLevel, passed: passedCount, total: checks.length })}
        </StatusBadge>
        {/* With seats the active seat's Next card (seats/SeatLayer.tsx) replaces this label. */}
        {firstOpen && !open && !hideNext && <span className="c2o-readiness__next c-2 ellipsis">{t('Next: {{label}}', { label: firstOpen.label })}</span>}
        <Chevron />
      </button>
      {open && (
        <ul id="c2o-readiness-list" className="c2o-readiness__list list-reset">
          {checks.map(c => (
            <li key={c.id} className="c2o-readiness__item">
              <StatusBadge status={c.passed ? 'ok' : 'caution'}>
                <span className="sr-only">{c.passed ? t('Met:') : t('Not met:')} </span>{c.label}
              </StatusBadge>
              <span className="t-12 c-2">{c.detail}</span>
            </li>
          ))}
          <li className="t-12 c-3">{source === 'server'
            ? t('Checked by the server with the same rules as the gate review.')
            : t('Checked in this browser: the server has no readiness check yet.')}</li>
        </ul>
      )}
    </div>
  )
}
