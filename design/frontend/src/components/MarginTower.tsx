/**
 * MarginTower — Persistent budget margin indicators in the app header.
 *
 * Per SPINE_SPEC §10.3. Shows mass/power/link/cost/ΔV margin bars
 * with phase-rule colours from ECSSMarginEnforcer.
 * Updates on every convergence.
 *
 * SCDF-178: two optional bars from the mission-root parameters written by
 * the analyses — "Battery SoC (sim)" (sim_min_soc_pct vs the 20 % floor) and
 * "Data return" (gs_data_return_gb_per_day vs gs_data_generated_gb_per_day).
 * Read through `GET /api/elements/{root}/parameters?option_id=` (shared
 * cache key with the Blocks parameter section). Shown whenever the
 * parameters exist, even without a designStore result.
 */
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useDesignStore } from '../stores/designStore'
import { useActiveParameters } from '../hooks/useActiveParameters'
import { useUIStore } from '../stores/uiStore'
import { useActiveOptionId, optionQuery } from '../stores/optionStore'

const API = '/api'

interface AnalysisBar { id: string; label: string; value: number | null; display: string; color: string; barPct: number; title: string }

/** Mission-root parameters written by the analyses (SCDF-173/174) as margin bars. */
function useAnalysisBars(): AnalysisBar[] {
  const { t } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const optionId = useActiveOptionId(studyId)
  const { data: elements = [] } = useQuery<any[]>({
    queryKey: ['elements', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/elements`).then(r => r.json()),
    enabled: !!studyId, structuralSharing: false,
  })
  const rootId: string | undefined = elements.find((e: any) => !e.parent_id)?.id
  const { data: params = [] } = useQuery<{ name: string; effective_value: number | null; unit?: string }[]>({
    queryKey: ['element-parameters', rootId, optionId ?? null],
    queryFn: () => fetch(`${API}/elements/${rootId}/parameters${optionQuery(optionId)}`).then(r => r.ok ? r.json() : []),
    enabled: !!rootId, structuralSharing: false,
  })
  const get = (name: string): number | null => {
    const p = params.find(x => x.name === name)
    return p && typeof p.effective_value === 'number' && Number.isFinite(p.effective_value) ? p.effective_value : null
  }
  const bars: AnalysisBar[] = []
  const soc = get('sim_min_soc_pct')
  if (soc !== null) {
    const min = 20
    const color = soc >= min + 10 ? '#10b981' : soc >= min ? '#f59e0b' : '#ef4444'
    bars.push({ id: 'soc', label: 'SoC', value: soc, display: `${soc.toFixed(0)}%`, color,
      barPct: Math.min(100, Math.max(0, soc)), title: t('Battery SoC (sim): min {{soc}} % vs {{min}} % floor (mission simulation)', { soc: soc.toFixed(1), min }) })
  }
  const ret = get('gs_data_return_gb_per_day')
  const gen = get('gs_data_generated_gb_per_day')
  if (ret !== null && gen !== null) {
    const ratio = gen > 0 ? ret / gen : ret > 0 ? 1 : 0
    const pct = 100 * ratio
    const color = ratio >= 1 ? '#10b981' : ratio >= 0.8 ? '#f59e0b' : '#ef4444'
    bars.push({ id: 'data', label: t('Data', { context: 'short' }), value: pct, display: `${pct.toFixed(0)}%`, color,
      barPct: Math.min(100, Math.max(0, pct)), title: t('Data return: {{ret}} of {{gen}} GB/day returned (ground segment)', { ret: ret.toFixed(2), gen: gen.toFixed(2) }) })
  }
  return bars
}

interface MarginItem {
  id: string; label: string; paramId: string; limitParamId?: string
  unit: string; goodAbove: number; warnAbove: number
}

const MARGINS: MarginItem[] = [
  { id: 'mass', label: 'Mass', paramId: 'systems.mass_margin_percent', unit: '%', goodAbove: 20, warnAbove: 0 },
  { id: 'power', label: 'Power', paramId: 'power.margin_percent', unit: '%', goodAbove: 15, warnAbove: 0 },
  { id: 'link', label: 'Link', paramId: 'link.margin_db', unit: 'dB', goodAbove: 3, warnAbove: 0 },
  { id: 'cost', label: 'Cost', paramId: 'cost.margin_percent', unit: '%', goodAbove: 10, warnAbove: 0 },
  { id: 'deltav', label: 'ΔV', paramId: 'propulsion.delta_v_margin_percent', unit: '%', goodAbove: 10, warnAbove: 0 },
]

// English text is the i18n key: bar labels (margin id → label), shown with
// t(label, { context: 'short' }) because the label column is only 30 px wide.
const MARGIN_LABELS: Record<string, string> = {
  mass: 'Mass', power: 'Power', link: 'Link', cost: 'Cost', deltav: 'ΔV',
}

export function MarginTower() {
  const { t } = useTranslation()
  const result = useDesignStore(s => s.result)
  const params = useActiveParameters()
  const analysisBars = useAnalysisBars()

  if (!result && analysisBars.length === 0) return null

  const get = (id: string): number | null => {
    const p = params[id]
    return p && typeof p.value === 'number' ? p.value : null
  }

  return (
    <div style={{ display: 'flex', gap: '0.4rem', padding: '0.25rem 0.5rem', background: 'var(--bg-secondary, #1f2937)', borderBottom: '1px solid var(--border, #374151)', fontSize: '0.7rem' }}>
      {result && MARGINS.map(m => {
        const val = get(m.paramId)
        const color = val === null ? '#6b7280' : val >= m.goodAbove ? '#10b981' : val >= m.warnAbove ? '#f59e0b' : '#ef4444'
        const barPct = val !== null ? Math.min(100, Math.max(0, (val / m.goodAbove) * 50 + 50)) : 0
        return (
          <div key={m.id} style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', minWidth: '80px' }}>
            <span style={{ color: '#9ca3af', width: '30px', textAlign: 'right', fontSize: '0.62rem' }}>{t(MARGIN_LABELS[m.id] ?? m.label, { context: 'short' })}</span>
            <div style={{ flex: 1, height: 6, background: '#111827', borderRadius: 3, minWidth: 30, position: 'relative' }}>
              <div style={{ height: '100%', width: `${barPct}%`, background: color, borderRadius: 3, transition: 'width 0.3s' }} />
            </div>
            <span style={{ color, fontFamily: 'monospace', fontWeight: 600, minWidth: '35px', textAlign: 'right', fontSize: '0.65rem' }}>
              {val !== null ? `${val.toFixed(0)}${m.unit}` : '—'}
            </span>
          </div>
        )
      })}
      {analysisBars.map(b => (
        <div key={b.id} title={b.title} style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', minWidth: '80px' }}>
          <span style={{ color: '#9ca3af', width: '30px', textAlign: 'right', fontSize: '0.62rem' }}>{b.label}</span>
          <div style={{ flex: 1, height: 6, background: '#111827', borderRadius: 3, minWidth: 30, position: 'relative' }}>
            <div style={{ height: '100%', width: `${b.barPct}%`, background: b.color, borderRadius: 3, transition: 'width 0.3s' }} />
          </div>
          <span style={{ color: b.color, fontFamily: 'monospace', fontWeight: 600, minWidth: '35px', textAlign: 'right', fontSize: '0.65rem' }}>
            {b.display}
          </span>
        </div>
      ))}
    </div>
  )
}
