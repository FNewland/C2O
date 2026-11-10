/**
 * NegotiationPanel — what the seats agree, and who has signed (wave 3, 3.H6).
 *
 * A negotiation record (GET/POST /api/studies/{id}/negotiations, services/negotiations.py) holds the
 * issue, the coupled parameters with their live values, the seats that must agree, the options with
 * their computed effects, the chosen option and agreed values, one sign-off per seat, the reopen
 * trigger and the links. The record is "agreed" when every seat has signed the current version;
 * changing the choice clears the sign-offs. Four templates carry the walkthrough's scenes: science
 * volume vs downlink (N1), payload peak and imaging duty (N3), mass envelopes (N7) and one more
 * ground station (GS4). Mounted in Decide (D, one line) and usable on its own.
 */
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { activeSeat, seatLabel } from '../seats/api'
import { Button, DataTable, Note, NoData, Panel, StatusBadge, Tag, askText, fmtNum, showAlert, type Status } from '../components/ui'

type Bi = { en: string; fr: string }
interface LiveParam { key: string; label: Bi; value: number | null; unit: string; source: string; owner_seat: string; agreed_value?: number | null }
interface SeatState { seat: string; label: Bi; signed: boolean; signoff?: { by: string; at: string; note: string; version: number } }
interface Option {
  key: string; label: Bi; values: Record<string, number>; effects: Record<string, unknown> | null
  delta?: Record<string, number>; affects?: { seat: string; what: Bi }[]; flight_rules?: string[]; computed_at?: string
}
export interface NegotiationRecord {
  id: string; code: string; issue: Bi; status: 'proposed' | 'agreed' | 'reopened'; version: number
  parameters: string[]; seats: string[]; options: Option[]; chosen_option: string | null; agreed: Record<string, number>
  live_parameters: LiveParam[]; seat_state: SeatState[]; signed_count: number; seat_count: number
  reopen_trigger: string; reopen_trigger_fr: string
  trigger: { fired: boolean | null; condition: { key: string; op: string; value: number } | null; value?: number | null }
  links: Record<string, string[]>; history: { at: string; by: string; action: string; seat?: string; reason?: string; fields?: string[] }[]
  agreed_at: string | null; template: string | null
}
interface ListView {
  items: NegotiationRecord[]; counts: Record<string, number>
  templates: { code: string; issue: Bi; seats: string[] }[]
}

const API = '/api'
async function call<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const r = await fetch(`${API}${path}`, { method, headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body) })
  if (!r.ok) {
    let msg = `${r.status}`
    try { const b = await r.json(); msg = typeof b.detail === 'string' ? b.detail : (b.detail?.message ?? JSON.stringify(b.detail)) } catch { /* status */ }
    throw new Error(msg)
  }
  return r.json() as Promise<T>
}

const STATUS_TONE: Record<NegotiationRecord['status'], Status> = { proposed: 'caution', agreed: 'ok', reopened: 'alarm' }
// English text is the i18n key
const STATUS_LABEL: Record<NegotiationRecord['status'], string> = { proposed: 'Proposed', agreed: 'Agreed', reopened: 'Reopened' }
// English text is the i18n key
const LINK_LABEL: Record<string, string> = {
  requirements: 'Requirements', risks: 'Risks', trades: 'Trades', rids: 'RIDs', changes: 'Change proposals', decisions: 'Open decisions',
}
// English text is the i18n key: what a computed effect measures
const EFFECT_LABEL: Record<string, string> = {
  margin_c1_pct: 'Daily margin (baseline)', margin_worst_site_out_pct: 'Daily margin, worst site out',
  margin_fallback_rate_pct: 'Daily margin at the fallback rate', capacity_mb_per_day: 'Capacity (MB/day)',
  demand_mb_per_day: 'Demand (MB/day)', compression_needed: 'Compression needed', union_min_per_day: 'Contact (min/day)',
  longest_gap_h: 'Longest gap (h)', downlink_share: 'Downlink share', orbit_average_cbe_w: 'Orbit average (W, CBE)',
  orbit_average_load_w: 'Orbit average with margins (W)', margin_pct: 'Daily margin', dod_percent: 'Depth of discharge',
  energy_balance_wh: 'Energy balance per orbit (Wh)', allocations_kg: 'Sum of the allocations (kg)', with_margin_kg: 'With the system margin (kg)',
  limit_kg: 'Limit (kg)', reserve_kg: 'Reserve held by Systems (kg)', closes: 'Closes',
}

function fmtVal(k: string, v: unknown): string {
  if (v == null) return '–'
  if (typeof v === 'boolean') return v ? '✓' : '✗'
  if (typeof v !== 'number') return String(v)
  if (k.endsWith('share')) return `${fmtNum(v * 100, 1)} %`
  if (k.endsWith('_pct') || k.endsWith('percent')) return `${v >= 0 && k.startsWith('margin') ? '+' : ''}${fmtNum(v, 1)} %`
  return fmtNum(v, Math.abs(v) >= 100 ? 0 : Math.abs(v) >= 10 ? 1 : 2)
}

export function NegotiationPanel({ studyId }: { studyId: string | null }) {
  const { t, i18n } = useTranslation()
  const qc = useQueryClient()
  const key = ['negotiations', studyId]
  const { data, error, isLoading } = useQuery<ListView>({ queryKey: key, enabled: !!studyId,
    queryFn: () => call(`/studies/${studyId}/negotiations`), refetchInterval: 10000 })
  const [open, setOpen] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const L = (b: Bi | null | undefined) => !b ? '' : (i18n.language === 'fr' ? b.fr || b.en : b.en || b.fr)
  if (!studyId) return null
  if (isLoading) return <p className="t-13 c-2">{t('Loading…')}</p>
  if (error || !data) return <Note tone="alarm">{t('The negotiations could not be loaded: {{message}}', { message: String((error as Error)?.message ?? '') })}</Note>

  const run = async (fn: () => Promise<unknown>) => {
    setBusy(true)
    try { await fn(); await qc.invalidateQueries({ queryKey: key }) }
    catch (e) { await showAlert((e as Error).message) }
    finally { setBusy(false) }
  }
  const create = (code: string) => run(async () => {
    const r = await call<NegotiationRecord>(`/studies/${studyId}/negotiations`, 'POST', { template: code })
    setOpen(r.id)
  })
  const existing = new Set(data.items.map(r => r.template))

  return (
    <Panel title={t('Negotiations')} meta={t('{{a}} agreed of {{n}}', { a: data.counts.agreed ?? 0, n: data.counts.total ?? 0 })}>
      <p className="t-12 c-2 m-0 pb-2">{t('Where one number is owned by one seat and constrained by others, the seats record the options with their computed effects, choose, and each signs. A change of the choice clears the signatures.')}</p>
      <div className="row wrap gap-2 pb-3" role="group" aria-label={t('New negotiation')}>
        {data.templates.map(tp => (
          <Button key={tp.code} size="sm" busy={busy} variant={existing.has(tp.code) ? 'quiet' : 'default'} onClick={() => create(tp.code)}
            title={L(tp.issue)}>{t('New {{code}}', { code: tp.code })}</Button>))}
      </div>
      {data.items.length === 0 && <NoData label={t('no negotiation yet')} />}
      <div className="stack gap-3">
        {data.items.map(r => (
          <RecordCard key={r.id} r={r} studyId={studyId} expanded={open === r.id} onToggle={() => setOpen(open === r.id ? null : r.id)}
            busy={busy} run={run} L={L} />))}
      </div>
    </Panel>
  )
}

function RecordCard({ r, studyId, expanded, onToggle, busy, run, L }: {
  r: NegotiationRecord; studyId: string; expanded: boolean; onToggle: () => void; busy: boolean
  run: (fn: () => Promise<unknown>) => Promise<void>; L: (b: Bi | null | undefined) => string
}) {
  const { t, i18n } = useTranslation()
  const base = `/studies/${studyId}/negotiations/${r.id}`
  const mine = activeSeat()
  const choose = (k: string) => run(() => call(base, 'PATCH', { chosen_option: k }))
  const sign = (seat: string, agree = true) => run(() => call(`${base}/signoff`, 'POST', { seat, agree }))
  const reopen = async () => {
    const reason = await askText(t('Why reopen {{code}}?', { code: r.code }))
    if (reason) await run(() => call(`${base}/reopen`, 'POST', { reason }))
  }
  const recompute = () => run(() => call(base, 'PATCH', { recompute_options: true }))
  const effectKeys = Array.from(new Set(r.options.flatMap(o => Object.keys(o.effects ?? {})))).filter(k => k in EFFECT_LABEL)
  const trig = i18n.language === 'fr' && r.reopen_trigger_fr ? r.reopen_trigger_fr : r.reopen_trigger
  return (
    <section className="card stack gap-2" data-testid={`negotiation-${r.code}`} aria-label={`${r.code} ${L(r.issue)}`}>
      <div className="row gap-2 ai-c wrap">
        <Tag>{r.code}</Tag>
        <StatusBadge status={STATUS_TONE[r.status]}>{t(STATUS_LABEL[r.status])}</StatusBadge>
        <span className="t-12 c-3">{t('{{s}} of {{n}} seats signed · version {{v}}', { s: r.signed_count, n: r.seat_count, v: r.version })}</span>
        {r.trigger.fired && <StatusBadge status="alarm">{t('Reopen trigger fired')}</StatusBadge>}
        <span className="grow" />
        <Button size="sm" variant="quiet" onClick={onToggle} aria-expanded={expanded}>{expanded ? t('Close') : t('Open')}</Button>
      </div>
      <p className="t-14 m-0">{L(r.issue)}</p>
      <div className="row wrap gap-2" aria-label={t('Sign-offs')}>
        {r.seat_state.map(s => (
          <StatusBadge key={s.seat} status={s.signed ? 'ok' : 'nodata'}
            title={s.signoff ? t('signed by {{by}} on {{at}}', { by: s.signoff.by || '–', at: s.signoff.at.slice(0, 16).replace('T', ' ') }) : undefined}>
            {L(s.label) || seatLabel(s.seat)}</StatusBadge>))}
      </div>
      {expanded && (
        <div className="stack gap-3">
          <DataTable dense caption={t('Coupled parameters')} rows={r.live_parameters} rowKey={p => p.key} columns={[
            { key: 'l', header: t('Parameter'), render: p => L(p.label) },
            { key: 'v', header: t('Now'), num: true, render: p => p.value == null ? <NoData label={t('no data')} /> : `${fmtVal(p.key, p.value)} ${p.key.endsWith('share') ? '' : p.unit}` },
            { key: 'a', header: t('When agreed'), num: true, render: p => p.agreed_value == null ? '' : `${fmtVal(p.key, p.agreed_value)} ${p.key.endsWith('share') ? '' : p.unit}` },
            { key: 'o', header: t('Owner'), render: p => seatLabel(p.owner_seat) },
            { key: 's', header: t('Source'), render: p => <span className="t-12 c-3 mono">{p.source}</span> },
          ]} />
          <DataTable dense caption={t('Options and their computed effects')} rows={r.options} rowKey={o => o.key} columns={[
            { key: 'o', header: t('Option'), render: o => (
              <span className="stack gap-0">
                <span className={r.chosen_option === o.key ? 'w-600' : ''}>{L(o.label)}</span>
                {o.affects && <span className="t-12 c-3">{t('Affects: {{list}}', { list: o.affects.map(a => `${seatLabel(a.seat)} (${L(a.what)})`).join('; ') })}</span>}
              </span>) },
            ...effectKeys.map(k => ({ key: k, header: t(EFFECT_LABEL[k]), num: true, render: (o: Option) => (
              <span>{fmtVal(k, (o.effects ?? {})[k])}{o.delta && o.delta[k] != null ? <span className="t-12 c-3"> ({o.delta[k] >= 0 ? '+' : ''}{fmtVal(k, o.delta[k])})</span> : null}</span>) })),
            { key: 'c', header: '', render: o => r.chosen_option === o.key
              ? <StatusBadge status="info">{t('Chosen')}</StatusBadge>
              : <Button size="sm" busy={busy} onClick={() => choose(o.key)}>{t('Choose')}</Button> },
          ]} />
          <div className="row wrap gap-2" aria-label={t('Sign for a seat')}>
            {r.seat_state.map(s => (
              <Button key={s.seat} size="sm" variant={s.signed ? 'quiet' : mine === s.seat ? 'primary' : 'default'} busy={busy}
                disabled={!r.chosen_option && !Object.keys(r.agreed).length}
                onClick={() => sign(s.seat, !s.signed)}>
                {s.signed ? t('Withdraw {{seat}}', { seat: L(s.label) }) : t('Sign as {{seat}}', { seat: L(s.label) })}</Button>))}
          </div>
          {trig && <p className="t-12 c-2 m-0">{t('Reopen trigger: {{text}}', { text: trig })}
            {r.trigger.condition && r.trigger.value != null && <span className="c-3"> {t('(now {{v}})', { v: fmtVal(r.trigger.condition.key, r.trigger.value) })}</span>}</p>}
          <div className="row wrap gap-3 t-12">
            {Object.entries(r.links).filter(([, v]) => v && v.length).map(([k, v]) => (
              <span key={k}><span className="c-3">{t(LINK_LABEL[k] ?? k)}:</span> <span className="mono">{v.join(', ')}</span></span>))}
          </div>
          <div className="row gap-2">
            {r.template && <Button size="sm" variant="quiet" busy={busy} onClick={recompute}>{t('Recompute the options')}</Button>}
            {r.status === 'agreed' && <Button size="sm" variant="danger" busy={busy} onClick={reopen}>{t('Reopen')}</Button>}
          </div>
          {r.history.length > 0 && (
            <details>
              <summary className="t-12 c-3">{t('History ({{n}})', { n: r.history.length })}</summary>
              <ul className="list-reset t-12 c-3 stack gap-0">
                {r.history.map((h, i) => <li key={i}>{h.at.slice(0, 16).replace('T', ' ')} · {h.by || '–'} · {h.action}{h.seat ? ` · ${seatLabel(h.seat)}` : ''}{h.reason ? ` · ${h.reason}` : ''}</li>)}
              </ul>
            </details>)}
        </div>
      )}
    </section>
  )
}

export default NegotiationPanel
