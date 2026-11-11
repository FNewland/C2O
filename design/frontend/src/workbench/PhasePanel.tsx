/**
 * PhasePanel — the systems-engineering phase card at the top of V&V › Review Gates (wave 3,
 * 3.D2, SE-03). It reads the protocol of the phase the study is in (``GET /phase``, agent S)
 * and the stage-transition inventory of the gate (``GET /gates/{gate}/inventory``, agent D):
 *
 *   Before you start         the entry items and the earlier gates not passed
 *   Deliverables this phase  ✅ / ⚠️ / ❌ per deliverable, owner seat, Fix, Draft it
 *   Analysis standard        the analysis checks (open assumptions …)
 *
 * plus the open items that block the gate and the enforcement mode (warn by default; the
 * instructor can set block). ``StartReviewInventory`` is what "Start review" shows before the
 * confirmation.
 */
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useUIStore, type ActivityPanel } from '../stores/uiStore'
import { seatLabel, useSeatStore } from '../seats/api'
import { openDiagram } from '../diagrams/GateDiagrams'
import { pick, type Bilingual } from '../components/useGateReview'
import { Button, Note, Panel, Select, StatusBadge, Tag, type Status } from '../components/ui'
import { PhaseCoaching } from './GuidancePanel'

const API = '/api'

type ItemState = 'ok' | 'pass' | 'warn' | 'missing' | string
type Fix = string | { view?: string; panel?: string; diagram?: string; section?: string } | null | undefined

export interface PhaseItem {
  id: string
  kind?: string
  label?: Bilingual | string
  owner_seat?: string
  state?: ItemState
  evidence?: string
  fix?: Fix
  draft?: Fix
}

export interface PhaseView {
  gate: string | null
  phase: string | null
  entry: PhaseItem[]
  deliverables: PhaseItem[]
  analysis: PhaseItem[]
  status?: string
}

export interface Finding { code: string; kind: string; id: string; label?: Bilingual | string; owner_seat?: string; state?: string; evidence?: string }

export interface OpenItem {
  id: string; code: string; kind: string; title: string; owner_seat: string; status: string
  blocks_gate: string; condition?: string; fallback?: string; source: string
}

export interface Inventory {
  gate: { id: string; short: string; name: Bilingual; covers?: string[] }
  entry: PhaseItem[]
  deliverables: PhaseItem[]
  protocol_source: string
  earlier_gates: Array<{ id: string; state: string }>
  products_baselined: Array<{ id: string; label: Bilingual; owner_seat: string }>
  baseline_kind: string
  enforcement: { mode: 'off' | 'warn' | 'block'; source: string }
  findings: Finding[]
  open_items: OpenItem[]
}

const STATE_STATUS: Record<string, Status> = { ok: 'ok', pass: 'ok', warn: 'caution', missing: 'alarm', fail: 'alarm' }
// English text is the i18n key
export const BASELINE_LABEL: Record<string, string> = {
  mission: 'Mission baseline', functional: 'Functional baseline', allocated: 'Allocated baseline', product: 'Product baseline',
}
// English text is the i18n key
const MODE_LABEL: Record<string, string> = { off: 'Off', warn: 'Warn', block: 'Block' }
// English text is the i18n key
const KIND_LABEL: Record<string, string> = {
  pi_decision: 'PI decision', seat_decision: 'Seat decision', decision: 'Decision', action: 'Action', rid: 'RID',
  conditional_decision: 'Conditional decision', undecided_trade: 'Undecided trade', change: 'Change proposal',
  conflict_resolution: 'Conflict resolution',
}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status}`)
  return res.json() as Promise<T>
}

export function usePhase(studyId: string | null) {
  return useQuery<PhaseView>({
    queryKey: ['phase', studyId],
    queryFn: () => getJson(`${API}/studies/${encodeURIComponent(studyId || '')}/phase`),
    enabled: !!studyId, staleTime: 5_000, retry: 1,
  })
}

export function useInventory(studyId: string | null, gate: string | null) {
  return useQuery<Inventory>({
    queryKey: ['gate-inventory', studyId, gate],
    queryFn: () => getJson(`${API}/studies/${encodeURIComponent(studyId || '')}/gates/${encodeURIComponent(gate || '')}/inventory`),
    enabled: !!studyId && !!gate, staleTime: 5_000, retry: 1,
  })
}

/** Open the place that fixes a deliverable: a diagram kind, a workbench panel or a V&V section. */
export function openFix(fix: Fix, item?: PhaseItem, onOpenSection?: (s: string) => void) {
  const ui = useUIStore.getState()
  const diag = typeof fix === 'object' && fix?.diagram ? fix.diagram
    : (item?.kind === 'diagram' && !fix ? String(item.id).replace(/^diagram\./, '') : null)
  if (diag) { openDiagram(diag); return }
  const target = typeof fix === 'string' ? fix : fix?.section ? `vv:${fix.section}` : fix?.panel ?? ''
  if (!target) return
  if (target.startsWith('vv:')) { onOpenSection?.(target.slice(3)); return }
  ui.drillUp(ui.breadcrumb.length - 1)
  ui.setActivePanel(target as ActivityPanel)
}

function ItemRow({ item, lang, onOpenSection }: { item: PhaseItem; lang: string; onOpenSection?: (s: string) => void }) {
  const { t } = useTranslation()
  const st = String(item.state ?? 'missing')
  const label = typeof item.label === 'string' ? item.label : pick(item.label, lang) || item.id
  const canFix = !!item.fix || item.kind === 'diagram'
  return (
    <li className="c2o-criteria__row" data-testid={`phase-item-${item.id}`}>
      <StatusBadge status={STATE_STATUS[st] ?? 'nodata'}>{st === 'ok' || st === 'pass' ? t('Done') : st === 'warn' ? t('Partial') : t('Missing')}</StatusBadge>
      <span className="c2o-criteria__q">{label}</span>
      <span className="t-12 c-2">{item.evidence ?? ''}</span>
      <span className="t-12 c-3 row gap-2 wrap ai-c">
        {item.owner_seat && <Tag>{t('Owner: {{seat}}', { seat: seatLabel(item.owner_seat) })}</Tag>}
        {canFix && st !== 'ok' && st !== 'pass' && (
          <Button size="sm" variant="quiet" onClick={() => openFix(item.fix, item, onOpenSection)}>{t('Fix')}</Button>
        )}
        {item.draft && st !== 'ok' && st !== 'pass' && (
          <Button size="sm" variant="quiet" onClick={() => openFix(item.draft, item, onOpenSection)}>{t('Draft it')}</Button>
        )}
      </span>
    </li>
  )
}

function Section({ title, items, empty, lang, onOpenSection, testid }: {
  title: string; items: PhaseItem[]; empty: string; lang: string; onOpenSection?: (s: string) => void; testid: string
}) {
  return (
    <section className="mt-2" data-testid={testid}>
      <h4 className="c2o-reqs__group">{title}</h4>
      {items.length === 0
        ? <p className="t-12 c-3 m-0">{empty}</p>
        : <ul className="list-reset c2o-criteria">{items.map(i => <ItemRow key={i.id} item={i} lang={lang} onOpenSection={onOpenSection} />)}</ul>}
    </section>
  )
}

export function OpenItemList({ items }: { items: OpenItem[] }) {
  const { t } = useTranslation()
  if (!items.length) return <p className="t-12 c-3 m-0">{t('No open item blocks this gate.')}</p>
  return (
    <ul className="list-reset stack gap-1 t-12" data-testid="gate-open-items">
      {items.map(i => (
        <li key={i.id} className="row gap-2 wrap ai-c">
          <span className="mono w-600">{i.code}</span>
          <Tag>{t(KIND_LABEL[i.kind] ?? i.kind)}</Tag>
          <span>{i.title}</span>
          {i.condition && <span className="c-2">{t('Condition: {{c}}', { c: i.condition })}</span>}
          {i.fallback && <span className="c-3">{t('Fallback: {{f}}', { f: i.fallback })}</span>}
          {i.owner_seat && <span className="c-3">{t('Owner: {{seat}}', { seat: seatLabel(i.owner_seat) })}</span>}
          {i.blocks_gate && <span className="c-3 mono">{i.blocks_gate.toUpperCase()}</span>}
        </li>
      ))}
    </ul>
  )
}

/** The card at the top of V&V › Review Gates. */
export function PhasePanel({ studyId, gate, onOpenSection }: { studyId: string | null; gate: string | null; onOpenSection?: (s: string) => void }) {
  const { t } = useTranslation()
  const lang = useUIStore(s => s.lang)
  const qc = useQueryClient()
  const { data: phase } = usePhase(studyId)
  const { data: inv, isError } = useInventory(studyId, gate)
  const seatTeam = useSeatStore(st => st.team)
  const isInstructor = !seatTeam?.enabled || !!seatTeam.me?.instructor
  if (!studyId || !gate) return null
  const usePhaseView = !!phase && phase.status !== 'not_implemented' && (phase.gate === gate || !inv)
  const entry: PhaseItem[] = [
    ...(inv?.earlier_gates ?? []).filter(g => g.state !== 'passed').map(g => ({
      id: `gate.${g.id}`, kind: 'gate', label: t('{{gate}} passed', { gate: g.id.toUpperCase() }), state: 'missing' as ItemState,
      evidence: t('{{gate}} has not passed', { gate: g.id.toUpperCase() }),
    })),
    ...((usePhaseView ? phase?.entry : inv?.entry) ?? []),
  ]
  const deliverables = (usePhaseView ? phase?.deliverables : inv?.deliverables) ?? []
  const analysis = phase?.analysis ?? []
  const short = inv?.gate.short ?? gate.toUpperCase()
  const phaseName = phase?.phase ?? ''
  const mode = inv?.enforcement.mode ?? 'warn'

  const setMode = async (m: string) => {
    const res = await fetch(`${API}/studies/${encodeURIComponent(studyId)}/gate-enforcement`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ mode: m }),
    })
    if (res.ok) {
      void qc.invalidateQueries({ queryKey: ['gate-inventory', studyId] })
      void qc.invalidateQueries({ queryKey: ['gate-review', studyId] })
    }
  }

  return (
    <Panel level={2} title={phaseName ? t('Phase {{phase}} → {{gate}}', { phase: phaseName, gate: short }) : t('Next review: {{gate}}', { gate: short })}
      meta={inv ? t(BASELINE_LABEL[inv.baseline_kind] ?? inv.baseline_kind) : undefined}
      actions={<span className="row gap-2 ai-c t-12" data-testid="phase-enforcement">
        <span className="c-2">{t('Protocol checks')}</span>
        {isInstructor
          ? <Select dense aria-label={t('Protocol checks at review start')} value={mode} onChange={e => void setMode(e.target.value)}>
              {(['warn', 'block', 'off'] as const).map(m => <option key={m} value={m}>{t(MODE_LABEL[m])}</option>)}
            </Select>
          : <Tag>{t(MODE_LABEL[mode] ?? mode)}</Tag>}
      </span>}>
      <div data-testid="phase-panel">
        {isError && <Note tone="caution">{t('The phase protocol could not be read.')}</Note>}
        <p className="t-12 c-2 m-0">
          {mode === 'block'
            ? t('Block: a review cannot start while a deliverable is missing or an earlier gate has not passed.')
            : mode === 'warn'
              ? t('Warn: a review can start; what is missing is written to the gate history.')
              : t('Off: the protocol is shown but not checked at review start.')}
        </p>
        <Section testid="phase-entry" title={t('Before you start')} items={entry} lang={lang} onOpenSection={onOpenSection}
          empty={t('Nothing to do before this review starts.')} />
        <Section testid="phase-deliverables" title={t('Deliverables this phase')} items={deliverables} lang={lang}
          onOpenSection={onOpenSection} empty={t('The protocol lists no deliverable for this gate yet.')} />
        <Section testid="phase-analysis" title={t('Analysis standard')} items={analysis} lang={lang} onOpenSection={onOpenSection}
          empty={t('No open assumption or analysis check.')} />
        {inv && (
          <section className="mt-2">
            <h4 className="c2o-reqs__group">{t('Open items that block {{gate}}', { gate: short })}</h4>
            <OpenItemList items={inv.open_items ?? []} />
          </section>
        )}
        {(inv?.gate.covers ?? [gate]).some(c => c === 'srr') && <SempIssueCard studyId={studyId} />}
        {/* wave 3 (3.S4): the coaching cards of this phase, by register and seat (agent S) */}
        <div className="mt-2"><PhaseCoaching studyId={studyId} gate={gate} /></div>
      </div>
    </Panel>
  )
}

interface SempIssue { ready: boolean; parts: number | null; of: number | null; issue: string | null; issued_at: string | null; by: string | null }

/** The SEMP generated from the study, issued by the team (SRR-EC-09). */
function SempIssueCard({ studyId }: { studyId: string }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)
  const { data } = useQuery<SempIssue | null>({
    queryKey: ['semp-issue', studyId],
    queryFn: () => fetch(`${API}/studies/${encodeURIComponent(studyId)}/semp/issue`).then(r => (r.ok ? r.json() : null)),
  })
  if (!data) return null
  const issue = async () => {
    setBusy(true); setMsg(null)
    const r = await fetch(`${API}/studies/${encodeURIComponent(studyId)}/semp/issue`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })
    setBusy(false)
    if (!r.ok) { setMsg(t('The SEMP could not be issued ({{code}}).', { code: r.status })); return }
    void qc.invalidateQueries({ queryKey: ['semp-issue', studyId] })
    void qc.invalidateQueries({ queryKey: ['gate-review', studyId] })
    void qc.invalidateQueries({ queryKey: ['gate-inventory', studyId] })
  }
  return (
    <section className="mt-2" data-testid="semp-issue">
      <h4 className="c2o-reqs__group">{t('Systems engineering management plan')}</h4>
      <p className="t-12 c-2 m-0">
        {data.issue
          ? t('SEMP issue {{issue}} recorded', { issue: data.issue })
          : data.ready
            ? t('SEMP content ready ({{parts}}/{{of}} parts): review it and record its issue', { parts: data.parts ?? 0, of: data.of ?? 0 })
            : t('The SEMP generator has no content yet ({{parts}}/{{of}} parts)', { parts: data.parts ?? 0, of: data.of ?? 0 })}
      </p>
      {data.ready && (
        <Button size="sm" busy={busy} onClick={() => void issue()}>
          {data.issue ? t('Record the next SEMP issue') : t('Record the SEMP issue')}
        </Button>
      )}
      {msg && <Note tone="caution" role="alert">{msg}</Note>}
    </section>
  )
}

/** The stage-transition inventory shown before a review starts, with the confirmation. */
export function StartReviewInventory({ studyId, gate, onConfirm, onCancel, busy }: {
  studyId: string; gate: string; onConfirm: () => void; onCancel: () => void; busy: boolean
}) {
  const { t } = useTranslation()
  const lang = useUIStore(s => s.lang)
  const { data: inv, isLoading } = useInventory(studyId, gate)
  if (isLoading || !inv) return <p className="t-12 c-2">{t('Preparing the inventory...')}</p>
  const blocking = inv.enforcement.mode === 'block' && inv.findings.some(f => ['out_of_order', 'deliverables_missing', 'entry_missing'].includes(f.code))
  return (
    <div className="c2o-dec-row mt-2" data-testid="start-inventory" role="region" aria-label={t('Stage-transition inventory')}>
      <h4 className="c2o-reqs__group">{t('Stage-transition inventory: {{gate}}', { gate: inv.gate.short })}</h4>
      <p className="t-12 c-2 m-0">{t('Passing this review sets the {{kind}}.', { kind: t(BASELINE_LABEL[inv.baseline_kind] ?? inv.baseline_kind).toLowerCase() })}</p>
      <ul className="list-reset c2o-criteria">
        {inv.deliverables.map(d => <ItemRow key={d.id} item={d} lang={lang} />)}
      </ul>
      {inv.products_baselined.length > 0 && (
        <p className="t-12 c-2">{t('Products baselined: {{list}}', { list: inv.products_baselined.map(p => pick(p.label, lang)).join(', ') })}</p>
      )}
      {inv.findings.length > 0 && (
        <Note tone={blocking ? 'alarm' : 'caution'}>
          {blocking ? t('The instructor set the protocol checks to block: fix these first.') : t('The review can start; these are written to the gate history:')}
          <ul className="m-0">{inv.findings.map(f => (
            <li key={`${f.code}-${f.id}`}>{f.code === 'out_of_order'
              ? t('{{gate}} has not passed', { gate: f.id.toUpperCase() })
              : `${typeof f.label === 'string' ? f.label : pick(f.label, lang) || f.id}${f.evidence ? `: ${f.evidence}` : ''}`}</li>
          ))}</ul>
        </Note>
      )}
      <h4 className="c2o-reqs__group">{t('Open items that block {{gate}}', { gate: inv.gate.short })}</h4>
      <OpenItemList items={inv.open_items ?? []} />
      <div className="row gap-2 mt-2">
        <Button size="sm" variant="primary" busy={busy} disabledReason={blocking ? t('Blocked by the protocol checks') : undefined}
          onClick={onConfirm}>{t('Confirm: start {{gate}} review', { gate: inv.gate.short })}</Button>
        <Button size="sm" onClick={onCancel}>{t('Back')}</Button>
      </div>
    </div>
  )
}
