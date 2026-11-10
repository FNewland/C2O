/**
 * ReliabilityPanel — reliability block diagram over the mission-success horizon and the FMEA/FMECA
 * worksheet (wave 3, 3.A5; PDR-EC-05 reads it).
 *
 * Picture first: R over the horizon against the target, one bar per subsystem. Then the blocks
 * (failure rate and its source, k of n, duty) and the worksheet (severity × probability =
 * criticality, the FDIR monitor that detects the mode, the risks it feeds).
 *
 * Server: routers/reliability.py. Mounted in AitPanel.
 */
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Button, DataTable, Disclosure, Note, Panel, StatusBadge, fmtNum } from '../components/ui'

const API = '/api'

interface Block { id: string; name: string; subsystem: string; k: number; n: number; failure_rate_fit: number; rate_source: string; duty_cycle: number | null; reliability: number | null }
interface FmeaRow { id: string; code: string; subsystem: string; item: string; failure_mode: string; system_effect: string; severity: number; probability: number; criticality: number; fdir_ref: string; mitigation: string; risk_ids_json: string[] | null; single_point: boolean }
interface RelResult { mission_reliability: number; target: number | null; meets_target: boolean | null; evidence: string; design_life_reliability: number; by_subsystem: Record<string, number>; horizon: { basis: string; warnings: string[] } }

export function ReliabilityPanel({ studyId }: { studyId: string | null }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const [busy, setBusy] = useState(false)
  const { data } = useQuery<{ blocks: Block[]; result: RelResult | Record<string, never>; fmea: FmeaRow[]; counts: Record<string, number> }>({
    queryKey: ['reliability', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/reliability`).then(r => r.json()),
    enabled: !!studyId,
  })
  if (!studyId) return null
  const refresh = () => qc.invalidateQueries({ queryKey: ['reliability', studyId] })
  const post = async (path: string) => {
    setBusy(true)
    try { await fetch(`${API}/studies/${studyId}/${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' }) }
    finally { setBusy(false); refresh() }
  }
  const res = (data?.result ?? {}) as Partial<RelResult>
  const blocks = data?.blocks ?? []
  const fmea = data?.fmea ?? []
  return (
    <Panel level={2} title={t('Reliability and FMEA')}
      meta={t('Block diagram over the mission-success horizon, failure modes per subsystem')}
      actions={<div className="row gap-2">
        <Button size="sm" onClick={() => post('reliability/run')} busy={busy}>{blocks.length ? t('Run again') : t('Build the block diagram')}</Button>
        <Button size="sm" onClick={() => post('fmea/propose')} busy={busy}>{fmea.length ? t('Add missing failure modes') : t('Propose the FMEA')}</Button>
      </div>}>
      {!blocks.length ? (
        <Note>{t('No reliability analysis yet. The block diagram takes every unit of the product tree with its failure rate and computes the reliability over the mission-success horizon.')}</Note>
      ) : (
        <section className="stack gap-2 mb-3" aria-label={t('Reliability result')}>
          <p className="t-13 m-0" data-testid="reliability-evidence">
            {res.meets_target != null && <StatusBadge status={res.meets_target ? 'ok' : 'alarm'}>{res.meets_target ? t('meets the target') : t('below the target')}</StatusBadge>}{' '}
            {t('R = {{r}} over {{basis}}; target {{target}}. Over the design life: {{life}}.', {
              r: fmtNum(res.mission_reliability ?? 0, 3), basis: res.horizon?.basis ?? '', target: res.target != null ? fmtNum(res.target, 2) : t('none'),
              life: fmtNum(res.design_life_reliability ?? 0, 3) })}
          </p>
          {(res.horizon?.warnings ?? []).map(w => <Note key={w} tone="caution">{w}</Note>)}
          <div className="c2o-mbar-list">
            {Object.entries(res.by_subsystem ?? {}).map(([sub, r]) => (
              <div key={sub} className="row gap-2 t-12">
                <span className="mono" style={{ width: '4em' }}>{sub}</span>
                <span style={{ display: 'inline-block', height: 8, width: `${Math.max(2, r * 100) * 2}px`, background: 'var(--interactive, #4a7)' }} aria-hidden="true" />
                <span className="mono">{fmtNum(r, 4)}</span>
              </div>
            ))}
          </div>
          <Disclosure summary={t('Blocks')} meta={t('{{n}} blocks', { n: blocks.length })} ruled>
            <DataTable dense caption={t('Blocks')} rows={blocks} rowKey={b => b.id} columns={[
              { key: 's', header: t('Subsystem'), render: b => <span className="mono">{b.subsystem}</span>, sort: b => b.subsystem },
              { key: 'n', header: t('Unit'), render: b => b.name },
              { key: 'k', header: t('k of n'), render: b => `${b.k}/${b.n}` },
              { key: 'f', header: 'FIT', num: true, render: b => fmtNum(b.failure_rate_fit, 0), sort: b => b.failure_rate_fit },
              { key: 'd', header: t('Duty'), num: true, render: b => b.duty_cycle != null ? `${fmtNum(b.duty_cycle * 100, 0)} %` : '100 %' },
              { key: 'r', header: 'R', num: true, render: b => fmtNum(b.reliability ?? 0, 4), sort: b => b.reliability },
              { key: 'src', header: t('Rate source'), render: b => <span className="t-12 c-2">{b.rate_source}</span> },
            ]} />
          </Disclosure>
        </section>
      )}
      {fmea.length > 0 && (
        <Disclosure summary={t('FMEA worksheet')} meta={t('{{n}} failure modes, {{c}} critical', { n: fmea.length, c: data?.counts?.critical ?? 0 })} ruled>
          <DataTable dense caption={t('FMEA worksheet')} rows={fmea} rowKey={r => r.id} defaultSort={{ key: 'c', dir: 'desc' }} columns={[
            { key: 'code', header: t('Code'), render: r => <span className="mono t-12">{r.code}</span>, sort: r => r.code },
            { key: 'item', header: t('Item'), render: r => <span className="t-12">{r.item}</span> },
            { key: 'mode', header: t('Failure mode'), render: r => <span className="t-12">{r.failure_mode}</span> },
            { key: 'eff', header: t('System effect'), render: r => <span className="t-12 c-2">{r.system_effect}</span> },
            { key: 'c', header: t('S × P'), num: true, render: r => <span className={r.criticality >= 12 ? 'c-alarm' : undefined}>{r.severity}×{r.probability} = {r.criticality}</span>, sort: r => r.criticality },
            { key: 'fdir', header: t('FDIR'), render: r => <span className="mono t-12">{r.fdir_ref || '—'}</span> },
            { key: 'risk', header: t('Risks'), render: r => <span className="mono t-12">{(r.risk_ids_json ?? []).join(', ') || '—'}</span> },
          ]} />
        </Disclosure>
      )}
    </Panel>
  )
}
