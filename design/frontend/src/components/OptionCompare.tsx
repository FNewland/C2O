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

const th: React.CSSProperties = { textAlign: 'left', padding: '0.15rem 0.35rem', fontSize: fs.label, color: 'var(--text-secondary)', borderBottom: '1px solid var(--border)', whiteSpace: 'nowrap' }
const td: React.CSSProperties = { padding: '0.15rem 0.35rem', fontSize: fs.label, borderBottom: '1px solid var(--border)', verticalAlign: 'top', fontVariantNumeric: 'tabular-nums' }
const sel: React.CSSProperties = { fontSize: fs.label, padding: '0.1rem 0.2rem', background: 'var(--bg-primary)', color: 'var(--text-primary)', border: '1px solid var(--border)', borderRadius: '3px' }

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
    <div style={{ fontSize: fs.label }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem', flexWrap: 'wrap' }}>
        <span style={{ color: 'var(--text-secondary)', fontSize: fs.label }}>{t('Compare')}</span>
        <select value={a} onChange={e => setA(e.target.value)} style={sel}>
          {options.map(o => <option key={o.id} value={o.id}>A: {o.is_baseline ? t('Baseline') : o.name}</option>)}
        </select>
        <span style={{ color: 'var(--text-secondary)' }}>{t('vs')}</span>
        <select value={b} onChange={e => setB(e.target.value)} style={sel}>
          {options.map(o => <option key={o.id} value={o.id}>B: {o.is_baseline ? t('Baseline') : o.name}</option>)}
        </select>
        <button onClick={() => { setA(b); setB(a) }} title={t('Swap A and B')}
          style={{ background: 'none', border: '1px solid var(--border)', borderRadius: '3px', cursor: 'pointer', fontSize: fs.label, color: 'var(--text-secondary)', padding: '0 0.3rem' }}>⇄</button>
        {isFetching && <span style={{ color: 'var(--text-secondary)', fontSize: fs.label }}>{t('loading…')}</span>}
        {data && (
          <span style={{ marginLeft: 'auto', color: 'var(--text-secondary)', fontSize: fs.label }}>
            {t('{{count}} parameters differ · conflicts A {{a}} / B {{b}}', { count: data.parameters.length, a: data.conflicts.a, b: data.conflicts.b, defaultValue_one: '{{count}} parameter differ · conflicts A {{a}} / B {{b}}' })}
          </span>
        )}
      </div>
      {error && <div style={{ color: 'var(--status-alarm)', fontSize: fs.label }}>{(error as Error).message}</div>}
      {options.length < 2 && <div style={{ color: 'var(--text-secondary)', fontSize: fs.label }}>{t('Create or branch an option to compare it with the baseline.')}</div>}
      {data && a === b && <div style={{ color: 'var(--text-secondary)', fontSize: fs.label }}>{t('Pick two different options.')}</div>}

      {data && data.parameters.length > 0 && (
        <table style={{ borderCollapse: 'collapse', width: '100%', marginBottom: '0.6rem' }}>
          <thead>
            <tr>
              <th style={th}>{t('Element')}</th><th style={th}>{t('Parameter')}</th>
              <th style={{ ...th, textAlign: 'right' }}>A: {nameOf(a)}</th>
              <th style={{ ...th, textAlign: 'right' }}>B: {nameOf(b)}</th>
              <th style={{ ...th, textAlign: 'right' }}>Δ (B − A)</th><th style={th}>{t('Unit')}</th>
            </tr>
          </thead>
          <tbody>
            {data.parameters.map(p => (
              <tr key={`${p.element_id}:${p.name}`}>
                <td style={td}>{p.element}</td>
                <td style={{ ...td, fontWeight: 600 }}>{p.name}</td>
                <td style={{ ...td, textAlign: 'right' }}>{fmt(p.a)}<OverrideDot on={p.a_override} side="A" /></td>
                <td style={{ ...td, textAlign: 'right' }}>{fmt(p.b)}<OverrideDot on={p.b_override} side="B" /></td>
                <td style={{ ...td, textAlign: 'right', color: deltaColor(p.delta), fontWeight: 600 }}>{fmtDelta(p.delta, p.a)}</td>
                <td style={{ ...td, color: 'var(--text-secondary)' }}>{p.unit}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {data && a !== b && data.parameters.length === 0 && (
        <div style={{ color: 'var(--text-secondary)', fontSize: fs.label, marginBottom: '0.5rem' }}>{t('No parameter differs between the two options.')}</div>
      )}

      {data && data.analyses.length > 0 && (
        <div>
          <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>{t('Analyses (last run per option)')}</div>
          <table style={{ borderCollapse: 'collapse', width: '100%' }}>
            <thead>
              <tr>
                <th style={th}>{t('Analysis')}</th><th style={th}>{t('A run')}</th><th style={th}>{t('B run')}</th><th style={th}>{t('Differences')}</th>
              </tr>
            </thead>
            <tbody>
              {data.analyses.map(x => (
                <tr key={x.analysis}>
                  <td style={{ ...td, fontWeight: 600 }}>{x.analysis}</td>
                  <td style={td}>{x.a_run_id ? `${x.a_status ?? ''} · ${x.a_finished_at?.slice(0, 16).replace('T', ' ') ?? ''}` : <span style={{ color: 'var(--text-secondary)' }}>{t('not run')}</span>}</td>
                  <td style={td}>{x.b_run_id ? `${x.b_status ?? ''} · ${x.b_finished_at?.slice(0, 16).replace('T', ' ') ?? ''}` : <span style={{ color: 'var(--text-secondary)' }}>{t('not run')}</span>}</td>
                  <td style={td}>
                    {x.deltas.length === 0 && <span style={{ color: 'var(--text-secondary)' }}>—</span>}
                    {x.deltas.slice(0, 12).map(d => (
                      <div key={d.key} style={{ whiteSpace: 'nowrap' }}>
                        <span style={{ color: 'var(--text-secondary)' }}>{d.key}</span>: {fmt(d.a)} → {fmt(d.b)}{' '}
                        <span style={{ color: deltaColor(d.delta), fontWeight: 600 }}>{fmtDelta(d.delta, d.a)}</span>
                      </div>
                    ))}
                    {x.deltas.length > 12 && <div style={{ color: 'var(--text-secondary)' }}>{t('… {{count}} more', { count: x.deltas.length - 12 })}</div>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {data && data.warnings.length > 0 && <div style={{ color: 'var(--status-caution)', fontSize: fs.label, marginTop: '0.3rem' }}>{data.warnings.join('; ')}</div>}
    </div>
  )
}

export default OptionCompare
