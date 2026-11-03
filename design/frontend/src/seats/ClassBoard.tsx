/**
 * Instructor class board (WP9): rows = studies, columns = seats. Each cell shows the holder,
 * presence (active / idle / free / locked) and a raised hand; each row its gate state.
 * "Needs attention" keeps the rows with a failed must-pass item, an idle seat or a raised
 * hand. Interventions: broadcast and per-team messages, timer, freeze, inject a customer
 * requirement change, reassign / lock seats (in the study's seat panel), gate sign-off of
 * manual / hybrid items, shadow a study read-only, and the post-session timeline export.
 */
import { Fragment, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useUIStore } from '../stores/uiStore'
import { StatusBadge, Tag } from '../components/ui/StatusBadge'
import { askText } from '../components/ui/Dialog'
import { api, pick, post, seatLabel, useSeatStore, type Lang2, type SeatView } from './api'

const enc = encodeURIComponent

interface BoardRow {
  study_id: string; name: string; enabled: boolean; preset: string | null; seats: SeatView[]
  gate: { gate: string | null; short?: string; state?: string; must_pass?: number; must_pass_met?: number
    failed?: { id: string; question: string; owner_seat: string | null }[]; manual_open?: number }
  hands: Record<string, { name: string; seat: string | null; at: string }>
  frozen: { by: string } | null; timer: { ends_at: number; label: string } | null
  pending: number; online: number; idle_seats: string[]; free_seats: string[]
  needs_attention: ('failed_must_pass' | 'idle_seat' | 'raised_hand')[]
}
interface Board { rows: BoardRow[]; seat_columns: string[]; labels: Record<string, Lang2>; now: string }

function Cell({ s }: { s: SeatView | undefined }) {
  const { t } = useTranslation()
  if (!s) return <td className="c2o-board__cell c-3">·</td>
  const h = s.holders[0]
  const status = s.state === 'held' ? 'ok' : s.state === 'idle' ? 'stale' : s.state === 'locked' ? 'neutral' : 'nodata'
  const word = s.state === 'held' ? t('Held') : s.state === 'idle' ? t('Idle') : s.state === 'locked' ? t('Locked') : t('Free')
  return (
    <td className={`c2o-board__cell is-${s.state}`} data-testid={`cell-${s.id}`}>
      <StatusBadge status={status} title={word}><span className="ellipsis">{h ? h.name : word}</span></StatusBadge>
      {h?.hand && <span className="c2o-board__hand" title={t('Hand raised')}>{t('hand')}</span>}
      {h && !h.verified && <span className="sr-only">{t('unverified')}</span>}
    </td>
  )
}

export function ClassBoard() {
  const { t, i18n } = useTranslation()
  const setBoard = useSeatStore(s => s.setBoard)
  const setShadow = useSeatStore(s => s.setShadow)
  const toast = useSeatStore(s => s.toast)
  const qc = useQueryClient()
  const [attention, setAttention] = useState(false)
  const [open, setOpen] = useState<string | null>(null)
  const q = useQuery<Board>({ queryKey: ['class-board'], queryFn: () => api('/api/instructor/board'), refetchInterval: 5000 })
  const rows = (q.data?.rows ?? []).filter(r => !attention || r.needs_attention.length > 0)
  const cols = q.data?.seat_columns ?? []
  const shownCols = cols.filter(c => (q.data?.rows ?? []).some(r => r.seats.some(s => s.id === c)))

  const run = async (fn: () => Promise<unknown>, ok?: string) => {
    try { await fn(); if (ok) toast(ok, 'ok') } catch (e) { toast((e as Error).message, 'alarm') }
    await qc.invalidateQueries({ queryKey: ['class-board'] })
    await qc.invalidateQueries({ queryKey: ['gate-items'] })
  }
  const broadcast = () => run(async () => {
    const text = await askText(t('Message to every team:'), '', { title: t('Broadcast') })
    if (text) await post('/api/instructor/broadcast', { text })
  })
  const timerAll = () => run(async () => {
    const m = await askText(t('Minutes (0 clears the timer):'), '10', { title: t('Timer for every team') })
    if (m === null) return
    const label = await askText(t('Label shown with the timer:'), t('Time left'), { title: t('Timer for every team') })
    await post('/api/instructor/timer', { minutes: Number(m) || 0, label: label || '' })
  })
  const shadow = (sid: string) => {
    setShadow(sid)
    useUIStore.getState().setStudyId(sid)
    setBoard(false)
  }
  const reasonText: Record<string, string> = {
    failed_must_pass: t('failed must-pass item'), idle_seat: t('idle seat'), raised_hand: t('raised hand'),
  }

  return (
    <div className="c2o-board" role="region" aria-labelledby="c2o-board-title">
      <header className="c2o-board__head">
        <h1 id="c2o-board-title" className="c2o-board__title">{t('Class board')}</h1>
        <label className="c2o-check t-12">
          <input type="checkbox" checked={attention} onChange={e => setAttention(e.target.checked)} data-testid="needs-attention" />
          {t('Needs attention only')}
        </label>
        <span className="grow" />
        <button type="button" className="c2o-btn c2o-btn--sm" onClick={broadcast}>{t('Broadcast')}</button>
        <button type="button" className="c2o-btn c2o-btn--sm" onClick={timerAll}>{t('Timer for all')}</button>
        <a className="c2o-btn c2o-btn--sm" href={`/api/instructor/timeline?format=csv&lang=${i18n.language}`} download>{t('Export CSV')}</a>
        <a className="c2o-btn c2o-btn--sm" href={`/api/instructor/timeline?format=md&lang=${i18n.language}`} download>{t('Export Markdown')}</a>
        <button type="button" className="c2o-btn c2o-btn--sm c2o-btn--quiet" onClick={() => setBoard(false)}>{t('Close')}</button>
      </header>
      {q.isError && <p className="c2o-note c2o-note--alarm c2o-board__note" role="alert">{(q.error as Error).message}</p>}
      <div className="c2o-table-wrap c2o-board__wrap">
        <table className="c2o-table c2o-table--dense c2o-board__table">
          <thead>
            <tr>
              <th scope="col">{t('Study')}</th>
              <th scope="col">{t('Gate')}</th>
              {shownCols.map(c => <th key={c} scope="col" className="c2o-board__col">{pick(q.data?.labels[c], i18n.language)}</th>)}
              <th scope="col">{t('Attention')}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(r => {
              const by = new Map(r.seats.map(s => [s.id, s]))
              const g = r.gate
              return (
                <Fragment key={r.study_id}>
                  <tr className={open === r.study_id ? 'is-open' : undefined} data-testid={`board-row-${r.study_id}`}>
                    <th scope="row" className="c2o-board__study">
                      <button type="button" className="c2o-board__name" aria-expanded={open === r.study_id}
                        onClick={() => setOpen(o => o === r.study_id ? null : r.study_id)}>{r.name || r.study_id}</button>
                      <div className="t-12 c-3 flex gap-1 wrap ai-c">
                        <span>{t('{{count}} online', { count: r.online })}</span>
                        {!r.enabled && <Tag>{t('solo')}</Tag>}
                        {r.frozen && <Tag accent>{t('frozen')}</Tag>}
                        {r.pending > 0 && <Tag>{t('{{count}} pending', { count: r.pending })}</Tag>}
                      </div>
                    </th>
                    <td className="c2o-board__gate">
                      {g.gate === 'done' ? <StatusBadge status="ok">{t('All gates passed')}</StatusBadge>
                        : g.gate ? <>
                          <StatusBadge status={(g.failed?.length ?? 0) > 0 ? 'alarm' : g.state === 'ready' ? 'ok' : 'caution'}>
                            {`${g.short} ${g.must_pass_met}/${g.must_pass}`}
                          </StatusBadge>
                          <div className="t-12 c-3">{g.state === 'under_review' ? t('under review') : g.state === 'ready' ? t('ready') : t('not ready')}</div>
                        </> : <span className="c-3">—</span>}
                    </td>
                    {shownCols.map(c => <Cell key={c} s={by.get(c)} />)}
                    <td className="t-12"><div className="c2o-board__attn">
                      {r.needs_attention.length === 0 ? <span className="c-3">—</span>
                        : r.needs_attention.map(a => <StatusBadge key={a} status={a === 'failed_must_pass' ? 'alarm' : 'caution'}>{reasonText[a]}</StatusBadge>)}
                    </div></td>
                  </tr>
                  {open === r.study_id && (
                    <tr className="c2o-board__detail"><td colSpan={shownCols.length + 3}>
                      <StudyDetail row={r} onShadow={() => shadow(r.study_id)} run={run} />
                    </td></tr>
                  )}
                </Fragment>
              )
            })}
            {rows.length === 0 && <tr><td colSpan={shownCols.length + 3} className="c2o-table__empty">{attention ? t('No team needs attention.') : t('No studies yet.')}</td></tr>}
          </tbody>
        </table>
      </div>
      <p className="t-12 c-3 c2o-board__note">{t('Cells: holder name; grey clock = idle 3 min, dashed ring = free. Open a study row for its interventions.')}</p>
    </div>
  )
}

function StudyDetail({ row, onShadow, run }: { row: BoardRow; onShadow: () => void; run: (fn: () => Promise<unknown>, ok?: string) => Promise<void> }) {
  const { t, i18n } = useTranslation()
  const sid = row.study_id
  const base = `/api/instructor/studies/${enc(sid)}`
  const items = useQuery<{ gate: string | null; short?: string; items: any[] }>({
    queryKey: ['gate-items', sid], queryFn: () => api(`${base}/gate-items`),
  })
  const hands = Object.values(row.hands)
  return (
    <div className="c2o-board__drill">
      <div className="flex wrap gap-1">
        <button type="button" className="c2o-btn c2o-btn--sm c2o-btn--primary" onClick={onShadow} data-testid="shadow">{t('Shadow (read-only)')}</button>
        <button type="button" className="c2o-btn c2o-btn--sm" onClick={() => run(async () => {
          const text = await askText(t('Message to this team:'), '', { title: t('Message {{name}}', { name: row.name }) })
          if (text) await post(`${base}/message`, { text })
        }, t('Message sent'))}>{t('Message team')}</button>
        <button type="button" className="c2o-btn c2o-btn--sm" onClick={() => run(async () => {
          const m = await askText(t('Minutes (0 clears the timer):'), '10', { title: t('Timer') })
          if (m === null) return
          const label = await askText(t('Label shown with the timer:'), t('Time left'), { title: t('Timer') })
          await post(`${base}/timer`, { minutes: Number(m) || 0, label: label || '' })
        })}>{t('Timer')}</button>
        <button type="button" className="c2o-btn c2o-btn--sm" onClick={() => run(() => post(`${base}/freeze`, { frozen: !row.frozen }))}>
          {row.frozen ? t('Unfreeze') : t('Freeze')}
        </button>
        <button type="button" className="c2o-btn c2o-btn--sm" onClick={() => run(async () => {
          const text = await askText(t('New or changed customer requirement (the team sees it as a message and a mission requirement):'), '', { title: t('Inject a customer requirement change') })
          if (text) await post(`${base}/inject`, { text })
        }, t('Customer change injected'))}>{t('Inject requirement change')}</button>
        {hands.length > 0 && <button type="button" className="c2o-btn c2o-btn--sm c2o-btn--quiet" onClick={() => run(() => post(`${base}/hands/clear`))}>{t('Lower all hands')}</button>}
        <a className="c2o-btn c2o-btn--sm c2o-btn--quiet" href={`/api/instructor/timeline?study_id=${enc(sid)}&format=csv&lang=${i18n.language}`} download>{t('Timeline CSV')}</a>
        <a className="c2o-btn c2o-btn--sm c2o-btn--quiet" href={`/api/instructor/timeline?study_id=${enc(sid)}&format=md&lang=${i18n.language}`} download>{t('Timeline Markdown')}</a>
      </div>
      {hands.length > 0 && (
        <p className="t-12 m-0">{t('Hands raised: {{list}}', { list: hands.map(h => `${h.name}${h.seat ? ` (${seatLabel(h.seat, i18n.language)})` : ''}`).join(', ') })}</p>
      )}
      {(row.gate.failed?.length ?? 0) > 0 && (
        <div>
          <h3 className="c2o-logbook__h">{t('Failed must-pass items')}</h3>
          <ul className="list-reset stack gap-1 t-12">
            {row.gate.failed!.map(f => <li key={f.id}><span className="mono">{f.id}</span> {t(f.question)} <Tag>{seatLabel(f.owner_seat, i18n.language)}</Tag></li>)}
          </ul>
        </div>
      )}
      <div>
        <h3 className="c2o-logbook__h">{t('Sign-off: manual and hybrid items ({{gate}})', { gate: items.data?.short ?? '—' })}</h3>
        <ul className="list-reset stack gap-1">
          {(items.data?.items ?? []).map(c => (
            <li key={c.id} className="flex ai-c gap-2 t-12 c2o-board__item">
              <span className="mono">{c.id}</span>
              <span className="grow">{t(c.question)}</span>
              <Tag>{c.mode}</Tag>
              <StatusBadge status={c.status === 'pass' ? 'ok' : c.status === 'fail' ? 'alarm' : 'nodata'}>
                {c.signoff ? t('signed off') : c.status}
              </StatusBadge>
              <button type="button" className="c2o-btn c2o-btn--sm" data-testid={`signoff-${c.id}`} onClick={() => run(async () => {
                if (c.signoff) { await post(`${base}/signoff`, { criterion_id: c.id, signed: false }); return }
                const note = await askText(t('Sign-off note (what you checked):'), '', { title: t('Sign off {{id}}', { id: c.id }) })
                if (note === null) return
                await post(`${base}/signoff`, { criterion_id: c.id, signed: true, note })
              })}>{c.signoff ? t('Withdraw sign-off') : t('Sign off')}</button>
            </li>
          ))}
          {(items.data?.items ?? []).length === 0 && <li className="c2o-nodata t-12">{t('No manual or hybrid items at this gate.')}</li>}
        </ul>
      </div>
    </div>
  )
}
