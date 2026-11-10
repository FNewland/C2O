/**
 * ConopsPhases (W7.01, Nov 2026) — the mission phases of the study's ConOps: name, type,
 * duration, entry and exit criteria, activities. GET/PUT /api/studies/{id}/conops/phases.
 * Once saved, a mission-definition change never regenerates them. "Use the template" loads
 * the LEO small-satellite pattern (LEOP about a week, platform commissioning to day 30,
 * payload commissioning to day 90, operations, disposal) for editing; nothing is saved until
 * Save. Also offers the ConOps document built from the study (Modes tab, phases, contacts,
 * data flow, flight rules, end of life).
 *
 * Mounted in Traceability › Mission need; the Modes panel can mount it as well
 * (``<ConopsPhases studyId={…} />``).
 */
import { useEffect, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import i18n from '../i18n'
import { Button, Disclosure, Note } from '../components/ui'

const API = '/api'

export interface Phase {
  id: string
  name: string
  phase_type: string
  duration_days: number
  description: string
  entry_criteria: string
  exit_criteria: string
  modes?: string[]
}

// English text is the i18n key
const TYPE_LABEL: Record<string, string> = {
  leop: 'LEOP', commissioning: 'Commissioning', transfer: 'Transfer', nominal: 'Nominal operations',
  extended: 'Extended mission', disposal: 'Disposal',
}

export function ConopsPhases({ studyId }: { studyId: string | null }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const { data } = useQuery<{ edited: boolean; phases: Phase[]; template: Phase[]; phase_types: string[] }>({
    queryKey: ['conops-phases', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/conops/phases`).then(r => (r.ok ? r.json() : null)),
    enabled: !!studyId,
  })
  const [rows, setRows] = useState<Phase[] | null>(null)
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState<{ tone: 'ok' | 'alarm'; text: string } | null>(null)
  useEffect(() => { setRows(null); setMsg(null) }, [studyId])
  const view = rows ?? data?.phases ?? []
  const dirty = rows !== null
  const set = (i: number, patch: Partial<Phase>) => setRows((rows ?? data?.phases ?? []).map((p, j) => (j === i ? { ...p, ...patch } : p)))
  let day = 0

  const save = async () => {
    if (!studyId || !rows) return
    setBusy(true); setMsg(null)
    const res = await fetch(`${API}/studies/${encodeURIComponent(studyId)}/conops/phases`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phases: rows.map(({ modes: _m, ...p }) => p) }),
    })
    setBusy(false)
    if (!res.ok) { setMsg({ tone: 'alarm', text: t('The phases could not be saved ({{code}}).', { code: res.status }) }); return }
    setRows(null)
    setMsg({ tone: 'ok', text: t('Phases saved.') })
    void qc.invalidateQueries({ queryKey: ['conops-phases', studyId] })
  }

  const download = async () => {
    if (!studyId) return
    const res = await fetch(`${API}/studies/${encodeURIComponent(studyId)}/conops/document?lang=${i18n.language === 'fr' ? 'fr' : 'en'}`, { method: 'POST' })
    if (!res.ok) { setMsg({ tone: 'alarm', text: t('The ConOps document could not be generated ({{code}}).', { code: res.status }) }); return }
    const blob = await res.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = /filename="([^"]+)"/.exec(res.headers.get('content-disposition') || '')?.[1] || 'SpaceCDF_ConOps.docx'
    a.click()
    setTimeout(() => URL.revokeObjectURL(a.href), 1000)
  }

  if (!studyId) return null
  return (
    <Disclosure ruled summary={t('ConOps phases')} meta={data?.edited ? t('edited by the team') : t('tool defaults')}>
      <div className="stack gap-1" data-testid="conops-phases">
        <p className="t-12 c-2 m-0">
          {t('Mission phases with their duration and entry and exit criteria. The ConOps document lists them with the modes of each phase (Modes tab).')}
        </p>
        <table className="c2o-table c2o-table--dense">
          <thead>
            <tr className="bb"><th>{t('Phase')}</th><th>{t('Type')}</th><th className="num">{t('Duration (days)')}</th>
              <th className="num">{t('Ends on day')}</th><th>{t('Entry criteria')}</th><th>{t('Exit criteria')}</th><th /></tr>
          </thead>
          <tbody>
            {view.map((p, i) => {
              day += Number(p.duration_days) || 0
              return (
                <tr key={`${p.id}-${i}`} className="bb">
                  <td><input className="c2o-input c2o-input--sm" aria-label={t('Phase {{n}}: name', { n: i + 1 })} value={p.name} onChange={e => set(i, { name: e.target.value })} /></td>
                  <td>
                    <select className="c2o-select c2o-select--sm" aria-label={t('Phase {{n}}: type', { n: i + 1 })} value={p.phase_type} onChange={e => set(i, { phase_type: e.target.value })}>
                      {(data?.phase_types ?? Object.keys(TYPE_LABEL)).map(x => <option key={x} value={x}>{t(TYPE_LABEL[x] ?? x)}</option>)}
                    </select>
                  </td>
                  <td className="num"><input className="c2o-input c2o-input--sm c2o-input--num" type="number" min={0} step={1} style={{ width: '5.5rem' }}
                    aria-label={t('Phase {{n}}: duration in days', { n: i + 1 })} value={p.duration_days} onChange={e => set(i, { duration_days: Number(e.target.value) })} /></td>
                  <td className="num t-12 c-2">{Math.round(day)}</td>
                  <td><textarea className="c2o-input" rows={2} aria-label={t('Phase {{n}}: entry criteria', { n: i + 1 })} value={p.entry_criteria} onChange={e => set(i, { entry_criteria: e.target.value })} /></td>
                  <td><textarea className="c2o-input" rows={2} aria-label={t('Phase {{n}}: exit criteria', { n: i + 1 })} value={p.exit_criteria} onChange={e => set(i, { exit_criteria: e.target.value })} /></td>
                  <td><button type="button" className="c2o-btn c2o-btn--sm c2o-btn--danger" aria-label={t('Remove phase {{n}}', { n: i + 1 })}
                    onClick={() => setRows(view.filter((_, j) => j !== i))}>×</button></td>
                </tr>
              )
            })}
          </tbody>
        </table>
        <div className="flex gap-1 wrap">
          <Button size="sm" onClick={() => setRows([...view, { id: '', name: t('New phase'), phase_type: 'nominal', duration_days: 0, description: '', entry_criteria: '', exit_criteria: '' }])}>
            {t('+ Add phase')}
          </Button>
          {data?.template && <Button size="sm" variant="quiet" onClick={() => setRows(data.template)}>{t('Use the template')}</Button>}
          <span className="grow" />
          <Button size="sm" variant="primary" busy={busy} disabledReason={!dirty ? t('Nothing to save') : undefined} onClick={() => void save()}>{t('Save phases')}</Button>
          <Button size="sm" onClick={() => void download()}>{t('ConOps document (.docx)')}</Button>
        </div>
        {msg && <Note tone={msg.tone} role="status">{msg.text}</Note>}
      </div>
    </Disclosure>
  )
}
