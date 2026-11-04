/**
 * SimConfigExportDialog — Export → "Simulator configuration" (design-to-ops, Nov 2026).
 *
 * Shows the readiness checklist of the simulator configuration the study would export now
 * (GET /api/studies/{sid}/export/sim-config): per CDR area, how many values come from the
 * design and which are still a default, missing in the design, or not representable by the
 * EOSAT-1-class simulator; whether the result passes the simulator's own loaders. Downloads
 * the configuration directory as a zip (…/sim-config.zip), to run with
 * `sim/start.sh --config=<dir>` (docs/plan_2026-11/design_sim/SIM_EXPORT.md).
 */
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { getLang } from '../i18n'
import { Button, Dialog, Disclosure, Note, StatusBadge, Tag } from '../components/ui'
import type { Status } from '../components/ui'

const API = '/api'

type ItemStatus = 'design' | 'default' | 'missing' | 'unsupported'

interface Item { area: string; item: string; status: ItemStatus; file: string; key: string; source: string }
interface Area {
  id: string; label: { en: string; fr: string }
  design: number; default: number; missing: number; unsupported: number; total: number; items: Item[]
}
interface Report {
  study_id: string; study_name: string; dataset: 'empty' | 'design' | 'reference'
  areas: Area[]; totals: Record<ItemStatus, number>; ready: boolean; files: string[]
  validation?: { available: boolean; errors: string[]; checked: string[] }
}

const BADGE: Record<ItemStatus, Status> = { design: 'ok', default: 'neutral', missing: 'caution', unsupported: 'alarm' }

export function SimConfigExportDialog({ studyId, onClose }: { studyId: string; onClose: () => void }) {
  const { t } = useTranslation()
  const [report, setReport] = useState<Report | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const lang = getLang() === 'fr' ? 'fr' : 'en'

  const statusLabel: Record<ItemStatus, string> = {
    design: t('from the design'), default: t('default'), missing: t('missing in the design'), unsupported: t('not supported by the simulator'),
  }
  const datasetLabel: Record<Report['dataset'], string> = {
    empty: t('No CDR database: the simulator model interface (EOSAT-1) is used for the TM/TC database, FDIR and operations tables.'),
    design: t('Designed CDR database: mapped onto the simulator model interface by name; the full database is in design_db/.'),
    reference: t('EOSAT-1 reference CDR database: the TM/TC database, FDIR and operations tables are written from it.'),
  }

  useEffect(() => {
    let live = true
    fetch(`${API}/studies/${studyId}/export/sim-config`)
      .then(async r => { if (!r.ok) throw new Error(`${r.status} ${(await r.text()).slice(0, 200)}`); return r.json() })
      .then(d => { if (live) setReport(d) })
      .catch(e => { if (live) setError(String(e.message || e)) })
    return () => { live = false }
  }, [studyId])

  const download = async () => {
    setBusy(true); setError(null)
    try {
      const res = await fetch(`${API}/studies/${studyId}/export/sim-config.zip`)
      if (!res.ok) throw new Error(`${res.status}`)
      const blob = await res.blob()
      const cd = res.headers.get('Content-Disposition') || ''
      const name = /filename="([^"]+)"/.exec(cd)?.[1] || `simconfig_${studyId}.zip`
      const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name; a.click(); URL.revokeObjectURL(a.href)
    } catch (e: any) {
      setError(t('Simulator configuration: {{message}}', { message: e.message }))
    } finally { setBusy(false) }
  }

  const v = report?.validation
  return (
    <Dialog open title={t('Simulator configuration')} onClose={onClose} width={720}
      actions={<>
        <button type="button" className="c2o-btn" onClick={onClose}>{t('Close')}</button>
        <Button variant="primary" onClick={download} busy={busy}
          disabledReason={!report ? t('Readiness checklist still loading') : undefined}>{t('Download ZIP')}</Button>
      </>}>
      <p className="t-12 c-2 m-0 mb-2">
        {t('A configuration directory for the EOSAT-1-class simulator. Every value comes from the design or is a documented default; run it with')}{' '}
        <span className="mono">sim/start.sh --config=&lt;dir&gt;</span>.
      </p>
      {error && <Note tone="alarm" role="alert" className="mb-2">{error}</Note>}
      {!report && !error && <p className="t-12 c-2" role="status">{t('Building the readiness checklist…')}</p>}
      {report && (
        <div className="stack gap-2">
          <div className="flex ai-c gap-2 wrap">
            {v && !v.available && <StatusBadge status="nodata">{t('Not validated (simulator packages not on this server)')}</StatusBadge>}
            {v && v.available && v.errors.length === 0 &&
              <StatusBadge status="ok">{t('Loads with the simulator’s own loaders ({{n}} files checked)', { n: v.checked.length })}</StatusBadge>}
            {v && v.available && v.errors.length > 0 &&
              <StatusBadge status="alarm">{t('{{n}} loader errors', { n: v.errors.length })}</StatusBadge>}
            <Tag>{t('{{n}} from the design', { n: report.totals.design })}</Tag>
            <Tag>{t('{{n}} default', { n: report.totals.default })}</Tag>
            {report.totals.missing > 0 && <Tag accent>{t('{{n}} missing', { n: report.totals.missing })}</Tag>}
            {report.totals.unsupported > 0 && <Tag accent>{t('{{n}} not supported', { n: report.totals.unsupported })}</Tag>}
          </div>
          <Note tone="info">{datasetLabel[report.dataset]}</Note>
          {v && v.errors.length > 0 && (
            <Note tone="alarm" role="alert">
              <ul className="m-0 pl-3 t-12">{v.errors.slice(0, 8).map(e => <li key={e} className="mono">{e}</li>)}</ul>
            </Note>
          )}
          <table className="c2o-table t-12" aria-label={t('Readiness by CDR area')}>
            <thead>
              <tr>
                <th scope="col">{t('Area')}</th>
                <th scope="col" className="ta-r">{t('Design')}</th>
                <th scope="col" className="ta-r">{t('Default')}</th>
                <th scope="col" className="ta-r">{t('Missing')}</th>
                <th scope="col" className="ta-r">{t('Not supported')}</th>
              </tr>
            </thead>
            <tbody>
              {report.areas.map(a => (
                <tr key={a.id}>
                  <th scope="row" className="w-600">{a.label[lang]}</th>
                  <td className="ta-r mono">{a.design}</td>
                  <td className="ta-r mono">{a.default}</td>
                  <td className="ta-r mono">{a.missing || ''}</td>
                  <td className="ta-r mono">{a.unsupported || ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="stack gap-1">
            {report.areas.filter(a => a.items.some(i => i.status !== 'design')).map(a => {
              const open = a.items.filter(i => i.status !== 'design')
              return (
                <Disclosure key={a.id} summary={a.label[lang]} defaultOpen={a.missing + a.unsupported > 0}
                  meta={t('{{n}} still default, missing or not supported', { n: open.length })}>
                  <ul className="list-reset t-12 stack gap-1">
                    {open.map((i, k) => (
                      <li key={`${i.item}-${k}`} className="flex gap-2 ai-b">
                        <StatusBadge status={BADGE[i.status]}>{statusLabel[i.status]}</StatusBadge>
                        <span className="grow min0"><span className="w-600">{i.item}</span>{' — '}<span className="c-2">{i.source}</span>
                          {i.file && <span className="mono c-3">{' '}({i.file}{i.key ? ` · ${i.key}` : ''})</span>}</span>
                      </li>
                    ))}
                  </ul>
                </Disclosure>
              )
            })}
          </div>
        </div>
      )}
    </Dialog>
  )
}
