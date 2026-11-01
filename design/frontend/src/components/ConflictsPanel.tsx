/**
 * ConflictsPanel — cross-domain conflicts of the design loop (designStore, as
 * before) merged with the persisted analysis conflicts of SCDF-170
 * (`GET /api/studies/{id}/conflicts?option_id=` → {design, analysis}).
 *
 * The designStore rendering is unchanged; when a `studyId` is given the
 * persisted rows are appended with a source badge (analysis name), severity,
 * element chips (click → focus that element in Blocks), the suggested fix and
 * a Resolve button (`POST /api/conflicts/{id}/resolve`).
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useDesignStore } from '../stores/designStore'
import { useUIStore } from '../stores/uiStore'
import { optionQuery } from '../stores/optionStore'
import type { AnalysisConflict } from '../types/analyses'
import { fs } from '../theme/tokens'

const API = '/api'

// English text is the i18n key
const ANALYSIS_LABELS: Record<string, string> = {
  design_loop: 'design loop', mission_simulation: 'mission sim', ground_segment: 'ground segment',
  physics: 'physics', vv: 'V&V', fmeca: 'FMECA',
}
const ANALYSIS_COLORS: Record<string, string> = {
  design_loop: 'var(--status-caution)', mission_simulation: 'var(--interactive)', ground_segment: 'var(--status-ok)',
  physics: 'var(--cat-2)', vv: 'var(--cat-3)', fmeca: 'var(--cat-6)',
}
const SEVERITY_COLORS: Record<string, string> = {
  critical: 'var(--status-alarm)', major: 'var(--status-caution)', minor: 'var(--status-caution)', warning: 'var(--status-caution)', info: 'var(--interactive)',
}
// English text is the i18n key
const SEVERITY_LABELS: Record<string, string> = {
  critical: 'critical', major: 'major', minor: 'minor', warning: 'warning', info: 'info',
}

async function jsonOrThrow(res: Response) {
  if (!res.ok) {
    let msg = `${res.status}`
    try { const b = await res.json(); msg = typeof b.detail === 'string' ? b.detail : JSON.stringify(b.detail ?? b) } catch { /* noop */ }
    throw new Error(msg)
  }
  return res.json()
}

interface ElementLite { id: string; name: string; parent_id: string | null }

/** Drill the workbench to an element so it is focused in Blocks (capped below the V&V level). */
function focusElementInBlocks(el: ElementLite, all: ElementLite[]) {
  const ui = useUIStore.getState()
  const byId = new Map(all.map(e => [e.id, e]))
  const chain: ElementLite[] = []
  let cur: ElementLite | undefined = el
  while (cur && cur.parent_id) { chain.unshift(cur); cur = byId.get(cur.parent_id) }
  ui.drillUp(-1)
  for (const c of chain.slice(0, 3)) ui.drillInto(c.id, c.name)
  ui.setActivePanel('blocks')
}

function AnalysisConflictCard({ c, elements, onResolve, resolving }: {
  c: AnalysisConflict; elements: ElementLite[]; onResolve: (id: string) => void; resolving: boolean
}) {
  const { t } = useTranslation()
  const sev = SEVERITY_COLORS[c.severity] || SEVERITY_COLORS.minor
  const src = ANALYSIS_COLORS[c.analysis] || 'var(--text-3)'
  const byId = new Map(elements.map(e => [e.id, e]))
  return (
    <div className="card" style={{ borderLeft: `4px solid ${sev}`, background: `color-mix(in srgb, ${sev} 6%, transparent)`, marginBottom: '0.5rem', padding: '0.5rem 0.65rem', opacity: c.resolved ? 0.55 : 1 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.3rem', flexWrap: 'wrap' }}>
        <span style={{ fontSize: fs.label, padding: '0 0.35rem', borderRadius: 3, background: `color-mix(in srgb, ${src} 13%, transparent)`, color: src, border: `1px solid color-mix(in srgb, ${src} 33%, transparent)`, whiteSpace: 'nowrap' }}>
          {ANALYSIS_LABELS[c.analysis] ? t(ANALYSIS_LABELS[c.analysis]) : c.analysis}
        </span>
        <span style={{ fontSize: fs.label, padding: '0 0.35rem', borderRadius: 3, background: `color-mix(in srgb, ${sev} 13%, transparent)`, color: sev, border: `1px solid color-mix(in srgb, ${sev} 33%, transparent)`, textTransform: 'uppercase' }}>
          {SEVERITY_LABELS[c.severity] ? t(SEVERITY_LABELS[c.severity]) : c.severity}
        </span>
        <h3 style={{ fontSize: fs.body, margin: 0 }}>{c.title}</h3>
        <span style={{ fontSize: fs.label, color: 'var(--text-secondary)', fontFamily: 'ui-monospace, monospace' }}>{c.code}</span>
        <span style={{ flex: 1 }} />
        {c.resolved ? (
          <span style={{ fontSize: fs.label, color: 'var(--success)' }}>{t('resolved')}</span>
        ) : (
          <button onClick={() => onResolve(c.id)} disabled={resolving}
            style={{ cursor: 'pointer', fontSize: fs.label, padding: '0.1rem 0.5rem', borderRadius: 4, border: '1px solid var(--success)', background: 'rgba(16,185,129,0.12)', color: 'var(--success)' }}>
            {t('Resolve')}
          </button>
        )}
      </div>
      {c.detail && <p style={{ fontSize: fs.label, marginBottom: '0.3rem' }}>{c.detail}</p>}
      {c.element_ids?.length > 0 && (
        <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap', marginBottom: '0.3rem' }}>
          {c.element_ids.map(id => {
            const el = byId.get(id)
            return (
              <button key={id} title={el ? t('Focus {{name}} in Blocks', { name: el.name }) : id}
                onClick={() => el && focusElementInBlocks(el, elements)}
                style={{ cursor: el ? 'pointer' : 'default', fontSize: fs.label, padding: '0 0.4rem', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--bg-primary)', color: el ? 'var(--accent)' : 'var(--text-secondary)' }}>
                {el?.name || id.slice(0, 8)}
              </button>
            )
          })}
        </div>
      )}
      {c.requirement_ids?.length > 0 && (
        <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>{t('requirements: {{ids}}', { ids: c.requirement_ids.join(', ') })}</div>
      )}
      {c.suggested_fix && (
        <div style={{ fontSize: fs.label, borderTop: '1px solid color-mix(in srgb, var(--text) 5%, transparent)', paddingTop: '0.25rem' }}>
          <span style={{ fontSize: fs.label, fontWeight: 600, color: 'var(--text-secondary)' }}>{t('SUGGESTED FIX:')} </span>{c.suggested_fix}
        </div>
      )}
    </div>
  )
}

function AnalysisConflicts({ studyId, optionId, analysisFilter }: { studyId: string; optionId?: string | null; analysisFilter?: string }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const opt = optionQuery(optionId)
  const { data, error } = useQuery<{ design: AnalysisConflict[]; analysis: AnalysisConflict[] }>({
    queryKey: ['conflicts', studyId, optionId ?? null],
    queryFn: () => fetch(`${API}/studies/${studyId}/conflicts${opt}`).then(jsonOrThrow),
    enabled: !!studyId, structuralSharing: false,
  })
  const { data: elements = [] } = useQuery<ElementLite[]>({
    queryKey: ['elements', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/elements`).then(r => r.json()),
    enabled: !!studyId, structuralSharing: false,
  })
  const resolve = useMutation({
    mutationFn: (id: string) => fetch(`${API}/conflicts/${id}/resolve`, { method: 'POST' }).then(jsonOrThrow),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['conflicts', studyId] }); qc.invalidateQueries({ queryKey: ['analyses', studyId] }) },
  })

  if (error) return <div style={{ fontSize: fs.label, color: 'var(--danger)' }}>{t('conflicts: {{message}}', { message: (error as Error).message })}</div>
  if (!data) return null
  let rows = [...data.design, ...data.analysis]
  if (analysisFilter) rows = rows.filter(c => c.analysis === analysisFilter)
  const open = rows.filter(c => !c.resolved)
  const counts: Record<string, number> = {}
  for (const c of open) counts[c.severity] = (counts[c.severity] || 0) + 1

  if (rows.length === 0) {
    return (
      <div style={{ fontSize: fs.label, color: 'var(--success)', padding: '0.3rem 0' }}>
        {analysisFilter
          ? (optionId
            ? t('No {{analysis}} conflicts in this option.', { analysis: ANALYSIS_LABELS[analysisFilter] ? t(ANALYSIS_LABELS[analysisFilter]) : analysisFilter })
            : t('No {{analysis}} conflicts.', { analysis: ANALYSIS_LABELS[analysisFilter] ? t(ANALYSIS_LABELS[analysisFilter]) : analysisFilter }))
          : (optionId ? t('No analysis conflicts in this option.') : t('No analysis conflicts.'))}
      </div>
    )
  }
  return (
    <div>
      <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
        {Object.entries(counts).map(([sev, n]) => (
          <span key={sev} style={{ fontSize: fs.label, padding: '0 0.4rem', borderRadius: 3, background: `color-mix(in srgb, ${SEVERITY_COLORS[sev] || 'var(--text-3)'} 13%, transparent)`, color: SEVERITY_COLORS[sev] || 'var(--text-3)', border: `1px solid color-mix(in srgb, ${SEVERITY_COLORS[sev] || 'var(--text-3)'} 33%, transparent)` }}>
            {t('{{n}} {{severity}}', { n, severity: SEVERITY_LABELS[sev] ? t(SEVERITY_LABELS[sev]) : sev })}
          </span>
        ))}
        {open.length === 0 && <span style={{ fontSize: fs.label, color: 'var(--success)' }}>{t('all resolved')}</span>}
        {resolve.error && <span style={{ fontSize: fs.label, color: 'var(--danger)' }}>{(resolve.error as Error).message}</span>}
      </div>
      {rows.map(c => <AnalysisConflictCard key={c.id} c={c} elements={elements} onResolve={id => resolve.mutate(id)} resolving={resolve.isPending} />)}
    </div>
  )
}

// English text is the i18n key
const SEVERITY_BADGES: Record<string, string> = { critical: 'CRITICAL', major: 'MAJOR', minor: 'MINOR' }
const SEVERITY_STYLES: Record<string, { border: string; bg: string; label: string }> = {
  critical: { border: 'var(--danger)', bg: 'rgba(239,68,68,0.1)', label: SEVERITY_BADGES.critical },
  major: { border: 'var(--warning)', bg: 'rgba(245,158,11,0.1)', label: SEVERITY_BADGES.major },
  minor: { border: 'var(--info)', bg: 'rgba(6,182,212,0.1)', label: SEVERITY_BADGES.minor },
}

export function ConflictsPanel({ studyId, optionId, analysisFilter }: { studyId?: string | null; optionId?: string | null; analysisFilter?: string } = {}) {
  const { t } = useTranslation()
  const { result } = useDesignStore()
  const conflicts = result?.conflicts || []

  // SCDF-178: persisted design-loop + analysis conflicts for the study
  const persisted = studyId ? <AnalysisConflicts studyId={studyId} optionId={optionId} analysisFilter={analysisFilter} /> : null

  if (!result) return persisted
  if (conflicts.length === 0) {
    if (persisted) return persisted
    return (
      <div className="card" style={{ borderColor: 'var(--success)' }}>
        <h3 style={{ color: 'var(--success)' }}>{t('No Cross-Domain Conflicts')}</h3>
        <p style={{ fontSize: fs.body, color: 'var(--text-secondary)' }}>
          {t('All subsystem designs are compatible. No position conflicts detected.')}
        </p>
      </div>
    )
  }

  const critical = conflicts.filter((c: any) => c.severity === 'critical').length
  const major = conflicts.filter((c: any) => c.severity === 'major').length
  const minor = conflicts.filter((c: any) => c.severity === 'minor').length

  return (
    <div>
      {persisted}
      {/* Summary bar */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
        {critical > 0 && <span className="badge badge-red">{t('{{count}} Critical', { count: critical })}</span>}
        {major > 0 && <span className="badge badge-amber">{t('{{count}} Major', { count: major })}</span>}
        {minor > 0 && <span className="badge" style={{ background: 'rgba(6,182,212,0.2)', color: 'var(--info)' }}>{t('{{count}} Minor', { count: minor })}</span>}
      </div>

      {/* Conflict cards */}
      {conflicts.map((conflict: any) => {
        const style = SEVERITY_STYLES[conflict.severity] || SEVERITY_STYLES.minor
        return (
          <div
            key={conflict.id}
            className="card"
            style={{ borderLeft: `4px solid ${style.border}`, background: style.bg, marginBottom: '0.75rem' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <h3 style={{ fontSize: fs.body }}>{conflict.title}</h3>
              <span className={`badge badge-${conflict.severity === 'critical' ? 'red' : conflict.severity === 'major' ? 'amber' : 'green'}`}>
                {t(style.label)}
              </span>
            </div>

            <p style={{ fontSize: fs.body, marginBottom: '0.5rem' }}>{conflict.description}</p>

            {/* Positions involved */}
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '0.5rem', fontSize: fs.label, color: 'var(--text-secondary)' }}>
              <span><strong>{conflict.position_a?.replace('_', ' ')}</strong>: {conflict.value_a_str}</span>
              <span>↔</span>
              <span><strong>{conflict.position_b?.replace('_', ' ')}</strong>: {conflict.value_b_str}</span>
            </div>

            {/* Resolutions */}
            {conflict.resolutions?.length > 0 && (
              <div style={{ marginTop: '0.5rem' }}>
                <div style={{ fontSize: fs.label, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                  {t('SUGGESTED RESOLUTIONS:')}
                </div>
                {conflict.resolutions.map((res: any, i: number) => (
                  <div key={i} style={{ fontSize: fs.label, padding: '0.25rem 0', borderTop: '1px solid color-mix(in srgb, var(--text) 5%, transparent)' }}>
                    <strong>{res.position_responsible?.replace('_', ' ')}:</strong> {res.description}
                    {res.estimated_impact && <span style={{ color: 'var(--text-secondary)' }}> — {res.estimated_impact}</span>}
                  </div>
                ))}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
