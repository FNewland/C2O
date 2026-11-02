/**
 * OptionCompare — A/B comparison of two design options (SCDF-172).
 *
 * GET /api/studies/{id}/options/compare?a=&b= → the parameters whose
 * effective value differs (with delta and which side carries an override),
 * the last-run summaries of every analysis side by side with the numeric
 * fields that moved, and the unresolved conflict counts.
 *
 * Not mounted here — SCDF-178 places it in the Analyses tab (a "Compare
 * options" card) or as a modal from the OptionSwitcher.
 */
import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useUIStore } from '../stores/uiStore'
import { useOptionStore } from '../stores/optionStore'
import { useOptions } from './OptionSwitcher'
import type { OptionCompareResult } from '../types/options'
import { fs } from '../theme/tokens'

const API = '/api'

async function jsonOrThrow(res: Response) {
  if (!res.ok) {
    let msg = `${res.status}`
    try { const b = await res.json(); msg = typeof b.detail === 'string' ? b.detail : JSON.stringify(b.detail ?? b) } catch { /* noop */ }
    throw new Error(msg)
  }
  return res.json()
}

function fmt(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '—'
  const a = Math.abs(v)
  if (a !== 0 && (a < 1e-3 || a >= 1e6)) return v.toExponential(3)
  return Number.isInteger(v) ? String(v) : v.toFixed(a < 1 ? 4 : 3).replace(/\.?0+$/, '')
}
function fmtDelta(d: number | null, a: number | null): string {
  if (d === null) return '—'
  const sign = d > 0 ? '+' : ''
  const pct = a && a !== 0 ? ` (${sign}${(100 * d / a).toFixed(1)}%)` : ''
  return `${sign}${fmt(d)}${pct}`
}
const deltaColor = (d: number | null) => d === null ? 'var(--text-secondary)' : d > 0 ? 'var(--status-caution)' : d < 0 ? 'var(--interactive)' : 'var(--text-primary)'


function OverrideDot({ on, side }: { on: boolean; side: 'A' | 'B' }) {
  const { t } = useTranslation()
  if (!on) return null
  return <span title={t('override row in option {{side}}', { side })} style={{ marginLeft: '0.25rem', fontSize: fs.label, padding: '0 0.25rem', borderRadius: '3px', background: 'color-mix(in srgb, var(--status-caution) 13%, transparent)', color: 'var(--status-caution)', border: '1px solid color-mix(in srgb, var(--status-caution) 33%, transparent)' }}>{t('override')}</span>
}

export function OptionCompare({ studyId: studyIdProp, initialA, initialB }: {
  studyId?: string | null; initialA?: string | null; initialB?: string | null
}) {
  const { t } = useTranslation()
  const wbStudy = useUIStore(s => s.studyId)
  const studyId = studyIdProp ?? wbStudy
  const activeId = useOptionStore(s => (studyId ? s.activeByStudy[studyId] ?? null : null))
  const { data: options = [] } = useOptions(studyId)
  const baseline = options.find(o => o.is_baseline)
  const [a, setA] = useState<string>(initialA ?? '')
  const [b, setB] = useState<string>(initialB ?? '')

  // Defaults: A = baseline, B = the active option (or the first non-baseline one).
  useEffect(() => {
    if (!options.length) return
    if (!a && baseline) setA(baseline.id)
    if (!b) {
      const cand = options.find(o => o.id === activeId && !o.is_baseline) ?? options.find(o => !o.is_baseline)
      if (cand) setB(cand.id)
    }
  }, [options, baseline, activeId, a, b])

  const { data, isFetching, error } = useQuery<OptionCompareResult>({
    queryKey: ['option-compare', studyId, a, b],
    queryFn: () => fetch(`${API}/studies/${studyId}/options/compare?a=${encodeURIComponent(a)}&b=${encodeURIComponent(b)}`).then(jsonOrThrow),
    enabled: !!studyId && !!a && !!b,
  })

  if (!studyId) return null
  const nameOf = (id: string) => { const o = options.find(x => x.id === id); return o ? (o.is_baseline ? t('Baseline') : o.name) : id }

  return (
    <div className="t-12">
      <div className="flex ai-c gap-2 mb-2 wrap">
        <span className="c-2 t-12">{t('Compare')}</span>
        <select value={a} onChange={e => setA(e.target.value)} className="c2o-select c2o-select--sm">
          {options.map(o => <option key={o.id} value={o.id}>A: {o.is_baseline ? t('Baseline') : o.name}</option>)}
        </select>
        <span className="c-2">{t('vs')}</span>
        <select value={b} onChange={e => setB(e.target.value)} className="c2o-select c2o-select--sm">
          {options.map(o => <option key={o.id} value={o.id}>B: {o.is_baseline ? t('Baseline') : o.name}</option>)}
        </select>
        <button onClick={() => { setA(b); setB(a) }} title={t('Swap A and B')}
          className="bg-none bd rounded cursor-p t-12 c-2 py-0 px-1">⇄</button>
        {isFetching && <span className="c-2 t-12">{t('loading…')}</span>}
        {data && (
          <span className="ml-auto c-2 t-12">
            {t('{{count}} parameters differ · conflicts A {{a}} / B {{b}}', { count: data.parameters.length, a: data.conflicts.a, b: data.conflicts.b, defaultValue_one: '{{count}} parameter differ · conflicts A {{a}} / B {{b}}' })}
          </span>
        )}
      </div>
      {error && <div className="c-alarm t-12">{(error as Error).message}</div>}
      {options.length < 2 && <div className="c-2 t-12">{t('Create or branch an option to compare it with the baseline.')}</div>}
      {data && a === b && <div className="c-2 t-12">{t('Pick two different options.')}</div>}

      {data && data.parameters.length > 0 && (
        <table className="c2o-table c2o-table--dense">
          <thead>
            <tr>
              <th>{t('Element')}</th><th>{t('Parameter')}</th>
              <th className="ta-r">A: {nameOf(a)}</th>
              <th className="ta-r">B: {nameOf(b)}</th>
              <th className="ta-r">Δ (B − A)</th><th>{t('Unit')}</th>
            </tr>
          </thead>
          <tbody>
            {data.parameters.map(p => (
              <tr key={`${p.element_id}:${p.name}`}>
                <td>{p.element}</td>
                <td className="w-600">{p.name}</td>
                <td className="ta-r">{fmt(p.a)}<OverrideDot on={p.a_override} side="A" /></td>
                <td className="ta-r">{fmt(p.b)}<OverrideDot on={p.b_override} side="B" /></td>
                <td style={{ textAlign: 'right', color: deltaColor(p.delta), fontWeight: 600 }}>{fmtDelta(p.delta, p.a)}</td>
                <td className="c-2">{p.unit}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {data && a !== b && data.parameters.length === 0 && (
        <div className="c-2 t-12 mb-2">{t('No parameter differs between the two options.')}</div>
      )}

      {data && data.analyses.length > 0 && (
        <div>
          <div className="t-12 c-2 mb-1">{t('Analyses (last run per option)')}</div>
          <table className="c2o-table c2o-table--dense">
            <thead>
              <tr>
                <th>{t('Analysis')}</th><th>{t('A run')}</th><th>{t('B run')}</th><th>{t('Differences')}</th>
              </tr>
            </thead>
            <tbody>
              {data.analyses.map(x => (
                <tr key={x.analysis}>
                  <td className="w-600">{x.analysis}</td>
                  <td>{x.a_run_id ? `${x.a_status ?? ''} · ${x.a_finished_at?.slice(0, 16).replace('T', ' ') ?? ''}` : <span className="c-2">{t('not run')}</span>}</td>
                  <td>{x.b_run_id ? `${x.b_status ?? ''} · ${x.b_finished_at?.slice(0, 16).replace('T', ' ') ?? ''}` : <span className="c-2">{t('not run')}</span>}</td>
                  <td>
                    {x.deltas.length === 0 && <span className="c-2">—</span>}
                    {x.deltas.slice(0, 12).map(d => (
                      <div key={d.key} className="nowrap">
                        <span className="c-2">{d.key}</span>: {fmt(d.a)} → {fmt(d.b)}{' '}
                        <span style={{ color: deltaColor(d.delta), fontWeight: 600 }}>{fmtDelta(d.delta, d.a)}</span>
                      </div>
                    ))}
                    {x.deltas.length > 12 && <div className="c-2">{t('… {{count}} more', { count: x.deltas.length - 12 })}</div>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {data && data.warnings.length > 0 && <div className="c-caution t-12 mt-1">{data.warnings.join('; ')}</div>}
    </div>
  )
}

export default OptionCompare
