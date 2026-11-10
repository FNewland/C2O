/**
 * RequirementsPanel — CRUD requirements scoped to current level.
 *
 * Requirements can be:
 * - Assigned to the parent element (mission-level) OR any child element (segment-level)
 * - Typed: functional, performance, interface, regulatory, process
 * - Verified: T (test, incl. demonstration), A (analysis), R (review), I (inspection)
 * - Levels (W2.01): stakeholder need, mission, segment, system, subsystem, interface
 *
 * Two views: "By level" (the requirements of the focused element and its children) and
 * "Table" (RequirementsTable: the whole baseline, filters, bulk edit, import). No polling:
 * requirement changes arrive on the study socket (W2.08).
 */
import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useUIStore } from '../stores/uiStore'
import { SUGGESTED_REQS } from './suggestedReqs'
import { ArmButton, Button, Disclosure, Field, Input, Panel, Select, StatusBadge, Tag, type Status } from '../components/ui'
import { askText, showAlert } from '../components/ui/Dialog'
import { RecordDecision } from '../logbook'
import { RequirementIrInfo } from './irParts'
import { LEVEL_LABELS, LEVEL_ORDER, RequirementEditor, RequirementsTable, treeOptions, useStudyContext, type Req } from './RequirementsTable'

const API = '/api'

// English text is the i18n key
const REQ_TYPE_LABELS: Record<string, string> = {
  functional: 'Functional', performance: 'Performance', interface: 'Interface', regulatory: 'Regulatory', process: 'Process',
}

// Requirement type is a category, not a status: neutral tag with its initial (full name on hover).
const REQ_TYPES = [
  { value: 'functional', label: REQ_TYPE_LABELS.functional },
  { value: 'performance', label: REQ_TYPE_LABELS.performance },
  { value: 'interface', label: REQ_TYPE_LABELS.interface },
  { value: 'regulatory', label: REQ_TYPE_LABELS.regulatory },
  { value: 'process', label: REQ_TYPE_LABELS.process },
]

// ECSS-E-ST-10-02C: demonstration is part of test (the server stores D as T)
const VERIFICATION_METHODS: Record<string, string> = {
  T: 'Test', A: 'Analysis', R: 'Review', I: 'Inspection',
}

// English text is the i18n key — SMART check finding codes (server: requirement_engine.validate_smart)
const SMART_CODES: Record<string, string> = {
  specific: 'not specific (use “shall”)',
  measurable: 'not measurable (no threshold)',
  relevant: 'not relevant (no objective, parent or rationale)',
  traceable: 'not traceable (no objective, function or parent)',
  how: 'says HOW, not WHAT',
  orphan: 'orphan (no parent)',
}

// Requirement status → display status (colour + glyph + text).
const REQ_STATUS: Record<string, Status> = {
  draft: 'neutral', approved: 'info', verified: 'ok', violated: 'alarm',
}

export function RequirementsPanel() {
  const { t } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const focusElementId = useUIStore(s => s.focusElementId)
  const currentLevel = useUIStore(s => s.currentLevel)
  const qc = useQueryClient()

  // Fetch all elements to build the element picker
  const { data: allElements = [] } = useQuery({
    queryKey: ['elements', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/elements`).then(r => r.json()),
    enabled: !!studyId, structuralSharing: false,
  })

  // Children of current focus (the elements we can assign requirements to)
  const children = allElements.filter((el: any) =>
    focusElementId ? el.parent_id === focusElementId : !el.parent_id
  )
  // The focus element itself (for mission-level requirements)
  const focusElement = allElements.find((el: any) => el.id === focusElementId)

  // Fetch requirements for this study — show requirements for focus element AND its children
  const { data: allRequirements = [] } = useQuery({
    queryKey: ['requirements', studyId],
    queryFn: () => fetch(`${API}/requirements/tree?study_id=${studyId}`).then(r => r.json()),
    enabled: !!studyId, structuralSharing: false,
  })
  const [view, setView] = useState<'level' | 'table'>(() => {
    try { return localStorage.getItem('c2o.req.view') === 'table' ? 'table' : 'level' } catch { return 'level' }
  })
  const chooseView = (v: 'level' | 'table') => { setView(v); try { localStorage.setItem('c2o.req.view', v) } catch { /* ignore */ } }
  const [levelFilter, setLevelFilter] = useState('')
  const ctx = useStudyContext(studyId)
  const seatLabel = (id?: string | null) => {
    const s = ctx.seats.find((x: any) => x.id === id)
    return s ? s.label.en : (id ?? '')
  }

  // Filter to requirements relevant to current view
  const relevantElementIds = new Set<string>()
  if (focusElementId) relevantElementIds.add(focusElementId)
  for (const child of children) relevantElementIds.add(child.id)

  const requirements = allRequirements.filter((r: any) =>
    (!r.element_id || relevantElementIds.has(r.element_id)) && (!levelFilter || r.level === levelFilter)
  )

  // Name lookup
  const nameOf = (elementId: string | null) => {
    if (!elementId) return t('Mission')
    return allElements.find((e: any) => e.id === elementId)?.name || t('Unknown')
  }

  // Add form state
  const [showAdd, setShowAdd] = useState(false)
  const [newText, setNewText] = useState('')
  const [newCode, setNewCode] = useState('')
  const [newMethod, setNewMethod] = useState('A')
  const [newReqType, setNewReqType] = useState('functional')
  const [newElementId, setNewElementId] = useState<string>(focusElementId || '')

  // W2.01: tab 1 (a segment and its systems) writes segment requirements
  const LEVEL_TO_REQ: Record<number, string> = { 0: 'mission', 1: 'segment', 2: 'subsystem', 3: 'subsystem', 4: 'subsystem' }
  const [newLevel, setNewLevel] = useState('')
  const levelName = LEVEL_TO_REQ[currentLevel] || 'system'

  const addMutation = useMutation({
    mutationFn: async () => {
      // If deriving from a parent, use the derive endpoint
      if (deriveFromId) {
        const res = await fetch(`${API}/requirements/${deriveFromId}/derive`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: newText,
            element_id: newElementId || focusElementId || undefined,
            code: newCode || undefined,
            req_type: newReqType,
            verification_method: newMethod,
          }),
        })
        if (!res.ok) throw new Error(await res.text())
        return res.json()
      }
      const res = await fetch(`${API}/requirements/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          study_id: studyId,
          element_id: newElementId || focusElementId || undefined,
          level: newLevel || levelName,
          code: newCode || undefined,
          text: newText,
          req_type: newReqType,
          verification_method: newMethod,
          status: 'draft',
        }),
      })
      if (!res.ok) throw new Error(await res.text())
      return res.json()
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['requirements', studyId] })
      setNewText('')
      setNewCode('')
      setDeriveFromId(null)
      setShowAdd(false)
    },
  })

  const updateStatus = useMutation({
    mutationFn: async ({ reqId, status }: { reqId: string; status: string }) => {
      await fetch(`${API}/requirements/${reqId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      })
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['requirements', studyId] }),
  })

  const deleteMutation = useMutation({
    mutationFn: async (reqId: string) => {
      await fetch(`${API}/requirements/${reqId}`, { method: 'DELETE' })
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['requirements', studyId] }),
  })

  // "Derive" pre-fills the add form with parent context — user edits before submitting
  const startDerive = (parentReq: any) => {
    setNewText(t('[Derived from {{code}}] ', { code: parentReq.code || t('parent') }))
    setNewReqType(parentReq.req_type || 'performance')
    setNewMethod(parentReq.verification_method || 'A')
    setNewElementId(focusElementId || '')
    // A child's code extends its parent's: SR-002 → SR-002.1, SR-002.2 …
    if (parentReq.code) {
      const taken = new Set(allRequirements.map((r: any) => r.code))
      let n = 1
      while (taken.has(`${parentReq.code}.${n}`)) n++
      setNewCode(`${parentReq.code}.${n}`)
    }
    // Store parent ID for the derive API call
    setDeriveFromId(parentReq.id)
    setShowAdd(true)
  }
  const [deriveFromId, setDeriveFromId] = useState<string | null>(null)

  // SMART findings for the requirements at this level, after a check (id → codes)
  const [smart, setSmart] = useState<Record<string, string[]> | null>(null)
  const [recheck, setRecheck] = useState(0)
  // a requirement added or removed at this level: re-run a check already on screen
  const visibleKey = requirements.map((r: any) => r.id).join(',')
  useEffect(() => { if (smart) setRecheck(n => n + 1) }, [visibleKey])  // eslint-disable-line react-hooks/exhaustive-deps

  // Edit: every field of the requirement (RequirementEditor: code, level, parents, objectives,
  // threshold with ranges and dates, unit, methods, stage, owner, allocation, IR interface)
  const [editId, setEditId] = useState<string | null>(null)
  const startEdit = (req: any) => setEditId(req.id)

  // Group requirements by element
  const grouped = new Map<string, any[]>()
  for (const req of requirements) {
    const key = req.element_id || '_mission'
    if (!grouped.has(key)) grouped.set(key, [])
    grouped.get(key)!.push(req)
  }

  const linkParent = async (req: any) => {
    const parentCode = await askText(req.derived_from_requirement_id
      ? t('Enter parent requirement code to link to (or leave empty to unlink):')
      : t('Enter parent requirement code to derive from:'))
    if (parentCode === null || (!parentCode && !req.derived_from_requirement_id)) return
    const parentReq = parentCode ? allRequirements.find((r: any) => r.code === parentCode) : null
    if (parentCode && !parentReq) { void showAlert(t('Requirement "{{code}}" not found', { code: parentCode })); return }
    fetch(`${API}/requirements/${req.id}`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ derived_from_requirement_id: parentReq?.id || null, parent_id: parentReq?.id || null }),
    }).then(() => { qc.invalidateQueries({ queryKey: ['requirements', studyId] }); setRecheck(n => n + 1) })
  }

  return (
    <div className="c2o-pane">
      <Panel
        title={t('Requirements ({{n}})', { n: requirements.length })}
        actions={<>
          <SmartVerifyButton studyId={studyId} visibleIds={requirements.map((r: any) => r.id)} recheck={recheck} onResult={setSmart} />
          <RecordDecision decision="D-2.1-FLOWDOWN" capture="requirements:flowdown" label={t('Record flow-down decision')}
            prefill={() => {
              const by = (lvl: string) => allRequirements.filter((r: any) => r.level === lvl).length
              const belowReqs = allRequirements.filter((r: any) => !['stakeholder', 'mission'].includes(r.level))
              const traced = belowReqs.filter((r: any) => (r.parent_ids ?? []).length || r.derived_from_requirement_id).length
              return {
                evidence: [
                  { label: t('Mission requirements'), value: by('mission') },
                  { label: t('Segment requirements'), value: by('segment') },
                  { label: t('System requirements'), value: by('system') },
                  { label: t('Subsystem requirements'), value: by('subsystem') },
                  { label: t('Interface requirements'), value: by('interface') },
                  { label: t('Derived requirements traced to a parent'), value: `${traced} / ${belowReqs.length}` },
                ],
              }
            }} />
          <span className="row gap-1" role="group" aria-label={t('View')}>
            <Button size="sm" active={view === 'level'} aria-pressed={view === 'level'} onClick={() => chooseView('level')}>{t('By level')}</Button>
            <Button size="sm" active={view === 'table'} aria-pressed={view === 'table'} onClick={() => chooseView('table')}>{t('Table')}</Button>
          </span>
          {view === 'level' && (
            <Select dense value={levelFilter} onChange={e => setLevelFilter(e.target.value)} aria-label={t('Level')} className="w-auto">
              <option value="">{t('All levels')}</option>
              {LEVEL_ORDER.map(l => <option key={l} value={l}>{t(LEVEL_LABELS[l])}</option>)}
            </Select>
          )}
          <Button variant="primary" size="sm" onClick={() => { setNewElementId(focusElementId || ''); setShowAdd(true) }}
            disabledReason={showAdd ? t('The add form is already open below') : undefined}>
            {t('+ Add Requirement')}
          </Button>
        </>}
      >
        {view === 'table' && studyId && <RequirementsTable studyId={studyId} requirements={allRequirements as Req[]} />}

        {view === 'level' && requirements.length === 0 && !showAdd && (
          <p className="t-13 c-2 m-0 py-2">{t('No requirements at this level.')}</p>
        )}

        {view === 'level' && Array.from(grouped.entries()).map(([elementKey, reqs]) => (
          <div key={elementKey} className="c2o-reqs">
            <h4 className="c2o-reqs__group">
              {elementKey === '_mission' ? (focusElement?.name || t('Mission Level')) : nameOf(elementKey)}
              <span className="c2o-panel__meta">{reqs.length}</span>
            </h4>
            {reqs.map((req: any) => {
              const reqType = REQ_TYPES.find(rt => rt.value === (req.level === 'interface' ? 'interface' : req.req_type)) || REQ_TYPES[0]
              const parentIds: string[] = req.parent_ids ?? (req.derived_from_requirement_id || req.parent_id ? [req.derived_from_requirement_id || req.parent_id] : [])
              const parentCode = parentIds.length
                ? parentIds.map(pid => allRequirements.find((r: any) => r.id === pid)?.code || t('traced')).join(', ')
                : null
              const findings = smart?.[req.id] ?? []
              const orphan = !parentCode && !['stakeholder', 'mission', 'interface'].includes(req.level)
              return (
                <div key={req.id}>
                <div className="c2o-reqs__row">
                  <span className="c2o-reqs__code mono">{req.code}</span>
                  <Tag title={t(reqType.label)}>{t(reqType.label)[0]}</Tag>
                  {req.level === 'interface' ? <RequirementIrInfo req={req} /> : <span className="c2o-reqs__text">{req.text}</span>}
                  <span className="c2o-reqs__meta">
                    {req.verification_method && (
                      <Tag title={t('Verification method')}>{VERIFICATION_METHODS[req.verification_method] ? t(VERIFICATION_METHODS[req.verification_method]) : req.verification_method}</Tag>
                    )}
                    <span className="iflex ai-c gap-1">
                      <StatusBadge status={REQ_STATUS[req.status] ?? 'neutral'}><span className="sr-only">{t('Status')}</span></StatusBadge>
                      <Select dense className="c2o-reqs__status" aria-label={t('Status of {{code}}', { code: req.code })}
                        value={req.status} onChange={e => updateStatus.mutate({ reqId: req.id, status: e.target.value })}>
                        <option value="draft">{t('Draft', { context: 'requirement' })}</option>
                        <option value="approved">{t('Approved', { context: 'requirement' })}</option>
                        <option value="verified">{t('Verified', { context: 'requirement' })}</option>
                        <option value="violated">{t('Violated', { context: 'requirement' })}</option>
                      </Select>
                    </span>
                    {parentCode ? (
                      <Button size="sm" variant="quiet" onClick={() => linkParent(req)}
                        title={t('Derived from {{id}} — click to change', { id: parentCode })}>
                        <span className="mono">↑ {parentCode}</span>
                      </Button>
                    ) : orphan ? (
                      <button type="button" className="c2o-reqs__orphan" onClick={() => linkParent(req)} title={t('Click to link to a parent requirement')}>
                        <StatusBadge status="caution">{t('Orphan')}</StatusBadge>
                        <span className="c-accent">{t('link ↑')}</span>
                      </button>
                    ) : (
                      <Button size="sm" variant="quiet" onClick={() => linkParent(req)} title={t('Click to link to a parent requirement')}>{t('link ↑')}</Button>
                    )}
                    <Button size="sm" variant="quiet" onClick={() => startEdit(req)} title={t('Edit every field of the requirement')}>{t('edit')}</Button>
                    <Button size="sm" variant="quiet" onClick={() => startDerive(req)} title={t('Flow down — derive a child requirement')}>{t('flow ↓')}</Button>
                    <ArmButton variant="icon" label="×" armedLabel={t('Delete')} aria-label={t('Delete {{code}}', { code: req.code })}
                      onConfirm={() => deleteMutation.mutate(req.id)} />
                  </span>
                </div>
                {findings.length > 0 && (
                  <div className="c2o-reqs__smart t-13" role="note" style={{ padding: '0 0 0.4rem 9.5rem', color: 'var(--caution, #b7791f)' }}>
                    {t('SMART: {{list}}', { list: findings.map(c => t(SMART_CODES[c] ?? c)).join(' · ') })}
                  </div>
                )}
                {editId === req.id && studyId && (
                  <RequirementEditor studyId={studyId} req={req as Req} requirements={allRequirements as Req[]}
                    elements={allElements} study={ctx.study} seats={ctx.seats} seatLabel={seatLabel}
                    onClose={() => setEditId(null)}
                    onSaved={() => { setEditId(null); qc.invalidateQueries({ queryKey: ['requirements', studyId] }); setRecheck(n => n + 1) }} />
                )}
                </div>
              )
            })}
          </div>
        ))}
      </Panel>

      {/* Add form */}
      {showAdd && (
        <form className="c2o-blocks__add" aria-label={t('Add requirement')}
          onSubmit={e => { e.preventDefault(); if (newText) addMutation.mutate() }}>
          <Field label={t('Allocated to')}>
            <Select dense value={newElementId} onChange={e => setNewElementId(e.target.value)}>
              <option value="">{t('Not allocated')}</option>
              {treeOptions(allElements)}
            </Select>
          </Field>
          <Field label={t('Level')}>
            <Select dense value={newLevel || levelName} onChange={e => setNewLevel(e.target.value)}>
              {LEVEL_ORDER.map(l => <option key={l} value={l}>{t(LEVEL_LABELS[l])}</option>)}
            </Select>
          </Field>
          <Field label={t('Type')}>
            <Select dense value={newReqType} onChange={e => setNewReqType(e.target.value)}>
              {REQ_TYPES.map(rt => <option key={rt.value} value={rt.value}>{t(rt.label)}</option>)}
            </Select>
          </Field>
          <Field label={t('Code')}>
            <Input dense className="mono c2o-reqs__codein" value={newCode} onChange={e => setNewCode(e.target.value)} />
          </Field>
          <Field label={t('Requirement text')} className="grow c2o-reqs__textfield">
            <Input dense value={newText} onChange={e => setNewText(e.target.value)} autoFocus />
          </Field>
          <Field label={t('Verification method')}>
            <Select dense value={newMethod} onChange={e => setNewMethod(e.target.value)}>
              {Object.entries(VERIFICATION_METHODS).map(([k, v]) => <option key={k} value={k}>{t(v)}</option>)}
            </Select>
          </Field>
          <span className="row gap-2">
            <Button type="submit" variant="primary" size="sm" disabledReason={!newText ? t('Write the requirement text first') : undefined}>{t('Add')}</Button>
            <Button size="sm" onClick={() => setShowAdd(false)}>{t('Cancel')}</Button>
          </span>
        </form>
      )}

      {/* Suggested requirement templates */}
      <SuggestedTemplates
        currentLevel={currentLevel}
        onUseTemplate={(template) => {
          setNewText(template.text)
          setNewReqType(template.type)
          setNewMethod(template.method)
          setNewElementId(focusElementId || '')
          setShowAdd(true)
        }}
      />
    </div>
  )
}

function SmartVerifyButton({ studyId, visibleIds, recheck, onResult }: {
  studyId: string | null
  visibleIds: string[]               // the requirements shown at this level: counts and findings are scoped to them
  recheck: number                    // bumped after an edit or a new link: re-run a check already shown
  onResult: (findings: Record<string, string[]>) => void
}) {
  const { t } = useTranslation()
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const verify = async () => {
    if (!studyId) return
    setLoading(true)
    try {
      const res = await fetch(`${API}/requirements/verify?study_id=${studyId}`)
      if (res.ok) {
        const all = await res.json()
        const ids = new Set(visibleIds)
        const issues = (all.issues ?? []).filter((i: any) => ids.has(i.requirement_id))
        const smartFail = issues.filter((i: any) => (i.codes ?? []).some((c: string) => c !== 'orphan')).length
        const orphans = issues.filter((i: any) => (i.codes ?? []).includes('orphan')).length
        setResult({ ...all, issues, smart_pass: ids.size - smartFail, smart_fail: smartFail, orphans })
        onResult(Object.fromEntries(issues.map((i: any) => [i.requirement_id, i.codes ?? []])))
      }
    } finally { setLoading(false) }
  }
  // re-run after an edit, but only if a check is already on screen
  useEffect(() => { if (recheck && result) void verify() }, [recheck])  // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="flex ai-c gap-3 wrap">
      {result && (
        <span className="iflex ai-c gap-3" role="status">
          <StatusBadge status="ok">{t('{{count}} ok', { count: result.smart_pass })}</StatusBadge>
          {result.smart_fail > 0 && (
            <span title={result.issues?.map((i: any) => `${i.code}: ${(i.codes ?? []).map((c: string) => t(SMART_CODES[c] ?? c)).join('; ')}`).join('\n')}>
              <StatusBadge status="caution">{t('{{count}} issues', { count: result.smart_fail })}</StatusBadge>
            </span>
          )}
          {result.orphans > 0 && <StatusBadge status="caution">{t('{{count}} orphans', { count: result.orphans })}</StatusBadge>}
          <RecordDecision decision="D-2.1-QUALITY" capture="requirements:verify" prefill={() => ({
            evidence: [
              { label: t('Requirements passing the SMART check'), value: result.smart_pass ?? 0 },
              { label: t('Requirements with quality issues'), value: result.smart_fail ?? 0 },
              { label: t('Orphan requirements (no parent)'), value: result.orphans ?? 0 },
            ],
            // The tool's findings, one line per requirement: the student says which get rewritten, split or deleted.
            open_issues: [
              ...(result.issues ?? []).map((i: any) => `${i.code ?? i.id ?? '?'}: ${(i.codes ?? []).map((c: string) => t(SMART_CODES[c] ?? c)).join('; ')}`.slice(0, 160)),
            ].join('\n') || undefined,
          })} />
        </span>
      )}
      <Button size="sm" onClick={verify} busy={loading} title={t('Check each requirement is specific, measurable, achievable, relevant and traceable')}>
        {loading ? t('Checking...') : t('SMART Check')}
      </Button>
      {result && (result.issues ?? []).length > 0 && (
        <Disclosure summary={t('Findings')} meta={String(result.issues.length)}>
          {/* every finding, in a scrolling list (it was cut at 12) */}
          <ul className="c2o-reqs__findings t-12">
            {result.issues.map((i: any) => (
              <li key={i.requirement_id}><span className="mono">{i.code}</span>: {(i.codes ?? []).map((c: string) => t(SMART_CODES[c] ?? c)).join('; ')}</li>
            ))}
          </ul>
        </Disclosure>
      )}
    </div>
  )
}

function SuggestedTemplates({ currentLevel, onUseTemplate }: {
  currentLevel: number
  onUseTemplate: (t: { type: string; text: string; method: string }) => void
}) {
  const { t } = useTranslation()
  const templates = SUGGESTED_REQS[currentLevel] || []
  if (templates.length === 0) return null

  return (
    <Disclosure ruled summary={t('Suggested templates')} meta={t('{{count}} for this level', { count: templates.length, defaultValue_one: '{{count}} for this level' })}>
      <p className="t-12 c-2 m-0 mb-2">
        {t('Click a template to pre-fill the add form — edit the [placeholders] before adding.')}
      </p>
      <ul className="list-reset stack gap-1">
        {templates.map((tpl, i) => (
          // The stored template stays English (it becomes requirement text); only the list shows t(text).
          <li key={i}>
            <button type="button" onClick={() => onUseTemplate(tpl)} className="c2o-reqs__tpl">
              <Tag>{t(REQ_TYPE_LABELS[tpl.type] ?? tpl.type)}</Tag>
              <span className="grow">{t(tpl.text)}</span>
              <Tag>{VERIFICATION_METHODS[tpl.method] ? t(VERIFICATION_METHODS[tpl.method]) : tpl.method}</Tag>
            </button>
          </li>
        ))}
      </ul>
    </Disclosure>
  )
}
