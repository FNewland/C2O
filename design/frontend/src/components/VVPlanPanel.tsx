/**
 * VVPlanPanel — SCDF-175 V&V closure.
 *
 * Run button with last-run / stale badge, roll-up bars per verification level
 * (planned / in progress / passed / failed / waived), an editable table of the
 * verification items (method / level / phase / facility / acceptance / status /
 * evidence) with an "auto" chip on items closed by an analysis run and a lock
 * on user-edited rows, status / level / method filters, and RTM CSV / VCD docx
 * downloads.
 *
 *   POST  /api/studies/{id}/analyses/vv/run?option_id=
 *   GET   /api/studies/{id}/analyses/vv?option_id=
 *   GET   /api/studies/{id}/verification-items
 *   PATCH /api/verification-items/{id}
 *   POST  /api/verification-items/{id}/evidence
 *   GET   /api/studies/{id}/export/rtm.csv | vcd.docx
 *
 * Mounted below the traceability tree in workbench/VVPanel.tsx; SCDF-178 also
 * places it in the Analyses tab.
 */
import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import i18n from '../i18n'
import type {
  AnalysisConflict, VerificationItemPatch, VerificationItemView, VerificationItemsResponse, VVLevel, VVLevelRollup,
  VVMethod, VVPhase, VVRun, VVRunResponse, VVStatus,
} from '../types/analyses'
import { fs } from '../theme/tokens'

const API = '/api'
const ANALYSIS = 'vv'

const METHODS: VVMethod[] = ['A', 'T', 'I', 'R', 'D']
// English text is the i18n key
const METHOD_FULL: Record<VVMethod, string> = { A: 'Analysis', T: 'Test', I: 'Inspection', R: 'Review of design', D: 'Demonstration' }
const LEVELS: VVLevel[] = ['unit', 'subsystem', 'system', 'segment']
// English text is the i18n key
const LEVEL_LABEL: Record<VVLevel, string> = { unit: 'unit', subsystem: 'subsystem', system: 'system', segment: 'segment' }
const PHASES: VVPhase[] = ['PDR', 'CDR', 'QR', 'AR']
const STATUSES: VVStatus[] = ['planned', 'in_progress', 'passed', 'failed', 'waived']
const STATUS_COLORS: Record<VVStatus, string> = {
  planned: 'var(--text-3)', in_progress: 'var(--status-caution)', passed: 'var(--status-ok)', failed: 'var(--status-alarm)', waived: 'var(--cat-2)',
}
// English text is the i18n key
const STATUS_LABEL: Record<VVStatus, string> = {
  planned: 'planned', in_progress: 'in progress', passed: 'passed', failed: 'failed', waived: 'waived',
}
const METHOD_COLORS: Record<VVMethod, string> = { A: 'var(--interactive)', T: 'var(--status-ok)', I: 'var(--cat-2)', R: 'var(--status-caution)', D: 'var(--cat-3)' }
const SEVERITY_COLORS: Record<string, string> = {
  critical: 'var(--status-alarm)', major: 'var(--status-caution)', minor: 'var(--status-caution)', warning: 'var(--status-caution)', info: 'var(--interactive)',
}

async function jsonOrThrow(res: Response) {
  if (!res.ok) {
    let msg = `${res.status}`
    try {
      const b = await res.json()
      const d = b.detail
      msg = typeof d === 'string' ? d : JSON.stringify(d ?? b)
    } catch { /* noop */ }
    throw new Error(msg)
  }
  return res.status === 204 ? null : res.json()
}

function ago(iso: string | null | undefined): string {
  if (!iso) return ''
  const s = (Date.now() - new Date(iso).getTime()) / 1000
  if (!Number.isFinite(s)) return ''
  if (s < 60) return i18n.t('just now')
  if (s < 3600) return i18n.t('{{n}} min ago', { n: Math.floor(s / 60) })
  if (s < 86400) return i18n.t('{{n}} h ago', { n: Math.floor(s / 3600) })
  return i18n.t('{{n}} d ago', { n: Math.floor(s / 86400) })
}

const card: React.CSSProperties = {
  flex: '1 1 140px', minWidth: 130, padding: '0.4rem 0.55rem', borderRadius: 6,
  background: 'var(--bg-primary)', border: '1px solid var(--border)',
}
const btn = (primary = false): React.CSSProperties => ({
  cursor: 'pointer', fontSize: fs.label, padding: '0.2rem 0.6rem', borderRadius: 4,
  border: `1px solid ${primary ? 'var(--interactive)' : 'var(--border)'}`,
  background: primary ? 'color-mix(in srgb, var(--interactive) 13%, transparent)' : 'none', color: primary ? 'var(--interactive)' : 'var(--text-secondary)',
})
const th: React.CSSProperties = { textAlign: 'left', fontWeight: 500, color: 'var(--text-secondary)', padding: '0.15rem 0.35rem', fontSize: fs.label, textTransform: 'uppercase', letterSpacing: '0.03em', borderBottom: '1px solid var(--border)', whiteSpace: 'nowrap' }
const td: React.CSSProperties = { padding: '0.15rem 0.35rem', fontSize: fs.label, borderBottom: '1px solid var(--border)', verticalAlign: 'top' }
const sel: React.CSSProperties = { fontSize: fs.label, background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)', borderRadius: 3, padding: '0.05rem 0.15rem' }
const inp: React.CSSProperties = { ...sel, width: '100%', minWidth: 60, boxSizing: 'border-box' }

function Badge({ text, color, title }: { text: string; color: string; title?: string }) {
  return (
    <span title={title} style={{ fontSize: fs.label, padding: '0 0.35rem', borderRadius: 3, background: `color-mix(in srgb, ${color} 13%, transparent)`, color, border: `1px solid color-mix(in srgb, ${color} 33%, transparent)`, whiteSpace: 'nowrap' }}>
      {text}
    </span>
  )
}

/** Stacked bar: passed / waived / in progress / failed / planned. */
function LevelBar({ level, r }: { level: VVLevel; r: VVLevelRollup }) {
  const { t } = useTranslation()
  const total = r.total || 0
  const closed = r.passed + r.waived
  const pct = total > 0 ? (100 * closed) / total : 0
  const segs: [VVStatus, number][] = [['passed', r.passed], ['waived', r.waived], ['in_progress', r.in_progress], ['failed', r.failed], ['planned', r.planned]]
  return (
    <div style={{ ...card, flex: '1 1 160px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: fs.label, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.03em' }}>
        <span>{t(LEVEL_LABEL[level] ?? level)}</span>
        <span style={{ fontFamily: 'ui-monospace, monospace', color: total === 0 ? 'var(--text-secondary)' : pct >= 100 ? 'var(--status-ok)' : r.failed > 0 ? 'var(--status-alarm)' : 'var(--text-primary)' }}>
          {total === 0 ? '—' : `${closed}/${total} · ${pct.toFixed(0)} %`}
        </span>
      </div>
      <div style={{ display: 'flex', height: 10, marginTop: 4, borderRadius: 5, overflow: 'hidden', background: 'var(--bg-secondary, var(--surface-2))', border: '1px solid var(--border)' }}
           title={segs.map(([s, n]) => t('{{label}}: {{value}}', { label: t(STATUS_LABEL[s]), value: n })).join(' · ')}>
        {total > 0 && segs.map(([s, n]) => n > 0 && (
          <div key={s} style={{ width: `${(100 * n) / total}%`, background: STATUS_COLORS[s], transition: 'width 0.3s' }} />
        ))}
      </div>
      <div style={{ display: 'flex', gap: '0.4rem', marginTop: 3, fontSize: fs.label, fontFamily: 'ui-monospace, monospace', flexWrap: 'wrap' }}>
        {segs.filter(([, n]) => n > 0).map(([s, n]) => <span key={s} style={{ color: STATUS_COLORS[s] }}>{n} {t(STATUS_LABEL[s])}</span>)}
      </div>
    </div>
  )
}

function rollup(items: VerificationItemView[]): Record<VVLevel, VVLevelRollup> {
  const out = Object.fromEntries(LEVELS.map(l => [l, { total: 0, planned: 0, in_progress: 0, passed: 0, failed: 0, waived: 0 }])) as Record<VVLevel, VVLevelRollup>
  for (const it of items) {
    const lvl = (it.level && LEVELS.includes(it.level) ? it.level : 'system') as VVLevel
    out[lvl].total++
    const st = (STATUSES.includes(it.status) ? it.status : 'planned') as VVStatus
    out[lvl][st]++
  }
  return out
}

interface RowProps {
  item: VerificationItemView
  onPatch: (id: string, patch: VerificationItemPatch) => void
  busy: boolean
}

function ItemRow({ item, onPatch, busy }: RowProps) {
  const { t } = useTranslation()
  const [facility, setFacility] = useState(item.facility ?? '')
  const [acceptance, setAcceptance] = useState(item.acceptance_criterion ?? '')
  const [evidence, setEvidence] = useState(item.evidence_ref ?? '')
  const commit = (field: 'facility' | 'acceptance_criterion' | 'evidence_ref', value: string) => {
    const current = item[field] ?? ''
    if (value !== current) onPatch(item.id, { [field]: value || null } as VerificationItemPatch)
  }
  const statusColor = STATUS_COLORS[item.status] || 'var(--text-3)'
  return (
    <tr style={{ opacity: busy ? 0.6 : 1, background: item.status === 'failed' ? 'rgba(239,68,68,0.05)' : undefined }}>
      <td style={{ ...td, whiteSpace: 'nowrap' }}>
        <span style={{ fontFamily: 'ui-monospace, monospace', color: 'var(--accent)', fontSize: fs.label }}>{item.requirement_code}</span>
        {item.edited_by_user && <span title={t('Edited by user — the generator only fills empty fields on this row')} style={{ marginLeft: 4, fontSize: fs.label }}>🔒</span>}
      </td>
      <td style={{ ...td, maxWidth: 260 }} title={item.requirement_text}>
        <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 260 }}>{item.requirement_text}</div>
        {item.linked_element_names.length > 0 && (
          <div style={{ fontSize: fs.label, color: 'var(--text-secondary)' }}>→ {item.linked_element_names.join(', ')}</div>
        )}
      </td>
      <td style={td}>
        <select value={item.method ?? ''} onChange={e => onPatch(item.id, { method: (e.target.value || null) as VVMethod | null })}
                style={{ ...sel, color: item.method ? METHOD_COLORS[item.method] : 'var(--text-secondary)', fontWeight: 600 }} title={item.method ? t(METHOD_FULL[item.method]) : ''}>
          <option value="">—</option>
          {METHODS.map(m => <option key={m} value={m}>{m}</option>)}
        </select>
      </td>
      <td style={td}>
        <select value={item.level ?? ''} onChange={e => onPatch(item.id, { level: (e.target.value || null) as VVLevel | null })} style={sel}>
          <option value="">—</option>
          {LEVELS.map(l => <option key={l} value={l}>{t(LEVEL_LABEL[l])}</option>)}
        </select>
      </td>
      <td style={td}>
        <select value={item.phase ?? ''} onChange={e => onPatch(item.id, { phase: (e.target.value || null) as VVPhase | null })} style={sel}>
          <option value="">—</option>
          {PHASES.map(p => <option key={p} value={p}>{p}</option>)}
        </select>
      </td>
      <td style={{ ...td, minWidth: 90 }}>
        <input value={facility} onChange={e => setFacility(e.target.value)} onBlur={() => commit('facility', facility)}
               onKeyDown={e => { if (e.key === 'Enter') (e.target as HTMLInputElement).blur() }} style={inp} placeholder={t('facility')} />
      </td>
      <td style={{ ...td, minWidth: 180 }}>
        <input value={acceptance} onChange={e => setAcceptance(e.target.value)} onBlur={() => commit('acceptance_criterion', acceptance)}
               onKeyDown={e => { if (e.key === 'Enter') (e.target as HTMLInputElement).blur() }} style={inp} placeholder={t('acceptance criterion')} title={acceptance} />
      </td>
      <td style={{ ...td, whiteSpace: 'nowrap' }}>
        <select value={item.status} onChange={e => onPatch(item.id, { status: e.target.value as VVStatus })}
                style={{ ...sel, color: statusColor, fontWeight: 600 }}>
          {STATUSES.map(s => <option key={s} value={s}>{t(STATUS_LABEL[s])}</option>)}
        </select>
        {item.auto_closed && <span style={{ marginLeft: 4 }}><Badge text="auto" color="var(--interactive)" title={t('Closed by analysis run {{run}}', { run: item.evidence_ref?.replace('analysis:', '') ?? '' })} /></span>}
      </td>
      <td style={{ ...td, minWidth: 110 }}>
        <input value={evidence} onChange={e => setEvidence(e.target.value)} onBlur={() => commit('evidence_ref', evidence)}
               onKeyDown={e => { if (e.key === 'Enter') (e.target as HTMLInputElement).blur() }} style={{ ...inp, fontFamily: 'ui-monospace, monospace' }} placeholder={t('evidence ref')} />
      </td>
    </tr>
  )
}

export function VVPlanPanel({ studyId, optionId }: { studyId: string | null; optionId?: string | null }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const opt = optionId ? `?option_id=${encodeURIComponent(optionId)}` : ''
  const [statusFilter, setStatusFilter] = useState<VVStatus | 'all'>('all')
  const [levelFilter, setLevelFilter] = useState<VVLevel | 'all'>('all')
  const [methodFilter, setMethodFilter] = useState<VVMethod | 'all'>('all')
  const [error, setError] = useState<string | null>(null)

  const runQ = useQuery<VVRun | null>({
    queryKey: ['analysis', ANALYSIS, studyId, optionId ?? null],
    queryFn: async () => {
      const res = await fetch(`${API}/studies/${studyId}/analyses/${ANALYSIS}${opt}`)
      if (res.status === 404) return null
      return jsonOrThrow(res)
    },
    enabled: !!studyId, structuralSharing: false,
  })
  const itemsQ = useQuery<VerificationItemsResponse>({
    queryKey: ['verification-items', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/verification-items`).then(jsonOrThrow),
    enabled: !!studyId, structuralSharing: false,
  })
  const conflictsQ = useQuery<{ analysis: AnalysisConflict[] }>({
    queryKey: ['conflicts', studyId, optionId ?? null],
    queryFn: () => fetch(`${API}/studies/${studyId}/conflicts${opt}`).then(jsonOrThrow),
    enabled: !!studyId, structuralSharing: false,
  })

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['analysis', ANALYSIS, studyId] })
    qc.invalidateQueries({ queryKey: ['verification-items', studyId] })
    qc.invalidateQueries({ queryKey: ['conflicts', studyId] })
    qc.invalidateQueries({ queryKey: ['parameters', studyId] })
  }

  const run = useMutation<VVRunResponse>({
    mutationFn: () => fetch(`${API}/studies/${studyId}/analyses/${ANALYSIS}/run${opt}`, { method: 'POST' }).then(jsonOrThrow),
    onSuccess: () => { setError(null); invalidate() },
    onError: (e: Error) => setError(e.message),
  })
  const patch = useMutation<VerificationItemView, Error, { id: string; patch: VerificationItemPatch }>({
    mutationFn: ({ id, patch }) => fetch(`${API}/verification-items/${id}`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(patch),
    }).then(jsonOrThrow),
    onSuccess: () => { setError(null); invalidate() },
    onError: (e: Error) => setError(e.message),
  })

  const items = itemsQ.data?.items ?? []
  const byLevel = useMemo(() => itemsQ.data?.by_level ?? rollup(items), [itemsQ.data, items])
  const filtered = useMemo(() => items.filter(it =>
    (statusFilter === 'all' || it.status === statusFilter) &&
    (levelFilter === 'all' || it.level === levelFilter) &&
    (methodFilter === 'all' || it.method === methodFilter),
  ), [items, statusFilter, levelFilter, methodFilter])
  const vvConflicts = (conflictsQ.data?.analysis ?? []).filter(c => c.analysis === ANALYSIS && !c.resolved)

  const total = items.length
  const passed = items.filter(i => i.status === 'passed').length
  const failed = items.filter(i => i.status === 'failed').length
  const waived = items.filter(i => i.status === 'waived').length
  const autoClosed = items.filter(i => i.auto_closed).length
  const closurePct = total > 0 ? (100 * (passed + waived)) / total : 0
  const byAnalysisPct = total > 0 ? (100 * items.filter(i => i.method === 'A').length) / total : 0
  const lastRun = runQ.data

  const download = (name: 'rtm.csv' | 'vcd.docx') => {
    if (!studyId) return
    const a = document.createElement('a')
    a.href = `${API}/studies/${studyId}/export/${name}`
    a.download = ''
    a.click()
  }

  if (!studyId) return <div style={{ fontSize: fs.label, color: 'var(--text-secondary)' }}>{t('Select a study.')}</div>

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      {/* header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
        <h3 style={{ fontSize: fs.body, margin: 0 }}>{t('V&V plan & closure')}</h3>
        {lastRun && (
          <span style={{ fontSize: fs.label, color: 'var(--text-secondary)' }}>
            {t('last run {{ago}}', { ago: ago(lastRun.finished_at ?? lastRun.started_at) })}
            {lastRun.status === 'failed' && <span style={{ color: 'var(--status-alarm)', marginLeft: 4 }}>{t('failed')}</span>}
          </span>
        )}
        {lastRun?.stale && <Badge text={t('stale')} color="var(--status-caution)" title={t('Requirements or elements changed since this run')} />}
        {!lastRun && !runQ.isLoading && <Badge text={t('never run')} color="var(--text-3)" />}
        <span style={{ flex: 1 }} />
        <button onClick={() => download('rtm.csv')} style={btn()} title={t('Requirement traceability matrix (CSV)')}>RTM CSV</button>
        <button onClick={() => download('vcd.docx')} style={btn()} title={t('Verification Control Document (Word)')}>VCD docx</button>
        <button onClick={() => run.mutate()} disabled={run.isPending} style={btn(true)}>
          {run.isPending ? t('Running…') : lastRun ? t('Re-run V&V') : t('Run V&V')}
        </button>
      </div>
      {error && <div style={{ fontSize: fs.label, color: 'var(--status-alarm)' }}>{error}</div>}

      {/* summary */}
      <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
        <div style={card}>
          <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.03em' }}>{t('Closure')}</div>
          <div style={{ fontSize: fs.value, fontWeight: 600, fontFamily: 'ui-monospace, monospace', color: total === 0 ? 'var(--text-secondary)' : closurePct >= 100 ? 'var(--status-ok)' : failed > 0 ? 'var(--status-alarm)' : 'var(--text-primary)' }}>
            {closurePct.toFixed(0)}<span style={{ fontSize: fs.label, marginLeft: 2, color: 'var(--text-secondary)' }}>%</span>
          </div>
          <div style={{ fontSize: fs.label, color: 'var(--text-secondary)' }}>{t('{{passed}} passed · {{waived}} waived · {{failed}} failed of {{total}}', { passed, waived, failed, total })}</div>
        </div>
        <div style={card}>
          <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.03em' }}>{t('By analysis')}</div>
          <div style={{ fontSize: fs.value, fontWeight: 600, fontFamily: 'ui-monospace, monospace' }}>
            {byAnalysisPct.toFixed(0)}<span style={{ fontSize: fs.label, marginLeft: 2, color: 'var(--text-secondary)' }}>%</span>
          </div>
          <div style={{ fontSize: fs.label, color: 'var(--text-secondary)' }}>{t('{{n}} closed automatically', { n: autoClosed })}</div>
        </div>
        {LEVELS.map(l => <LevelBar key={l} level={l} r={byLevel[l]} />)}
      </div>

      {/* conflicts */}
      {vvConflicts.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {vvConflicts.map(c => (
            <div key={c.id} style={{ display: 'flex', gap: '0.4rem', alignItems: 'baseline', fontSize: fs.label, padding: '0.2rem 0.4rem', borderLeft: `3px solid ${SEVERITY_COLORS[c.severity] || 'var(--text-3)'}`, background: 'var(--bg-card)', borderRadius: 3 }}>
              <Badge text={c.severity} color={SEVERITY_COLORS[c.severity] || 'var(--text-3)'} />
              <span style={{ fontFamily: 'ui-monospace, monospace', color: 'var(--text-secondary)' }}>{c.code}</span>
              <span style={{ fontWeight: 500 }}>{c.title}</span>
              {c.suggested_fix && <span style={{ color: 'var(--text-secondary)' }}>— {c.suggested_fix}</span>}
            </div>
          ))}
        </div>
      )}

      {/* filters */}
      <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center', fontSize: fs.label, flexWrap: 'wrap' }}>
        <span style={{ color: 'var(--text-secondary)' }}>{t('Filter')}</span>
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value as VVStatus | 'all')} style={sel}>
          <option value="all">{t('all statuses')}</option>
          {STATUSES.map(s => <option key={s} value={s}>{t(STATUS_LABEL[s])}</option>)}
        </select>
        <select value={levelFilter} onChange={e => setLevelFilter(e.target.value as VVLevel | 'all')} style={sel}>
          <option value="all">{t('all levels')}</option>
          {LEVELS.map(l => <option key={l} value={l}>{t(LEVEL_LABEL[l])}</option>)}
        </select>
        <select value={methodFilter} onChange={e => setMethodFilter(e.target.value as VVMethod | 'all')} style={sel}>
          <option value="all">{t('all methods')}</option>
          {METHODS.map(m => <option key={m} value={m}>{m} — {t(METHOD_FULL[m])}</option>)}
        </select>
        <span style={{ color: 'var(--text-secondary)' }}>{t('{{shown}} of {{total}} items', { shown: filtered.length, total })}</span>
        <span style={{ flex: 1 }} />
        <span style={{ color: 'var(--text-secondary)', fontSize: fs.label }}>
          <Badge text="auto" color="var(--interactive)" /> {t('closed by analysis · 🔒 user-edited (generator fills empty fields only)')}
        </span>
      </div>

      {/* table */}
      {itemsQ.isLoading ? (
        <div style={{ fontSize: fs.label, color: 'var(--text-secondary)' }}>{t('Loading…')}</div>
      ) : total === 0 ? (
        <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', padding: '0.5rem 0' }}>
          {t('No verification items yet — run V&V to generate one per requirement (method, level, phase, facility and acceptance criterion are derived from the requirement and its allocation).')}
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={th}>{t('Req')}</th><th style={th}>{t('Requirement')}</th><th style={th} title={t('A analysis · T test · I inspection · R review · D demonstration')}>{t('Method')}</th>
                <th style={th}>{t('Level')}</th><th style={th}>{t('Phase')}</th><th style={th}>{t('Facility')}</th><th style={th}>{t('Acceptance criterion')}</th>
                <th style={th}>{t('Status')}</th><th style={th}>{t('Evidence')}</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(it => (
                <ItemRow key={`${it.id}-${it.updated_at}`} item={it} busy={patch.isPending && patch.variables?.id === it.id}
                         onPatch={(id, p) => patch.mutate({ id, patch: p })} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default VVPlanPanel
