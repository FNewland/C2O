/**
 * Seat chrome in the workbench (WP9): the active-seat switch in the app bar, the banners
 * (frozen, timer, instructor messages, seat requests to me, shadow mode), toasts, the
 * per-seat "Next" card. Hooks for the seat's view: ./view.ts.
 */
import { useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useUIStore, type Level } from '../stores/uiStore'
import { StatusBadge } from '../components/ui/StatusBadge'
import { post, seatLabel, pick, useSeatStore, type TeamView } from './api'
import { useNextCard, usePending, useSeatBootstrap, useTeam } from './hooks'

const enc = encodeURIComponent

// ─── app bar ────────────────────────────────────────────────────────────────

export function SeatBar() {
  const { t, i18n } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const { me } = useSeatBootstrap()
  const q = useTeam()
  const team = q.data
  const setDrawer = useSeatStore(s => s.setDrawer)
  const setBoard = useSeatStore(s => s.setBoard)
  const shadow = useSeatStore(s => s.shadow)
  const toast = useSeatStore(s => s.toast)
  const qc = useQueryClient()
  const held = team?.me?.held ?? []
  const active = team?.me?.active ?? null
  const inbox = usePending({}, !!team?.enabled && held.length > 0)
  const mine = (inbox.data ?? []).filter(p => held.includes(p.owner_seat)).length
  const handUp = !!(team?.me && team.hands?.[team.me.id])

  const switchTo = async (seat: string) => {
    try {
      // Take the answer at once: every request carries the active seat (X-C2O-Seat), so a
      // refetch sent before the store knows the new seat would bring the old one back.
      const view = await post<TeamView>(`/api/studies/${enc(studyId!)}/team/active`, { seat })
      if (view?.me) {
        qc.setQueryData(['team', studyId], view)
        useSeatStore.getState().setTeam(view)
      }
      await qc.invalidateQueries({ queryKey: ['team'] })
    } catch (e) { toast((e as Error).message, 'alarm') }
  }
  const hand = async () => {
    try {
      await post(`/api/studies/${enc(studyId!)}/team/hand`, { raised: !handUp })
      await qc.invalidateQueries({ queryKey: ['team'] })
    } catch (e) { toast((e as Error).message, 'alarm') }
  }

  return (
    <div className="c2o-seatbar" role="group" aria-label={t('Seat')}>
      {shadow ? (
        <StatusBadge status="info">{t('Shadowing (read-only)')}</StatusBadge>
      ) : !team?.enabled ? (
        <button type="button" className="c2o-btn c2o-btn--sm c2o-btn--quiet" onClick={() => setDrawer('seats')}
          title={t('This study has no seats: everyone may edit everything.')}>
          {t('Solo study')}
        </button>
      ) : held.length === 0 ? (
        <button type="button" className="c2o-btn c2o-btn--sm c2o-btn--primary" onClick={() => setDrawer('seats')}>
          {t('Choose a seat')}
        </button>
      ) : (
        <label className="c2o-seatbar__switch">
          <span className="c2o-seatbar__lbl">{t('Seat')}</span>
          <select className="c2o-select c2o-select--sm" value={active ?? ''} onChange={e => switchTo(e.target.value)}
            aria-label={t('Active seat')} data-testid="active-seat">
            {held.map(s => <option key={s} value={s}>{seatLabel(s, i18n.language)}</option>)}
          </select>
        </label>
      )}
      {team?.enabled && !shadow && (
        <button type="button" className="c2o-btn c2o-btn--sm" onClick={() => setDrawer(mine ? 'review' : 'seats')}
          aria-label={mine ? t('Seats — {{count}} changes to review', { count: mine, defaultValue_one: 'Seats — {{count}} change to review' }) : t('Seats')}>
          {t('Seats')}
          {mine > 0 && <span className="c2o-seatbar__count" aria-hidden="true">{mine}</span>}
        </button>
      )}
      {team?.enabled && held.length > 0 && !shadow && (
        <button type="button" className={`c2o-btn c2o-btn--sm${handUp ? ' c2o-btn--active' : ''}`} aria-pressed={handUp}
          onClick={hand} title={handUp ? t('Lower your hand') : t('Raise your hand: the instructor sees it on the class board')}>
          {handUp ? t('Hand raised') : t('Raise hand')}
        </button>
      )}
      {me?.instructor && (
        <button type="button" className="c2o-btn c2o-btn--sm" onClick={() => setBoard(true)}>{t('Class board')}</button>
      )}
    </div>
  )
}

// ─── banners and toasts ─────────────────────────────────────────────────────

const DISMISS_KEY = 'scdf.seat.msgSeen'
function readSeen(): string { try { return localStorage.getItem(DISMISS_KEY) || '' } catch { return '' } }

function Countdown({ endsAt }: { endsAt: number }) {
  const [now, setNow] = useState(() => Date.now() / 1000)
  useEffect(() => { const id = window.setInterval(() => setNow(Date.now() / 1000), 1000); return () => window.clearInterval(id) }, [])
  const left = Math.max(0, Math.round(endsAt - now))
  const mm = Math.floor(left / 60), ss = left % 60
  return <span className="mono w-600">{`${mm}:${String(ss).padStart(2, '0')}`}</span>
}

export function SeatBanners() {
  const { t } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const team = useSeatStore(s => s.team)
  const shadow = useSeatStore(s => s.shadow)
  const setShadow = useSeatStore(s => s.setShadow)
  const setBoard = useSeatStore(s => s.setBoard)
  const toasts = useSeatStore(s => s.toasts)
  const dismiss = useSeatStore(s => s.dismiss)
  const toast = useSeatStore(s => s.toast)
  const showAll = useSeatStore(s => s.showAll)
  const qc = useQueryClient()
  const [seen, setSeen] = useState(readSeen)
  const last = team?.messages?.[team.messages.length - 1]
  const showMsg = last && last.id !== seen
  const reqs = team?.me?.requests_to_me ?? []

  const answer = async (seat: string, accept: boolean) => {
    try {
      await post(`/api/studies/${enc(studyId!)}/team/answer`, { seat, accept })
      await qc.invalidateQueries({ queryKey: ['team'] })
    } catch (e) { toast((e as Error).message, 'alarm') }
  }

  return (
    <>
      {shadow && (
        <div className="c2o-seatbanner c2o-seatbanner--info" role="status">
          <StatusBadge status="info">{t('Shadow mode')}</StatusBadge>
          <span>{t('You are watching this study read-only, as the team sees it.')}</span>
          <button type="button" className="c2o-btn c2o-btn--sm" onClick={() => { setShadow(null); useUIStore.getState().setStudyId(null); setBoard(true) }}>
            {t('Back to the class board')}
          </button>
        </div>
      )}
      {team?.frozen && (
        <div className="c2o-seatbanner c2o-seatbanner--caution" role="status">
          <StatusBadge status="caution">{t('Study frozen')}</StatusBadge>
          <span>{t('{{name}} paused editing. You can still look around.', { name: team.frozen.by })}</span>
        </div>
      )}
      {team?.timer && (
        <div className="c2o-seatbanner" role="timer" aria-live="off">
          <span className="w-600">{team.timer.label || t('Timer')}</span>
          <Countdown endsAt={team.timer.ends_at} />
        </div>
      )}
      {showMsg && (
        <div className="c2o-seatbanner c2o-seatbanner--info" role="status" aria-live="polite">
          <StatusBadge status="info">{last!.kind === 'inject' ? t('Customer change') : last!.scope === 'all' ? t('Message to the class') : t('Message from the instructor')}</StatusBadge>
          <span className="grow">{last!.text}{last!.code ? ` (${last!.code})` : ''}</span>
          <button type="button" className="c2o-btn c2o-btn--sm c2o-btn--quiet" onClick={() => {
            try { localStorage.setItem(DISMISS_KEY, last!.id) } catch { /* private mode */ }
            setSeen(last!.id)
          }}>{t('Dismiss')}</button>
        </div>
      )}
      {reqs.map(r => (
        <div key={r.seat} className="c2o-seatbanner c2o-seatbanner--caution" role="alertdialog" aria-label={t('Seat request')}>
          <StatusBadge status="caution">{t('Seat request')}</StatusBadge>
          <span className="grow">{t('{{name}} asks for your seat {{seat}}.', { name: r.name, seat: seatLabel(r.seat) })}{' '}
            <span className="c-3">{t('Answer within')} <Countdown endsAt={r.expires} /></span></span>
          <button type="button" className="c2o-btn c2o-btn--sm c2o-btn--primary" onClick={() => answer(r.seat, true)}>{t('Hand over')}</button>
          <button type="button" className="c2o-btn c2o-btn--sm" onClick={() => answer(r.seat, false)}>{t('Keep it')}</button>
        </div>
      ))}
      {showAll && team?.enabled && !shadow && (
        <div className="c2o-seatbanner c2o-seatbanner--quiet" role="status">
          <span>{t('Show all: tabs outside your seat are read-only.')}</span>
        </div>
      )}
      <div className="c2o-toasts" aria-live="polite">
        {toasts.map(x => (
          <div key={x.id} className={`c2o-toast c2o-toast--${x.tone}`} role={x.tone === 'alarm' ? 'alert' : 'status'}>
            <StatusBadge status={x.tone === 'info' ? 'info' : x.tone}>{x.text}</StatusBadge>
            <button type="button" className="c2o-btn c2o-btn--icon" aria-label={t('Dismiss')} onClick={() => dismiss(x.id)}>×</button>
          </div>
        ))}
      </div>
    </>
  )
}

// ─── Next card ──────────────────────────────────────────────────────────────

/** "Next" for the active seat: failing must-pass gate item → proposals to review →
 * changed subscriptions → unstarted step. Replaces the readiness "Next: All elements frozen". */
export function SeatNext() {
  const { t, i18n } = useTranslation()
  const team = useSeatStore(s => s.team)
  const setDrawer = useSeatStore(s => s.setDrawer)
  const seat = team?.enabled ? team.me?.active ?? null : null
  const q = useNextCard(seat)
  const d = q.data
  if (!seat || !d) return null
  const goVV = () => { useSeatStore.getState().openVV('gates'); useUIStore.getState().goToLevel(4 as Level) }
  let status: 'alarm' | 'caution' | 'info' | 'ok' = 'info'
  let text = ''
  let act: (() => void) | null = null
  switch (d.kind) {
    case 'gate_item':
      status = 'alarm'
      text = t('Next ({{gate}}): {{question}}', { gate: d.gate ?? '', question: t(d.question ?? '') })
      act = goVV
      break
    case 'proposals':
      status = 'caution'
      text = t('Next: review {{count}} proposed changes to your parameters', { count: d.count ?? 0, defaultValue_one: 'Next: review {{count}} proposed change to your parameters' })
      act = () => setDrawer('review')
      break
    case 'subscriptions':
      status = 'caution'
      text = t('Next: {{count}} subscribed values changed since you looked', { count: d.count ?? 0, defaultValue_one: 'Next: {{count}} subscribed value changed since you looked' })
      act = () => setDrawer('subs')
      break
    case 'step':
      text = d.step_label
        ? t('Next: start {{step}} — {{question}}', { step: pick(d.step_label, i18n.language), question: t(d.question ?? '') })
        : t('Next: {{question}}', { question: t(d.question ?? '') })
      act = goVV
      break
    default:
      status = 'ok'
      text = t('Nothing waiting for {{seat}}', { seat: seatLabel(seat, i18n.language) })
  }
  return (
    <button type="button" className="c2o-seatnext" onClick={act ?? undefined} disabled={!act} data-testid="seat-next"
      title={seatLabel(seat, i18n.language)}>
      <StatusBadge status={status}><span className="ellipsis">{text}</span></StatusBadge>
    </button>
  )
}

