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
import {
  VALUE_SWITCHES, type ParameterUpsert, type ParameterView, type Provenance, type ValueSwitch,
} from '../types/arcadia'
import { optionQuery, useActiveOptionId } from '../stores/optionStore'
import { useOptions } from './OptionSwitcher'

const API = '/api'

const inputStyle: React.CSSProperties = {
  padding: '0.12rem 0.3rem', fontSize: '0.64rem', borderRadius: '3px',
  background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)',
}
const monoInput: React.CSSProperties = { ...inputStyle, fontFamily: 'ui-monospace, monospace' }
const smallBtn = (color = 'var(--text-secondary)'): React.CSSProperties => ({
  background: 'none', border: '1px solid var(--border)', borderRadius: '3px', cursor: 'pointer',
  fontSize: '0.6rem', padding: '0.08rem 0.3rem', color,
})
const PROV_COLORS: Record<Provenance, string> = { manual: '#f59e0b', formula: '#8b5cf6', column: '#3b82f6', agent: '#10b981' }
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
  const c = PROV_COLORS[p] || '#6b7280'
  return <span title={PROV_TITLES[p] || p} style={{ fontSize: '0.56rem', padding: '0 0.3rem', borderRadius: '3px', background: `${c}22`, color: c, border: `1px solid ${c}55` }}>{p}</span>
}

export function OptionOverrideChip({ optionName }: { optionName: string }) {
  const c = '#f59e0b'
  return <span title={`This value is an override that exists only in option "${optionName}"; the baseline row is shadowed`}
    style={{ fontSize: '0.56rem', padding: '0 0.3rem', borderRadius: '3px', background: `${c}22`, color: c, border: `1px solid ${c}55`, marginLeft: '0.2rem', whiteSpace: 'nowrap' }}>
    override in {optionName}
  </span>
}

export function ParameterPanel({ elementId, studyId, compact }: { elementId: string | null; studyId: string | null; compact?: boolean }) {
  const qc = useQueryClient()
  const optionId = useActiveOptionId(studyId)
  const oq = optionQuery(optionId)
  const { data: options = [] } = useOptions(studyId)
  const activeOption = options.find(o => o.id === optionId)
  const optionName = activeOption?.name ?? 'option'
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
      setError(n || c ? `Recomputed with ${n} error(s), ${c} cycle(s)` : null)
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
    if (mv !== null && Number.isNaN(mv)) { setError('Manual value must be a number'); return }
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
    if (v !== null && Number.isNaN(v)) { setError('Value must be a number'); return }
    upsert.mutate({ name, body: { unit: newUnit.trim() || null, manual_value: v, value_switch: v === null ? 'computed' : 'manual' } })
    setAdding(false); setNewName(''); setNewUnit(''); setNewValue('')
  }

  const th: React.CSSProperties = { textAlign: 'left', padding: '0.15rem 0.3rem', fontSize: '0.58rem', color: 'var(--text-secondary)', borderBottom: '1px solid var(--border)', whiteSpace: 'nowrap' }
  const td: React.CSSProperties = { padding: '0.15rem 0.3rem', fontSize: compact ? '0.62rem' : '0.66rem', borderBottom: '1px solid var(--border)', verticalAlign: 'top' }

  return (
    <div style={{ fontSize: '0.7rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.3rem', flexWrap: 'wrap' }}>
        <span style={{ color: 'var(--text-secondary)', fontSize: '0.62rem' }}>
          {params.length} parameter{params.length === 1 ? '' : 's'} · formulas use names on this element, <code>el("Name").x</code>, <code>children("mass_kg")</code>, <code>budget("power")</code>
        </span>
        {optionId && (
          <span title="Edits are written into this option only; the baseline is untouched"
            style={{ fontSize: '0.58rem', color: '#f59e0b', border: '1px solid #f59e0b55', borderRadius: '3px', padding: '0 0.3rem' }}>
            editing option: {optionName}
          </span>
        )}
        <span style={{ flex: 1 }} />
        <button style={smallBtn('#3b82f6')} onClick={() => setAdding(v => !v)}>+ parameter</button>
        <button style={smallBtn('#8b5cf6')} disabled={!studyId || recompute.isPending} onClick={() => recompute.mutate()}>
          {recompute.isPending ? 'Recomputing…' : 'Recompute'}
        </button>
      </div>
      {error && (
        <div style={{ color: '#ef4444', fontSize: '0.64rem', marginBottom: '0.3rem' }}>
          {error} <button style={smallBtn('#ef4444')} onClick={() => setError(null)}>dismiss</button>
        </div>
      )}
      {adding && (
        <div style={{ display: 'flex', gap: '0.3rem', alignItems: 'center', marginBottom: '0.3rem', flexWrap: 'wrap' }}>
          <input value={newName} onChange={e => setNewName(e.target.value)} placeholder="name (e.g. peak_power_w)" style={{ ...inputStyle, minWidth: 160 }}
            onKeyDown={e => e.key === 'Enter' && addParam()} />
          <input value={newUnit} onChange={e => setNewUnit(e.target.value)} placeholder="unit" style={{ ...inputStyle, width: 60 }} />
          <input value={newValue} onChange={e => setNewValue(e.target.value)} placeholder="value (optional)" style={{ ...inputStyle, width: 110 }}
            onKeyDown={e => e.key === 'Enter' && addParam()} />
          <button style={smallBtn('#10b981')} disabled={!newName.trim()} onClick={addParam}>add</button>
          <button style={smallBtn()} onClick={() => setAdding(false)}>cancel</button>
        </div>
      )}
      {isLoading && <div style={{ color: 'var(--text-secondary)' }}>Loading…</div>}
      {!isLoading && params.length === 0 && (
        <div style={{ color: 'var(--text-secondary)', fontSize: '0.64rem' }}>No parameters on this element yet.</div>
      )}
      {params.length > 0 && (
        <table style={{ borderCollapse: 'collapse', width: '100%' }}>
          <thead>
            <tr>
              <th style={th}>Name</th><th style={th}>Value</th><th style={th}>Unit</th><th style={th}>Switch</th>
              <th style={th}>Formula</th><th style={th}>Source</th><th style={th}></th>
            </tr>
          </thead>
          <tbody>
            {params.map(p => {
              const isEd = editing === p.name
              const hasErr = (p.errors || []).length > 0
              return (
                <tr key={p.id || p.name}>
                  <td style={{ ...td, fontWeight: 600, whiteSpace: 'nowrap' }} title={p.quantity_kind || undefined}>{p.name}</td>
                  <td style={{ ...td, whiteSpace: 'nowrap' }}>
                    {isEd ? (
                      <input value={manual} onChange={e => setManual(e.target.value)} placeholder="manual value" style={{ ...inputStyle, width: 90 }}
                        onKeyDown={e => { if (e.key === 'Enter') commitEdit(p); if (e.key === 'Escape') setEditing(null) }} />
                    ) : (
                      <span onDoubleClick={() => startEdit(p)} title={`manual ${fmt(p.manual_value)} · computed ${fmt(p.computed_value)} · reference ${fmt(p.reference_value)}`}
                        style={{ color: hasErr ? '#ef4444' : 'var(--text-primary)', cursor: 'text', fontVariantNumeric: 'tabular-nums' }}>
                        {fmt(p.effective_value)}
                      </span>
                    )}
                  </td>
                  <td style={{ ...td, color: 'var(--text-secondary)' }}>{p.unit || ''}</td>
                  <td style={td}>
                    <select value={p.value_switch} onChange={e => setSwitch(p, e.target.value as ValueSwitch)} style={{ ...inputStyle, fontSize: '0.58rem', padding: '0 0.15rem' }}>
                      {VALUE_SWITCHES.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </td>
                  <td style={{ ...td, minWidth: 140 }}>
                    {isEd ? (
                      <input value={formula} onChange={e => setFormula(e.target.value)} placeholder='e.g. mass_kg * 1.2 or el("Bus").power_avg_w' style={{ ...monoInput, width: '100%' }}
                        onKeyDown={e => { if (e.key === 'Enter') commitEdit(p); if (e.key === 'Escape') setEditing(null) }} />
                    ) : (
                      <span onDoubleClick={() => startEdit(p)} style={{ fontFamily: 'ui-monospace, monospace', fontSize: '0.6rem', color: p.formula ? '#c4b5fd' : 'var(--text-secondary)', cursor: 'text' }}>
                        {p.formula ? `= ${p.formula}` : '—'}
                        {p.formula && p.formula_kind && <span style={{ opacity: 0.6 }}> [{p.formula_kind}]</span>}
                      </span>
                    )}
                    {hasErr && <div style={{ color: '#ef4444', fontSize: '0.58rem', marginTop: '0.1rem' }}>{p.errors.join('; ')}</div>}
                  </td>
                  <td style={{ ...td, whiteSpace: 'nowrap' }}>
                    <ProvenanceChip p={p.provenance} />
                    {p.option_id && <OptionOverrideChip optionName={options.find(o => o.id === p.option_id)?.name ?? optionName} />}
                  </td>
                  <td style={{ ...td, whiteSpace: 'nowrap' }}>
                    {isEd ? (<>
                      <button style={smallBtn('#10b981')} onClick={() => commitEdit(p)}>save</button>{' '}
                      <button style={smallBtn()} onClick={() => setEditing(null)}>cancel</button>
                    </>) : (<>
                      <button style={smallBtn()} onClick={() => startEdit(p)}>edit</button>{' '}
                      <button style={smallBtn('#ef4444')}
                        title={p.option_id ? `Remove the override from option "${optionName}" (the baseline value shows through)` : 'Delete (well-known parameters are reset to the column value)'}
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
  const [open, setOpen] = useState(defaultOpen)
  if (!elementId) return null
  return (
    <div style={{ marginTop: '0.5rem', borderTop: '1px solid var(--border)', paddingTop: '0.4rem' }}>
      <button onClick={() => setOpen(v => !v)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.68rem', color: '#8b5cf6', fontWeight: 600, padding: 0 }}>
        {open ? '▾' : '▸'} Parameters & equations{elementName ? `: ${elementName}` : ''}
      </button>
      {open && <div style={{ marginTop: '0.3rem' }}><ParameterPanel elementId={elementId} studyId={studyId} compact /></div>}
    </div>
  )
}

export default ParameterPanel
