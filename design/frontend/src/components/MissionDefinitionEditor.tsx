/**
 * MissionDefinitionEditor (Nov 2026) — edit the mission after creation: problem, context,
 * objectives and the mission definition (orbit, payloads, class, lifetime, launch /
 * disposal, link). Saves with PATCH /api/studies/{id}/mission; the server validates,
 * and every analysis run made with the old values is reported stale.
 */
import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { MissionDefinitionFields } from '../workbench/MissionDefinitionFields'
import { fromRequirements, toPatch, validateDraft, type MissionDefDraft } from '../workbench/missionDef'
import { serverText } from '../i18n/serverText'

const API = '/api'

interface ObjectiveRow { id: string; text: string; priority: string; measurable_criterion: string }

const PRIORITIES = ['primary', 'secondary', 'constraint'] as const

export function MissionDefinitionEditor({ studyId, study, onDone }: { studyId: string; study: any; onDone: () => void }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const need = study?.mission_need || {}
  const [problem, setProblem] = useState<string>(need.problem_statement || '')
  const [context, setContext] = useState<string>(need.operational_context || '')
  const [objectives, setObjectives] = useState<ObjectiveRow[]>(
    (need.objectives || []).map((o: any) => ({ id: o.id || '', text: o.text || '', priority: o.priority || 'primary', measurable_criterion: o.measurable_criterion || '' })))
  const [def, setDef] = useState<MissionDefDraft>(() => fromRequirements(study?.requirements))
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<{ warnings: string[]; stale: string[]; changed: number } | null>(null)
  const errs = validateDraft(def)

  const setObj = (i: number, patch: Partial<ObjectiveRow>) => setObjectives(os => os.map((o, j) => (j === i ? { ...o, ...patch } : o)))

  const save = async () => {
    setSaving(true); setError(null); setResult(null)
    try {
      // Keep the objectives' other fields (type, stakeholder links, status) as they were
      const old: any[] = need.objectives || []
      const body = {
        ...toPatch(def),
        mission_need: {
          problem_statement: problem,
          operational_context: context,
          objectives: objectives.filter(o => o.text.trim()).map((o, i) => {
            const prev = old.find(x => x.id && x.id === o.id) || {}
            return { ...prev, id: o.id || `obj-${Date.now().toString(36)}-${i}`, text: o.text.trim(), priority: o.priority, measurable_criterion: o.measurable_criterion }
          }),
        },
      }
      const res = await fetch(`${API}/studies/${encodeURIComponent(studyId)}/mission`, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        const d = data?.detail
        setError(typeof d === 'string' ? serverText(d) : Array.isArray(d) ? d.map((x: any) => `${(x.loc || []).join('.')}: ${x.msg}`).join('; ') : t('Could not save the mission definition'))
        return
      }
      setResult({ warnings: data.warnings || [], stale: data.stale_analyses || [], changed: (data.changed || []).length })
      for (const k of ['study', 'analyses', 'analysis', 'conflicts', 'ground-stations', 'readiness']) qc.invalidateQueries({ queryKey: [k] })
    } finally { setSaving(false) }
  }

  return (
    <div className="stack gap-2" data-testid="mission-definition-editor">
      <label className="c2o-wfield">
        <span className="c2o-wfield__label">{t('Problem Statement')}</span>
        <textarea className="c2o-input" rows={3} value={problem} onChange={e => setProblem(e.target.value)} />
      </label>
      <label className="c2o-wfield">
        <span className="c2o-wfield__label">{t('Operational Context')}</span>
        <textarea className="c2o-input" rows={2} value={context} onChange={e => setContext(e.target.value)} />
      </label>
      <fieldset className="c2o-wfield">
        <legend className="c2o-wfield__label">{t('Objectives')}</legend>
        {objectives.map((o, i) => (
          <div key={i} className="flex wrap gap-1 ai-c mb-1">
            <select className="c2o-select" aria-label={t('Objective {{n}}: priority', { n: i + 1 })} value={o.priority} onChange={e => setObj(i, { priority: e.target.value })}>
              {PRIORITIES.map(p => <option key={p} value={p}>{p === 'primary' ? t('Primary') : p === 'secondary' ? t('Secondary', { context: 'priority' }) : t('Constraint', { context: 'priority' })}</option>)}
            </select>
            <input className="c2o-input" style={{ flex: 2, minWidth: '12rem' }} aria-label={t('Objective {{n}}', { n: i + 1 })} value={o.text} onChange={e => setObj(i, { text: e.target.value })} />
            <input className="c2o-input" style={{ flex: 1, minWidth: '8rem' }} aria-label={t('Objective {{n}}: how to measure', { n: i + 1 })} placeholder={t('how to measure')} value={o.measurable_criterion} onChange={e => setObj(i, { measurable_criterion: e.target.value })} />
            <button type="button" className="c2o-btn c2o-btn--sm c2o-btn--danger" aria-label={t('Remove objective {{n}}', { n: i + 1 })}
              onClick={() => setObjectives(os => os.filter((_, j) => j !== i))}>×</button>
          </div>
        ))}
        <button type="button" className="c2o-btn c2o-btn--sm" onClick={() => setObjectives(os => [...os, { id: '', text: '', priority: 'primary', measurable_criterion: '' }])}>
          {t('+ Add objective')}
        </button>
      </fieldset>

      <MissionDefinitionFields value={def} onChange={setDef} />

      {errs.length > 0 && <ul className="m-0 pl-4 c-alarm t-12" role="alert">{errs.map(e => <li key={e}>{t(e)}</li>)}</ul>}
      {error && <div className="c-alarm t-12" role="alert">{error}</div>}
      {result && (
        <div className="t-12" role="status" data-testid="mission-saved">
          <div className="c-ok">{result.changed ? t('Mission definition saved.') : t('Nothing changed.')}</div>
          {result.stale.length > 0 && <div className="c-caution">{t('Re-run these analyses, they used the old values: {{list}}', { list: result.stale.join(', ') })}</div>}
          {result.warnings.map(w => <div key={w} className="c-caution">{serverText(w)}</div>)}
        </div>
      )}
      <div className="flex gap-1">
        <button type="button" className="c2o-btn c2o-btn--primary c2o-btn--sm" disabled={saving || errs.length > 0} onClick={save}>
          {saving ? t('Saving…') : t('Save mission definition')}
        </button>
        <button type="button" className="c2o-btn c2o-btn--sm" onClick={onDone}>{t('Close')}</button>
      </div>
    </div>
  )
}
