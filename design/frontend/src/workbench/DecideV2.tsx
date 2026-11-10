/**
 * Decide, wave 3 (agent D): the v2 trade model and the registers around decisions.
 *
 *   TradeGateSummary       trades by review gate and level (PI ruling: orbit and launch at MDR,
 *                          data architecture at SRR, architecture trades at PDR)
 *   AbsoluteScaleMatrix    absolute 1–5 scores per criterion with the scale, source (MOE or
 *                          requirement), must-screen and the weights' lock (3.D3)
 *   TradeSensitivityPm20   each weight ×0.8 and ×1.2, robustness and break-even (3.D3)
 *   RecordAsTradeButton    "Record as trade" from the orbit and ground tools (3.D3)
 *   OpenItemsPanel         the open-item register, by the gate each item blocks (3.D4)
 *   ChangeControlCard      the change-control flow of ECP / CR: impact, affected seats agree,
 *                          board decision, new baseline (3.D7, PI addendum)
 */
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useSeatStore } from '../seats/api'
import { showAlert } from '../components/ui/Dialog'
import { Button, Disclosure, Input, Note, Select, StatusBadge, Tag, Textarea, type Status } from '../components/ui'
import { BASELINE_LABEL, OpenItemList, type OpenItem } from './PhasePanel'

const API = '/api'

// English text is the i18n key
export const LEVEL_LABEL: Record<string, string> = {
  mission: 'Mission', system: 'System', architecture: 'Architecture', subsystem: 'Subsystem', equipment: 'Equipment',
}
export const LEVELS = ['mission', 'system', 'architecture', 'subsystem', 'equipment'] as const
export const GATES = ['mdr', 'prr', 'srr', 'pdr', 'cdr'] as const

export interface Pm20Row { criterion: string; factor: number; winner: string; winner_total: number; margin_to_next: number | null }
export interface TradeEvaluationV2 {
  method?: string
  totals: Array<{ option: string; datum: boolean; weighted: number; screened?: boolean; screen_reason?: string; acceptable: boolean }>
  weights: Record<string, number>
  winner: string | null
  runner_up?: string | null
  margin?: number | null
  sensitivity_pm20?: Pm20Row[]
  robust_pm20?: boolean
  flips_at?: string[]
  break_even?: Array<{ criterion: string; multiplier: number }>
  issues?: string[]
}

export interface TradeStateV2 {
  criteria: string[]
  options: string[]
  datum: number
  scores: Record<string, Record<string, number>>
  method?: 'pugh_weighted' | 'absolute_scale'
  level?: string
  gate?: string
  option_labels?: Record<string, string>
  must?: string[]
  screened?: Record<string, string>
  criteria_meta?: Record<string, { source?: string[]; scale?: string; rationale?: string }>
  evidence_by_criterion?: Record<string, string>
  weights_locked_at?: string
  post_hoc_weights?: boolean
  weights?: Record<string, number>
  weights_mode?: 'pairwise' | 'direct'
  dissent?: string
  acceptance_conditions?: string[]
  risks_of_selected?: string[]
  recommendation?: string
  decision_question?: string
}

async function json<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) {
    let msg = String(res.status)
    try { const d = (await res.json())?.detail; msg = typeof d === 'string' ? d : d?.message ?? msg } catch { /* not JSON */ }
    throw new Error(msg)
  }
  return res.json() as Promise<T>
}

// ─── trades by gate ────────────────────────────────────────────────────────

interface Summary { by_gate: Record<string, { total: number; decided: number; open: number; undecided: string[] }> }

export function TradeGateSummary({ studyId }: { studyId: string | null }) {
  const { t } = useTranslation()
  const { data } = useQuery<Summary>({
    queryKey: ['trades-summary', studyId],
    queryFn: () => json(`${API}/studies/${studyId}/trades/summary`),
    enabled: !!studyId, staleTime: 5_000,
  })
  if (!data) return null
  const gates = GATES.filter(g => data.by_gate[g])
  if (!gates.length) return null
  return (
    <p className="t-12 c-2 m-0 mb-1 row gap-2 wrap" data-testid="trade-gate-summary">
      <span>{t('System and architecture trades by review:')}</span>
      {gates.map(g => {
        const b = data.by_gate[g]
        return (
          <Tag key={g}>{b.open
            ? t('{{gate}}: {{n}} ({{open}} undecided)', { gate: g.toUpperCase(), n: b.total, open: b.open })
            : t('{{gate}}: {{n}} ({{d}} decided)', { gate: g.toUpperCase(), n: b.total, d: b.decided })}</Tag>
        )
      })}
    </p>
  )
}

// ─── absolute-scale matrix ─────────────────────────────────────────────────

export function AbsoluteScaleMatrix({ state, evaluation, onChange }: {
  state: TradeStateV2; evaluation: TradeEvaluationV2 | null; onChange: (patch: Partial<TradeStateV2>) => void
}) {
  const { t } = useTranslation()
  const w = evaluation?.weights ?? {}
  const totals = Object.fromEntries((evaluation?.totals ?? []).map(x => [x.option, x]))
  const meta = state.criteria_meta ?? {}
  const setScore = (o: string, c: string, v: number) =>
    onChange({ scores: { ...state.scores, [o]: { ...(state.scores[o] ?? {}), [c]: v } } })
  const setWeight = (c: string, v: number) =>
    onChange({ weights: { ...Object.fromEntries(state.criteria.map(k => [k, w[k] ?? 0])), [c]: v }, weights_mode: 'direct' })
  const setSource = (c: string, v: string) =>
    onChange({ criteria_meta: { ...meta, [c]: { ...(meta[c] ?? {}), source: v.split(/[,;]/).map(x => x.trim()).filter(Boolean) } } })
  return (
    <div className="stack gap-1" data-testid="absolute-matrix">
      <p className="t-12 c-2 m-0">
        {t('Absolute scale: each option is scored 1 to 5 on each criterion against the written scale (5 best credible, 3 meets the requirement, 1 fails). Weights are fixed before scoring.')}
      </p>
      {state.post_hoc_weights && <Note tone="caution">{t('The weights were changed after scoring: the change is kept and shown in the report.')}</Note>}
      {(state.must ?? []).length > 0 && (
        <div className="t-12"><span className="w-600">{t('Must-criteria (screening)')}:</span> {(state.must ?? []).join(' · ')}</div>
      )}
      <div style={{ overflowX: 'auto' }}>
        <table className="c2o-table c2o-table--dense">
          <thead>
            <tr className="bb">
              <th>{t('Criterion')}</th><th className="num">{t('Weight')}</th><th>{t('Source (MOE or requirement)')}</th>
              {state.options.map(o => (
                <th key={o} className="num" title={state.option_labels?.[o] ?? o}>
                  {o}{state.options[state.datum] === o ? ` (${t('datum')})` : ''}{state.screened?.[o] ? ' ⊘' : ''}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {state.criteria.map(c => (
              <tr key={c} className="bb">
                <td title={meta[c]?.scale ?? ''}>{c}{meta[c]?.scale && <div className="t-12 c-3">{meta[c]?.scale}</div>}</td>
                <td className="num">
                  <Input dense type="number" step="0.05" min="0" max="1" style={{ width: '4.5rem' }} aria-label={t('Weight of {{c}}', { c })}
                    value={(w[c] ?? 0).toFixed(2)} onChange={e => setWeight(c, Math.max(0, Number(e.target.value) || 0))} />
                </td>
                <td>
                  <Input dense style={{ width: '9rem' }} aria-label={t('Source of {{c}}', { c })} placeholder="MOE-01"
                    value={(meta[c]?.source ?? []).join(', ')} onChange={e => setSource(c, e.target.value)} />
                </td>
                {state.options.map(o => (
                  <td key={o} className="num">
                    <Select dense className="c2o-num-select" aria-label={t('Score of {{o}} on {{c}}', { o, c })}
                      value={state.scores[o]?.[c] ?? ''} onChange={e => setScore(o, c, Number(e.target.value))}>
                      <option value="">—</option>
                      {[1, 2, 3, 4, 5].map(v => <option key={v} value={v}>{v}</option>)}
                    </Select>
                  </td>
                ))}
              </tr>
            ))}
            <tr>
              <td className="w-600">{t('Weighted Total')}</td><td /><td />
              {state.options.map(o => (
                <td key={o} className={`num mono${evaluation?.winner === o ? ' c-ok w-600' : ''}`}>
                  {totals[o] ? totals[o].weighted.toFixed(2) : '—'}{totals[o]?.screened ? ` (${t('screened out')})` : ''}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
      {Object.keys(state.screened ?? {}).length > 0 && (
        <ul className="t-12 c-2 m-0">
          {Object.entries(state.screened ?? {}).map(([o, why]) => <li key={o}>{t('{{o}} screened out: {{why}}', { o, why })}</li>)}
        </ul>
      )}
      {Object.keys(state.option_labels ?? {}).length > 0 && (
        <ul className="t-12 c-3 m-0">
          {state.options.map(o => state.option_labels?.[o] ? <li key={o}><span className="mono">{o}</span> {state.option_labels[o]}</li> : null)}
        </ul>
      )}
      {(evaluation?.issues ?? []).length > 0 && (
        <Note tone="caution">{(evaluation?.issues ?? []).map(i => t(i)).join(' · ')}</Note>
      )}
    </div>
  )
}

// ─── ±20 % sensitivity ─────────────────────────────────────────────────────

export function TradeSensitivityPm20({ evaluation }: { evaluation: TradeEvaluationV2 | null }) {
  const { t } = useTranslation()
  const rows = evaluation?.sensitivity_pm20 ?? []
  if (!rows.length) return null
  return (
    <Disclosure ruled summary={t('Sensitivity to ±20 % on each weight')}
      meta={evaluation?.robust_pm20 ? t('robust') : t('{{n}} changes flip the winner', { n: evaluation?.flips_at?.length ?? 0 })}>
      <p className="t-12 c-2 m-0 mb-1" data-testid="trade-pm20">
        {evaluation?.robust_pm20
          ? t('The winner ({{w}}) is unchanged for every single weight ×0.8 and ×1.2.', { w: evaluation?.winner ?? '' })
          : t('The winner changes for: {{list}}.', { list: (evaluation?.flips_at ?? []).join(', ') })}
        {evaluation?.runner_up ? ` ${t('Runner-up: {{r}}, behind by {{m}}.', { r: evaluation.runner_up, m: (evaluation.margin ?? 0).toFixed(2) })}` : ''}
      </p>
      <table className="c2o-table c2o-table--dense">
        <thead><tr className="bb"><th>{t('Criterion')}</th><th className="num">{t('Factor')}</th><th>{t('Winner')}</th><th className="num">{t('Total')}</th><th className="num">{t('Lead')}</th></tr></thead>
        <tbody>
          {rows.map(r => (
            <tr key={`${r.criterion}-${r.factor}`} className="bb">
              <td>{r.criterion}</td><td className="num">×{r.factor}</td>
              <td className={r.winner !== evaluation?.winner ? 'c-caution w-600' : undefined}>{r.winner}</td>
              <td className="num mono">{r.winner_total.toFixed(3)}</td>
              <td className="num mono">{r.margin_to_next != null ? r.margin_to_next.toFixed(3) : '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {(evaluation?.break_even ?? []).length > 0 && (
        <p className="t-12 c-3 m-0 mt-1">
          {t('Break-even (one weight multiplied until the runner-up wins): {{list}}', {
            list: (evaluation?.break_even ?? []).map(b => `${b.criterion} ×${b.multiplier}`).join('; ') })}
        </p>
      )}
    </Disclosure>
  )
}

// ─── conditional decision ─────────────────────────────────────────────────

export interface ConditionValue { condition: string; due: string; fallback: string; risks: string; blocks_gate: string }

export function ConditionFields({ value, onChange }: { value: ConditionValue; onChange: (v: ConditionValue) => void }) {
  const { t } = useTranslation()
  const set = (k: keyof ConditionValue, v: string) => onChange({ ...value, [k]: v })
  return (
    <Disclosure ruled summary={t('Conditional decision')} meta={value.condition ? t('condition set') : t('optional')}>
      <div className="stack gap-1 t-12" data-testid="trade-condition">
        <label className="flex gap-1 ai-c"><span style={{ width: '11rem' }}>{t('Condition')}</span>
          <Input dense style={{ flex: 1 }} value={value.condition} placeholder={t('What must be confirmed for the decision to stand')}
            onChange={e => set('condition', e.target.value)} /></label>
        <label className="flex gap-1 ai-c"><span style={{ width: '11rem' }}>{t('Fallback')}</span>
          <Input dense style={{ flex: 1 }} value={value.fallback} onChange={e => set('fallback', e.target.value)} /></label>
        <label className="flex gap-1 ai-c"><span style={{ width: '11rem' }}>{t('Due date')}</span>
          <Input dense type="date" value={value.due} onChange={e => set('due', e.target.value)} />
          <span>{t('Must be met by')}</span>
          <Select dense value={value.blocks_gate} onChange={e => set('blocks_gate', e.target.value)}>
            <option value="">—</option>{GATES.map(g => <option key={g} value={g}>{g.toUpperCase()}</option>)}
          </Select></label>
        <label className="flex gap-1 ai-c"><span style={{ width: '11rem' }}>{t('Linked risks')}</span>
          <Input dense style={{ flex: 1 }} value={value.risks} placeholder="RSK-001, RSK-010" onChange={e => set('risks', e.target.value)} /></label>
      </div>
    </Disclosure>
  )
}

// ─── record as trade ──────────────────────────────────────────────────────

export function RecordAsTradeButton({ studyId, tool, title, options }: {
  studyId: string | null; tool: 'orbit' | 'ground'; title: string
  options: Array<{ id: string; label: string; metrics: Record<string, number | string | null | undefined> }>
}) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const [busy, setBusy] = useState(false)
  return (
    <Button size="sm" busy={busy} disabledReason={options.length < 2 ? t('At least two candidates are needed') : undefined}
      title={t('Make these candidates a system-level trade study in Decide')}
      onClick={async () => {
        if (!studyId) return
        setBusy(true)
        try {
          const clean = options.map(o => ({ ...o, metrics: Object.fromEntries(Object.entries(o.metrics).filter(([, v]) => v != null)) }))
          const it = await json<{ id: string }>(`${API}/studies/${studyId}/trades/from-tool`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ tool, title, options: clean }),
          })
          void qc.invalidateQueries({ queryKey: ['trades', studyId] })
          void qc.invalidateQueries({ queryKey: ['trades-summary', studyId] })
          void showAlert(t('Recorded as trade {{id}}: write the scales, sources and weights before scoring.', { id: it.id }))
        } catch (e) {
          void showAlert(t('The trade could not be recorded ({{msg}}).', { msg: String((e as Error).message) }))
        } finally { setBusy(false) }
      }}>{t('Record as trade')}</Button>
  )
}

// ─── open-item register ───────────────────────────────────────────────────

export function OpenItemsPanel({ studyId }: { studyId: string | null }) {
  const { t } = useTranslation()
  const [gate, setGate] = useState('')
  const [showClosed, setShowClosed] = useState(false)
  const { data } = useQuery<{ items: OpenItem[]; counts: { total: number; open: number } }>({
    queryKey: ['open-items', studyId, gate, showClosed],
    queryFn: () => json(`${API}/studies/${studyId}/open-items?${new URLSearchParams({ ...(gate ? { blocks_gate: gate } : {}), include_closed: String(showClosed) })}`),
    enabled: !!studyId, staleTime: 5_000,
  })
  return (
    <section className="c2o-dec-row mt-2" data-testid="open-items-panel">
      <div className="row gap-2 ai-c wrap mb-1">
        <h3 className="c2o-reqs__group m-0">{t('Open items')}</h3>
        <Select dense aria-label={t('Blocks gate')} value={gate} onChange={e => setGate(e.target.value)}>
          <option value="">{t('Every gate')}</option>
          {GATES.map(g => <option key={g} value={g}>{t('Blocks {{gate}}', { gate: g.toUpperCase() })}</option>)}
        </Select>
        <label className="t-12 row gap-1 ai-c"><input type="checkbox" checked={showClosed} onChange={e => setShowClosed(e.target.checked)} />{t('Show closed')}</label>
        {data && <span className="t-12 c-3">{t('{{n}} open', { n: data.counts.open ?? 0 })}</span>}
      </div>
      <p className="t-12 c-3 m-0 mb-1">{t('RIDs and actions, conditional decisions, PI and seat decisions, undecided gate trades and change proposals, with the gate each one blocks.')}</p>
      <OpenItemList items={data?.items ?? []} />
    </section>
  )
}

// ─── change control ───────────────────────────────────────────────────────

interface ChangeRow { id: string; code: string; title: string; status: string; decision_gate?: string }
interface Approval { id: string; seat: string; decision: string; note: string; by: string; at: string | null }
interface Control {
  change: ChangeRow & { impact?: unknown; affected_codes?: string[] }
  state: 'not_started' | 'in_review' | 'agreed' | 'objected' | 'approved' | 'rejected'
  impact: { source?: string; deltas?: Record<string, { before?: number; after?: number; delta?: number; unit?: string; owner_seat?: string }>; stated_impact?: unknown; seats?: unknown[] }
  seats: Approval[]
  pending_seats: string[]
  board: (Approval & { baseline_ref: string; data?: { baseline?: { label?: string; kind?: string; revision?: number }; applied?: Array<{ code: string; applied: boolean }> } }) | null
  baseline_ref: string
}

// English text is the i18n key
const FLOW_LABEL: Record<string, string> = {
  not_started: 'Not started', in_review: 'In review', agreed: 'All seats agree', objected: 'Objection raised',
  approved: 'Approved', rejected: 'Rejected',
}
const FLOW_STATUS: Record<string, Status> = {
  not_started: 'neutral', in_review: 'info', agreed: 'ok', objected: 'caution', approved: 'ok', rejected: 'alarm',
}

function ChangeFlow({ studyId, change }: { studyId: string; change: ChangeRow }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const team = useSeatStore(s => s.team)
  const mySeats = team?.enabled ? (team.me?.held ?? []) : null
  const canBoard = !team?.enabled || !!team.me?.instructor || (team.me?.held ?? []).includes('team_leader')
  const key = ['change-control', studyId, change.id]
  const { data: flow } = useQuery<Control>({ queryKey: key, queryFn: () => json(`${API}/studies/${studyId}/changes/${change.id}/control`) })
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState<string | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const post = async (what: string, body: unknown) => {
    setBusy(what); setErr(null)
    try {
      await json(`${API}/studies/${studyId}/changes/${change.id}/control/${what}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      for (const k of [key, ['open-items', studyId], ['gate-review', studyId], ['gate-inventory', studyId], ['changes', studyId]]) {
        void qc.invalidateQueries({ queryKey: k })
      }
    } catch (e) { setErr(String((e as Error).message)) } finally { setBusy(null) }
  }
  if (!flow) return null
  const deltas = Object.entries(flow.impact?.deltas ?? {})
  return (
    <div className="c2o-dec-row" data-testid={`change-flow-${change.code}`}>
      <div className="row gap-2 ai-c wrap">
        <span className="mono w-600">{change.code}</span>
        <span>{change.title}</span>
        <StatusBadge status={FLOW_STATUS[flow.state] ?? 'neutral'}>{t(FLOW_LABEL[flow.state] ?? flow.state)}</StatusBadge>
        {change.decision_gate && <Tag>{t('Decision at {{gate}}', { gate: change.decision_gate.toUpperCase() })}</Tag>}
      </div>
      {flow.state === 'not_started' && (
        <Button size="sm" variant="primary" busy={busy === 'start'} onClick={() => void post('start', {})}>
          {t('Start change review (impact preview)')}
        </Button>
      )}
      {flow.state !== 'not_started' && (<>
        <div className="t-12 mt-1">
          <span className="w-600">{t('Impact')}:</span>{' '}
          {deltas.length > 0
            ? deltas.map(([k, d]) => `${k} ${d.delta != null ? (d.delta > 0 ? '+' : '') + d.delta : '—'} ${d.unit ?? ''}`).join(' · ')
            : flow.impact?.stated_impact ? String(flow.impact.stated_impact) : t('no change to the key numbers')}
          {flow.impact?.source === 'key_numbers' && <span className="c-3"> ({t('stated impact; the dry-run preview is not available')})</span>}
        </div>
        <ul className="list-reset stack gap-1 t-12 mt-1">
          {flow.seats.map(a => {
            const mine = mySeats === null || mySeats.includes(a.seat) || canBoard
            return (
              <li key={a.id} className="row gap-2 ai-c wrap">
                <Tag>{a.seat}</Tag>
                <StatusBadge status={a.decision === 'agree' ? 'ok' : a.decision === 'object' ? 'caution' : 'neutral'}>
                  {a.decision === 'agree' ? t('agrees') : a.decision === 'object' ? t('objects') : t('pending')}
                </StatusBadge>
                {a.note && <span className="c-2">{a.note}</span>}
                {mine && (flow.state === 'in_review' || flow.state === 'objected' || flow.state === 'agreed') && (<>
                  <Button size="sm" variant="quiet" busy={busy === `agree-${a.seat}`} onClick={() => void post('agree', { seat: a.seat, decision: 'agree', note })}>{t('Agree')}</Button>
                  <Button size="sm" variant="quiet" disabledReason={!note.trim() ? t('Write the reason first') : undefined}
                    onClick={() => void post('agree', { seat: a.seat, decision: 'object', note })}>{t('Object')}</Button>
                </>)}
              </li>
            )
          })}
        </ul>
        {(flow.state === 'in_review' || flow.state === 'objected' || flow.state === 'agreed') && (<>
          <Textarea rows={2} aria-label={t('Note')} placeholder={t('Note (reason for an objection, or the board decision)')}
            value={note} onChange={e => setNote(e.target.value)} />
          {canBoard && (
            <div className="row gap-2 mt-1">
              <Button size="sm" variant="primary" busy={busy === 'decide'}
                disabledReason={flow.state !== 'agreed' ? t('Every affected seat must agree first') : undefined}
                onClick={() => void post('decide', { decision: 'approve', note })}>{t('Approve and update the baseline')}</Button>
              <Button size="sm" onClick={() => void post('decide', { decision: 'reject', note })}>{t('Reject')}</Button>
            </div>
          )}
        </>)}
        {flow.board?.decision === 'approve' && flow.board.data?.baseline?.label && (
          <Note tone="ok">{t('New baseline: {{kind}}, revision {{rev}} ({{code}}).', {
            kind: t(BASELINE_LABEL[flow.board.data.baseline.kind ?? ''] ?? flow.board.data.baseline.kind ?? ''),
            rev: flow.board.data.baseline.revision ?? 1, code: change.code })}</Note>
        )}
      </>)}
      {err && <Note tone="caution">{err}</Note>}
    </div>
  )
}

export function ChangeControlCard({ studyId }: { studyId: string | null }) {
  const { t } = useTranslation()
  const { data } = useQuery<{ items: ChangeRow[]; status?: string }>({
    queryKey: ['changes', studyId],
    queryFn: () => json(`${API}/studies/${studyId}/changes`),
    enabled: !!studyId, staleTime: 5_000,
  })
  if (!studyId) return null
  const items = data?.items ?? []
  return (
    <section className="c2o-dec-row mt-2" data-testid="change-control-card">
      <h3 className="c2o-reqs__group m-0">{t('Change control')}</h3>
      <p className="t-12 c-3 m-0 mb-1">{t('A change proposal is reviewed with its impact; each affected seat agrees or objects; the board then approves (a new baseline revision) or rejects it.')}</p>
      {items.length === 0
        ? <p className="t-12 c-3 m-0">{t('No change proposal yet.')}</p>
        : <div className="stack gap-1">{items.map(c => <ChangeFlow key={c.id} studyId={studyId} change={c} />)}</div>}
    </section>
  )
}
