/**
 * ParameterPanel — parameters & equations for one design element (SCDF-160).
 *
 * Rows from GET /api/elements/{id}/parameters. Each row: name, unit,
 * effective value, value switch, formula (beside the value), provenance chip,
 * evaluation errors in red. Inline edit of manual value and formula via
 * PUT /api/elements/{id}/parameters/{name}; add / delete; study-wide
 * "Recompute".
 *
 * Options (SCDF-172): every request carries the active option from
 * `optionStore` (`?option_id=`; none for the baseline). Rows that are
 * overrides of the active option show an "override in <option>" chip; a PUT
 * while an option is active writes the option row and leaves the baseline
 * alone; delete removes the override so the baseline shows through.
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import {
  VALUE_SWITCHES, type ParameterUpsert, type ParameterView, type Provenance, type ValueSwitch,
} from '../types/arcadia'
import { optionQuery, useActiveOptionId } from '../stores/optionStore'
import { useOptions } from './OptionSwitcher'
import { fs } from '../theme/tokens'

const API = '/api'

const PROV_COLORS: Record<Provenance, string> = { manual: 'var(--status-caution)', formula: 'var(--cat-2)', column: 'var(--interactive)', agent: 'var(--status-ok)' }
// English text is the i18n key
const PROV_LABELS: Record<string, string> = { manual: 'manual', formula: 'formula', column: 'column', agent: 'agent' }
// English text is the i18n key
const SWITCH_LABELS: Record<string, string> = { manual: 'manual', computed: 'computed', reference: 'reference' }
// English text is the i18n key
const PROV_TITLES: Record<Provenance, string> = {
  manual: 'Entered by hand (value switch = manual)',
  formula: 'Computed from the formula',
  column: 'Mirrors the element column (mass_kg, power_avg_w, …)',
  agent: 'Set by a design agent / analysis run',
}

async function jsonOrThrow(res: Response) {
  if (!res.ok) {
    let msg = `${res.status}`
    try {
      const b = await res.json()
      const d = b.detail
      msg = typeof d === 'string' ? d : d?.details ? (Array.isArray(d.details) ? d.details.join('; ') : String(d.details)) : JSON.stringify(d ?? b)
    } catch { /* noop */ }
    throw new Error(msg)
  }
  return res.status === 204 ? null : res.json()
}

function fmt(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '—'
  const a = Math.abs(v)
  if (a !== 0 && (a < 1e-3 || a >= 1e6)) return v.toExponential(3)
  return Number.isInteger(v) ? String(v) : v.toFixed(a < 1 ? 4 : 3).replace(/\.?0+$/, '')
}

export function ProvenanceChip({ p }: { p: Provenance }) {
  const { t } = useTranslation()
  const c = PROV_COLORS[p] || 'var(--text-3)'
  return <span title={PROV_TITLES[p] ? t(PROV_TITLES[p]) : p} style={{ fontSize: fs.label, padding: '0 0.3rem', borderRadius: '3px', background: `color-mix(in srgb, ${c} 13%, transparent)`, color: c, border: `1px solid color-mix(in srgb, ${c} 33%, transparent)` }}>{PROV_LABELS[p] ? t(PROV_LABELS[p]) : p}</span>
}

export function OptionOverrideChip({ optionName }: { optionName: string }) {
  const { t } = useTranslation()
  const c = 'var(--status-caution)'
  return <span title={t('This value is an override that exists only in option "{{name}}"; the baseline row is shadowed', { name: optionName })}
    style={{ fontSize: fs.label, padding: '0 0.3rem', borderRadius: '3px', background: `color-mix(in srgb, ${c} 13%, transparent)`, color: c, border: `1px solid color-mix(in srgb, ${c} 33%, transparent)`, marginLeft: '0.2rem', whiteSpace: 'nowrap' }}>
    {t('override in {{name}}', { name: optionName })}
  </span>
}

export function ParameterPanel({ elementId, studyId, compact }: { elementId: string | null; studyId: string | null; compact?: boolean }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const optionId = useActiveOptionId(studyId)
  const oq = optionQuery(optionId)
  const { data: options = [] } = useOptions(studyId)
  const activeOption = options.find(o => o.id === optionId)
  const optionName = activeOption?.name ?? t('option')
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState<string | null>(null)   // parameter name being edited
  const [manual, setManual] = useState('')
  const [formula, setFormula] = useState('')
  const [adding, setAdding] = useState(false)
  const [newName, setNewName] = useState('')
  const [newUnit, setNewUnit] = useState('')
  const [newValue, setNewValue] = useState('')

  const { data: params = [], isLoading } = useQuery<ParameterView[]>({
    queryKey: ['element-parameters', elementId, optionId ?? null],
    queryFn: () => fetch(`${API}/elements/${elementId}/parameters${oq}`).then(jsonOrThrow),
    enabled: !!elementId, structuralSharing: false,
  })

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['element-parameters'] })
    qc.invalidateQueries({ queryKey: ['study-parameters', studyId] })
    qc.invalidateQueries({ queryKey: ['elements', studyId] })
    qc.invalidateQueries({ queryKey: ['budget'] })
  }
  const onErr = (e: Error) => setError(e.message)

  const upsert = useMutation({
    mutationFn: ({ name, body }: { name: string; body: ParameterUpsert }) =>
      fetch(`${API}/elements/${elementId}/parameters/${encodeURIComponent(name)}${oq}`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
      }).then(jsonOrThrow),
    onSuccess: () => { invalidate(); setEditing(null); setError(null) }, onError: onErr,
  })
  const remove = useMutation({
    mutationFn: (name: string) =>
      fetch(`${API}/elements/${elementId}/parameters/${encodeURIComponent(name)}${oq}`, { method: 'DELETE' }).then(jsonOrThrow),
    onSuccess: invalidate, onError: onErr,
  })
  const recompute = useMutation({
    mutationFn: () => fetch(`${API}/studies/${studyId}/parameters/recompute${oq}`, { method: 'POST' }).then(jsonOrThrow),
    onSuccess: (res: any) => {
      invalidate()
      const n = (res?.errors || []).length; const c = (res?.cycles || []).length
      setError(n || c ? t('Recomputed with {{n}} error(s), {{c}} cycle(s)', { n, c }) : null)
    },
    onError: onErr,
  })

  if (!elementId) return null

  const startEdit = (p: ParameterView) => {
    setEditing(p.name)
    setManual(p.manual_value === null || p.manual_value === undefined ? '' : String(p.manual_value))
    setFormula(p.formula || '')
  }
  const commitEdit = (p: ParameterView) => {
    const body: ParameterUpsert = {}
    const mv = manual.trim() === '' ? null : Number(manual)
    if (mv !== null && Number.isNaN(mv)) { setError(t('Manual value must be a number')); return }
    if (mv !== (p.manual_value ?? null)) body.manual_value = mv
    const f = formula.trim() || null
    if (f !== (p.formula || null)) { body.formula = f; body.formula_kind = p.formula_kind || 'ref' }
    if (Object.keys(body).length === 0) { setEditing(null); return }
    upsert.mutate({ name: p.name, body })
  }
  const setSwitch = (p: ParameterView, sw: ValueSwitch) => upsert.mutate({ name: p.name, body: { value_switch: sw } })
  const addParam = () => {
    const name = newName.trim()
    if (!name) return
    const v = newValue.trim() === '' ? null : Number(newValue)
    if (v !== null && Number.isNaN(v)) { setError(t('Value must be a number')); return }
    upsert.mutate({ name, body: { unit: newUnit.trim() || null, manual_value: v, value_switch: v === null ? 'computed' : 'manual' } })
    setAdding(false); setNewName(''); setNewUnit(''); setNewValue('')
  }


  return (
    <div className="t-12">
      <div className="flex ai-c gap-2 mb-1 wrap">
        <span className="c-2 t-12">
          {t('{{count}} parameters', { count: params.length, defaultValue_one: '{{count}} parameter' })} · {t('formulas use names on this element,')} <code>el("Name").x</code>, <code>children("mass_kg")</code>, <code>budget("power")</code>
        </span>
        {optionId && (
          <span title={t('Edits are written into this option only; the baseline is untouched')}
            style={{ fontSize: fs.label, color: 'var(--status-caution)', border: '1px solid color-mix(in srgb, var(--status-caution) 33%, transparent)', borderRadius: '3px', padding: '0 0.3rem' }}>
            {t('editing option: {{name}}', { name: optionName })}
          </span>
        )}
        <span className="grow" />
        <button className="c2o-btn c2o-btn--sm" onClick={() => setAdding(v => !v)}>{t('+ parameter')}</button>
        <button className="c2o-btn c2o-btn--sm" disabled={!studyId || recompute.isPending} onClick={() => recompute.mutate()}>
          {recompute.isPending ? t('Recomputing…') : t('Recompute')}
        </button>
      </div>
      {error && (
        <div className="c-alarm t-12 mb-1">
          {error} <button className="c2o-btn c2o-btn--sm" onClick={() => setError(null)}>{t('dismiss')}</button>
        </div>
      )}
      {adding && (
        <div className="flex gap-1 ai-c mb-1 wrap">
          <input value={newName} onChange={e => setNewName(e.target.value)} placeholder={t('name (e.g. peak_power_w)')} className="c2o-input c2o-input--sm" style={{ minWidth: 160 }}
            onKeyDown={e => e.key === 'Enter' && addParam()} />
          <input value={newUnit} onChange={e => setNewUnit(e.target.value)} placeholder={t('unit')} className="c2o-input c2o-input--sm" style={{ width: 60 }} />
          <input value={newValue} onChange={e => setNewValue(e.target.value)} placeholder={t('value (optional)')} className="c2o-input c2o-input--sm" style={{ width: 110 }}
            onKeyDown={e => e.key === 'Enter' && addParam()} />
          <button className="c2o-btn c2o-btn--sm" disabled={!newName.trim()} onClick={addParam}>{t('add')}</button>
          <button className="c2o-btn c2o-btn--sm" onClick={() => setAdding(false)}>{t('cancel')}</button>
        </div>
      )}
      {isLoading && <div className="c-2">{t('Loading…')}</div>}
      {!isLoading && params.length === 0 && (
        <div className="c-2 t-12">{t('No parameters on this element yet.')}</div>
      )}
      {params.length > 0 && (
        <table className={compact ? "c2o-table c2o-table--dense" : "c2o-table"}>
          <thead>
            <tr>
              <th>{t('Name')}</th><th>{t('Value')}</th><th>{t('Unit')}</th><th>{t('Switch')}</th>
              <th>{t('Formula')}</th><th>{t('Source')}</th><th></th>
            </tr>
          </thead>
          <tbody>
            {params.map(p => {
              const isEd = editing === p.name
              const hasErr = (p.errors || []).length > 0
              return (
                <tr key={p.id || p.name}>
                  <td className="w-600 nowrap" title={p.quantity_kind || undefined}>{p.name}</td>
                  <td className="nowrap">
                    {isEd ? (
                      <input value={manual} onChange={e => setManual(e.target.value)} placeholder={t('manual value')} className="c2o-input c2o-input--sm" style={{ width: 90 }}
                        onKeyDown={e => { if (e.key === 'Enter') commitEdit(p); if (e.key === 'Escape') setEditing(null) }} />
                    ) : (
                      <span onDoubleClick={() => startEdit(p)} title={t('manual {{manual}} · computed {{computed}} · reference {{reference}}', { manual: fmt(p.manual_value), computed: fmt(p.computed_value), reference: fmt(p.reference_value) })}
                        style={{ color: hasErr ? 'var(--status-alarm)' : 'var(--text-primary)', cursor: 'text', fontVariantNumeric: 'tabular-nums' }}>
                        {fmt(p.effective_value)}
                      </span>
                    )}
                  </td>
                  <td className="c-2">{p.unit || ''}</td>
                  <td>
                    <select value={p.value_switch} onChange={e => setSwitch(p, e.target.value as ValueSwitch)} className="c2o-select c2o-select--sm t-12 py-0 px-1">
                      {VALUE_SWITCHES.map(s => <option key={s} value={s}>{SWITCH_LABELS[s] ? t(SWITCH_LABELS[s]) : s}</option>)}
                    </select>
                  </td>
                  <td style={{ minWidth: 140 }}>
                    {isEd ? (
                      <input value={formula} onChange={e => setFormula(e.target.value)} placeholder={t('e.g. mass_kg * 1.2 or el("Bus").power_avg_w')} className="c2o-input c2o-input--sm mono w-full"
                        onKeyDown={e => { if (e.key === 'Enter') commitEdit(p); if (e.key === 'Escape') setEditing(null) }} />
                    ) : (
                      <span onDoubleClick={() => startEdit(p)} style={{ fontFamily: 'ui-monospace, monospace', fontSize: fs.label, color: p.formula ? 'var(--cat-2)' : 'var(--text-secondary)', cursor: 'text' }}>
                        {p.formula ? `= ${p.formula}` : '—'}
                        {p.formula && p.formula_kind && <span style={{ opacity: 0.6 }}> [{p.formula_kind}]</span>}
                      </span>
                    )}
                    {hasErr && <div className="c-alarm t-12 mt-1">{p.errors.join('; ')}</div>}
                  </td>
                  <td className="nowrap">
                    <ProvenanceChip p={p.provenance} />
                    {p.option_id && <OptionOverrideChip optionName={options.find(o => o.id === p.option_id)?.name ?? optionName} />}
                  </td>
                  <td className="nowrap">
                    {isEd ? (<>
                      <button className="c2o-btn c2o-btn--sm" onClick={() => commitEdit(p)}>{t('save')}</button>{' '}
                      <button className="c2o-btn c2o-btn--sm" onClick={() => setEditing(null)}>{t('cancel')}</button>
                    </>) : (<>
                      <button className="c2o-btn c2o-btn--sm" onClick={() => startEdit(p)}>{t('edit')}</button>{' '}
                      <button className="c2o-btn c2o-btn--sm"
                        title={p.option_id ? t('Remove the override from option "{{name}}" (the baseline value shows through)', { name: optionName }) : t('Delete (well-known parameters are reset to the column value)')}
                        disabled={!!optionId && !p.option_id}
                        onClick={() => remove.mutate(p.name)}>×</button>
                    </>)}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </div>
  )
}

/** Collapsible wrapper used in element detail areas. */
export function ParameterSection({ elementId, studyId, elementName, defaultOpen = false }: {
  elementId: string | null; studyId: string | null; elementName?: string; defaultOpen?: boolean
}) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(defaultOpen)
  if (!elementId) return null
  return (
    <div className="mt-2 bt pt-2">
      <button onClick={() => setOpen(v => !v)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: fs.label, color: 'var(--cat-2)', fontWeight: 600, padding: 0 }}>
        {open ? '▾' : '▸'} {elementName ? t('Parameters & equations: {{name}}', { name: elementName }) : t('Parameters & equations')}
      </button>
      {open && <div className="mt-1"><ParameterPanel elementId={elementId} studyId={studyId} compact /></div>}
    </div>
  )
}

export default ParameterPanel
