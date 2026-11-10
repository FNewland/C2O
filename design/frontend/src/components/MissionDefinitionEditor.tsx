/**
 * MissionDefinitionEditor (Nov 2026) — edit the mission after creation: problem, context,
 * stakeholders (needs, constraints), objectives (editable ids, default O1, O2 …), success
 * criteria, the ConOps summary, the alternatives (pros, cons, feasibility, decision) and the
 * mission definition (orbit, payloads, class, lifetime, launch / disposal, link). Saves with
 * PATCH /api/studies/{id}/mission; the server validates, and every analysis run made with the
 * old values is reported stale. W1.06: the ConOps summary closes MDR-EC-06; the MRD prints the
 * ConOps summary, the success criteria and the constraints.
 */
import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { MissionDefinitionFields } from '../workbench/MissionDefinitionFields'
import { fromRequirements, toPatch, validateDraft, type MissionDefDraft } from '../workbench/missionDef'
import { serverText } from '../i18n/serverText'

const API = '/api'

/** ``orig`` is the id the row was loaded with, so a renamed objective keeps its other fields. */
interface ObjectiveRow { id: string; text: string; priority: string; measurable_criterion: string; orig?: string }
interface StakeholderRow { id: string; name: string; role: string; needs: string; constraints: string }
interface AlternativeRow { id: string; name: string; pros: string; cons: string; feasibility_score: number; decision: string }

const PRIORITIES = ['primary', 'secondary', 'constraint'] as const
const ROLES = ['sponsor', 'user', 'operator', 'science_pi', 'regulator', 'partner', 'public', 'launch_provider'] as const
// English text is the i18n key
const ROLE_LABEL: Record<string, string> = {
  sponsor: 'Sponsor / Funder', user: 'End User', operator: 'Operator', science_pi: 'Science PI', regulator: 'Regulator',
  partner: 'Partner Organisation', public: 'Public', launch_provider: 'Launch provider',
}
const DECISIONS = ['under_review', 'selected', 'rejected', 'deferred'] as const
// English text is the i18n key
const DECISION_LABEL: Record<string, string> = { under_review: 'Under review', selected: 'Selected', rejected: 'Rejected', deferred: 'Deferred' }

const lines = (v: string): string[] => v.split('\n').map(x => x.trim()).filter(Boolean)

export function MissionDefinitionEditor({ studyId, study, onDone }: { studyId: string; study: any; onDone: () => void }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const need = study?.mission_need || {}
  const [problem, setProblem] = useState<string>(need.problem_statement || '')
  const [context, setContext] = useState<string>(need.operational_context || '')
  const [objectives, setObjectives] = useState<ObjectiveRow[]>(
    (need.objectives || []).map((o: any) => ({ id: o.id || '', orig: o.id || '', text: o.text || '', priority: o.priority || 'primary', measurable_criterion: o.measurable_criterion || '' })))
  const [conops, setConops] = useState<string>(need.conops_summary || '')
  const [success, setSuccess] = useState<string[]>(need.success_criteria?.length ? need.success_criteria : [''])
  const [stakeholders, setStakeholders] = useState<StakeholderRow[]>(
    (need.stakeholders || []).map((sh: any) => ({ id: sh.id || '', name: sh.name || '', role: sh.role || 'user',
      needs: (sh.needs || []).join('\n'), constraints: (sh.constraints || []).join('\n') })))
  const [alternatives, setAlternatives] = useState<AlternativeRow[]>(
    (need.alternatives_considered || []).map((a: any) => ({ id: a.id || '', name: a.name || '', pros: (a.pros || []).join('\n'),
      cons: (a.cons || []).join('\n'), feasibility_score: Number(a.feasibility_score) || 0, decision: a.decision || 'under_review' })))
  const [def, setDef] = useState<MissionDefDraft>(() => fromRequirements(study?.requirements))
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<{ warnings: string[]; stale: string[]; changed: number } | null>(null)
  const errs = validateDraft(def)

  const setObj = (i: number, patch: Partial<ObjectiveRow>) => setObjectives(os => os.map((o, j) => (j === i ? { ...o, ...patch } : o)))
  const setSh = (i: number, patch: Partial<StakeholderRow>) => setStakeholders(xs => xs.map((x, j) => (j === i ? { ...x, ...patch } : x)))
  const setAlt = (i: number, patch: Partial<AlternativeRow>) => setAlternatives(xs => xs.map((x, j) => (j === i ? { ...x, ...patch } : x)))
  /** The next free objective id (O1, O2 …) — ids stay editable (W1.05). */
  /** Same rule as the wizard: O1, O2 … (C1, C2 … for constraints), the first free number. */
  const nextObjectiveId = (priority = 'primary') => {
    const prefix = priority === 'constraint' ? 'C' : 'O'
    const used = new Set(objectives.map(o => o.id))
    let n = 1
    while (used.has(`${prefix}${n}`)) n++
    return `${prefix}${n}`
  }
  const objIds = objectives.filter(o => o.text.trim()).map((o, i) => o.id.trim() || `O${i + 1}`)
  const dupObjIds = [...new Set(objIds.filter((x, i) => objIds.indexOf(x) !== i))]

  const save = async () => {
    setSaving(true); setError(null); setResult(null)
    try {
      // Keep the objectives' other fields (type, stakeholder links, status) as they were
      const old: any[] = need.objectives || []
      const oldSh: any[] = need.stakeholders || []
      const oldAlt: any[] = need.alternatives_considered || []
      const altRows = alternatives.filter(x => x.name.trim()).map((x, i) => ({ ...x, id: x.id || `ALT-${String(i + 1).padStart(2, '0')}` }))
      const selectedAlt = altRows.find(x => x.decision === 'selected')
      const body = {
        ...toPatch(def),
        mission_need: {
          problem_statement: problem,
          operational_context: context,
          objectives: objectives.filter(o => o.text.trim()).map((o, i) => {
            const prev = old.find(x => x.id && x.id === (o.orig || o.id)) || {}
            return { ...prev, id: o.id.trim() || `O${i + 1}`, text: o.text.trim(), priority: o.priority, measurable_criterion: o.measurable_criterion }
          }),
          conops_summary: conops.trim(),
          success_criteria: success.map(x => x.trim()).filter(Boolean),
          stakeholders: stakeholders.filter(x => x.name.trim()).map((x, i) => {
            const prev = oldSh.find(y => y.id && y.id === x.id) || {}
            return { ...prev, id: x.id || `SH-${String(i + 1).padStart(2, '0')}`, name: x.name.trim(), role: x.role,
              needs: lines(x.needs), constraints: lines(x.constraints) }
          }),
          alternatives_considered: altRows.map(x => {
            const prev = oldAlt.find(y => y.id && y.id === x.id) || {}
            return { ...prev, id: x.id, name: x.name.trim(), pros: lines(x.pros),
              cons: lines(x.cons), feasibility_score: Math.max(0, Math.min(1, x.feasibility_score || 0)), decision: x.decision }
          }),
          ...(selectedAlt ? { selected_alternative_id: selectedAlt.id } : {}),
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
      <fieldset className="c2o-wfield" data-testid="stakeholders-editor">
        <legend className="c2o-wfield__label">{t('Stakeholders')}</legend>
        {stakeholders.map((x, i) => (
          <div key={i} className="flex wrap gap-1 ai-s mb-1">
            <input className="c2o-input" style={{ flex: 2, minWidth: '10rem' }} aria-label={t('Stakeholder {{n}}', { n: i + 1 })} value={x.name} onChange={e => setSh(i, { name: e.target.value })} />
            <select className="c2o-select" aria-label={t('Stakeholder {{n}}: role', { n: i + 1 })} value={x.role} onChange={e => setSh(i, { role: e.target.value })}>
              {ROLES.map(r => <option key={r} value={r}>{t(ROLE_LABEL[r])}</option>)}
            </select>
            <textarea className="c2o-input" rows={2} style={{ flex: 2, minWidth: '10rem' }} aria-label={t('Stakeholder {{n}}: needs (one per line)', { n: i + 1 })}
              placeholder={t('needs, one per line')} value={x.needs} onChange={e => setSh(i, { needs: e.target.value })} />
            <textarea className="c2o-input" rows={2} style={{ flex: 2, minWidth: '10rem' }} aria-label={t('Stakeholder {{n}}: constraints (one per line)', { n: i + 1 })}
              placeholder={t('constraints, one per line')} value={x.constraints} onChange={e => setSh(i, { constraints: e.target.value })} />
            <button type="button" className="c2o-btn c2o-btn--sm c2o-btn--danger" aria-label={t('Remove stakeholder {{n}}', { n: i + 1 })}
              onClick={() => setStakeholders(xs => xs.filter((_, j) => j !== i))}>×</button>
          </div>
        ))}
        <button type="button" className="c2o-btn c2o-btn--sm" onClick={() => setStakeholders(xs => [...xs, { id: '', name: '', role: 'user', needs: '', constraints: '' }])}>
          {t('+ Add stakeholder')}
        </button>
      </fieldset>
      <fieldset className="c2o-wfield">
        <legend className="c2o-wfield__label">{t('Objectives')}</legend>
        {objectives.map((o, i) => (
          <div key={i} className="flex wrap gap-1 ai-c mb-1">
            <input className="c2o-input mono" style={{ width: '5rem' }} aria-label={t('Objective {{n}}: id', { n: i + 1 })} value={o.id}
              placeholder={`O${i + 1}`} onChange={e => setObj(i, { id: e.target.value.replace(/\s+/g, '').slice(0, 12) })}
              title={t('Short identifier, used in the requirement code OBJ-{{id}}', { id: o.id })} />
            <select className="c2o-select" aria-label={t('Objective {{n}}: priority', { n: i + 1 })} value={o.priority} onChange={e => setObj(i, { priority: e.target.value })}>
              {PRIORITIES.map(p => <option key={p} value={p}>{p === 'primary' ? t('Primary') : p === 'secondary' ? t('Secondary', { context: 'priority' }) : t('Constraint', { context: 'priority' })}</option>)}
            </select>
            <input className="c2o-input" style={{ flex: 2, minWidth: '12rem' }} aria-label={t('Objective {{n}}', { n: i + 1 })} value={o.text} onChange={e => setObj(i, { text: e.target.value })} />
            <input className="c2o-input" style={{ flex: 1, minWidth: '8rem' }} aria-label={t('Objective {{n}}: how to measure', { n: i + 1 })} placeholder={t('how to measure')} value={o.measurable_criterion} onChange={e => setObj(i, { measurable_criterion: e.target.value })} />
            <button type="button" className="c2o-btn c2o-btn--sm c2o-btn--danger" aria-label={t('Remove objective {{n}}', { n: i + 1 })}
              onClick={() => setObjectives(os => os.filter((_, j) => j !== i))}>×</button>
          </div>
        ))}
        <button type="button" className="c2o-btn c2o-btn--sm" onClick={() => setObjectives(os => [...os, { id: nextObjectiveId('primary'), text: '', priority: 'primary', measurable_criterion: '' }])}>
          {t('+ Add objective')}
        </button>
        {dupObjIds.length > 0 && <div className="c-alarm t-12" role="alert">{t('Two objectives share the id {{ids}}: give each a unique id', { ids: dupObjIds.join(', ') })}</div>}
      </fieldset>
      <fieldset className="c2o-wfield" data-testid="success-criteria-editor">
        <legend className="c2o-wfield__label">{t('Success criteria')}</legend>
        <p className="t-12 c-3 m-0 mb-1">{t('How do we know the mission succeeded? One measurable statement per line.')}</p>
        {success.map((c, i) => (
          <div key={i} className="flex gap-1 ai-c mb-1">
            <input className="c2o-input" style={{ flex: 1 }} aria-label={t('Success criterion {{n}}', { n: i + 1 })} value={c}
              onChange={e => setSuccess(xs => xs.map((x, j) => (j === i ? e.target.value : x)))} />
            <button type="button" className="c2o-btn c2o-btn--sm c2o-btn--danger" aria-label={t('Remove success criterion {{n}}', { n: i + 1 })}
              onClick={() => setSuccess(xs => xs.filter((_, j) => j !== i))}>×</button>
          </div>
        ))}
        <button type="button" className="c2o-btn c2o-btn--sm" onClick={() => setSuccess(xs => [...xs, ''])}>{t('+ Add success criterion')}</button>
      </fieldset>
      <label className="c2o-wfield">
        <span className="c2o-wfield__label">{t('ConOps summary')}</span>
        <textarea className="c2o-input" rows={4} value={conops} data-testid="conops-summary" onChange={e => setConops(e.target.value)}
          placeholder={t('How the system is operated: phases, modes, ground segment, data flow, end of life')} />
      </label>
      <fieldset className="c2o-wfield" data-testid="alternatives-editor">
        <legend className="c2o-wfield__label">{t('Alternatives considered')}</legend>
        {alternatives.map((x, i) => (
          <div key={i} className="flex wrap gap-1 ai-s mb-1">
            <input className="c2o-input" style={{ flex: 2, minWidth: '10rem' }} aria-label={t('Alternative {{n}}', { n: i + 1 })} value={x.name} onChange={e => setAlt(i, { name: e.target.value })} />
            <textarea className="c2o-input" rows={2} style={{ flex: 2, minWidth: '8rem' }} aria-label={t('Alternative {{n}}: pros (one per line)', { n: i + 1 })}
              placeholder={t('pros, one per line')} value={x.pros} onChange={e => setAlt(i, { pros: e.target.value })} />
            <textarea className="c2o-input" rows={2} style={{ flex: 2, minWidth: '8rem' }} aria-label={t('Alternative {{n}}: cons (one per line)', { n: i + 1 })}
              placeholder={t('cons, one per line')} value={x.cons} onChange={e => setAlt(i, { cons: e.target.value })} />
            <input className="c2o-input" type="number" min={0} max={1} step={0.1} style={{ width: '5rem' }} aria-label={t('Alternative {{n}}: feasibility (0 to 1)', { n: i + 1 })}
              value={x.feasibility_score} onChange={e => setAlt(i, { feasibility_score: Number(e.target.value) })} />
            <select className="c2o-select" aria-label={t('Alternative {{n}}: decision', { n: i + 1 })} value={x.decision} onChange={e => setAlt(i, { decision: e.target.value })}>
              {DECISIONS.map(d => <option key={d} value={d}>{t(DECISION_LABEL[d])}</option>)}
            </select>
            <button type="button" className="c2o-btn c2o-btn--sm c2o-btn--danger" aria-label={t('Remove alternative {{n}}', { n: i + 1 })}
              onClick={() => setAlternatives(xs => xs.filter((_, j) => j !== i))}>×</button>
          </div>
        ))}
        <button type="button" className="c2o-btn c2o-btn--sm" onClick={() => setAlternatives(xs => [...xs, { id: '', name: '', pros: '', cons: '', feasibility_score: 0, decision: 'under_review' }])}>
          {t('+ Add alternative')}
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
        <button type="button" className="c2o-btn c2o-btn--primary c2o-btn--sm" disabled={saving || errs.length > 0 || dupObjIds.length > 0} onClick={save}>
          {saving ? t('Saving…') : t('Save mission definition')}
        </button>
        <button type="button" className="c2o-btn c2o-btn--sm" onClick={onDone}>{t('Close')}</button>
      </div>
    </div>
  )
}
