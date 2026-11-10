/**
 * RequirementsTable — the whole requirement baseline of a study in one table (W2.08).
 *
 * - Virtualised rows (only the visible window is rendered), so 220+ rows scroll smoothly.
 * - Filters: text, level, category, owner seat, status, verification stage, priority.
 * - Sort by any column; group by level; column chooser; inline rationale.
 * - Select rows → bulk edit (priority, category, owner, stage, status).
 * - Click a code → the full editor (RequirementEditor): code, level, several parents and
 *   objectives, threshold with range and date operators and a unit, verification methods,
 *   stage and level, allocation over the whole product tree, and for an interface requirement
 *   its interface and ICD row (exchange item).
 * - "Import requirements": YAML / JSON / CSV with a dry-run preview, or ReqIF.
 * - Wave 3: a Functions column and picker (the functions and processes that satisfy a row,
 *   3.R1); a "Checked against" column with the proposed binding of each threshold to a figure
 *   the tool computes, accepted per row or all at once, and its verdict (3.R2); the acceptance
 *   criterion, verification model and event; the allocation flag of rule AR-01 (3.R3).
 *
 * No polling: the study socket broadcasts every requirement change (useCollaboration).
 */
import { useMemo, useRef, useState, type ReactNode } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Button, Field, Input, Select, Textarea, StatusBadge, Tag, Disclosure, type Status } from '../components/ui'
import { showAlert } from '../components/ui/Dialog'
import './RequirementsTable.css'

const API = '/api'
const ROW_H = 34
const OVERSCAN = 12

// English text is the i18n key
export const LEVEL_LABELS: Record<string, string> = {
  stakeholder: 'Stakeholder need', mission: 'Mission', segment: 'Segment', system: 'System',
  subsystem: 'Subsystem', interface: 'Interface',
}
export const LEVEL_ORDER = ['stakeholder', 'mission', 'segment', 'system', 'subsystem', 'interface']
const STATUS_LABELS: Record<string, string> = { draft: 'Draft', approved: 'Approved', verified: 'Verified', violated: 'Violated' }
const REQ_STATUS: Record<string, Status> = { draft: 'neutral', approved: 'info', verified: 'ok', violated: 'alarm' }
export const STAGES = ['PRR', 'SRR', 'PDR', 'CDR', 'QR', 'AR', 'IOV']
const STAGE_LABELS: Record<string, string> = { IOV: 'In-orbit verification' }
export const METHODS: Record<string, string> = { T: 'Test', A: 'Analysis', R: 'Review', I: 'Inspection' }
const PRIORITY_LABELS: Record<string, string> = { '1': '1 mandatory', '2': '2 performance', '3': '3 goal' }
export const OPS = ['<=', '>=', '<', '>', '==', 'in_range', 'before', 'after', 'exists']
const OP_LABELS: Record<string, string> = { in_range: 'in range', before: 'before (date)', after: 'after (date)', exists: 'exists' }
const VER_LEVELS = ['mission', 'segment', 'system', 'subsystem', 'unit']
const TYPES = ['functional', 'performance', 'interface', 'regulatory', 'process']
const TYPE_LABELS: Record<string, string> = {
  functional: 'Functional', performance: 'Performance', interface: 'Interface', regulatory: 'Regulatory', process: 'Process',
}

export interface Req {
  id: string; code: string; level: string; text: string; rationale?: string | null; req_type?: string | null
  category?: string | null; element_id?: string | null; parent_id?: string | null; parent_ids?: string[]
  objective_id?: string | null; objective_ids?: string[]; verification_method?: string | null
  verification_methods?: string[] | null; verification_phase?: string | null; verification_level?: string | null
  responsible_position?: string | null; priority?: number | null; source_ref?: string | null; status: string
  threshold_op?: string | null; threshold_value?: unknown; threshold_unit?: string | null; open_item?: boolean | null
  ir_json?: Record<string, any> | null
  // wave 3 (v2 baseline)
  acceptance?: string | null; verification_model?: string | null; verification_event?: string | null
  budget_ref?: string | null; function_codes?: string[] | null; allocation_codes?: string[] | null
  threshold_param_path?: string | null; external_ids?: Record<string, any> | null
}

export interface FnLink { id: string; code?: string | null; name?: string | null; kind: string; level?: number; is_leaf?: boolean }
export interface BindingRow {
  requirement_id: string; code: string; budget_ref?: string | null; current_path?: string | null; accepted: boolean
  proposal?: { path: string; reason: string; unit: string } | null; status?: string | null; achieved?: number | null
  margin_pct?: number | null
}
export interface CatalogueItem { path: string; unit: string; family: string; label: { en: string; fr: string }; value?: number | null }

type ColKey = 'code' | 'level' | 'text' | 'owner' | 'category' | 'priority' | 'method' | 'stage' | 'status'
  | 'parents' | 'objectives' | 'element' | 'threshold' | 'rationale' | 'source'
  | 'functions' | 'checked' | 'acceptance' | 'vmodel' | 'vevent'
// English text is the i18n key
const COLUMNS: { key: ColKey; label: string; width: string }[] = [
  { key: 'code', label: 'Code', width: '9.5rem' },
  { key: 'level', label: 'Level', width: '6.5rem' },
  { key: 'text', label: 'Requirement', width: 'minmax(16rem, 3fr)' },
  { key: 'owner', label: 'Owner', width: '9rem' },
  { key: 'category', label: 'Category', width: '7.5rem' },
  { key: 'priority', label: 'Priority', width: '4.5rem' },
  { key: 'method', label: 'Method', width: '4.5rem' },
  { key: 'stage', label: 'Stage', width: '4.5rem' },
  { key: 'status', label: 'Status', width: '6.5rem' },
  { key: 'parents', label: 'Parents', width: '9rem' },
  { key: 'objectives', label: 'Objectives', width: '6rem' },
  { key: 'element', label: 'Allocated to', width: '9rem' },
  { key: 'threshold', label: 'Threshold', width: '9rem' },
  { key: 'rationale', label: 'Rationale', width: 'minmax(10rem, 2fr)' },
  { key: 'source', label: 'Source', width: '9rem' },
  { key: 'functions', label: 'Functions', width: '7rem' },
  { key: 'checked', label: 'Checked against', width: '13rem' },
  { key: 'acceptance', label: 'Acceptance', width: 'minmax(10rem, 2fr)' },
  { key: 'vmodel', label: 'Model', width: '4.5rem' },
  { key: 'vevent', label: 'Event', width: '7rem' },
]
const DEFAULT_COLS: ColKey[] = ['code', 'level', 'text', 'owner', 'priority', 'method', 'stage', 'status', 'parents',
  'functions', 'checked']

function loadCols(): ColKey[] {
  try {
    const v = JSON.parse(localStorage.getItem('c2o.reqtable.cols') || 'null')
    if (Array.isArray(v) && v.length) return v.filter((k: string) => COLUMNS.some(c => c.key === k)) as ColKey[]
  } catch { /* storage unavailable */ }
  return DEFAULT_COLS
}

export function thresholdText(r: Pick<Req, 'threshold_op' | 'threshold_value' | 'threshold_unit'>): string {
  const op = r.threshold_op
  if (!op) return ''
  const v = r.threshold_value as any
  const unit = r.threshold_unit ? ` ${r.threshold_unit}` : ''
  if (op === 'in_range' && v && typeof v === 'object') return `${v.min ?? '…'} – ${v.max ?? '…'}${unit}`
  if (op === 'exists') return 'exists'
  return `${op} ${v ?? ''}${unit}`
}

async function send(url: string, method: string, body: unknown): Promise<any> {
  const r = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
  const data = await r.json().catch(() => null)
  if (!r.ok) throw new Error(typeof data?.detail === 'string' ? data.detail : JSON.stringify(data?.detail ?? data))
  return data
}

export function useStudyContext(studyId: string | null) {
  const elements = useQuery({
    queryKey: ['elements', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/elements`).then(r => r.json()),
    enabled: !!studyId, structuralSharing: false,
  })
  const study = useQuery({
    queryKey: ['study', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}`).then(r => r.json()),
    enabled: !!studyId,
  })
  const seats = useQuery({
    queryKey: ['seat-catalogue'],
    queryFn: () => fetch(`${API}/seats/catalogue`).then(r => (r.ok ? r.json() : { seats: [] })),
    staleTime: Infinity,
  })
  return { elements: (elements.data ?? []) as any[], study: study.data as any, seats: (seats.data?.seats ?? []) as any[] }
}

export function RequirementsTable({ studyId, requirements }: { studyId: string; requirements: Req[] }) {
  const { t, i18n } = useTranslation()
  const qc = useQueryClient()
  const { elements, study, seats } = useStudyContext(studyId)
  const fr = i18n.language.startsWith('fr')
  const seatLabel = (id?: string | null) => {
    if (!id) return ''
    const s = seats.find((x: any) => x.id === id)
    return s ? (fr ? s.label.fr : s.label.en) : id
  }
  const nameOf = useMemo(() => Object.fromEntries(elements.map((e: any) => [e.id, e.name])), [elements])
  const codeOf = useMemo(() => Object.fromEntries(requirements.map(r => [r.id, r.code])), [requirements])
  const { links, functions, bindings, catalogue } = useTraceData(studyId, requirements)
  const bindingOf = useMemo(() => Object.fromEntries(bindings.map(b => [b.requirement_id, b])), [bindings])
  const pathLabel = (path?: string | null) => {
    if (!path) return ''
    const c = catalogue.find(x => x.path === path)
    return c ? (fr ? c.label.fr : c.label.en) : path
  }
  const pending = bindings.filter(b => b.proposal && b.proposal.reason === 'budget_ref' && !b.accepted && !b.current_path)

  // filters
  const [q, setQ] = useState('')
  const [level, setLevel] = useState('')
  const [category, setCategory] = useState('')
  const [owner, setOwner] = useState('')
  const [status, setStatus] = useState('')
  const [stage, setStage] = useState('')
  const [priority, setPriority] = useState('')
  const [groupByLevel, setGroupByLevel] = useState(true)
  const [sort, setSort] = useState<{ key: ColKey; dir: 1 | -1 }>({ key: 'code', dir: 1 })
  const [cols, setCols] = useState<ColKey[]>(loadCols)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [editing, setEditing] = useState<string | null>(null)
  const [showImport, setShowImport] = useState(false)

  const categories = useMemo(() => Array.from(new Set(requirements.map(r => r.category).filter(Boolean))).sort() as string[], [requirements])
  const owners = useMemo(() => Array.from(new Set(requirements.map(r => r.responsible_position).filter(Boolean))).sort() as string[], [requirements])

  const sortVal = (r: Req, k: ColKey): string | number => {
    switch (k) {
      case 'level': return LEVEL_ORDER.indexOf(r.level)
      case 'priority': return r.priority ?? 9
      case 'owner': return seatLabel(r.responsible_position)
      case 'method': return r.verification_method ?? ''
      case 'stage': return STAGES.indexOf(r.verification_phase ?? '') + 1 || 99
      case 'parents': return (r.parent_ids ?? []).map(p => codeOf[p] ?? '').join(',')
      case 'objectives': return (r.objective_ids ?? []).join(',')
      case 'element': return nameOf[r.element_id ?? ''] ?? ''
      case 'threshold': return thresholdText(r)
      case 'source': return r.source_ref ?? ''
      case 'functions': return (links[r.id] ?? []).map(f => f.code ?? '').join(',')
      case 'checked': return r.threshold_param_path ?? (bindingOf[r.id]?.proposal ? '~' : '~~')
      case 'acceptance': return r.acceptance ?? ''
      case 'vmodel': return r.verification_model ?? ''
      case 'vevent': return r.verification_event ?? ''
      default: return String((r as any)[k === 'text' ? 'text' : k] ?? '')
    }
  }

  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase()
    const out = requirements.filter(r =>
      (!level || r.level === level) && (!category || r.category === category)
      && (!owner || r.responsible_position === owner) && (!status || r.status === status)
      && (!stage || r.verification_phase === stage) && (!priority || String(r.priority ?? '') === priority)
      && (!needle || `${r.code} ${r.text} ${r.rationale ?? ''} ${r.source_ref ?? ''}`.toLowerCase().includes(needle)))
    out.sort((a, b) => {
      if (groupByLevel) {
        const d = LEVEL_ORDER.indexOf(a.level) - LEVEL_ORDER.indexOf(b.level)
        if (d) return d
      }
      const x = sortVal(a, sort.key), y = sortVal(b, sort.key)
      return (x < y ? -1 : x > y ? 1 : 0) * sort.dir
    })
    return out
  }, [requirements, q, level, category, owner, status, stage, priority, groupByLevel, sort, codeOf, nameOf, seats])  // eslint-disable-line react-hooks/exhaustive-deps

  // flat list with group headers
  type Item = { kind: 'group'; level: string; n: number } | { kind: 'row'; r: Req }
  const items: Item[] = useMemo(() => {
    if (!groupByLevel) return rows.map(r => ({ kind: 'row' as const, r }))
    const out: Item[] = []
    let cur = ''
    for (const r of rows) {
      if (r.level !== cur) {
        cur = r.level
        out.push({ kind: 'group', level: cur, n: rows.filter(x => x.level === cur).length })
      }
      out.push({ kind: 'row', r })
    }
    return out
  }, [rows, groupByLevel])

  // virtual window
  const scroller = useRef<HTMLDivElement>(null)
  const [scrollTop, setScrollTop] = useState(0)
  const viewH = 520
  const first = Math.max(0, Math.floor(scrollTop / ROW_H) - OVERSCAN)
  const last = Math.min(items.length, Math.ceil((scrollTop + viewH) / ROW_H) + OVERSCAN)

  const shown = COLUMNS.filter(c => cols.includes(c.key))
  const grid = `2rem ${shown.map(c => c.width).join(' ')}`
  const setColumns = (next: ColKey[]) => {
    setCols(next)
    try { localStorage.setItem('c2o.reqtable.cols', JSON.stringify(next)) } catch { /* ignore */ }
  }
  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['requirements', studyId] })
    qc.invalidateQueries({ queryKey: ['requirement-bindings', studyId] })
    qc.invalidateQueries({ queryKey: ['function-links', studyId] })
    qc.invalidateQueries({ queryKey: ['function-coverage', studyId] })
  }

  const patch = async (id: string, body: Record<string, unknown>) => {
    try { await send(`${API}/requirements/${id}`, 'PATCH', body); invalidate() } catch (e: any) { void showAlert(e.message) }
  }

  const cell = (r: Req, k: ColKey): ReactNode => {
    switch (k) {
      case 'code': return (
        <button type="button" className="c2o-rt__code mono" onClick={() => setEditing(r.id)} title={t('Edit {{code}}', { code: r.code })}>
          {r.code}{r.open_item ? ' ⚑' : ''}
          {['stale', 'retired'].includes(r.external_ids?.allocation_sync?.state)
            ? <span className="c-caution" title={r.external_ids?.allocation_sync?.state === 'stale'
              ? t('The allocation changed: {{v}} proposed', { v: r.external_ids?.allocation_sync?.proposed_value })
              : t('Allocation retired')}> ⚠</span> : null}
        </button>)
      case 'level': return <Tag>{t(LEVEL_LABELS[r.level] ?? r.level)}</Tag>
      case 'text': return <span className="c2o-rt__clip" title={r.text}>{r.text}</span>
      case 'owner': return <span className="c2o-rt__clip">{seatLabel(r.responsible_position)}</span>
      case 'category': return <span className="c2o-rt__clip">{r.category ?? ''}</span>
      case 'priority': return <span className="mono">{r.priority ?? ''}</span>
      case 'method': return <span className="mono" title={(r.verification_methods ?? []).map(m => t(METHODS[m] ?? m)).join(', ')}>
        {(r.verification_methods?.length ? r.verification_methods : [r.verification_method]).filter(Boolean).join('+')}</span>
      case 'stage': return <span className="mono">{r.verification_phase ?? ''}</span>
      case 'status': return <StatusBadge status={REQ_STATUS[r.status] ?? 'neutral'}>{t(STATUS_LABELS[r.status] ?? r.status, { context: 'requirement' })}</StatusBadge>
      case 'parents': return <span className="mono c2o-rt__clip" title={(r.parent_ids ?? []).map(p => codeOf[p]).join(', ')}>
        {(r.parent_ids ?? []).map(p => codeOf[p] ?? '?').join(', ')}</span>
      case 'objectives': return <span className="mono">{(r.objective_ids ?? []).join(', ')}</span>
      case 'element': return <span className="c2o-rt__clip">{nameOf[r.element_id ?? ''] ?? ''}</span>
      case 'threshold': return <span className="mono c2o-rt__clip">{thresholdText(r)}</span>
      case 'rationale': return <InlineText value={r.rationale ?? ''} label={t('Rationale of {{code}}', { code: r.code })}
        onSave={v => patch(r.id, { rationale: v || null })} />
      case 'source': return <span className="c2o-rt__clip" title={r.source_ref ?? ''}>{r.source_ref ?? ''}</span>
      case 'functions': {
        const fs = links[r.id] ?? []
        return <button type="button" className="c2o-rt__inline mono c2o-rt__clip" onClick={() => setEditing(r.id)}
          title={fs.map(f => `${f.code ?? ''} ${f.name ?? ''}`).join('\n') || t('No function: pick one in the editor')}>
          {fs.map(f => f.code ?? f.name).join(', ') || <span className="c-caution">{t('none')}</span>}</button>
      }
      case 'checked': {
        const b = bindingOf[r.id]
        if (r.threshold_param_path) {
          const st = b?.status === 'pass' ? 'ok' : b?.status === 'fail' ? 'alarm' : 'neutral'
          return <span className="row gap-1 ai-c c2o-rt__clip" title={r.threshold_param_path}>
            <StatusBadge status={st as Status}>{b?.achieved != null ? String(Math.round(b.achieved * 1000) / 1000) : '–'}</StatusBadge>
            <span className="c2o-rt__clip t-12">{pathLabel(r.threshold_param_path)}</span></span>
        }
        if (b?.proposal) return (
          <Button size="sm" onClick={() => void bind(r.id, b.proposal!.path)} title={b.proposal.path}>
            {t('Accept: {{figure}}', { figure: pathLabel(b.proposal.path) })}</Button>)
        return <span className="c-3 t-12">{r.budget_ref ? t('no figure yet') : ''}</span>
      }
      case 'acceptance': return <InlineText value={r.acceptance ?? ''} label={t('Acceptance of {{code}}', { code: r.code })}
        onSave={v => patch(r.id, { acceptance: v || null })} />
      case 'vmodel': return <span className="mono">{r.verification_model ?? ''}</span>
      case 'vevent': return <span className="mono c2o-rt__clip">{r.verification_event ?? ''}</span>
    }
  }
  const bind = async (id: string, path: string | null) => {
    try { await send(`${API}/requirements/${id}/binding`, 'PUT', { path }); invalidate() } catch (e: any) { void showAlert(e.message) }
  }
  const acceptAll = async () => {
    try {
      const res = await send(`${API}/studies/${studyId}/requirements/bindings/accept`, 'POST', {})
      void showAlert(t('{{n}} threshold(s) now checked against a computed figure.', { n: res.accepted }))
      invalidate()
    } catch (e: any) { void showAlert(e.message) }
  }

  const allVisibleSelected = rows.length > 0 && rows.every(r => selected.has(r.id))
  const toggleAll = () => setSelected(allVisibleSelected ? new Set() : new Set(rows.map(r => r.id)))
  const editReq = requirements.find(r => r.id === editing) ?? null

  return (
    <div className="c2o-rt">
      <div className="c2o-rt__filters" role="search" aria-label={t('Filter requirements')}>
        <Input dense value={q} onChange={e => setQ(e.target.value)} placeholder={t('Search code, text, rationale, source')}
          aria-label={t('Search requirements')} className="c2o-rt__search" />
        <Select dense value={level} onChange={e => setLevel(e.target.value)} aria-label={t('Level')}>
          <option value="">{t('All levels')}</option>
          {LEVEL_ORDER.map(l => <option key={l} value={l}>{t(LEVEL_LABELS[l])}</option>)}
        </Select>
        <Select dense value={category} onChange={e => setCategory(e.target.value)} aria-label={t('Category')}>
          <option value="">{t('All categories')}</option>
          {categories.map(c => <option key={c} value={c}>{c}</option>)}
        </Select>
        <Select dense value={owner} onChange={e => setOwner(e.target.value)} aria-label={t('Owner')}>
          <option value="">{t('All owners')}</option>
          {owners.map(o => <option key={o} value={o}>{seatLabel(o)}</option>)}
        </Select>
        <Select dense value={status} onChange={e => setStatus(e.target.value)} aria-label={t('Status')}>
          <option value="">{t('All statuses')}</option>
          {Object.entries(STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{t(v, { context: 'requirement' })}</option>)}
        </Select>
        <Select dense value={stage} onChange={e => setStage(e.target.value)} aria-label={t('Verification stage')}>
          <option value="">{t('All stages')}</option>
          {STAGES.map(s => <option key={s} value={s}>{STAGE_LABELS[s] ? `${s} (${t(STAGE_LABELS[s])})` : s}</option>)}
        </Select>
        <Select dense value={priority} onChange={e => setPriority(e.target.value)} aria-label={t('Priority')}>
          <option value="">{t('All priorities')}</option>
          {Object.entries(PRIORITY_LABELS).map(([k, v]) => <option key={k} value={k}>{t(v)}</option>)}
        </Select>
        <label className="c2o-check t-12">
          <input type="checkbox" checked={groupByLevel} onChange={e => setGroupByLevel(e.target.checked)} /> {t('Group by level')}
        </label>
        <span className="t-12 c-2" role="status">{t('{{shown}} of {{total}} requirements', { shown: rows.length, total: requirements.length })}</span>
        <Button size="sm" onClick={() => setShowImport(v => !v)}>{t('Import requirements')}</Button>
        {pending.length > 0 && (
          <Button size="sm" variant="primary" onClick={() => void acceptAll()}
            title={t('Bind each budget threshold to the figure the tool computes for it')}>
            {t('Accept {{n}} proposed bindings', { n: pending.length })}</Button>)}
      </div>

      <Disclosure summary={t('Columns')} meta={String(shown.length)}>
        <div className="c2o-rt__cols">
          {COLUMNS.map(c => (
            <label key={c.key} className="c2o-check t-12">
              <input type="checkbox" checked={cols.includes(c.key)} disabled={c.key === 'code'}
                onChange={e => setColumns(e.target.checked ? COLUMNS.filter(x => cols.includes(x.key) || x.key === c.key).map(x => x.key)
                  : cols.filter(k => k !== c.key))} /> {t(c.label)}
            </label>
          ))}
        </div>
      </Disclosure>

      {showImport && <ImportRequirements studyId={studyId} onDone={() => { setShowImport(false); invalidate() }} />}

      {selected.size > 0 && <BulkEdit studyId={studyId} ids={Array.from(selected)} seats={seats} seatLabel={seatLabel}
        onDone={() => { setSelected(new Set()); invalidate() }} />}

      <div className="c2o-rt__table" role="table" aria-label={t('Requirements')} aria-rowcount={rows.length + 1}>
        <div className="c2o-rt__row c2o-rt__head" role="row" style={{ gridTemplateColumns: grid }}>
          <span role="columnheader">
            <input type="checkbox" checked={allVisibleSelected} onChange={toggleAll} aria-label={t('Select all shown')} />
          </span>
          {shown.map(c => (
            <span key={c.key} role="columnheader"
              aria-sort={sort.key === c.key ? (sort.dir === 1 ? 'ascending' : 'descending') : 'none'}>
              <button type="button" className="c2o-rt__sort"
                onClick={() => setSort(s => ({ key: c.key, dir: s.key === c.key ? (s.dir === 1 ? -1 : 1) : 1 }))}>
                {t(c.label)}{sort.key === c.key ? (sort.dir === 1 ? ' ▲' : ' ▼') : ''}
              </button>
            </span>
          ))}
        </div>
        <div className="c2o-rt__scroll" ref={scroller} style={{ height: Math.min(viewH, Math.max(ROW_H * 3, items.length * ROW_H)) }}
          onScroll={e => setScrollTop((e.target as HTMLDivElement).scrollTop)}>
          <div style={{ height: items.length * ROW_H, position: 'relative' }}>
            {items.slice(first, last).map((it, k) => {
              const top = (first + k) * ROW_H
              if (it.kind === 'group') return (
                <div key={`g-${it.level}`} className="c2o-rt__group" style={{ top, height: ROW_H }} role="row">
                  <span role="cell">{t(LEVEL_LABELS[it.level] ?? it.level)} · {it.n}</span>
                </div>)
              const r = it.r
              return (
                <div key={r.id} className={`c2o-rt__row${selected.has(r.id) ? ' is-selected' : ''}`} role="row"
                  style={{ top, height: ROW_H, gridTemplateColumns: grid, position: 'absolute', left: 0, right: 0 }}>
                  <span role="cell">
                    <input type="checkbox" checked={selected.has(r.id)} aria-label={t('Select {{code}}', { code: r.code })}
                      onChange={e => setSelected(prev => { const n = new Set(prev); if (e.target.checked) n.add(r.id); else n.delete(r.id); return n })} />
                  </span>
                  {shown.map(c => <span key={c.key} role="cell" className="c2o-rt__cell">{cell(r, c.key)}</span>)}
                </div>)
            })}
          </div>
        </div>
        {rows.length === 0 && <p className="t-13 c-2 p-2 m-0">{t('No requirement matches these filters.')}</p>}
      </div>

      {editReq && <RequirementEditor key={editReq.id} studyId={studyId} req={editReq} requirements={requirements}
        elements={elements} study={study} seats={seats} seatLabel={seatLabel}
        fnLinks={links[editReq.id] ?? []} functions={functions} binding={bindingOf[editReq.id]} catalogue={catalogue}
        pathLabel={pathLabel}
        onClose={() => setEditing(null)} onSaved={() => { setEditing(null); invalidate() }} />}
    </div>
  )
}

function InlineText({ value, label, onSave }: { value: string; label: string; onSave: (v: string) => void }) {
  const [v, setV] = useState<string | null>(null)
  if (v === null) return (
    <button type="button" className="c2o-rt__inline c2o-rt__clip" onClick={() => setV(value)} aria-label={label} title={value}>
      {value || '…'}
    </button>)
  return (
    <input className="c2o-input c2o-input--dense c2o-rt__inlinein" autoFocus value={v} aria-label={label}
      onChange={e => setV(e.target.value)}
      onBlur={() => { if (v !== value) onSave(v); setV(null) }}
      onKeyDown={e => { if (e.key === 'Enter') (e.target as HTMLInputElement).blur(); if (e.key === 'Escape') setV(null) }} />)
}

function BulkEdit({ studyId, ids, seats, seatLabel, onDone }: {
  studyId: string; ids: string[]; seats: any[]; seatLabel: (id?: string | null) => string; onDone: () => void
}) {
  const { t } = useTranslation()
  const [field, setField] = useState('priority')
  const [value, setValue] = useState('')
  const [busy, setBusy] = useState(false)
  const options: Record<string, [string, string][]> = {
    priority: Object.entries(PRIORITY_LABELS).map(([k, v]) => [k, t(v)]),
    verification_phase: STAGES.map(s => [s, s]),
    status: Object.entries(STATUS_LABELS).map(([k, v]) => [k, t(v, { context: 'requirement' })]),
    responsible_position: seats.map((s: any) => [s.id, seatLabel(s.id)]),
    verification_method: Object.entries(METHODS).map(([k, v]) => [k, t(v)]),
  }
  const apply = async () => {
    setBusy(true)
    try {
      await send(`${API}/requirements/bulk`, 'PATCH', { study_id: studyId, ids, changes: { [field]: value === '' ? null : value } })
      onDone()
    } catch (e: any) { void showAlert(e.message) } finally { setBusy(false) }
  }
  return (
    <form className="c2o-rt__bulk" aria-label={t('Bulk edit')} onSubmit={e => { e.preventDefault(); void apply() }}>
      <span className="t-12">{t('{{count}} selected', { count: ids.length })}</span>
      <Select dense value={field} onChange={e => { setField(e.target.value); setValue('') }} aria-label={t('Field')}>
        <option value="priority">{t('Priority')}</option>
        <option value="category">{t('Category')}</option>
        <option value="responsible_position">{t('Owner')}</option>
        <option value="verification_phase">{t('Verification stage')}</option>
        <option value="verification_method">{t('Verification method')}</option>
        <option value="status">{t('Status')}</option>
      </Select>
      {options[field]
        ? <Select dense value={value} onChange={e => setValue(e.target.value)} aria-label={t('New value')}>
          <option value="">{t('none')}</option>
          {options[field].map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </Select>
        : <Input dense value={value} onChange={e => setValue(e.target.value)} aria-label={t('New value')} />}
      <Button type="submit" size="sm" variant="primary" busy={busy}>{t('Apply to selection')}</Button>
    </form>
  )
}

// ─── Editor ───

export function RequirementEditor({ studyId, req, requirements, elements, study, seats, seatLabel, onClose, onSaved,
  fnLinks = [], functions = [], binding, catalogue = [], pathLabel = (p?: string | null) => p ?? '' }: {
  studyId: string; req: Req; requirements: Req[]; elements: any[]; study: any; seats: any[]
  seatLabel: (id?: string | null) => string; onClose: () => void; onSaved: () => void
  fnLinks?: FnLink[]; functions?: FnLink[]; binding?: BindingRow; catalogue?: CatalogueItem[]
  pathLabel?: (p?: string | null) => string
}) {
  const { t } = useTranslation()
  const [fnIds, setFnIds] = useState<string[]>(fnLinks.map(f => f.id))
  const [fnPick, setFnPick] = useState('')
  const [path, setPath] = useState<string>(req.threshold_param_path ?? '')
  const flag = req.external_ids?.allocation_sync
  const v0 = req.threshold_value as any
  const [f, setF] = useState({
    code: req.code, level: req.level, text: req.text, rationale: req.rationale ?? '', req_type: req.req_type ?? '',
    category: req.category ?? '', element_id: req.element_id ?? '', responsible_position: req.responsible_position ?? '',
    priority: req.priority != null ? String(req.priority) : '', source_ref: req.source_ref ?? '',
    verification_methods: (req.verification_methods?.length ? req.verification_methods : [req.verification_method]).filter(Boolean) as string[],
    verification_phase: req.verification_phase ?? '', verification_level: req.verification_level ?? '',
    threshold_op: req.threshold_op ?? '', threshold_unit: req.threshold_unit ?? '',
    tv: req.threshold_op === 'in_range' ? '' : (v0 != null && typeof v0 !== 'object' ? String(v0) : ''),
    tmin: v0 && typeof v0 === 'object' ? String(v0.min ?? '') : '', tmax: v0 && typeof v0 === 'object' ? String(v0.max ?? '') : '',
    parent_ids: req.parent_ids ?? [], objective_ids: req.objective_ids ?? [],
    acceptance: req.acceptance ?? '', verification_model: req.verification_model ?? '', verification_event: req.verification_event ?? '',
    interface_id: req.ir_json?.interface_id ?? '', exchange_item_ids: (req.ir_json?.exchange_item_ids ?? []) as string[],
  })
  const [busy, setBusy] = useState(false)
  const set = (k: string, v: unknown) => setF(p => ({ ...p, [k]: v }))
  const objectives: string[] = useMemo(() => {
    const ids = (study?.mission_need?.objectives ?? []).map((o: any) => o.id)
    for (const r of requirements) for (const o of r.objective_ids ?? []) if (!ids.includes(o)) ids.push(o)
    return ids
  }, [study, requirements])
  const isIR = req.level === 'interface'
  const ifaces = useQuery({
    queryKey: ['interfaces', studyId, 'accepted-for-ir'],
    queryFn: () => fetch(`${API}/studies/${studyId}/interfaces`).then(r => r.json()), enabled: isIR,
  })
  const items = useQuery({
    queryKey: ['exchange-items', studyId], queryFn: () => fetch(`${API}/studies/${studyId}/exchange-items`).then(r => r.json()),
    enabled: isIR,
  })
  const nameOf = Object.fromEntries(elements.map((e: any) => [e.id, e.name]))

  const value = (): unknown => {
    const num = (s: string) => (s.trim() === '' ? null : (isNaN(Number(s.replace(',', '.'))) ? s.trim() : Number(s.replace(',', '.'))))
    if (!f.threshold_op || f.threshold_op === 'exists') return null
    if (f.threshold_op === 'in_range') return { min: num(f.tmin), max: num(f.tmax) }
    if (f.threshold_op === 'before' || f.threshold_op === 'after') return f.tv.trim() || null
    return num(f.tv)
  }
  const save = async () => {
    setBusy(true)
    try {
      const body: Record<string, unknown> = {
        code: f.code.trim(), level: f.level, text: f.text, rationale: f.rationale || null, req_type: f.req_type || null,
        category: f.category || null, element_id: f.element_id || null, responsible_position: f.responsible_position || null,
        priority: f.priority || null, source_ref: f.source_ref || null, verification_methods: f.verification_methods,
        verification_method: f.verification_methods[0] ?? null, verification_phase: f.verification_phase || null,
        verification_level: f.verification_level || null, threshold_op: f.threshold_op || null,
        threshold_value: value(), threshold_unit: f.threshold_unit || null,
        parent_ids: f.parent_ids, objective_ids: f.objective_ids,
        acceptance: f.acceptance || null, verification_model: f.verification_model || null,
        verification_event: f.verification_event || null,
      }
      if (isIR) { body.interface_id = f.interface_id || null; body.exchange_item_ids = f.exchange_item_ids }
      await send(`${API}/requirements/${req.id}`, 'PATCH', body)
      const before = fnLinks.map(x => x.id)
      if (fnIds.length !== before.length || fnIds.some(x => !before.includes(x))) {
        await send(`${API}/requirements/${req.id}/functions`, 'PUT', { function_ids: fnIds })
      }
      if ((path || null) !== (req.threshold_param_path ?? null)) {
        await send(`${API}/requirements/${req.id}/binding`, 'PUT', { path: path || null })
      }
      onSaved()
    } catch (e: any) { void showAlert(e.message) } finally { setBusy(false) }
  }
  const resolveFlag = async (action: string) => {
    try { await send(`${API}/requirements/${req.id}/allocation-sync`, 'POST', { action }); onSaved() }
    catch (e: any) { void showAlert(e.message) }
  }
  const others = requirements.filter(r => r.id !== req.id && LEVEL_ORDER.indexOf(r.level) <= LEVEL_ORDER.indexOf(req.level === 'interface' ? 'subsystem' : req.level))
  const toggle = (k: 'verification_methods' | 'objective_ids' | 'exchange_item_ids', id: string) =>
    set(k, (f[k] as string[]).includes(id) ? (f[k] as string[]).filter(x => x !== id) : [...(f[k] as string[]), id])
  const [parentPick, setParentPick] = useState('')

  return (
    <form className="c2o-rt__editor" aria-label={t('Edit {{code}}', { code: req.code })} onSubmit={e => { e.preventDefault(); void save() }}>
      <div className="c2o-rt__grid">
        <Field label={t('Code')}><Input dense className="mono" value={f.code} onChange={e => set('code', e.target.value)} maxLength={32} /></Field>
        <Field label={t('Level')}>
          <Select dense value={f.level} onChange={e => set('level', e.target.value)}>
            {LEVEL_ORDER.map(l => <option key={l} value={l}>{t(LEVEL_LABELS[l])}</option>)}
          </Select>
        </Field>
        <Field label={t('Type')}>
          <Select dense value={f.req_type} onChange={e => set('req_type', e.target.value)}>
            <option value="">{t('none')}</option>
            {TYPES.map(x => <option key={x} value={x}>{t(TYPE_LABELS[x])}</option>)}
          </Select>
        </Field>
        <Field label={t('Priority')}>
          <Select dense value={f.priority} onChange={e => set('priority', e.target.value)}>
            <option value="">{t('none')}</option>
            {Object.entries(PRIORITY_LABELS).map(([k, v]) => <option key={k} value={k}>{t(v)}</option>)}
          </Select>
        </Field>
        <Field label={t('Category')}><Input dense value={f.category} onChange={e => set('category', e.target.value)} /></Field>
        <Field label={t('Owner')}>
          <Select dense value={f.responsible_position} onChange={e => set('responsible_position', e.target.value)}>
            <option value="">{t('none')}</option>
            {seats.filter((s: any) => !['observer', 'instructor'].includes(s.kind)).map((s: any) => <option key={s.id} value={s.id}>{seatLabel(s.id)}</option>)}
          </Select>
        </Field>
        <Field label={t('Allocated to')}>
          <Select dense value={f.element_id} onChange={e => set('element_id', e.target.value)}>
            <option value="">{t('Not allocated')}</option>
            {treeOptions(elements)}
          </Select>
        </Field>
      </div>
      <Field label={t('Requirement text')}><Textarea rows={2} value={f.text} onChange={e => set('text', e.target.value)} /></Field>
      <Field label={t('Rationale')}><Textarea rows={2} value={f.rationale} onChange={e => set('rationale', e.target.value)} /></Field>
      <div className="c2o-rt__grid">
        <Field label={t('Operator')}>
          <Select dense value={f.threshold_op} onChange={e => set('threshold_op', e.target.value)}>
            <option value="">{t('no threshold')}</option>
            {OPS.map(o => <option key={o} value={o}>{OP_LABELS[o] ? t(OP_LABELS[o]) : o}</option>)}
          </Select>
        </Field>
        {f.threshold_op === 'in_range' ? <>
          <Field label={t('Minimum')}><Input dense className="mono" value={f.tmin} onChange={e => set('tmin', e.target.value)} inputMode="decimal" /></Field>
          <Field label={t('Maximum')}><Input dense className="mono" value={f.tmax} onChange={e => set('tmax', e.target.value)} inputMode="decimal" /></Field>
        </> : f.threshold_op && f.threshold_op !== 'exists' ? (
          <Field label={f.threshold_op === 'before' || f.threshold_op === 'after' ? t('Date') : t('Threshold')}>
            <Input dense className="mono" type={f.threshold_op === 'before' || f.threshold_op === 'after' ? 'date' : 'text'}
              value={f.tv} onChange={e => set('tv', e.target.value)} />
          </Field>) : null}
        <Field label={t('Unit')}><Input dense value={f.threshold_unit} onChange={e => set('threshold_unit', e.target.value)} /></Field>
        <Field label={t('Verification stage')}>
          <Select dense value={f.verification_phase} onChange={e => set('verification_phase', e.target.value)}>
            <option value="">{t('none')}</option>
            {STAGES.map(s => <option key={s} value={s}>{STAGE_LABELS[s] ? `${s} (${t(STAGE_LABELS[s])})` : s}</option>)}
          </Select>
        </Field>
        <Field label={t('Verification level')}>
          <Select dense value={f.verification_level} onChange={e => set('verification_level', e.target.value)}>
            <option value="">{t('none')}</option>
            {VER_LEVELS.map(s => <option key={s} value={s}>{t(LEVEL_LABELS[s] ?? 'Unit')}</option>)}
          </Select>
        </Field>
      </div>
      <fieldset className="c2o-rt__set">
        <legend className="t-12">{t('Verification methods (the first is the main one)')}</legend>
        {Object.entries(METHODS).map(([k, v]) => (
          <label key={k} className="c2o-check t-12">
            <input type="checkbox" checked={f.verification_methods.includes(k)} onChange={() => toggle('verification_methods', k)} /> {t(v)}
          </label>))}
      </fieldset>
      <fieldset className="c2o-rt__set">
        <legend className="t-12">{t('Parents (the first is the main parent)')}</legend>
        {f.parent_ids.map(p => (
          <span key={p} className="c2o-rt__chip mono">{requirements.find(r => r.id === p)?.code ?? p}
            <button type="button" aria-label={t('Remove parent {{code}}', { code: requirements.find(r => r.id === p)?.code ?? p })}
              onClick={() => set('parent_ids', f.parent_ids.filter(x => x !== p))}>×</button></span>))}
        <Select dense value={parentPick} aria-label={t('Add a parent')}
          onChange={e => { const id = e.target.value; setParentPick(''); if (id && !f.parent_ids.includes(id)) set('parent_ids', [...f.parent_ids, id]) }}>
          <option value="">{t('+ parent…')}</option>
          {others.map(r => <option key={r.id} value={r.id}>{r.code} — {r.text.slice(0, 60)}</option>)}
        </Select>
      </fieldset>
      <fieldset className="c2o-rt__set">
        <legend className="t-12">{t('Objectives')}</legend>
        {objectives.length === 0 && <span className="t-12 c-3">{t('No objectives in the mission need yet.')}</span>}
        {objectives.map(o => (
          <label key={o} className="c2o-check t-12 mono">
            <input type="checkbox" checked={f.objective_ids.includes(o)} onChange={() => toggle('objective_ids', o)} /> {o}
          </label>))}
      </fieldset>
      {isIR && (
        <fieldset className="c2o-rt__set">
          <legend className="t-12">{t('Interface and ICD row')}</legend>
          <Select dense value={f.interface_id} onChange={e => set('interface_id', e.target.value)} aria-label={t('Interface')}>
            <option value="">{t('No interface')}</option>
            {((ifaces.data ?? []) as any[]).filter(i => i.status !== 'rejected').map(i => (
              <option key={i.id} value={i.id}>{i.name || `${nameOf[i.from_element_id] ?? '?'} → ${nameOf[i.to_element_id] ?? '?'}`} ({i.type ?? i.interface_type})</option>))}
          </Select>
          {((items.data ?? []) as any[]).map(x => (
            <label key={x.id} className="c2o-check t-12">
              <input type="checkbox" checked={f.exchange_item_ids.includes(x.id)} onChange={() => toggle('exchange_item_ids', x.id)} /> {x.name}
            </label>))}
        </fieldset>)}
      <Field label={t('Source')}><Input dense value={f.source_ref} onChange={e => set('source_ref', e.target.value)} /></Field>
      <Field label={t('Acceptance criterion')}>
        <Textarea rows={2} value={f.acceptance} onChange={e => set('acceptance', e.target.value)} />
      </Field>
      <div className="c2o-rt__grid">
        <Field label={t('Verification model')}><Input dense className="mono" value={f.verification_model} maxLength={16}
          onChange={e => set('verification_model', e.target.value)} /></Field>
        <Field label={t('Verification event')}><Input dense className="mono" value={f.verification_event} maxLength={32}
          onChange={e => set('verification_event', e.target.value)} /></Field>
        <Field label={t('Checked against')}>
          <Select dense value={path} onChange={e => setPath(e.target.value)}>
            <option value="">{t('not checked against a figure')}</option>
            {binding?.proposal && <option value={binding.proposal.path}>{t('Proposed: {{figure}}', { figure: pathLabel(binding.proposal.path) })}</option>}
            {catalogue.filter(c => c.path !== binding?.proposal?.path).map(c => (
              <option key={c.path} value={c.path}>{pathLabel(c.path)}{c.value != null ? ` (${Math.round(c.value * 1000) / 1000} ${c.unit})` : ''}</option>))}
          </Select>
        </Field>
      </div>
      <fieldset className="c2o-rt__set">
        <legend className="t-12">{t('Functions and processes this requirement serves')}</legend>
        {fnIds.length === 0 && <span className="t-12 c-caution">{t('No function yet: every requirement should serve a function or an enabling process.')}</span>}
        {fnIds.map(id => {
          const fn = functions.find(x => x.id === id) ?? fnLinks.find(x => x.id === id)
          return <span key={id} className="c2o-rt__chip mono">{fn?.code ?? fn?.name ?? id}
            <button type="button" aria-label={t('Remove function {{code}}', { code: fn?.code ?? fn?.name ?? id })}
              onClick={() => setFnIds(fnIds.filter(x => x !== id))}>×</button></span>
        })}
        <Select dense value={fnPick} aria-label={t('Add a function')}
          onChange={e => { const id = e.target.value; setFnPick(''); if (id && !fnIds.includes(id)) setFnIds([...fnIds, id]) }}>
          <option value="">{t('+ function…')}</option>
          {functions.map(x => <option key={x.id} value={x.id}>{x.code ? `${x.code} — ` : ''}{x.name}{x.kind === 'process' ? ` (${t('enabling process')})` : ''}</option>)}
        </Select>
      </fieldset>
      {flag && ['stale', 'retired'].includes(flag.state) && (
        <div className="card bl-caution t-12" role="status">
          {flag.state === 'stale'
            ? t('The allocation ledger now says {{v}}; this requirement still says {{old}}.', { v: flag.proposed_value, old: flag.row_value })
            : t('Its allocation line was deleted from the ledger (allocation retired).')}
          <span className="row gap-2 mt-1">
            <Button size="sm" variant="primary" onClick={() => void resolveFlag('accept')}>
              {flag.state === 'stale' ? t('Take the ledger value') : t('Retire this requirement')}</Button>
            <Button size="sm" onClick={() => void resolveFlag('dismiss')}>{t('Keep as it is')}</Button>
          </span>
        </div>)}
      <span className="row gap-2">
        <Button type="submit" variant="primary" size="sm" busy={busy}>{t('Save')}</Button>
        <Button size="sm" onClick={onClose}>{t('Cancel')}</Button>
      </span>
    </form>
  )
}

/** The function links and the threshold bindings of the study (wave 3, 3.R1 and 3.R2). */
export function useTraceData(studyId: string | null, requirements: Req[]) {
  const n = requirements.length
  const fl = useQuery({
    queryKey: ['function-links', studyId, n],
    queryFn: () => fetch(`${API}/studies/${studyId}/requirements/function-links`).then(r => (r.ok ? r.json() : { links: {}, functions: [] })),
    enabled: !!studyId, structuralSharing: false,
  })
  const bd = useQuery({
    queryKey: ['requirement-bindings', studyId, n],
    queryFn: () => fetch(`${API}/studies/${studyId}/requirements/bindings`).then(r => (r.ok ? r.json() : { rows: [], catalogue: [] })),
    enabled: !!studyId, structuralSharing: false,
  })
  return {
    links: (fl.data?.links ?? {}) as Record<string, FnLink[]>, functions: (fl.data?.functions ?? []) as FnLink[],
    bindings: (bd.data?.rows ?? []) as BindingRow[], catalogue: (bd.data?.catalogue ?? []) as CatalogueItem[],
  }
}

/** Every element of the product tree, indented by depth (allocation picker over the whole tree). */
export function treeOptions(elements: any[]): ReactNode[] {
  const kids: Record<string, any[]> = {}
  for (const e of elements) {
    if (['mode', 'logical'].includes(e.element_type)) continue
    const p = e.parent_id && elements.some(x => x.id === e.parent_id) ? e.parent_id : ''
    ;(kids[p] ??= []).push(e)
  }
  const out: ReactNode[] = []
  const walk = (pid: string, depth: number) => {
    for (const e of (kids[pid] ?? []).sort((a, b) => String(a.name).localeCompare(String(b.name)))) {
      out.push(<option key={e.id} value={e.id}>{'  '.repeat(depth)}{e.name}</option>)
      if (depth < 6) walk(e.id, depth + 1)
    }
  }
  walk('', 0)
  return out
}

// ─── Import ───

function ImportRequirements({ studyId, onDone }: { studyId: string; onDone: () => void }) {
  const { t } = useTranslation()
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<any>(null)
  const [busy, setBusy] = useState(false)
  const fmt = (name: string) => name.toLowerCase().endsWith('.csv') ? 'csv' : name.toLowerCase().endsWith('.json') ? 'json' : 'yaml'
  const isReqif = (name: string) => /\.reqif(z)?$/i.test(name)

  const run = async (dry: boolean) => {
    if (!file) return
    setBusy(true)
    try {
      if (isReqif(file.name)) {
        const fd = new FormData()
        fd.append('file', file)
        const r = await fetch(`${API}/studies/${studyId}/import/reqif`, { method: 'POST', body: fd })
        const data = await r.json()
        if (!r.ok) throw new Error(data?.detail ?? r.statusText)
        void showAlert(t('ReqIF import: {{created}} created, {{updated}} updated.', { created: data.created, updated: data.updated }))
        onDone()
        return
      }
      const content = await file.text()
      const r = await fetch(`${API}/studies/${studyId}/requirements/import`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, format: fmt(file.name), dry_run: dry, study_id: studyId }),
      })
      const data = await r.json()
      if (!r.ok && typeof data?.detail === 'string') throw new Error(data.detail)
      const rep = r.ok ? data : data.detail
      if (dry || !r.ok) setPreview(rep)
      else {
        void showAlert(t('{{created}} created, {{updated}} updated, {{unchanged}} unchanged.',
          { created: rep.created, updated: rep.updated, unchanged: rep.unchanged }))
        onDone()
      }
    } catch (e: any) { void showAlert(e.message) } finally { setBusy(false) }
  }
  return (
    <section className="c2o-rt__import" aria-label={t('Import requirements')}>
      <p className="t-12 c-2 m-0">{t('A requirements file (YAML, JSON or CSV with the baseline columns) or a ReqIF file. Parents are given by code; rows are matched by code, so importing again updates them.')}</p>
      <span className="row gap-2 ai-c">
        <input type="file" accept=".yaml,.yml,.json,.csv,.reqif,.reqifz" aria-label={t('Requirements file')}
          onChange={e => { setFile(e.target.files?.[0] ?? null); setPreview(null) }} />
        <Button size="sm" onClick={() => run(true)} busy={busy} disabledReason={!file ? t('Choose a file first') : undefined}>
          {file && isReqif(file.name) ? t('Import') : t('Preview')}
        </Button>
        {preview?.ok && <Button size="sm" variant="primary" onClick={() => run(false)} busy={busy}>{t('Import')}</Button>}
      </span>
      {preview && (
        <div className="t-12" role="status">
          <p className="m-0">{t('{{created}} new, {{updated}} changed, {{unchanged}} unchanged; {{errors}} error(s).',
            { created: preview.created, updated: preview.updated, unchanged: preview.unchanged, errors: preview.errors?.length ?? 0 })}</p>
          {(preview.warnings ?? []).map((w: string, i: number) => <p key={i} className="m-0 c-caution">{w}</p>)}
          {(preview.errors ?? []).length > 0 && (
            <ul className="c2o-rt__errors">
              {preview.errors.map((e: any, i: number) => <li key={i}><span className="mono">{e.code || `#${e.row}`}</span> {e.field}: {e.message}</li>)}
            </ul>)}
        </div>)}
    </section>
  )
}
