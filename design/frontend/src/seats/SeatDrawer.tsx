/**
 * The seat panel (WP9): seat board (claim / request / release, team size), the review inbox
 * for my seats (accept / reject pending changes, ruling 5), my proposals, subscriptions with
 * "changed since you looked", the wanted-vs-provided ledger (Systems) and recent activity.
 */
import { useMemo, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useUIStore } from '../stores/uiStore'
import { Tabs } from '../components/ui/Tabs'
import { tabPanelProps } from '../components/ui/util'
import { StatusBadge, Tag } from '../components/ui/StatusBadge'
import { askConfirm, askText } from '../components/ui/Dialog'
import { fmtDate } from '../i18n'
import { api, pick, post, seatLabel, useSeatStore, type DrawerTab, type PendingChange, type SeatView } from './api'
import { useLedger, usePending, useSeatEvents, useSubscriptions } from './hooks'

const enc = encodeURIComponent

function fmtVal(v: unknown): string {
  if (v === null || v === undefined || v === '') return '—'
  if (typeof v === 'number') return Number.isInteger(v) ? String(v) : v.toPrecision(4).replace(/\.?0+$/, '')
  if (typeof v === 'object') return JSON.stringify(v)
  return String(v)
}

export function SeatDrawer() {
  const { t } = useTranslation()
  const drawer = useSeatStore(s => s.drawer)
  const setDrawer = useSeatStore(s => s.setDrawer)
  const team = useSeatStore(s => s.team)
  if (!drawer) return null
  const held = team?.me?.held ?? []
  const isSys = held.includes('systems_engineer') || held.includes('team_leader') || !!team?.me?.instructor
  const items: { id: DrawerTab; label: string }[] = [
    { id: 'seats', label: t('Seats') },
    ...(team?.enabled ? [
      { id: 'review' as DrawerTab, label: t('Review') },
      { id: 'subs' as DrawerTab, label: t('Subscriptions') },
      ...(isSys ? [{ id: 'ledger' as DrawerTab, label: t('Wanted / provided') }] : []),
      { id: 'activity' as DrawerTab, label: t('Activity') },
    ] : []),
  ]
  return (
    <aside className="c2o-logbook c2o-seatpanel" aria-labelledby="c2o-seatpanel-title"
      onKeyDown={e => { if (e.key === 'Escape') setDrawer(null) }}>
      <header className="c2o-logbook__head">
        <h2 id="c2o-seatpanel-title" className="c2o-logbook__title">{t('Seats')}</h2>
        <span className="c2o-logbook__who t-12 c-3 ellipsis">
          {team?.me ? `${team.me.name}${team.me.verified ? '' : ` · ${t('unverified name')}`}` : ''}
        </span>
        <button type="button" className="c2o-btn c2o-btn--icon" aria-label={t('Close')} onClick={() => setDrawer(null)}>×</button>
      </header>
      <Tabs<DrawerTab> idBase="seat" label={t('Seats')} value={drawer} onChange={setDrawer} className="c2o-logbook__tabs" items={items} />
      <div className="c2o-logbook__body" {...tabPanelProps('seat', drawer)}>
        {drawer === 'seats' && <SeatBoard />}
        {drawer === 'review' && <ReviewTab />}
        {drawer === 'subs' && <SubsTab />}
        {drawer === 'ledger' && <LedgerTab />}
        {drawer === 'activity' && <ActivityTab />}
      </div>
    </aside>
  )
}

// ─── seat board ─────────────────────────────────────────────────────────────

function useAct() {
  const qc = useQueryClient()
  const toast = useSeatStore(s => s.toast)
  return async (fn: () => Promise<unknown>, ok?: string) => {
    try {
      await fn()
      if (ok) toast(ok, 'ok')
    } catch (e) { toast((e as Error).message, 'alarm') }
    await qc.invalidateQueries({ queryKey: ['team'] })
    await qc.invalidateQueries({ queryKey: ['seat-pending'] })
  }
}

function stateBadge(s: SeatView, t: (k: string, o?: any) => string) {
  switch (s.state) {
    case 'free': return <StatusBadge status="nodata">{t('Free')}</StatusBadge>
    case 'held': return <StatusBadge status="ok">{t('Held')}</StatusBadge>
    case 'idle': return <StatusBadge status="stale">{s.reclaimable ? t('Idle — reclaimable') : t('Idle')}</StatusBadge>
    case 'locked': return <StatusBadge status="neutral">{t('Locked')}</StatusBadge>
  }
}

function SeatBoard() {
  const { t, i18n } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const team = useSeatStore(s => s.team)
  const me = useSeatStore(s => s.me)
  const catalogue = useSeatStore(s => s.catalogue)
  const act = useAct()
  const qc = useQueryClient()
  const [size, setSize] = useState<string>(team?.preset ?? '9')
  const [optional, setOptional] = useState<string[]>(team?.optional ?? [])
  const base = `/api/studies/${enc(studyId!)}/team`
  const myId = team?.me?.id
  const canPreset = !team?.enabled || team?.me?.held.includes('team_leader') || team?.me?.instructor
  const byId = useMemo(() => new Map((team?.seats ?? []).map(s => [s.id, s])), [team])
  const people = useQuery<any[]>({ queryKey: ['team-people', studyId], queryFn: () => api(`${base}/people`),
    enabled: !!studyId && !!team?.me?.instructor })

  const groups = team?.groups ?? []
  const shared = (team?.seats ?? []).filter(s => !s.exclusive)
  const optionalSeats = (catalogue?.seats ?? []).filter(s => s.optional)

  const becomeInstructor = () => act(() => post('/api/seats/instructor/claim'), t('You are the instructor on this server.'))
    .then(() => qc.invalidateQueries({ queryKey: ['seat-me'] }))

  return (
    <div className="stack gap-3">
      <section className="c2o-seatsec" aria-labelledby="seat-size-h">
        <h3 id="seat-size-h" className="c2o-logbook__h">{t('Team size')}</h3>
        {!team?.enabled && <p className="t-12 c-2 m-0">{t('This study has no seats: everyone may edit everything. Choose a team size to give each person a seat with its own parameters.')}</p>}
        <div className="flex wrap ai-e gap-2">
          <label className="c2o-field">
            <span className="c2o-field__label">{t('People in the team')}</span>
            <select className="c2o-select" value={team?.enabled ? size : 'solo'} disabled={!canPreset}
              onChange={e => setSize(e.target.value)} data-testid="team-size">
              <option value="solo">{t('Solo (no seats)')}</option>
              {(catalogue?.presets ?? []).map(p => <option key={p.id} value={p.id}>{pick(p.label, i18n.language)}</option>)}
            </select>
          </label>
          {optionalSeats.map(s => (
            <label key={s.id} className="c2o-check t-12">
              <input type="checkbox" disabled={!canPreset} checked={optional.includes(s.id)}
                onChange={e => setOptional(o => e.target.checked ? [...o, s.id] : o.filter(x => x !== s.id))} />
              {pick(s.label, i18n.language)}
            </label>
          ))}
          <button type="button" className="c2o-btn c2o-btn--sm" disabled={!canPreset}
            onClick={() => act(() => post(`${base}/preset`, { team_size: size === 'solo' ? null : size, optional }), t('Team size saved'))}>
            {t('Apply')}
          </button>
        </div>
        {!canPreset && <p className="t-12 c-3 m-0">{t('Only the Team leader or the instructor changes the team size.')}</p>}
      </section>

      {team?.enabled && (
        <section className="c2o-seatsec" aria-labelledby="seat-grid-h">
          <h3 id="seat-grid-h" className="c2o-logbook__h">{t('Seats')}</h3>
          <p className="t-12 c-2 m-0">{t('Claim a free seat. A held seat can be requested from its holder (they have 60 s to answer); an idle seat can be claimed after 5 minutes. Your data stays with the seat, not with you.')}</p>
          <ul className="list-reset c2o-seatgrid">
            {groups.map(g => {
              const seats = g.map(id => byId.get(id)).filter(Boolean) as SeatView[]
              const mineAll = seats.every(s => s.holders.some(h => h.person_id === myId))
              const allFree = seats.every(s => s.state === 'free' || s.reclaimable)
              return (
                <li key={g.join('+')} className={`c2o-seatcard${mineAll ? ' is-mine' : ''}`} data-testid={`seat-${g[0]}`}>
                  {seats.map(s => {
                    const h = s.holders[0]
                    const mine = s.holders.some(x => x.person_id === myId)
                    return (
                      <div key={s.id} className="c2o-seatcard__seat">
                        <div className="flex ai-c gap-2">
                          <span className="w-600 grow">{pick(s.label, i18n.language)}</span>
                          {stateBadge(s, t)}
                        </div>
                        <div className="t-12 c-2 flex ai-c gap-1 wrap">
                          {h ? <>{h.name}{!h.verified && <Tag>{t('unverified')}</Tag>}{mine && <Tag>{t('you')}</Tag>}{h.hand && <Tag>{t('hand raised')}</Tag>}</> : <span className="c-3">{t('nobody')}</span>}
                          {s.request && <Tag>{t('requested by {{name}}', { name: s.request.name })}</Tag>}
                        </div>
                        <div className="flex gap-1 wrap">
                          {mine && s.state !== 'locked' && (
                            <button type="button" className="c2o-btn c2o-btn--sm c2o-btn--quiet"
                              onClick={() => act(() => post(`${base}/release`, { seat: s.id }))}>{t('Release')}</button>
                          )}
                          {!mine && h && s.state !== 'locked' && !s.reclaimable && seats.length > 1 && (
                            <button type="button" className="c2o-btn c2o-btn--sm"
                              onClick={() => act(() => post(`${base}/request`, { seat: s.id }), t('Request sent: the holder has 60 s to answer.'))}>
                              {t('Request seat')}
                            </button>
                          )}
                          {team?.me?.instructor && <InstructorSeatControls seat={s} people={people.data ?? []} />}
                        </div>
                      </div>
                    )
                  })}
                  {!mineAll && (
                    <div className="flex gap-1">
                      {allFree ? (
                        <button type="button" className="c2o-btn c2o-btn--sm c2o-btn--primary" data-testid={`claim-${g[0]}`}
                          onClick={() => act(() => post(`${base}/claim`, { seats: g }), t('Seat claimed'))}>
                          {g.length > 1 ? t('Claim these {{count}} seats', { count: g.length }) : t('Claim')}
                        </button>
                      ) : seats.length === 1 && seats[0].state !== 'locked' && (
                        <button type="button" className="c2o-btn c2o-btn--sm"
                          onClick={() => act(() => post(`${base}/request`, { seat: seats[0].id }), t('Request sent: the holder has 60 s to answer.'))}>
                          {t('Request seat')}
                        </button>
                      )}
                    </div>
                  )}
                </li>
              )
            })}
            {shared.map(s => {
              const mine = s.holders.some(x => x.person_id === myId)
              return (
                <li key={s.id} className={`c2o-seatcard c2o-seatcard--shared${mine ? ' is-mine' : ''}`}>
                  <div className="flex ai-c gap-2">
                    <span className="w-600 grow">{pick(s.label, i18n.language)}</span>
                    <Tag>{t('{{count}} people', { count: s.holders.length, defaultValue_one: '{{count}} person' })}</Tag>
                  </div>
                  <div className="t-12 c-2">{s.kind === 'customer' ? t('Reads the model, writes mission requirements.') : t('Read-only.')}</div>
                  <div>
                    {mine
                      ? <button type="button" className="c2o-btn c2o-btn--sm c2o-btn--quiet" onClick={() => act(() => post(`${base}/release`, { seat: s.id }))}>{t('Leave')}</button>
                      : <button type="button" className="c2o-btn c2o-btn--sm" onClick={() => act(() => post(`${base}/claim`, { seats: [s.id] }))}>{t('Join')}</button>}
                  </div>
                </li>
              )
            })}
          </ul>
        </section>
      )}

      {me && !me.instructor && me.instructor_mode === 'laptop' && !me.laptop_instructor && (
        <section className="c2o-seatsec">
          <h3 className="c2o-logbook__h">{t('Instructor')}</h3>
          <p className="t-12 c-2 m-0">{t('No instructor list is configured on this server (laptop mode). The first person to take the instructor role gets the class board and may delete studies.')}</p>
          <div><button type="button" className="c2o-btn c2o-btn--sm" onClick={becomeInstructor}>{t('Become instructor')}</button></div>
        </section>
      )}
    </div>
  )
}

function InstructorSeatControls({ seat, people }: { seat: SeatView; people: any[] }) {
  const { t } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const act = useAct()
  const base = `/api/studies/${enc(studyId!)}/team`
  return (
    <>
      <select className="c2o-select c2o-select--sm" aria-label={t('Reassign {{seat}}', { seat: seatLabel(seat.id) })} value=""
        onChange={e => {
          const pid = e.target.value
          if (pid === '') return
          const p = people.find(x => x.id === pid)
          void act(() => post(`${base}/reassign`, { seat: seat.id, person_id: pid === '-' ? null : pid, name: p?.name || '' }), t('Seat reassigned'))
        }}>
        <option value="">{t('Reassign…')}</option>
        <option value="-">{t('Nobody (free the seat)')}</option>
        {people.map(p => <option key={p.id} value={p.id}>{p.name}{p.verified ? '' : ` (${t('unverified')})`}</option>)}
      </select>
      <button type="button" className="c2o-btn c2o-btn--sm c2o-btn--quiet"
        onClick={() => act(() => post(`${base}/lock`, { seat: seat.id, locked: seat.state !== 'locked' }))}>
        {seat.state === 'locked' ? t('Unlock') : t('Lock')}
      </button>
    </>
  )
}

// ─── review inbox (ruling 5) ────────────────────────────────────────────────

function ChangeRow({ pc, review }: { pc: PendingChange; review: boolean }) {
  const { t, i18n } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const act = useAct()
  const qc = useQueryClient()
  const base = `/api/studies/${enc(studyId!)}/team/pending/${pc.id}`
  const fields = pc.param_keys.length ? pc.param_keys : Object.keys(pc.new)
  const after = async () => { await qc.refetchQueries({ type: 'active' }) }
  return (
    <li className="c2o-pcrow" data-testid="pending-row">
      <div className="flex ai-c gap-2 wrap">
        <span className="w-600">{pc.element_name}</span>
        {fields.map(f => <Tag key={f} mono>{f}</Tag>)}
        <span className="grow" />
        {pc.status !== 'pending' && <StatusBadge status={pc.status === 'accepted' ? 'ok' : pc.status === 'rejected' ? 'alarm' : 'neutral'}>{pc.status === 'accepted' ? t('Accepted') : pc.status === 'rejected' ? t('Rejected') : t('Withdrawn')}</StatusBadge>}
      </div>
      <table className="c2o-table c2o-table--dense">
        <thead><tr><th>{t('Parameter')}</th><th>{t('Owner value')}</th><th>{t('Proposed')}</th></tr></thead>
        <tbody>
          {Object.entries(pc.new).filter(([k]) => k !== '_name').map(([k, v]) => (
            <tr key={k}><td className="mono">{k}</td><td className="mono">{fmtVal((pc.old as any)[k] ?? Object.values(pc.old)[0])}</td><td className="mono w-600">{fmtVal(v)}</td></tr>
          ))}
          {pc.kind === 'element_param_delete' && <tr><td className="mono">{String(pc.new._name)}</td><td className="mono">{fmtVal(Object.values(pc.old)[0])}</td><td>{t('delete')}</td></tr>}
        </tbody>
      </table>
      <div className="t-12 c-2">
        {t('{{name}} ({{seat}}) · {{when}}', { name: pc.by_name, seat: seatLabel(pc.by_seat, i18n.language), when: fmtDate(pc.created_at, { timeStyle: 'short' } as any) })}
        {pc.comment && <> · <q>{pc.comment}</q></>}
      </div>
      {pc.status === 'pending' && (
        <div className="flex gap-1">
          {review ? <>
            <button type="button" className="c2o-btn c2o-btn--sm c2o-btn--primary" data-testid="accept-change"
              onClick={() => act(async () => {
                const c = await askText(t('Comment (optional):'), '', { title: t('Accept the change') })
                if (c === null) return
                await post(`${base}/accept`, { comment: c })
                await after()
              }, t('Change accepted and applied'))}>{t('Accept')}</button>
            <button type="button" className="c2o-btn c2o-btn--sm"
              onClick={() => act(async () => {
                const c = await askText(t('Why do you reject it? The proposer sees this.'), '', { title: t('Reject the change') })
                if (!c) return
                await post(`${base}/reject`, { comment: c })
              }, t('Change rejected'))}>{t('Reject')}</button>
          </> : (
            <button type="button" className="c2o-btn c2o-btn--sm c2o-btn--quiet"
              onClick={() => act(async () => {
                if (!(await askConfirm(t('Withdraw this proposal?')))) return
                await post(`${base}/withdraw`, {})
              })}>{t('Withdraw')}</button>
          )}
        </div>
      )}
    </li>
  )
}

function ReviewTab() {
  const { t } = useTranslation()
  const team = useSeatStore(s => s.team)
  const held = team?.me?.held ?? []
  const inbox = usePending({})
  const mine = usePending({ mine: true, status: 'all' })
  const toReview = (inbox.data ?? []).filter(p => held.includes(p.owner_seat) || team?.me?.instructor)
  return (
    <div className="stack gap-3">
      <section>
        <h3 className="c2o-logbook__h">{t('Waiting for your seats')} <span className="mono">{toReview.length}</span></h3>
        <p className="t-12 c-2 m-0 mb-2">{t('Another seat proposed a value for a parameter you own. Until you accept, your value stands in every analysis.')}</p>
        {toReview.length === 0 ? <p className="c2o-nodata t-12">{t('Nothing to review.')}</p> : (
          <ul className="list-reset stack gap-2">{toReview.map(pc => <ChangeRow key={pc.id} pc={pc} review />)}</ul>
        )}
      </section>
      <section>
        <h3 className="c2o-logbook__h">{t('Your proposals')}</h3>
        {(mine.data ?? []).length === 0 ? <p className="c2o-nodata t-12">{t('You have not proposed changes to other seats.')}</p> : (
          <ul className="list-reset stack gap-2">{(mine.data ?? []).slice().reverse().map(pc => <ChangeRow key={pc.id} pc={pc} review={false} />)}</ul>
        )}
      </section>
    </div>
  )
}

// ─── subscriptions ──────────────────────────────────────────────────────────

const SUB_FIELDS = ['mass_kg', 'power_avg_w', 'power_peak_w', 'volume_cm3', 'cost_recurring_keur', 'cost_nre_keur', 'trl', 'quantity', 'margin_percent']

function SubsTab() {
  const { t, i18n } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const team = useSeatStore(s => s.team)
  const seat = team?.me?.active ?? null
  const q = useSubscriptions(seat)
  const act = useAct()
  const qc = useQueryClient()
  const base = `/api/studies/${enc(studyId!)}/team/subscriptions`
  const els = useQuery<any[]>({ queryKey: ['elements', studyId], queryFn: () => fetch(`/api/studies/${studyId}/elements`).then(r => r.json()), enabled: !!studyId })
  const [el, setEl] = useState('')
  const [field, setField] = useState('power_avg_w')
  const refresh = () => qc.invalidateQueries({ queryKey: ['seat-subs'] })
  if (!seat) return <p className="c2o-nodata t-12">{t('Claim a seat to subscribe to parameters.')}</p>
  return (
    <div className="stack gap-3">
      <p className="t-12 c-2 m-0">{t('Values owned by other seats that {{seat}} depends on. They are read-only here; "changed" means the owner changed them since you last looked.', { seat: seatLabel(seat, i18n.language) })}</p>
      <ul className="list-reset stack gap-1">
        {(q.data ?? []).map(s => (
          <li key={`${s.element_id}|${s.field}`} className={`c2o-subrow${s.changed ? ' is-changed' : ''}`}>
            <span className="grow min0">
              <span className="w-600">{s.element_name}</span> <span className="mono t-12">{s.field}</span>
              <span className="t-12 c-3"> · {t('owner')}: {seatLabel(s.owner_seat, i18n.language) || t('none')}</span>
            </span>
            <span className="mono">{fmtVal(s.value)}</span>
            {s.changed && <StatusBadge status="caution">{t('changed (was {{v}})', { v: fmtVal(s.seen_value) })}</StatusBadge>}
            {s.changed && <button type="button" className="c2o-btn c2o-btn--sm c2o-btn--quiet" onClick={() => act(() => post(`${base}/seen`, { seat, element_id: s.element_id, field: s.field })).then(refresh)}>{t('Seen')}</button>}
            <button type="button" className="c2o-btn c2o-btn--icon" aria-label={t('Unsubscribe')}
              onClick={() => act(() => api(`${base}?seat=${enc(seat)}&element_id=${enc(s.element_id)}&field=${enc(s.field)}`, { method: 'DELETE' })).then(refresh)}>×</button>
          </li>
        ))}
        {(q.data ?? []).length === 0 && <li className="c2o-nodata t-12">{t('No subscriptions yet.')}</li>}
      </ul>
      <div className="flex wrap ai-e gap-2">
        <label className="c2o-field">
          <span className="c2o-field__label">{t('Element')}</span>
          <select className="c2o-select" value={el} onChange={e => setEl(e.target.value)}>
            <option value="">{t('Choose…')}</option>
            {(els.data ?? []).filter((x: any) => x.element_type !== 'mode').map((x: any) => <option key={x.id} value={x.id}>{x.name}</option>)}
          </select>
        </label>
        <label className="c2o-field">
          <span className="c2o-field__label">{t('Value')}</span>
          <select className="c2o-select" value={field} onChange={e => setField(e.target.value)}>
            {SUB_FIELDS.map(f => <option key={f} value={f}>{f}</option>)}
          </select>
        </label>
        <button type="button" className="c2o-btn c2o-btn--sm" disabled={!el}
          onClick={() => act(() => post(base, { seat, element_id: el, field })).then(refresh)}>{t('Subscribe')}</button>
      </div>
    </div>
  )
}

// ─── wanted vs provided (Systems) ───────────────────────────────────────────

function LedgerTab() {
  const { t, i18n } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const team = useSeatStore(s => s.team)
  const q = useLedger()
  const act = useAct()
  const qc = useQueryClient()
  const [key, setKey] = useState('')
  const seat = team?.me?.active ?? null
  const STATUS: Record<string, { s: 'alarm' | 'caution' | 'nodata' | 'ok'; l: string }> = {
    unowned: { s: 'alarm', l: t('Wanted, nobody owns it') },
    requested: { s: 'caution', l: t('Requested') },
    no_value: { s: 'nodata', l: t('Owned, no value yet') },
    provided: { s: 'ok', l: t('Provided') },
  }
  return (
    <div className="stack gap-3">
      <p className="t-12 c-2 m-0">{t('Every parameter a seat subscribed to or asked for, who owns it and whether it has a value (ICEMaker "Parameters wanted").')}</p>
      <div className="c2o-table-wrap">
        <table className="c2o-table c2o-table--dense">
          <thead><tr><th>{t('Parameter')}</th><th>{t('Wanted by')}</th><th>{t('Owner')}</th><th>{t('Value')}</th><th>{t('Status')}</th></tr></thead>
          <tbody>
            {(q.data?.rows ?? []).map(r => (
              <tr key={`${r.source}|${r.key}|${r.element_id}`}>
                <td><span className="mono">{r.key}</span>{r.element_name && <div className="t-12 c-3">{r.element_name}</div>}</td>
                <td className="t-12">{r.wanted_by.map(s => seatLabel(s, i18n.language)).join(', ')}</td>
                <td className="t-12">{seatLabel(r.owner_seat, i18n.language) || '—'}{r.owner_holder ? ` · ${r.owner_holder}` : ''}</td>
                <td className="mono">{fmtVal(r.value)}</td>
                <td><StatusBadge status={STATUS[r.status].s}>{STATUS[r.status].l}</StatusBadge></td>
              </tr>
            ))}
            {(q.data?.rows ?? []).length === 0 && <tr><td colSpan={5} className="c2o-table__empty">{t('Nothing wanted yet.')}</td></tr>}
          </tbody>
        </table>
      </div>
      {seat && (
        <div className="flex wrap ai-e gap-2">
          <label className="c2o-field">
            <span className="c2o-field__label">{t('Ask for a parameter (key)')}</span>
            <input className="c2o-input" value={key} placeholder="payload.data_rate_kbps" onChange={e => setKey(e.target.value)} />
          </label>
          <button type="button" className="c2o-btn c2o-btn--sm" disabled={key.trim().length < 3}
            onClick={() => act(() => post(`/api/studies/${enc(studyId!)}/team/wanted`, { seat, key: key.trim() })).then(() => { setKey(''); void qc.invalidateQueries({ queryKey: ['seat-ledger'] }) })}>
            {t('Add to wanted')}
          </button>
        </div>
      )}
    </div>
  )
}

// ─── activity ───────────────────────────────────────────────────────────────

function ActivityTab() {
  const { t, i18n } = useTranslation()
  const q = useSeatEvents()
  return (
    <ul className="list-reset stack gap-1">
      {(q.data ?? []).map((e, i) => (
        <li key={i} className="c2o-actrow t-12">
          <span className="mono c-3">{fmtDate(e.ts, { timeStyle: 'short' } as any)}</span>{' '}
          <span className="w-600">{e.person_name || e.person_id}</span>{' '}
          {e.seat_id && <Tag>{seatLabel(e.seat_id, i18n.language)}</Tag>}{' '}
          <span className="mono">{e.action}</span> <span className="c-2">{e.target}</span>
        </li>
      ))}
      {(q.data ?? []).length === 0 && <li className="c2o-nodata">{t('No activity yet.')}</li>}
    </ul>
  )
}
