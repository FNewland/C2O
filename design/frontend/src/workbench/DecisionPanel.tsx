/**
 * DecisionPanel — Context-sensitive decision support tools.
 *
 * Shows different tools depending on what element is focused and what level:
 * - Level 0: Mission trade (space vs non-space), orbit trade, launch selection
 * - Level 1: Constellation sizing, ground station trade, system architecture trade
 * - Level 2: Subsystem architecture trade
 * - Level 3: Equipment trade (weighted scoring from KB)
 * - Any: Generic trade study builder
 */
import { useState, useCallback, useEffect, useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { RecordDecision } from '../logbook'
import { useTranslation } from 'react-i18next'
import { serverText } from '../i18n/serverText'
import i18n, { fmtProse } from '../i18n'
import { useUIStore } from '../stores/uiStore'
import { pairKey, pairwiseWeights } from './pairwise'
import { fs } from '../theme/tokens'
import { askConfirm, askText, showAlert } from '../components/ui/Dialog'
import { Button, Disclosure, Input, Note, Select, Tag, Textarea } from '../components/ui'
import { useSeatStore } from '../seats/api'
import { useWhereSection } from '../where/where'
import { AbsoluteScaleMatrix, ChangeControlCard, ConditionFields, GATES, LEVEL_LABEL, LEVELS, OpenItemsPanel, RecordAsTradeButton,
  TradeGateSummary, TradeSensitivityPm20, type ConditionValue, type TradeEvaluationV2, type TradeStateV2 } from './DecideV2'
import { ChangesPanel, RaiseChangeButton } from './ChangesPanel'
import { NegotiationPanel } from './NegotiationPanel'
import { SensitivityView } from '../components/SensitivityView'

const API = '/api'

// English text is the i18n key: default trade criteria, kept in English in the stored
// trade record; displayed with t(c, { context: 'criterion' }) (user-added names fall through).
const DEFAULT_CRITERIA = ['Mass', 'Power', 'Cost', 'TRL', 'Risk']

/** One criterion-weighted Pugh trade with its pairwise weighting (W6: many per study, T-01…). */
interface PughState {
  criteria: string[]
  options: string[]
  datum: number
  scores: Record<string, Record<string, number>>
  comparisons: Record<string, number>
}

interface TradeDecision {
  selected?: string; rationale?: string; record_id?: string; decided_at?: string; decided_by_seat?: string
  condition?: string; due?: string; fallback?: string; risks?: string[]; blocks_gate?: string
}
interface TradeLinks { decision_record?: string; requirements?: string[]; risks?: string[]; elements?: string[] }

interface TradeState extends PughState, Omit<TradeStateV2, keyof PughState> {
  id: string
  title: string
  seat: string
  level: string
  status: 'open' | 'decided'
  weights_mode?: 'pairwise' | 'direct'
  weights?: Record<string, number>
  thresholds: Record<string, number>
  evidence?: string
  note?: string
  decision?: TradeDecision
  links?: TradeLinks
}

interface TradeEvaluation extends Omit<TradeEvaluationV2, 'totals' | 'weights' | 'winner'> {
  weights: Record<string, number>
  weights_source: 'pairwise' | 'direct'
  totals: Array<{ option: string; datum: boolean; weighted: number; unweighted: number; below_threshold: string[]; acceptable: boolean }>
  winner: string | null
  sensitivity: Array<{ criterion: string; weight: number; robust: boolean; flip: { delta: number; new_weight: number; new_winner: string } | null }>
  robust: boolean
  decision_differs_from_winner: boolean
}

interface TradeItem { id: string; state: TradeState; version: number; evaluation: TradeEvaluation | null }

const LEGACY_PUGH_KEY = 'spacecdf-pugh'

/** Weights of a trade: typed (``weights_mode`` direct) or derived from the pairwise comparisons. */
function tradeWeights(st: TradeState): Record<string, number> {
  if (st.weights_mode === 'direct' && st.weights && Object.keys(st.weights).length) {
    const total = st.criteria.reduce((s, c) => s + (st.weights?.[c] ?? 0), 0)
    if (total > 0) return Object.fromEntries(st.criteria.map(c => [c, (st.weights?.[c] ?? 0) / total]))
  }
  return pairwiseWeights(st.criteria, st.comparisons || {})
}

/**
 * The study's trade studies (GET/POST/PUT/DELETE /api/studies/{id}/trades…). Edits are kept
 * locally and saved after 400 ms with the version they were made on (409 = someone else saved:
 * reload). The server returns each trade's evaluation (weights, totals, winner, sensitivity).
 * A browser's old single Pugh record (localStorage, before Nov 2026) becomes T-01 once.
 */
function useTrades(studyId: string | null) {
  const qc = useQueryClient()
  const key = ['trades', studyId]
  const { data, isLoading } = useQuery<{ items: TradeItem[] }>({
    queryKey: key,
    queryFn: () => fetch(`${API}/studies/${studyId}/trades`).then(r => (r.ok ? r.json() : { items: [] })),
    enabled: !!studyId,
  })
  const [local, setLocal] = useState<Record<string, TradeState>>({})
  const versions = useRef<Record<string, number>>({})
  const timers = useRef<Record<string, number>>({})
  const migrated = useRef(false)

  useEffect(() => {
    for (const it of data?.items ?? []) {
      if (!timers.current[it.id]) versions.current[it.id] = it.version
    }
    if (!studyId || !data || migrated.current || data.items.length) return
    migrated.current = true
    let legacy: Partial<PughState> | null = null
    try { const raw = localStorage.getItem(LEGACY_PUGH_KEY); legacy = raw ? JSON.parse(raw) : null } catch { legacy = null }
    if (!legacy) return
    void fetch(`${API}/studies/${studyId}/trades`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: 'T-01', state: legacy }),
    }).then(r => {
      if (r.ok) { try { localStorage.removeItem(LEGACY_PUGH_KEY) } catch { /* private mode */ } }
      void qc.invalidateQueries({ queryKey: key })
    })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, studyId])

  const put = useCallback(async (tid: string, state: TradeState) => {
    if (!studyId) return
    const res = await fetch(`${API}/studies/${studyId}/trades/${encodeURIComponent(tid)}`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ state, version: versions.current[tid] ?? 0 }),
    })
    delete timers.current[tid]
    if (res.ok) {
      const saved: TradeItem = await res.json()
      versions.current[tid] = saved.version
      qc.setQueryData<{ items: TradeItem[] }>(key, old => old ? { ...old, items: old.items.map(x => (x.id === tid ? saved : x)) } : old)
    } else if (res.status === 409) {
      setLocal(l => { const n = { ...l }; delete n[tid]; return n })
      void qc.invalidateQueries({ queryKey: key })
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [studyId, qc])

  const items: TradeItem[] = (data?.items ?? []).map(it => (local[it.id] ? { ...it, state: local[it.id] } : it))

  const update = useCallback((tid: string, patch: Partial<TradeState>) => {
    const base = local[tid] ?? data?.items.find(x => x.id === tid)?.state
    if (!base) return
    const next = { ...base, ...patch }
    setLocal(l => ({ ...l, [tid]: next }))
    if (timers.current[tid]) window.clearTimeout(timers.current[tid])
    timers.current[tid] = window.setTimeout(() => { void put(tid, next) }, 400)
  }, [local, data, put])

  const create = useCallback(async (title: string, seat: string) => {
    if (!studyId) return null
    const res = await fetch(`${API}/studies/${studyId}/trades`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ state: { title, seat, criteria: DEFAULT_CRITERIA, options: [i18n.t('Option A'), i18n.t('Option B'), i18n.t('Option C')], datum: 0 } }),
    })
    if (!res.ok) return null
    const it: TradeItem = await res.json()
    await qc.invalidateQueries({ queryKey: key })
    return it.id
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [studyId, qc])

  const remove = useCallback(async (tid: string) => {
    if (!studyId) return
    await fetch(`${API}/studies/${studyId}/trades/${encodeURIComponent(tid)}`, { method: 'DELETE' })
    setLocal(l => { const n = { ...l }; delete n[tid]; return n })
    await qc.invalidateQueries({ queryKey: key })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [studyId, qc])

  /** Record the decision on the server (the trade is kept; the study decision record is written). */
  const decide = useCallback(async (tid: string, selected: string, rationale: string, seat: string, cond?: ConditionValue) => {
    if (!studyId) return false
    if (timers.current[tid]) { window.clearTimeout(timers.current[tid]); const st = local[tid]; if (st) await put(tid, st) }
    const extra = cond ? { condition: cond.condition, due: cond.due, fallback: cond.fallback, blocks_gate: cond.blocks_gate,
      risks: cond.risks.split(/[,;\s]+/).map(x => x.trim()).filter(Boolean) } : {}
    const res = await fetch(`${API}/studies/${studyId}/trades/${encodeURIComponent(tid)}/decision`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ selected, rationale, seat, ...extra }),
    })
    if (!res.ok) return false
    setLocal(l => { const n = { ...l }; delete n[tid]; return n })
    await qc.invalidateQueries({ queryKey: key })
    await qc.invalidateQueries({ queryKey: ['trades-summary', studyId] })
    await qc.invalidateQueries({ queryKey: ['open-items', studyId] })
    return true
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [studyId, qc, local, put])

  return { items, isLoading, update, create, remove, decide }
}

export function DecisionPanel() {
  const { t } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const focusElementId = useUIStore(s => s.focusElementId)
  const currentLevel = useUIStore(s => s.currentLevel)

  const { data: allElements = [] } = useQuery({
    queryKey: ['elements', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/elements`).then(r => r.json()),
    enabled: !!studyId, structuralSharing: false,
  })

  const focusElement = allElements.find((e: any) => e.id === focusElementId)
  const isSpaceSegment = focusElement?.segment === 'space'
  const isGroundSegment = focusElement?.segment === 'ground'

  return (
    <div className="c2o-pane">
      <h2 className="c2o-panel__title mb-2">
        {t('Decision Support — Level {{level}}', { level: currentLevel })}
      </h2>

      {/* Decision categorization — always shown */}
      <DecisionCategorizer currentLevel={currentLevel} focusElement={focusElement} />

      {/* Architecture trades driven by requirements */}
      <ArchitectureTradeWidget currentLevel={currentLevel} focusElement={focusElement} />

      {/* Level 0: Mission-level decisions */}
      {currentLevel === 0 && <MissionTradeWidget studyId={studyId} />}
      {currentLevel === 0 && <OrbitTradeWidget studyId={studyId} />}

      {/* Level 1: System-level decisions */}
      {(currentLevel === 1 || isSpaceSegment) && <ConstellationWidget studyId={studyId} />}
      {currentLevel === 1 && isSpaceSegment && <CostLearningCurveWidget />}
      {(currentLevel === 1 || isGroundSegment) && <GroundTradeWidget studyId={studyId} />}
      {currentLevel >= 1 && <ContactScheduleWidget studyId={studyId} />}

      {/* Any level: the study's trade studies — weighting first, then scoring */}
      <TradeStudies studyId={studyId} />

      {/* Wave 3 (3.D4, 3.D7): the open-item register and the change-control flow */}
      <OpenItemsPanel studyId={studyId} />
      <ChangeControlCard studyId={studyId} />
      {/* Wave 3: change proposals (L 3.L4), negotiation records (H 3.H6), sensitivity (H 3.H5) */}
      {studyId && <div className="mt-2"><ChangesPanel studyId={studyId} /></div>}
      <div className="mt-2"><NegotiationPanel studyId={studyId} /></div>
      <div className="mt-2"><SensitivityView studyId={studyId} /></div>
    </div>
  )
}

// ─── Trade studies (W6): list, weighting, Pugh matrix, sensitivity, decision ───

function splitList(v: string): string[] {
  return v.split(/[,;\n]/).map(x => x.trim()).filter(Boolean)
}

function TradeStudies({ studyId }: { studyId: string | null }) {
  const { t } = useTranslation()
  const trades = useTrades(studyId)
  const [picked, setPicked] = useState<string | null>(null)
  const seatTeam = useSeatStore(st => st.team)
  const mySeat = seatTeam?.enabled ? (seatTeam.me?.active ?? '') : ''
  const current = trades.items.find(x => x.id === picked) ?? trades.items[0] ?? null
  const tid = current?.id ?? null
  const st = current?.state ?? null
  const weights = st ? tradeWeights(st) : {}
  const upd = (patch: Partial<TradeState>) => { if (tid) trades.update(tid, patch) }

  const addTrade = async () => {
    const title = await askText(t('Title of the new trade study:'), '')
    if (title == null) return
    const id = await trades.create(title.trim() || t('New trade'), mySeat)
    if (id) setPicked(id)
  }
  const removeTrade = async () => {
    if (!tid || !(await askConfirm(t('Delete the trade study {{id}}?', { id: tid }), { danger: true }))) return
    await trades.remove(tid)
    setPicked(null)
  }

  return (
    <>
      <ToolSection whereId="trades" title={t('Trade studies')} color="var(--cat-6)">
        <div className="t-12 c-2 mb-1">
          {t('Each trade compares options against a datum with weighted criteria. Every trade is kept with the study; Record decision writes its decision record and keeps the trade.')}
        </div>
        <TradeGateSummary studyId={studyId} />
        <div className="flex gap-1 wrap ai-c mb-1" data-testid="trade-list">
          {trades.items.length > 0 && (
            <Select dense aria-label={t('Trade study')} value={tid ?? ''} onChange={e => setPicked(e.target.value)}>
              {[...LEVELS, ''].map(lv => {
                const group = trades.items.filter(it => (it.state.level || '') === lv)
                if (!group.length) return null
                return (
                  <optgroup key={lv || 'other'} label={lv ? t(LEVEL_LABEL[lv]) : t('Other')}>
                    {group.map(it => (
                      <option key={it.id} value={it.id}>
                        {it.id} {it.state.title}{it.state.gate ? ` · ${it.state.gate.toUpperCase()}` : ''}{it.state.status === 'decided' ? ` ✓` : ''}
                      </option>
                    ))}
                  </optgroup>
                )
              })}
            </Select>
          )}
          <Button size="sm" onClick={() => void addTrade()}>{t('+ New trade')}</Button>
          {tid && <Button size="sm" variant="quiet" onClick={() => void removeTrade()}>{t('Delete trade')}</Button>}
          <span className="grow" />
          {studyId && trades.items.length > 0 && (
            <Button size="sm" variant="quiet" onClick={() => void downloadPost(`${API}/studies/${studyId}/trades/report?lang=${i18n.language === 'fr' ? 'fr' : 'en'}`, 'SpaceCDF_Trade_reports.docx')}>
              {t('Trade-off report (.docx)')}
            </Button>
          )}
        </div>
        {trades.isLoading && <p className="t-12 c-2 m-0">{t('Loading...')}</p>}
        {!trades.isLoading && trades.items.length === 0 && (
          <p className="t-12 c-2 m-0">{t('No trade study yet. Add one to compare options.')}</p>
        )}
        {st && tid && (
          <div className="stack gap-1">
            <div className="flex gap-1 wrap">
              <Input dense aria-label={t('Title')} placeholder={t('Title')} value={st.title} style={{ flex: 2, minWidth: '14rem' }}
                onChange={e => upd({ title: e.target.value })} />
              <Input dense aria-label={t('Owner seat')} placeholder={t('Owner seat')} value={st.seat} style={{ flex: 1, minWidth: '8rem' }}
                onChange={e => upd({ seat: e.target.value })} />
              <Select dense aria-label={t('Level')} value={st.level} onChange={e => upd({ level: e.target.value })}>
                <option value="">{t('Level')}</option>
                {LEVELS.map(lv => <option key={lv} value={lv}>{t(LEVEL_LABEL[lv])}</option>)}
              </Select>
              <Select dense aria-label={t('Review gate')} value={st.gate ?? ''} onChange={e => upd({ gate: e.target.value })}>
                <option value="">{t('No gate')}</option>
                {GATES.map(g => <option key={g} value={g}>{g.toUpperCase()}</option>)}
              </Select>
              <Select dense aria-label={t('Scoring')} value={st.method ?? 'pugh_weighted'}
                onChange={e => upd({ method: e.target.value as TradeState['method'] })}>
                <option value="pugh_weighted">{t('Weighted Pugh (−2 to +2 against the datum)')}</option>
                <option value="absolute_scale">{t('Absolute scale (1 to 5 per criterion)')}</option>
              </Select>
            </div>
            {st.decision_question && <p className="t-12 c-2 m-0">{t('Decision to make: {{q}}', { q: st.decision_question })}</p>}
          </div>
        )}
      </ToolSection>
      {st && tid && st.method === 'absolute_scale' && (
        <ToolSection whereId="trade-absolute" title={t('Absolute-scale matrix')} color="var(--cat-6)">
          <AbsoluteScaleMatrix state={st} evaluation={current?.evaluation ?? null} onChange={p => upd(p as Partial<TradeState>)} />
          <TradeSensitivityPm20 evaluation={current?.evaluation ?? null} />
        </ToolSection>
      )}
      {st && tid && (<>
        {st.method !== 'absolute_scale' && (<>
          <PairwiseWeightingWidget weights={weights} comparisons={st.comparisons || {}}
            onComparisonsChanged={c => upd({ comparisons: c, weights_mode: 'pairwise' })}
            criteria={st.criteria} onCriteriaChanged={c => upd({ criteria: c })} />
          <PughMatrixWidget tradeId={tid} weights={weights} criteria={st.criteria} onCriteriaChanged={c => upd({ criteria: c })}
            state={st} onChange={upd} />
          <TradeSensitivity evaluation={current?.evaluation ?? null} />
          <TradeSensitivityPm20 evaluation={current?.evaluation ?? null} />
        </>)}
        <TradeLinksAndDecision tradeId={tid} state={st} evaluation={current?.evaluation ?? null} onChange={upd}
          onDecide={(sel, why, cond) => trades.decide(tid, sel, why, mySeat || st.seat, cond)} />
      </>)}
    </>
  )
}

async function downloadPost(url: string, fallbackName: string) {
  const res = await fetch(url, { method: 'POST' })
  if (!res.ok) { void showAlert(i18n.t('The document could not be generated ({{code}}).', { code: res.status })); return }
  const blob = await res.blob()
  const cd = res.headers.get('content-disposition') || ''
  const name = /filename="([^"]+)"/.exec(cd)?.[1] || fallbackName
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = name
  a.click()
  setTimeout(() => URL.revokeObjectURL(a.href), 1000)
}

function TradeSensitivity({ evaluation }: { evaluation: TradeEvaluation | null }) {
  const { t } = useTranslation()
  if (!evaluation || !evaluation.sensitivity.length) return null
  return (
    <ToolSection whereId="trade-sensitivity" title={t('Weight sensitivity')} color="var(--cat-2)">
      <div className="t-12 c-2 mb-1">
        {evaluation.robust
          ? t('Robust: no single weight change of 10 points or less changes the leader ({{w}}).', { w: evaluation.winner ?? '' })
          : t('Sensitive: a change of 10 points or less in one weight changes the leader ({{w}}).', { w: evaluation.winner ?? '' })}
      </div>
      <table className="c2o-table c2o-table--dense" data-testid="trade-sensitivity">
        <thead><tr className="bb"><th>{t('Criterion')}</th><th className="num">{t('Weight')}</th><th className="num">{t('Change that flips the leader')}</th><th>{t('New leader')}</th></tr></thead>
        <tbody>
          {evaluation.sensitivity.map(s => (
            <tr key={s.criterion} className="bb">
              <td>{t(s.criterion, { context: 'criterion' })}</td>
              <td className="num">{(s.weight * 100).toFixed(0)}%</td>
              <td className={`num${s.robust ? '' : ' c-caution w-600'}`}>{s.flip ? `${s.flip.delta > 0 ? '+' : ''}${(s.flip.delta * 100).toFixed(0)} ${t('points')}` : t('none')}</td>
              <td>{s.flip?.new_winner ?? ''}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </ToolSection>
  )
}

function TradeLinksAndDecision({ tradeId, state, evaluation, onChange, onDecide }: {
  tradeId: string; state: TradeState; evaluation: TradeEvaluation | null
  onChange: (patch: Partial<TradeState>) => void
  onDecide: (selected: string, rationale: string, cond: ConditionValue) => Promise<boolean>
}) {
  const { t } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const links = state.links ?? {}
  const dec = state.decision ?? {}
  const [selected, setSelected] = useState<string>(dec.selected ?? evaluation?.winner ?? state.options[state.datum] ?? '')
  const [why, setWhy] = useState<string>(dec.rationale ?? '')
  const condOf = (d: TradeDecision): ConditionValue => ({ condition: d.condition ?? '', due: d.due ?? '', fallback: d.fallback ?? '',
    risks: (d.risks ?? []).join(', '), blocks_gate: d.blocks_gate ?? '' })
  const [cond, setCond] = useState<ConditionValue>(condOf(dec))
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)
  useEffect(() => {
    setSelected(state.decision?.selected ?? evaluation?.winner ?? state.options[state.datum] ?? '')
    setWhy(state.decision?.rationale ?? '')
    setCond(condOf(state.decision ?? {}))
    setMsg(null)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tradeId])
  const setLinks = (patch: Partial<TradeLinks>) => onChange({ links: { ...links, ...patch } })
  const totals = evaluation?.totals ?? []
  const best = evaluation?.winner ?? ''
  return (
    <ToolSection whereId="trade-decision" title={t('Links and decision')} color="var(--cat-6)">
      <div className="stack gap-1 t-12">
        <label className="flex gap-1 ai-c">
          <span style={{ width: '11rem' }}>{t('Decision record')}</span>
          <Input dense value={links.decision_record ?? ''} placeholder="D-PAY-01" onChange={e => setLinks({ decision_record: e.target.value })} />
        </label>
        <label className="flex gap-1 ai-c">
          <span style={{ width: '11rem' }}>{t('Requirements affected')}</span>
          <Input dense style={{ flex: 1 }} value={(links.requirements ?? []).join(', ')} placeholder="PAY-OPT-01, EPS-SA-01"
            onChange={e => setLinks({ requirements: splitList(e.target.value) })} />
        </label>
        <label className="flex gap-1 ai-c">
          <span style={{ width: '11rem' }}>{t('Risks affected')}</span>
          <Input dense style={{ flex: 1 }} value={(links.risks ?? []).join(', ')} placeholder="RSK-010"
            onChange={e => setLinks({ risks: splitList(e.target.value) })} />
        </label>
        <label className="flex gap-1 ai-c">
          <span style={{ width: '11rem' }}>{t('Selected option')}</span>
          <Select dense value={selected} onChange={e => setSelected(e.target.value)}>
            {state.options.map(o => <option key={o} value={o} disabled={!!state.screened?.[o]}>{o}{state.option_labels?.[o] ? `: ${state.option_labels[o]}` : ''}{o === best ? ' ★' : ''}{state.screened?.[o] ? ` (${t('screened out')})` : ''}</option>)}
          </Select>
          {dec.selected && <Tag>{t('Decided: {{o}}', { o: dec.selected })}</Tag>}
        </label>
        <Textarea rows={3} aria-label={t('Rationale')} placeholder={t('Why this option (required when it is not the highest score)')}
          value={why} onChange={e => setWhy(e.target.value)} />
        {selected && best && selected !== best && <Note tone="caution">{t('The selected option is not the highest weighted score: say why in the rationale.')}</Note>}
        <ConditionFields value={cond} onChange={setCond} />
        <div className="flex gap-1 wrap ai-c">
          <Button size="sm" variant="primary" busy={busy}
            disabledReason={!selected ? t('Pick the selected option') : (selected !== best && !why.trim()) ? t('Give the rationale first') : undefined}
            onClick={async () => {
              setBusy(true); setMsg(null)
              const ok = await onDecide(selected, why, cond)
              setBusy(false)
              setMsg(ok ? t('Decision recorded on {{id}}; the trade is kept.', { id: tradeId }) : t('The decision could not be recorded.'))
            }}>
            {t('Record decision on the trade')}
          </Button>
          <RecordDecision decision="D-3.4-TRADE" capture="decide:pugh" context={{ trade: tradeId }} label={t('Write it in my logbook')} prefill={() => ({
            options: state.options.map(o => {
              const tot = totals.find(x => x.option === o)
              return {
                name: o,
                summary: tot?.datum ? t('Datum (reference)') : undefined,
                values: tot && !tot.datum ? { [t('Weighted Total')]: tot.weighted } : {},
                chosen: o === selected || undefined,
              }
            }),
            criteria: state.criteria.map(c => ({ name: t(c, { context: 'criterion' }), weight: Math.round((evaluation?.weights?.[c] ?? 0) * 100) / 100 })),
            choice: selected,
            rationale: why || undefined,
            evidence: [{ label: t('Method'), value: t('Pugh Matrix (Weighted)') }, { label: t('Trade'), value: `${tradeId} ${state.title}` }],
          })} />
          {studyId && dec.selected && (
            <RaiseChangeButton studyId={studyId} tradeId={tradeId} decided={state.status === 'decided' || !!dec.selected} />
          )}
        </div>
        {msg && <div role="status" className="t-12 c-2">{msg}</div>}
      </div>
    </ToolSection>
  )
}

// ─── Mission Trade: Space vs Non-Space ───

function MissionTradeWidget(_props: { studyId: string | null }) {
  const { t } = useTranslation()
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [gsd, setGsd] = useState('5')
  const [revisit, setRevisit] = useState('1')
  const [budget, setBudget] = useState('2000')

  const runTrade = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API}/lifecycle/mission-trade`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_gsd_m: parseFloat(gsd) || 5,
          target_revisit_days: parseFloat(revisit) || 1,
          target_coverage: 'regional',
          target_latency_hours: 24,
          require_data_ownership: true,
          max_annual_budget_keur: parseFloat(budget) || 2000,
          mission_type: 'earth_observation',
          num_spacecraft: 1,
        }),
      })
      if (res.ok) setResult(await res.json())
    } finally { setLoading(false) }
  }

  return (
    <ToolSection whereId="mission-trade" title={t('Mission Trade: Space vs Alternatives')} color="var(--interactive)">
      <div className="flex gap-1 mb-1 wrap">
        <label className="c2o-inline-field">{t('GSD (m):')} <input type="number" value={gsd} onChange={e => setGsd(e.target.value)} className="c2o-input c2o-input--sm c2o-input--num c2o-w-num" /></label>
        <label className="c2o-inline-field">{t('Revisit (days):')} <input type="number" value={revisit} onChange={e => setRevisit(e.target.value)} className="c2o-input c2o-input--sm c2o-input--num c2o-w-num" /></label>
        <label className="c2o-inline-field">{t('Budget (kEUR/yr):')} <input type="number" value={budget} onChange={e => setBudget(e.target.value)} className="c2o-input c2o-input--sm c2o-input--num c2o-w-num" /></label>
      </div>
      <Button onClick={runTrade} busy={loading} variant="primary" size="sm">
        {loading ? t('Analysing...') : t('Evaluate Alternatives')}
      </Button>
      {result?.alternatives && (
        <div className="mt-2">
          {result.question && (
            <div className="t-12 c-accent w-600 mb-1">{result.question}</div>
          )}
          {result.alternatives.map((alt: any, i: number) => {
            const score = alt.score ?? (alt.rank ? (1 - (alt.rank - 1) * 0.15) : 0.5)
            return (
              <div key={i} className={`c2o-dec-row ${score > 0.7 ? '' : score > 0.4 ? 'is-caution' : 'is-alarm'}`}>
                <div className="flex jc-sb mb-1">
                  <span className="w-600">{alt.name}</span>
                  <span className="t-12 c-2">
                    {alt.category && <span className="mr-1">{alt.category}</span>}
                    #{alt.rank || i + 1}
                  </span>
                </div>
                <div className="t-12 c-2">{alt.description}</div>
                {alt.gsd_m && (
                  <div className="t-12 c-2 mt-1">
                    {t('GSD: {{gsd}}m | Revisit: {{revisit}}d | Cost: {{cost}} kEUR/yr', { gsd: alt.gsd_m, revisit: alt.revisit_days, cost: alt.annual_cost_keur })}
                  </div>
                )}
              </div>
            )
          })}
          {result.recommendation && (
            <div className="mt-1 p-1 bg-ok rounded t-12 c-ok">
              {result.recommendation}
            </div>
          )}
          <div className="row mt-1">
            <RecordDecision decision="D-1.4-SPACE" capture="decide:mission-trade" prefill={() => ({
              options: result.alternatives.map((alt: any, i: number) => ({
                name: String(alt.name),
                summary: String(alt.description || '').slice(0, 200),
                values: {
                  ...(alt.gsd_m != null ? { 'GSD (m)': alt.gsd_m } : {}),
                  ...(alt.revisit_days != null ? { [t('Revisit (d)')]: alt.revisit_days } : {}),
                  ...(alt.annual_cost_keur != null ? { [t('kEUR/yr')]: alt.annual_cost_keur } : {}),
                  [t('Rank')]: alt.rank || i + 1,
                },
                ...(typeof alt.score === 'number' ? { score: alt.score } : {}),
              })),
              criteria: [
                { name: t('GSD (m)'), direction: 'lower' as const },
                { name: t('Revisit (days)'), direction: 'lower' as const },
                { name: t('Budget (kEUR/yr)'), direction: 'lower' as const },
              ],
              evidence: [
                { label: t('Target GSD'), value: parseFloat(gsd) || gsd, unit: 'm' },
                { label: t('Target revisit'), value: parseFloat(revisit) || revisit, unit: t('days') },
                { label: t('Budget'), value: parseFloat(budget) || budget, unit: t('kEUR/yr') },
                ...(result.recommendation ? [{ label: t('Tool recommendation'), value: String(result.recommendation).slice(0, 200) }] : []),
              ],
            })} />
          </div>
        </div>
      )}
    </ToolSection>
  )
}

/** The candidates the orbit trade showed, as record options (the picked one chosen). */
function orbitName(c: any): string {
  return c.name || `${String(c.orbit_type || '').toUpperCase()} ${c.altitude_km} km`
}

/** The trade's top five (the workbook asks for the top three) plus the one picked. */
function orbitOptions(candidates: any[], picked: any) {
  const top = candidates.slice(0, 5)
  if (!top.includes(picked)) top.push(picked)
  return top.map((c: any) => ({
    name: orbitName(c),
    values: {
      'i (°)': Number((c.inclination_deg ?? 0).toFixed(1)),
      ...(c.achievable_gsd_m != null ? { 'GSD (m)': Number(c.achievable_gsd_m.toFixed(1)) } : {}),
      ...(c.revisit_days != null ? { [i18n.t('Revisit (d)')]: Number(c.revisit_days.toFixed(0)) } : {}),
      ...(c.natural_lifetime_years != null ? { [i18n.t('Lifetime (yr)')]: Number(c.natural_lifetime_years.toFixed(0)) } : {}),
      ...(c.compliant_25yr != null ? { [i18n.t('25-yr rule')]: !!c.compliant_25yr } : {}),
    },
    score: c.total_score || c.weighted_score || c.score || 0,
    chosen: c === picked || undefined,
  }))
}

// ─── Orbit Trade ───

/** ✓ / ✗ with the words for screen readers; — when the server did not say. */
function Compliance({ ok }: { ok: boolean | null | undefined }) {
  const { t } = useTranslation()
  if (ok == null) return <>—</>
  return (
    <span style={{ color: ok ? 'var(--success)' : 'var(--danger)' }}>
      <span aria-hidden="true">{ok ? '✓' : '✗'}</span>
      <span className="sr-only">{ok ? t('meets the rule') : t('does not meet the rule')}</span>
    </span>
  )
}

/** Orbit-trade candidate → PATCH /studies/{id}/mission ``orbit`` (SSO: inclination from the altitude). */
function tradeOrbitPatch(c: any): Record<string, unknown> {
  const t = String(c.orbit_type || '').toLowerCase()
  if (t === 'sso') return { orbit_type: 'sso', altitude_km: c.altitude_km, auto_inclination: true }
  const type = ['leo', 'meo', 'geo', 'heo', 'gto'].includes(t) ? t : t === 'molniya' || t === 'tundra' ? 'heo' : t === 'lunar' ? 'lunar' : 'leo'
  return { orbit_type: type, altitude_km: c.altitude_km, inclination_deg: c.inclination_deg, ltan: null, ...(c.eccentricity ? { eccentricity: c.eccentricity } : {}) }
}

function OrbitTradeWidget({ studyId }: { studyId: string | null }) {
  const { t } = useTranslation()
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const qc = useQueryClient()

  const runTrade = async () => {
    if (!studyId) return
    setLoading(true)
    try {
      const res = await fetch(`${API}/lifecycle/orbit-trade/${studyId}`)
      if (res.ok) setResult(await res.json())
    } finally { setLoading(false) }
  }

  return (
    <ToolSection whereId="orbit-trade" title={t('Orbit Trade Study')} color="var(--cat-2)">
      <Button onClick={runTrade} busy={loading} variant="primary" size="sm">
        {loading ? t('Computing...') : t('Evaluate Orbit Options')}
      </Button>
      {result?.candidates && (
        <div className="mt-2" style={{ overflowX: 'auto' }}>
          <table className="c2o-table c2o-table--dense">
            <thead>
              <tr className="bb">
                <th className="num">{t('Rank')}</th>
                <th>{t('Orbit')}</th>
                <th className="num">{t('Alt', { context: 'column' })}</th>
                <th className="num">{t('Inc', { context: 'column' })}</th>
                <th className="num" title={t('Orbital period (min)')}>{t('Period')}</th>
                <th className="num" title={t('Longest eclipse as a share of the orbit')}>{t('Eclipse')}</th>
                <th className="num">GSD</th>
                <th className="num">{t('Revisit')}</th>
                <th className="num" title={t('Natural orbital lifetime without propulsion (mean solar activity)')}>{t('Lifetime')}</th>
                <th className="ctr" title={t('Re-entry within 25 years (IADC / COPUOS guideline)')}>{t('25-yr')}</th>
                <th className="ctr" title={t('Re-entry within 5 years of the end of the mission (FCC rule, 2022)')}>{t('FCC 5-yr')}</th>
                <th className="num">{t('Score')}</th>
                <th className="ctr"></th>
              </tr>
            </thead>
            <tbody>
              {result.candidates.map((c: any, i: number) => (
                <tr key={i} className="bb">
                  <td className="p-1 ta-r mono">{c.rank ?? i + 1}</td>
                  <td className="p-1 w-500">{c.name || c.orbit_type}</td>
                  <td className="p-1 ta-r mono">{c.altitude_km}</td>
                  <td className="p-1 ta-r mono">{c.inclination_deg?.toFixed(1)}</td>
                  <td className="p-1 ta-r mono">{c.period_min != null ? `${Number(c.period_min).toFixed(1)} min` : '—'}</td>
                  <td className="p-1 ta-r mono">{c.eclipse_fraction != null ? `${(Number(c.eclipse_fraction) * 100).toFixed(0)} %` : '—'}</td>
                  <td style={{ padding: '0.2rem 0.3rem', textAlign: 'right', fontFamily: 'monospace', color: c.meets_gsd ? 'var(--success)' : 'var(--text-secondary)' }}>{c.achievable_gsd_m?.toFixed(1)}m</td>
                  <td className="p-1 ta-r mono">{c.revisit_days?.toFixed(0)}d</td>
                  <td className="p-1 ta-r mono t-12">{c.natural_lifetime_years != null ? `${Number(c.natural_lifetime_years).toFixed(1)} yr` : '—'}</td>
                  <td className="p-1 ta-c"><Compliance ok={c.compliant_25yr} /></td>
                  <td className="p-1 ta-c"><Compliance ok={c.compliant_5yr} /></td>
                  <td className="p-1 ta-r mono c-ok">{((c.total_score || c.weighted_score || c.score || 0) * 100).toFixed(0)}%</td>
                  <td className="p-1 ta-c">
                    <button onClick={async () => {
                      // Make this the mission orbit (study.requirements.orbit, read by every
                      // analysis). It used to go on the focused element's performance, which no
                      // analysis read.
                      const sid = useUIStore.getState().studyId
                      if (!sid) return
                      const res = await fetch(`${API}/studies/${encodeURIComponent(sid)}/mission`, {
                        method: 'PATCH', headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ orbit: tradeOrbitPatch(c) }),
                      })
                      if (!res.ok) {
                        const d = (await res.json().catch(() => ({})))?.detail
                        void showAlert(typeof d === 'string' ? serverText(d) : i18n.t('Could not save the mission definition'))
                        return
                      }
                      for (const k of ['study', 'analyses', 'analysis']) qc.invalidateQueries({ queryKey: [k] })
                      void showAlert(i18n.t('Applied: {{name}} ({{alt}}km, {{incl}}°)', { name: c.name, alt: c.altitude_km, incl: c.inclination_deg }))
                    }} type="button" className="c2o-btn c2o-btn--sm">
                      {t('Apply')}
                    </button>
                    <RecordDecision decision="D-2.3-ORBIT" capture="decide:orbit-trade" label={t('Record')}
                      context={{ element: (() => {
                        const els: any[] = qc.getQueryData(['elements', useUIStore.getState().studyId]) || []
                        return els.find((e: any) => e.id === useUIStore.getState().focusElementId)?.name ?? null
                      })() }}
                      prefill={() => {
                        const study: any = qc.getQueryData(['study', useUIStore.getState().studyId])
                        const o = study?.requirements?.orbit || {}
                        const perf = { orbit_altitude_km: o.altitude_km, orbit_inclination_deg: o.inclination_deg }
                        return {
                          options: orbitOptions(result.candidates, c),
                          choice: `${orbitName(c)}, ${Number(c.inclination_deg ?? 0).toFixed(1)}°`,
                          evidence: [
                            { label: t('Altitude'), unit: 'km', after: c.altitude_km, ...(perf.orbit_altitude_km != null ? { before: perf.orbit_altitude_km } : {}) },
                            { label: t('Inclination'), unit: '°', after: Number(Number(c.inclination_deg ?? 0).toFixed(1)), ...(perf.orbit_inclination_deg != null ? { before: perf.orbit_inclination_deg } : {}) },
                            ...(c.natural_lifetime_years != null ? [{ label: t('Natural lifetime'), value: Number(c.natural_lifetime_years.toFixed(1)), unit: t('yr') }] : []),
                            ...(c.achievable_gsd_m != null ? [{ label: 'GSD', value: Number(c.achievable_gsd_m.toFixed(1)), unit: 'm' }] : []),
                          ],
                        }
                      }} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="mt-1">
            <RecordAsTradeButton studyId={studyId} tool="orbit" title={t('Operational orbit')}
              options={result.candidates.slice(0, 8).map((c: any, i: number) => ({
                id: String.fromCharCode(65 + i), label: `${orbitName(c)}, ${Number(c.inclination_deg ?? 0).toFixed(1)}°`,
                metrics: { [t('GSD (m)')]: c.achievable_gsd_m != null ? Number(Number(c.achievable_gsd_m).toFixed(1)) : null,
                  [t('Revisit (days)')]: c.revisit_days != null ? Number(Number(c.revisit_days).toFixed(1)) : null,
                  [t('Natural lifetime (yr)')]: c.natural_lifetime_years != null ? Number(Number(c.natural_lifetime_years).toFixed(1)) : null,
                  [t('Eclipse (% of orbit)')]: c.eclipse_fraction != null ? Math.round(Number(c.eclipse_fraction) * 100) : null },
              }))} />
          </div>
          <p className="t-12 c-3 m-0 mt-1 measure">
            {t('Lifetime: natural decay without propulsion at mean solar activity. 25-yr: re-entry within 25 years (IADC / COPUOS guideline). FCC 5-yr: re-entry within 5 years after the mission ends (FCC rule, 2022). Apply makes it the mission orbit; the analyses run with the old orbit are then marked stale.')}
          </p>
        </div>
      )}
    </ToolSection>
  )
}

// ─── Constellation Sizing ───

function ConstellationWidget(_props: { studyId: string | null }) {
  const { t } = useTranslation()
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const qc = useQueryClient()
  const [altitude, setAltitude] = useState('500')
  const [inclination, setInclination] = useState('97.4')
  const [revisitHours, setRevisitHours] = useState('24')

  const runDesign = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API}/lifecycle/constellation/design`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          altitude_km: parseFloat(altitude),
          inclination_deg: parseFloat(inclination),
          target_revisit_hours: parseFloat(revisitHours),
        }),
      })
      if (res.ok) setResult(await res.json())
    } finally { setLoading(false) }
  }

  return (
    <ToolSection whereId="constellation" title={t('Constellation Sizing')} color="var(--interactive)">
      <div className="flex gap-1 mb-1 wrap">
        <label className="c2o-inline-field">{t('Alt (km):')} <input type="number" value={altitude} onChange={e => setAltitude(e.target.value)} className="c2o-input c2o-input--sm c2o-input--num c2o-w-num" /></label>
        <label className="c2o-inline-field">{t('Inc (°):')} <input type="number" value={inclination} onChange={e => setInclination(e.target.value)} className="c2o-input c2o-input--sm c2o-input--num c2o-w-num" /></label>
        <label className="c2o-inline-field">{t('Revisit (h):')} <input type="number" value={revisitHours} onChange={e => setRevisitHours(e.target.value)} className="c2o-input c2o-input--sm c2o-input--num c2o-w-num" /></label>
      </div>
      <Button onClick={runDesign} busy={loading} variant="primary" size="sm">
        {loading ? t('Computing...') : t('Size Constellation')}
      </Button>
      {result && (
        <div className="mt-2 t-12">
          {(result.candidates || result.options || []).map((opt: any, i: number) => (
            <div key={i} className="c2o-dec-row">
              <div className="flex jc-sb">
                <span className="w-600">
                  {opt.walker_notation || t('{{planes}}P × {{sats}}S = {{total}} sats', { planes: opt.num_planes || opt.planes, sats: opt.sats_per_plane, total: opt.total_satellites || opt.total_sats })}
                </span>
                <span className="c-accent mono">
                  {opt.total_cost_meur != null ? `${opt.total_cost_meur.toFixed(1)}M€` : ''}
                </span>
              </div>
              <div className="t-12 c-2">
                {t('Revisit: {{max}}h max, {{mean}}h mean', { max: (opt.max_revisit_hours || opt.revisit_hours)?.toFixed(1), mean: (opt.mean_revisit_hours)?.toFixed(1) })}
                {opt.coverage_percent != null && t(' | Coverage: {{pct}}%', { pct: opt.coverage_percent.toFixed(0) })}
                {opt.total_mass_kg != null && t(' | Mass: {{mass}}kg', { mass: opt.total_mass_kg })}
                {opt.spares != null && t(' | Spares: {{n}}', { n: opt.spares })}
              </div>
              <button onClick={async () => {
                const fid = useUIStore.getState().focusElementId
                const sid = useUIStore.getState().studyId
                if (!fid || !sid) { void showAlert(i18n.t('Drill into a spacecraft element first')); return }
                const els: any[] = qc.getQueryData(['elements', sid]) || []
                const el = els.find((e: any) => e.id === fid)
                if (!el) return
                await fetch(`${API}/elements/${fid}`, {
                  method: 'PATCH', headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({
                    quantity: opt.total_satellites || opt.total_sats,
                    performance: { ...((el as any).performance || {}), constellation: true, orbital_planes: opt.num_planes || opt.planes, sats_per_plane: opt.sats_per_plane, walker_notation: opt.walker_notation },
                    version: el.version,
                  }),
                })
                qc.invalidateQueries({ queryKey: ['elements'] })
                void showAlert(i18n.t('Applied: {{what}}', { what: opt.walker_notation || i18n.t('{{n}} sats', { n: opt.total_satellites }) }))
              }} type="button" className="c2o-btn c2o-btn--sm mt-1">
                {t('Apply to Design')}
              </button>
              <RecordDecision decision="D-2.3-CONSTELLATION" capture="decide:constellation" prefill={() => {
                const label = (o: any) => o.walker_notation || t('{{planes}}P × {{sats}}S = {{total}} sats', { planes: o.num_planes || o.planes, sats: o.sats_per_plane, total: o.total_satellites || o.total_sats })
                return {
                  options: (result.candidates || result.options || []).map((o: any) => ({
                    name: label(o),
                    values: {
                      [t('Max revisit (h)')]: Number(((o.max_revisit_hours || o.revisit_hours) ?? 0).toFixed(1)),
                      ...(o.coverage_percent != null ? { [t('Coverage (%)')]: Number(o.coverage_percent.toFixed(0)) } : {}),
                      ...(o.total_cost_meur != null ? { 'M€': Number(o.total_cost_meur.toFixed(1)) } : {}),
                      ...(o.total_mass_kg != null ? { kg: o.total_mass_kg } : {}),
                    },
                    chosen: o === opt || undefined,
                  })),
                  choice: label(opt),
                  evidence: [
                    { label: t('Altitude'), value: parseFloat(altitude), unit: 'km' },
                    { label: t('Inclination'), value: parseFloat(inclination), unit: '°' },
                    { label: t('Target revisit'), value: parseFloat(revisitHours), unit: 'h' },
                  ],
                }
              }} />
            </div>
          ))}
          {result.count != null && (
            <div className="t-12 c-2 mt-1">
              {t('{{count}} configurations evaluated', { count: result.count })}
            </div>
          )}
        </div>
      )}
    </ToolSection>
  )
}

// ─── Ground Segment Trade ───

function GroundTradeWidget({ studyId }: { studyId: string | null }) {
  const { t } = useTranslation()
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const runTrade = async () => {
    if (!studyId) return
    setLoading(true)
    try {
      const res = await fetch(`${API}/lifecycle/ground/trade/${studyId}`)
      if (res.ok) setResult(await res.json())
    } finally { setLoading(false) }
  }

  return (
    <ToolSection whereId="ground-trade" title={t('Ground Segment Trade')} color="var(--status-ok)">
      <Button onClick={runTrade} busy={loading} variant="primary" size="sm">
        {loading ? t('Analysing...') : t('Evaluate Ground Architectures')}
      </Button>
      {result?.alternatives && (
        <div className="mt-2">
          {result.alternatives.map((alt: any, i: number) => (
            <div key={i} className="c2o-dec-row">
              <div className="flex jc-sb">
                <span className="w-600">{alt.name}</span>
                <span className="mono c-ok">{((alt.score || 0) * 100).toFixed(0)}%</span>
              </div>
              <div className="t-12 c-2">
                {alt.stations?.join(', ') || alt.description}
                {alt.contact_minutes_per_day && t(' | {{min}} min/day contact', { min: alt.contact_minutes_per_day.toFixed(0) })}
                {alt.annual_cost_keur && t(' | {{cost}} kEUR/yr', { cost: alt.annual_cost_keur })}
              </div>
              <RecordDecision decision="D-5.1-GROUND" capture="decide:ground-trade" prefill={() => ({
                options: result.alternatives.map((a: any) => ({
                  name: String(a.name),
                  summary: (a.stations?.join(', ') || a.description || '').slice(0, 200),
                  values: {
                    ...(a.contact_minutes_per_day ? { [t('min/day')]: Number(a.contact_minutes_per_day.toFixed(0)) } : {}),
                    ...(a.annual_cost_keur ? { [t('kEUR/yr')]: a.annual_cost_keur } : {}),
                  },
                  score: a.score || 0,
                  chosen: a === alt || undefined,
                })),
                choice: String(alt.name),
                evidence: result.recommendation ? [{ label: t('Tool recommendation'), value: String(result.recommendation).slice(0, 200) }] : undefined,
              })} />
            </div>
          ))}
          {result.recommendation && (
            <div className="mt-1 p-1 bg-ok rounded t-12 c-ok">
              {result.recommendation}
            </div>
          )}
          <div className="mt-1">
            <RecordAsTradeButton studyId={studyId} tool="ground" title={t('Ground segment architecture')}
              options={result.alternatives.slice(0, 8).map((a: any, i: number) => ({
                id: String.fromCharCode(65 + i), label: String(a.name),
                metrics: { [t('Contact (min/day)')]: a.contact_minutes_per_day != null ? Math.round(a.contact_minutes_per_day) : null,
                  [t('Annual cost (kEUR)')]: a.annual_cost_keur ?? null },
              }))} />
          </div>
        </div>
      )}
    </ToolSection>
  )
}

// ─── Contact Schedule ───

function ContactScheduleWidget({ studyId }: { studyId: string | null }) {
  const { t } = useTranslation()
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const qc = useQueryClient()

  const runSchedule = async () => {
    if (!studyId) return
    setLoading(true)
    try {
      // The mission orbit (study.requirements.orbit) and the study's ground stations with
      // their own coordinates (KB picks and stations entered by hand)
      const elements: any[] = qc.getQueryData(['elements', studyId]) || await fetch(`${API}/studies/${studyId}/elements`).then(r => r.json())
      const study: any = await fetch(`${API}/studies/${studyId}`).then(r => (r.ok ? r.json() : null))
      const altitude = study?.requirements?.orbit?.altitude_km ?? 500
      const inclination = study?.requirements?.orbit?.inclination_deg ?? 97.4
      const gs: any = await fetch(`${API}/studies/${studyId}/ground-stations`).then(r => (r.ok ? r.json() : { selected: [] }))
      const gsElements: any[] = (gs.selected || []).filter((s: any) => s.lat !== null && s.lat !== undefined && s.lon !== null && s.lon !== undefined)
      // POST /api/ground/schedule takes ``orbit_params`` and ``stations`` (StationIn); the
      // widget used to send ``orbit`` / ``custom_stations``, which the server ignored.
      const customStations = gsElements.map((s: any) => ({
        id: String(s.station_id || s.kb_station_id || s.element_id),
        name: s.name,
        latitude_deg: Number(s.lat),
        longitude_deg: Number(s.lon),
        elevation_m: Number(s.alt_m) || 0,
        antenna_diameter_m: Number(s.antenna_m) || 3.7,
        min_elevation_deg: Number(s.min_elevation_deg) || 5,
        band: String((s.bands || ['S'])[0] || 'S'),
      }))

      // Find number of spacecraft
      const spacecraft = elements.filter((e: any) => e.segment === 'space' && e.element_type === 'system')
      const totalSats = spacecraft.reduce((s: number, e: any) => s + (e.quantity || 1), 0)

      const body: any = { orbit_params: { altitude_km: altitude, inclination_deg: inclination } }
      if (customStations.length > 0) body.stations = customStations
      const rate = Number(study?.requirements?.link?.downlink_rate_bps)
      if (rate > 0) body.data_rate_mbps = rate / 1e6

      const res = await fetch(`${API}/ground/schedule`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (res.ok) {
        const data = await res.json()
        data._design_context = { altitude, inclination, ground_stations: gsElements.length, spacecraft: totalSats }
        data._names = Object.fromEntries(customStations.map((s: any) => [s.id, s.name]))
        setResult(data)
      }
    } finally { setLoading(false) }
  }

  return (
    <ToolSection whereId="contacts" title={t('Ground Contact Schedule')} color="var(--interactive)">
      <div className="t-12 c-2 mb-1">
        {t("Uses your design's orbit parameters and ground stations from the element tree.")}
      </div>
      <Button onClick={runSchedule} busy={loading} variant="primary" size="sm">
        {loading ? t('Computing...') : t('Predict Contact Windows')}
      </Button>
      {result?._design_context && (
        <div className="t-12 c-accent mt-1">
          {t('Using: {{alt}}km, {{incl}}° inc, {{count}} ground stations, {{sc}} spacecraft', { alt: result._design_context.altitude, incl: result._design_context.inclination, count: result._design_context.ground_stations, sc: result._design_context.spacecraft, defaultValue_one: 'Using: {{alt}}km, {{incl}}° inc, {{count}} ground station, {{sc}} spacecraft' })}
        </div>
      )}
      {result && (
        <div className="mt-2 t-12">
          {(result.coverage_stats || result.contacts) && (
            <div className="c2o-dec-row">
              <span>{t('Contacts:')} <b>{result.contacts?.length || result.coverage_stats?.total_passes_per_day || '?'}</b></span>
              {(result.total_contact_min_per_day ?? result.coverage_stats?.total_contact_minutes_per_day) != null && (
                <span className="ml-2">{t('Contact:')} <b>{t('{{min}} min/day', { min: Number(result.total_contact_min_per_day ?? result.coverage_stats?.total_contact_minutes_per_day).toFixed(1) })}</b></span>
              )}
            </div>
          )}
          {(result.contacts || result.windows)?.slice(0, 8).map((w: any, i: number) => {
            const dur = w.duration_min ?? ((w.end_s - w.start_s) / 60)
            return (
              <div key={i} className="p-1 t-12 c-2 bb">
                <span className="w-500 c-1">{w.station || result._names?.[w.station_id] || w.station_id}</span>
                {' '}{t('{{dur}} min | max el: {{el}}°', { dur: dur.toFixed(1), el: w.max_elevation_deg?.toFixed(0) })}
                {w.data_volume_mbit && ` | ${(w.data_volume_mbit / 1000).toFixed(1)} Gbit`}
              </div>
            )
          })}
        </div>
      )}
    </ToolSection>
  )
}

// ─── Pugh Matrix ───

function PughMatrixWidget({ tradeId, weights, criteria, onCriteriaChanged, state, onChange }: {
  tradeId: string
  weights?: Record<string, number>; criteria: string[]; onCriteriaChanged: (c: string[]) => void
  state: TradeState; onChange: (patch: Partial<TradeState>) => void
}) {
  const { t } = useTranslation()
  const { options, datum, scores } = state
  const thresholds = state.thresholds ?? {}
  const setThreshold = (crit: string, v: string) => {
    const next = { ...thresholds }
    if (v === '') delete next[crit]; else next[crit] = parseInt(v)
    onChange({ thresholds: next })
  }
  const belowThreshold = (opt: string, i: number) => criteria.filter(c => c in thresholds && (i === datum ? 0 : getScore(opt, c)) < thresholds[c])
  const setDatum = (i: number) => onChange({ datum: i })
  const setOptions = (f: (p: string[]) => string[]) => onChange({ options: f(options) })
  const [newCriterion, setNewCriterion] = useState('')
  const [newOption, setNewOption] = useState('')

  const setScore = (opt: string, crit: string, val: number) => {
    onChange({ scores: { ...scores, [opt]: { ...(scores[opt] || {}), [crit]: val } } })
  }
  const getScore = (opt: string, crit: string) => scores[opt]?.[crit] ?? 0
  const hasWeights = weights && Object.keys(weights).length > 0

  // Compute weighted totals
  const totals = options.map((opt, i) => {
    if (i === datum) return { unweighted: 0, weighted: 0 }
    let unweighted = 0, weighted = 0
    for (const c of criteria) {
      const s = getScore(opt, c)
      unweighted += s
      const w = weights?.[c] ?? (1 / criteria.length)
      weighted += s * w
    }
    return { unweighted, weighted: Math.round(weighted * 100) / 100 }
  })

  // the leader: the highest weighted total among acceptable options; the datum counts as 0 and wins ties
  const best = totals.reduce((bi, tot, i) => {
    if (belowThreshold(options[i], i).length) return bi
    const cur = bi < 0 ? -Infinity : totals[bi].weighted
    return tot.weighted > cur + 1e-9 || (Math.abs(tot.weighted - cur) < 1e-9 && i === datum) ? i : bi
  }, -1)

  return (
    <ToolSection whereId="pugh" title={hasWeights ? t('Pugh Matrix (Weighted)') : t('Pugh Matrix (Unweighted)')} color="var(--cat-6)">
      <div className="t-12 c-2 mb-1">
        {t('Score each option vs datum: +2 much better, +1 better, 0 same, −1 worse, −2 much worse.')}
        {' '}{hasWeights ? t('Weights from pairwise comparison applied.') : t('Define weights above for weighted scoring.')}
      </div>

      <table className="c2o-table c2o-table--dense mb-1">
        <thead>
          <tr className="bb">
            <th>{t('Criteria')}</th>
            {hasWeights && <th className="num">{t('Wt')}</th>}
            {options.map((opt, i) => (
              <th key={opt} className={`ctr c2o-pugh__opt${i === datum ? ' is-datum' : i === best ? ' is-best' : ''}`}
                onClick={() => setDatum(i)} title={t('Click to set as datum')}>
                {opt} {i === datum ? '(D)' : ''}{i === best ? '★' : ''}
              </th>
            ))}
            <th className="ctr" title={t('Minimum acceptable score on this criterion')}>{t('Threshold')}</th>
          </tr>
        </thead>
        <tbody>
          {criteria.map(crit => (
            <tr key={crit} className="bb">
              <td className="p-1 w-500">{t(crit, { context: 'criterion' })}</td>
              {hasWeights && <td className="p-1 ta-r t-12 c-accent">{((weights?.[crit] ?? 0) * 100).toFixed(0)}%</td>}
              {options.map((opt, i) => (
                <td key={opt} className="p-1 ta-c">
                  {i === datum ? <span className="c-2">D</span> : (
                    <select value={getScore(opt, crit)} onChange={e => setScore(opt, crit, parseInt(e.target.value))}
                      style={{ width: 40, fontSize: fs.label, padding: '0.1rem', borderRadius: '2px', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: getScore(opt, crit) > 0 ? 'var(--success)' : getScore(opt, crit) < 0 ? 'var(--danger)' : 'var(--text-secondary)', textAlign: 'center' }}>
                      <option value={2}>+2</option><option value={1}>+1</option><option value={0}>0</option><option value={-1}>−1</option><option value={-2}>−2</option>
                    </select>
                  )}
                </td>
              ))}
              <td className="p-1 ta-c">
                <select aria-label={t('Threshold for {{c}}', { c: crit })} value={crit in thresholds ? String(thresholds[crit]) : ''}
                  onChange={e => setThreshold(crit, e.target.value)} style={{ fontSize: fs.label }}>
                  <option value="">{t('none')}</option>
                  <option value="-2">≥ −2</option><option value="-1">≥ −1</option><option value="0">≥ 0</option><option value="1">≥ +1</option>
                </select>
              </td>
            </tr>
          ))}
          <tr style={{ borderTop: '2px solid var(--border)' }}>
            <td className="p-1 w-600">{hasWeights ? t('Weighted Total') : t('Total')}</td>
            {hasWeights && <td />}
            {totals.map((tot, i) => (
              <td key={i} title={belowThreshold(options[i], i).length ? t('Below threshold: {{c}}', { c: belowThreshold(options[i], i).join(', ') }) : undefined}
                style={{ padding: '0.2rem', textAlign: 'center', fontWeight: 700, textDecoration: belowThreshold(options[i], i).length ? 'line-through' : undefined, color: i === datum ? 'var(--text-secondary)' : i === best ? 'var(--success)' : tot.weighted > 0 ? 'var(--success)' : tot.weighted < 0 ? 'var(--danger)' : 'var(--text-primary)' }}>
                {i === datum ? '—' : hasWeights ? tot.weighted.toFixed(2) : tot.unweighted}
              </td>
            ))}
            <td />
          </tr>
        </tbody>
      </table>

      <div className="flex gap-1 wrap">
        <input value={newCriterion} onChange={e => setNewCriterion(e.target.value)} placeholder={t('+ criterion')} className="c2o-input c2o-input--sm c2o-w-num"
          onKeyDown={e => { if (e.key === 'Enter' && newCriterion) { onCriteriaChanged([...criteria, newCriterion]); setNewCriterion('') } }} />
        <input value={newOption} onChange={e => setNewOption(e.target.value)} placeholder={t('+ option')} className="c2o-input c2o-input--sm c2o-w-num"
          onKeyDown={e => { if (e.key === 'Enter' && newOption) { setOptions(p => [...p, newOption]); setNewOption('') } }} />
        <span className="grow" />
        <span className="t-12 c-3 mono">{tradeId}</span>
      </div>
    </ToolSection>
  )
}

// ─── Pairwise Comparison Weighting ───

function PairwiseWeightingWidget({ weights, comparisons, onComparisonsChanged, criteria, onCriteriaChanged }: {
  weights: Record<string, number>
  comparisons: Record<string, number>
  onComparisonsChanged: (c: Record<string, number>) => void
  criteria: string[]
  onCriteriaChanged: (c: string[]) => void
}) {
  const { t } = useTranslation()
  const [newCrit, setNewCrit] = useState('')

  const setComparison = (a: string, b: string, val: number) => {
    onComparisonsChanged({ ...comparisons, [pairKey(a, b)]: val })
  }

  // Weights are derived by the parent (pairwise.ts) — an untouched pair counts as equal,
  // and nothing sets parent state during render (WP0: 0 % weights + React warning).
  const normalizedWeights = criteria.map(c => ({ criterion: c, weight: weights[c] ?? 0 }))

  // Generate pairs
  const pairs: Array<[string, string]> = []
  for (let i = 0; i < criteria.length; i++) {
    for (let j = i + 1; j < criteria.length; j++) {
      pairs.push([criteria[i], criteria[j]])
    }
  }

  return (
    <ToolSection whereId="pairwise" title={t('Pairwise Comparison Weighting')} color="var(--cat-2)">
      <div className="t-12 c-2 mb-1">
        {t('For each pair: which criterion is more important? 1 = left wins, 0.5 = equal, 0 = right wins')}
      </div>

      <div className="stack gap-1 mb-2">
        {pairs.map(([a, b]) => (
          <div key={`${a}-${b}`} className="flex ai-c gap-1 t-12">
            <span style={{ width: 60, textAlign: 'right', fontWeight: 500 }}>{t(a, { context: 'criterion' })}</span>
            <input type="range" min={0} max={1} step={0.5} value={comparisons[pairKey(a, b)] ?? 0.5}
              onChange={e => setComparison(a, b, parseFloat(e.target.value))}
              style={{ width: 80 }} />
            <span style={{ width: 60, fontWeight: 500 }}>{t(b, { context: 'criterion' })}</span>
            <span style={{ fontSize: fs.label, color: 'var(--text-secondary)', width: 20 }}>
              {(comparisons[pairKey(a, b)] ?? 0.5) === 1 ? '←' : (comparisons[pairKey(a, b)] ?? 0.5) === 0 ? '→' : '='}
            </span>
          </div>
        ))}
      </div>

      {/* Derived weights */}
      <div className="t-12 w-600 mb-1 c-2">{t('Derived Weights:')}</div>
      <div className="flex gap-1 wrap">
        {normalizedWeights.sort((a, b) => b.weight - a.weight).map(w => (
          <div key={w.criterion} className="py-1 px-2 rounded bg-2 t-12">
            <span className="w-500">{t(w.criterion, { context: 'criterion' })}</span>
            <span className="ml-1 c-accent w-600">{(w.weight * 100).toFixed(0)}%</span>
          </div>
        ))}
      </div>

      <input value={newCrit} onChange={e => setNewCrit(e.target.value)} placeholder={t('+ criterion')}
        className="c2o-input c2o-input--sm c2o-w-num mt-2"
        onKeyDown={e => { if (e.key === 'Enter' && newCrit) { onCriteriaChanged([...criteria, newCrit]); setNewCrit('') } }} />
    </ToolSection>
  )
}

// ─── Constellation Cost Learning Curve ───

function CostLearningCurveWidget() {
  const { t } = useTranslation()
  const [unitCost, setUnitCost] = useState('500')
  const [quantity, setQuantity] = useState('12')
  const [learningRate, setLearningRate] = useState('0.90')

  // C_total = C_1 × Σ(i^log2(L))
  const c1 = parseFloat(unitCost) || 500
  const n = parseInt(quantity) || 12
  const lr = parseFloat(learningRate) || 0.90
  const b = Math.log2(lr)

  const units: Array<{ unit: number; cost: number; cumulative: number }> = []
  let cumulative = 0
  for (let i = 1; i <= n; i++) {
    const cost = c1 * Math.pow(i, b)
    cumulative += cost
    units.push({ unit: i, cost: Math.round(cost), cumulative: Math.round(cumulative) })
  }
  const avgCost = n > 0 ? Math.round(cumulative / n) : 0

  return (
    <ToolSection whereId="learning-curve" title={t('Constellation Cost Learning Curve')} color="var(--status-caution)">
      <div className="flex gap-1 mb-1 wrap">
        <label className="c2o-inline-field">{t('First unit (kEUR):')} <input type="number" value={unitCost} onChange={e => setUnitCost(e.target.value)} className="c2o-input c2o-input--sm c2o-input--num c2o-w-num" /></label>
        <label className="c2o-inline-field">{t('Quantity:')} <input type="number" value={quantity} onChange={e => setQuantity(e.target.value)} className="c2o-input c2o-input--sm c2o-input--num c2o-w-num" /></label>
        <label className="c2o-inline-field">{t('Learning rate:')} <input type="number" value={learningRate} onChange={e => setLearningRate(e.target.value)} step="0.01" min="0.7" max="1.0" className="c2o-input c2o-input--sm c2o-input--num c2o-w-num" /></label>
      </div>

      <div className="flex gap-3 mb-1 t-12">
        <span>{t('Total:')} <b>{fmtProse(Math.round(cumulative))} kEUR</b></span>
        <span>{t('Average:')} <b>{t('{{cost}} kEUR/unit', { cost: fmtProse(avgCost) })}</b></span>
        <span>{t('Savings vs flat:')} <b>{Math.round((1 - cumulative / (c1 * n)) * 100)}%</b></span>
      </div>

      {/* Mini bar chart */}
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 1, height: 50, marginBottom: '0.2rem' }}>
        {units.map(u => (
          <div key={u.unit} style={{
            flex: 1, background: 'var(--accent)',
            height: `${(u.cost / c1) * 100}%`,
            borderRadius: '2px 2px 0 0', minWidth: 3,
          }} title={t('Unit {{n}}: {{cost}} kEUR', { n: u.unit, cost: u.cost })} />
        ))}
      </div>
      <div className="t-12 c-2 ta-c">
        {t('Unit cost decreases with production experience (Wright learning curve)')}
      </div>
    </ToolSection>
  )
}

// ─── Shared components ───

// ─── 3-Bin Decision Categorizer ───

type DecisionItems = Record<number, Array<{ item: string; category: 'obvious' | 'trade' | 'explore'; rationale: string }>>

// English text is the i18n key: item and rationale are translated at render time
// (split in two literals so each stays short enough for the i18n key scanner).
const DECISION_ITEMS_L01: DecisionItems = {
  0: [
    { item: 'Orbit type (SSO for EO)', category: 'obvious', rationale: 'SSO is standard for EO; other types for comms/science' },
    { item: 'Mission vs non-space alternative', category: 'trade', rationale: 'Commercial data may meet needs at lower cost — run mission trade' },
    { item: 'Constellation vs single sat', category: 'trade', rationale: 'Revisit requirement drives this — run constellation sizing' },
    { item: 'Ground station network', category: 'trade', rationale: 'Data volume and latency drive GS selection — run ground trade' },
    { item: 'Launch vehicle', category: 'trade', rationale: 'Mass, orbit, cost, schedule constraints — compare options' },
    { item: 'Regulatory regime', category: 'obvious', rationale: 'Driven by operator country and orbit — ISED/ITU for Canada' },
  ],
  1: [
    { item: 'Spacecraft bus architecture', category: 'obvious', rationale: 'Standard subsystem decomposition for CubeSats' },
    { item: 'Number of spacecraft', category: 'trade', rationale: 'Coverage, revisit, and cost trade-off' },
    { item: 'Ground station locations', category: 'trade', rationale: 'Contact time, data throughput, redundancy trade' },
    { item: 'Inter-satellite links', category: 'explore', rationale: 'Reduces ground dependency but adds mass/power/complexity' },
    { item: 'Operations concept (autonomous vs manual)', category: 'explore', rationale: 'Drives staffing, software, ground segment design' },
  ],
}

// English text is the i18n key (continued).
const DECISION_ITEMS_L234: DecisionItems = {
  2: [
    { item: 'AOCS architecture', category: 'trade', rationale: 'Pointing requirement drives 3-axis/spin/gravity-gradient — see arch trades' },
    { item: 'EPS topology (MPPT vs DET)', category: 'trade', rationale: 'Power regulation approach trades efficiency vs complexity' },
    { item: 'TTC frequency band', category: 'trade', rationale: 'UHF/S/X/Ka — data rate vs antenna size vs regulatory' },
    { item: 'Thermal control (passive vs active)', category: 'obvious', rationale: 'CubeSats use passive (coatings + heaters); active only for extreme thermal' },
    { item: 'Propulsion type', category: 'trade', rationale: 'Delta-V drives cold gas vs monoprop vs electric — run propulsion trade' },
    { item: 'Structure form factor', category: 'obvious', rationale: 'Driven by payload volume and mass constraints' },
  ],
  3: [
    { item: 'Component selection (COTS)', category: 'trade', rationale: 'Compare KB options by mass, power, cost, TRL — use equipment browser' },
    { item: 'Redundancy approach', category: 'trade', rationale: 'Cold/warm/hot redundancy trades reliability vs mass/cost' },
    { item: 'Custom hardware design', category: 'explore', rationale: 'When no COTS meets requirements — needs design space analysis' },
  ],
  4: [],
}

const DECISION_ITEMS_BY_LEVEL: DecisionItems = { ...DECISION_ITEMS_L01, ...DECISION_ITEMS_L234 }

const BIN_COLORS = { obvious: 'var(--status-ok)', trade: 'var(--status-caution)', explore: 'var(--cat-2)' }
// English text is the i18n key.
const BIN_LABELS = { obvious: 'Obvious Choice', trade: 'Trade Study', explore: 'Design Space' }
const BIN_ICONS = { obvious: '✓', trade: '⇄', explore: '?' }

function DecisionCategorizer({ currentLevel }: { currentLevel: number; focusElement: any }) {
  const { t } = useTranslation()
  const items = DECISION_ITEMS_BY_LEVEL[currentLevel] || []
  if (items.length === 0) return null

  const bins = { obvious: items.filter(i => i.category === 'obvious'), trade: items.filter(i => i.category === 'trade'), explore: items.filter(i => i.category === 'explore') }

  return (
    <ToolSection whereId="categorize" title={t('Decision Categorization')} color="var(--interactive)">
      <div className="t-12 c-2 mb-1">
        {t("Categorize decisions at this level: what's obvious, what needs a trade, what needs exploration.")}
      </div>
      <div className="flex gap-2 mb-1">
        {(['obvious', 'trade', 'explore'] as const).map(bin => (
          <div key={bin} style={{ flex: 1, fontSize: fs.label, textAlign: 'center', padding: '0.15rem', borderRadius: '3px', background: `color-mix(in srgb, ${BIN_COLORS[bin]} 8%, transparent)`, color: BIN_COLORS[bin], fontWeight: 700 }}>
            {BIN_ICONS[bin]} {t(BIN_LABELS[bin])} ({bins[bin].length})
          </div>
        ))}
      </div>
      {items.map((item, i) => (
        <div key={i} className="flex ai-c gap-1 p-1 t-12 bb">
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: BIN_COLORS[item.category], flexShrink: 0 }} />
          <span className="w-500 grow">{t(item.item)}</span>
          <span style={{ color: 'var(--text-secondary)', fontSize: fs.label, maxWidth: 200 }}>{t(item.rationale)}</span>
        </div>
      ))}
    </ToolSection>
  )
}

// ─── Architecture Trade Templates ───

type ArchTrades = Record<string, Array<{ name: string; driver: string; options: Array<{ name: string; when: string }> }>>

// English text is the i18n key: name/driver/option name/when are translated at render time.
const ARCH_TRADES_AOCS_EPS: ArchTrades = {
  aocs: [
    { name: 'AOCS Architecture', driver: 'Pointing accuracy requirement',
      options: [
        { name: '3-axis stabilized (reaction wheels + star tracker)', when: 'Pointing < 0.1° — EO, science, comms' },
        { name: 'Spin-stabilized', when: 'Pointing 1-5° — simple missions, low cost' },
        { name: 'Gravity gradient + magnetorquer', when: 'Pointing 5-10° — IoT, AIS, tech demo' },
        { name: 'Momentum bias (1 wheel + magnetorquers)', when: 'Pointing 0.5-2° — moderate cost, good reliability' },
      ],
    },
  ],
  power: [
    { name: 'EPS Architecture', driver: 'Power demand and eclipse duration',
      options: [
        { name: 'Body-mounted cells + Li-ion battery', when: '< 15W average — simple CubeSats' },
        { name: 'Deployable panels + Li-ion', when: '15-80W — most 3U-6U missions' },
        { name: 'Dual-deploy + high-capacity battery', when: '> 80W — 12U+ or high-power payloads' },
        { name: 'RTG (radioisotope)', when: 'Deep space, no solar — lunar night, outer planets' },
      ],
    },
  ],
}

// English text is the i18n key: name/driver/option name/when are translated at render time.
const ARCH_TRADES_TTC_PROP: ArchTrades = {
  ttc: [
    { name: 'TTC Architecture', driver: 'Data rate and ground station infrastructure',
      options: [
        { name: 'UHF simplex (400 MHz)', when: '< 9.6 kbps — beacon, IoT, AIS' },
        { name: 'UHF/VHF duplex', when: '< 100 kbps — command + low-rate telemetry' },
        { name: 'S-band', when: '100 kbps - 2 Mbps — standard TT&C' },
        { name: 'X-band downlink + S-band TT&C', when: '2-100 Mbps — EO payload data' },
        { name: 'Ka-band', when: '> 100 Mbps — high-throughput, weather-dependent' },
      ],
    },
  ],
  propulsion: [
    { name: 'Propulsion Architecture', driver: 'Total delta-V requirement',
      options: [
        { name: 'No propulsion (drag deorbit)', when: 'ΔV = 0, altitude < 600 km — natural decay' },
        { name: 'Cold gas', when: 'ΔV < 10 m/s — attitude control, small maneuvers' },
        { name: 'Green monopropellant', when: 'ΔV 10-200 m/s — orbit maintenance, deorbit' },
        { name: 'Hall-effect electric', when: 'ΔV 100-2000 m/s, time available — orbit raising, station-keeping' },
        { name: 'Bipropellant', when: 'ΔV > 500 m/s, time-critical — lunar transfer, fast maneuvers' },
      ],
    },
  ],
}

// English text is the i18n key: name/driver/option name/when are translated at render time.
const ARCH_TRADES_THERMAL: ArchTrades = {
  thermal: [
    { name: 'Thermal Architecture', driver: 'Internal dissipation and orbit environment',
      options: [
        { name: 'Passive (surface coatings + MLI)', when: '< 20W dissipation — most CubeSats' },
        { name: 'Passive + heaters', when: 'Cold case concern — eclipse survival, battery protection' },
        { name: 'Active (heat pipes + radiator)', when: '> 50W or tight temp control — large payloads' },
        { name: 'Louvers', when: 'Variable dissipation — mode-dependent thermal load' },
      ],
    },
  ],
}

const ARCH_TRADES: ArchTrades = { ...ARCH_TRADES_AOCS_EPS, ...ARCH_TRADES_TTC_PROP, ...ARCH_TRADES_THERMAL }

/** Architecture trade → the workbook decision it settles (decision_catalogue.yaml). */
const ARCH_DECISION: Record<string, string> = {
  'AOCS Architecture': 'D-3.2-AOCS',
  'EPS Architecture': 'D-3.1-EPS',
  'TTC Architecture': 'D-3.3-BAND',
  'Propulsion Architecture': 'D-3.4-PROPULSION',
  'Thermal Architecture': 'D-3.1-THERMAL',
}

function ArchitectureTradeWidget({ currentLevel, focusElement }: { currentLevel: number; focusElement: any }) {
  const { t } = useTranslation()
  const domain = focusElement?.subsystem_domain
  const trades = domain ? (ARCH_TRADES[domain] || []) : (currentLevel === 2 ? Object.values(ARCH_TRADES).flat() : [])
  if (trades.length === 0) return null

  return (
    <ToolSection whereId="arch-trades" title={t('Architecture Trades')} color="var(--cat-6)">
      <div className="t-12 c-2 mb-1">
        {t('Which architecture is right? The driving requirement determines the answer.')}
      </div>
      {trades.map((trade, i) => (
        <div key={i} className="mb-2">
          <div className="flex ai-c gap-2 mb-1">
            <span className="w-600 t-12">{t(trade.name)}</span>
            <span className="grow" />
            {ARCH_DECISION[trade.name] && (
              <RecordDecision decision={ARCH_DECISION[trade.name]} capture="decide:arch-trade" prefill={() => ({
                options: trade.options.map(o => ({ name: t(o.name), summary: t(o.when) })),
                criteria: [{ name: t(trade.driver) }],
                evidence: focusElement?.name ? [{ label: t('Element'), value: String(focusElement.name) }] : undefined,
              })} />
            )}
          </div>
          <div className="t-12 c-caution mb-1">{t('Driver: {{driver}}', { driver: t(trade.driver) })}</div>
          {trade.options.map((opt, j) => (
            <div key={j} className="flex gap-1 p-1 t-12 bl ml-1 mb-1">
              <span style={{ fontWeight: 500, minWidth: 120 }}>{t(opt.name)}</span>
              <span className="c-2">→ {t(opt.when)}</span>
            </div>
          ))}
        </div>
      ))}
    </ToolSection>
  )
}

// ─── Shared components ───

/** A Decide tool; a "Where in SpaceCDF" link (decide:<whereId>) opens it and scrolls to it. */
function ToolSection({ title, whereId, children }: { title: string; whereId: string; color?: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(false)
  useWhereSection('decide', sec => { if (sec === whereId) setOpen(true) })
  return (
    <div data-where={`decide:${whereId}`}>
      <Disclosure ruled summary={title} open={open} onToggle={setOpen}>{children}</Disclosure>
    </div>
  )
}

