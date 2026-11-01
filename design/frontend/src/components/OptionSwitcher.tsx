/**
 * OptionSwitcher — pick the active design option (SCDF-172).
 *
 * Small enough for the workbench status bar: a dropdown over
 * GET /api/studies/{id}/options (baseline first), "branch" (POST
 * /api/options/{id}/branch — copies the current option's overrides into a new
 * option and activates it), "rename" (PATCH /api/options/{id}) and "delete"
 * (DELETE /api/options/{id}; not for the baseline). Selecting the baseline
 * stores `null` in `optionStore` so requests carry no `option_id`.
 *
 * Not mounted here — SCDF-178 places it in `PresenceBar` (workbench/PresenceBar.tsx)
 * between the user list and the AI status indicator, or next to `StudyStepper`.
 */
import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useUIStore } from '../stores/uiStore'
import { useOptionStore } from '../stores/optionStore'
import type { DesignOption } from '../types/options'
import { fs } from '../theme/tokens'
import { askConfirm, askText } from './ui/Dialog'

const API = '/api'

async function jsonOrThrow(res: Response) {
  if (!res.ok) {
    let msg = `${res.status}`
    try { const b = await res.json(); msg = typeof b.detail === 'string' ? b.detail : JSON.stringify(b.detail ?? b) } catch { /* noop */ }
    throw new Error(msg)
  }
  return res.json()
}

const btn = (color = 'var(--text-secondary)'): React.CSSProperties => ({
  background: 'none', border: '1px solid var(--border)', borderRadius: '3px', cursor: 'pointer',
  fontSize: fs.label, padding: '0 0.3rem', color, lineHeight: '1.1rem',
})

export function useOptions(studyId: string | null) {
  return useQuery<DesignOption[]>({
    queryKey: ['options', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/options`).then(jsonOrThrow),
    enabled: !!studyId,
  })
}

export function OptionSwitcher({ studyId: studyIdProp }: { studyId?: string | null }) {
  const { t } = useTranslation()
  const wbStudy = useUIStore(s => s.studyId)
  const studyId = studyIdProp ?? wbStudy
  const qc = useQueryClient()
  const activeId = useOptionStore(s => (studyId ? s.activeByStudy[studyId] ?? null : null))
  const setActive = useOptionStore(s => s.setActiveOption)
  const [error, setError] = useState<string | null>(null)
  const { data: options = [] } = useOptions(studyId)

  const baseline = options.find(o => o.is_baseline)
  const active = options.find(o => o.id === activeId) ?? baseline
  // A stale persisted id (deleted option) falls back to the baseline.
  useEffect(() => {
    if (studyId && activeId && options.length > 0 && !options.some(o => o.id === activeId)) setActive(studyId, null)
  }, [studyId, activeId, options, setActive])

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['options', studyId] })
    qc.invalidateQueries({ queryKey: ['element-parameters'] })
    qc.invalidateQueries({ queryKey: ['study-parameters', studyId] })
    qc.invalidateQueries({ queryKey: ['analyses'] })
    qc.invalidateQueries({ queryKey: ['conflicts'] })
  }
  const onErr = (e: Error) => setError(e.message)

  const branch = useMutation({
    mutationFn: (name: string) =>
      fetch(`${API}/options/${active?.id}/branch`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }),
      }).then(jsonOrThrow),
    onSuccess: (opt: DesignOption) => { invalidate(); if (studyId) setActive(studyId, opt.id); setError(null) },
    onError: onErr,
  })
  const rename = useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) =>
      fetch(`${API}/options/${id}`, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }),
      }).then(jsonOrThrow),
    onSuccess: () => { invalidate(); setError(null) }, onError: onErr,
  })
  const remove = useMutation({
    mutationFn: (id: string) => fetch(`${API}/options/${id}`, { method: 'DELETE' }).then(jsonOrThrow),
    onSuccess: () => { invalidate(); if (studyId) setActive(studyId, null); setError(null) }, onError: onErr,
  })

  if (!studyId) return null

  const onSelect = (id: string) => {
    const opt = options.find(o => o.id === id)
    setActive(studyId, !opt || opt.is_baseline ? null : opt.id)
    invalidate()
  }
  const onBranch = async () => {
    const from = active?.name ?? t('Baseline')
    const name = (await askText(t('Branch "{{name}}" as:', { name: from }), t('{{name}} (copy)', { name: from })))
    if (name && name.trim()) branch.mutate(name.trim())
  }
  const onRename = async () => {
    if (!active || active.is_baseline) return
    const name = (await askText(t('Rename option:'), active.name))
    if (name && name.trim() && name.trim() !== active.name) rename.mutate({ id: active.id, name: name.trim() })
  }
  const onDelete = async () => {
    if (!active || active.is_baseline) return
    if (await askConfirm(t('Delete option "{{name}}" and its overrides?', { name: active.name }), { danger: true, confirmLabel: t('Delete') })) remove.mutate(active.id)
  }

  const isBaseline = !active || active.is_baseline
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', fontSize: fs.label }} title={t('Design option (SCDF-172): parameter overrides and analysis runs are scoped to the active option')}>
      <label htmlFor="scdf-option-select" style={{ color: 'var(--text-secondary)' }}>{t('Option')}</label>
      <select id="scdf-option-select" value={active?.id ?? ''} onChange={e => onSelect(e.target.value)}
        style={{ fontSize: fs.label, padding: '0 0.2rem', background: 'var(--bg-primary)', color: isBaseline ? 'var(--text-primary)' : 'var(--status-caution)', border: '1px solid var(--border)', borderRadius: '3px', fontWeight: isBaseline ? 400 : 600 }}>
        {options.map(o => <option key={o.id} value={o.id}>{o.is_baseline ? t('Baseline') : o.name}</option>)}
      </select>
      <button style={btn('var(--interactive)')} onClick={onBranch} disabled={branch.isPending} title={t("Copy the active option's overrides into a new option")}>{t('branch')}</button>
      {!isBaseline && <button style={btn()} onClick={onRename} title={t('Rename')}>{t('rename')}</button>}
      {!isBaseline && <button style={btn('var(--status-alarm)')} onClick={onDelete} title={t('Delete this option and its overrides')}>×</button>}
      {error && <span style={{ color: 'var(--status-alarm)' }} title={error}>{t('error')} <button style={btn('var(--status-alarm)')} onClick={() => setError(null)}>{t('ok')}</button></span>}
    </span>
  )
}

export default OptionSwitcher
