/**
 * RequirementsPanel — CRUD requirements scoped to current level.
 *
 * Requirements can be:
 * - Assigned to the parent element (mission-level) OR any child element (segment-level)
 * - Typed: functional, performance, interface, regulatory, process
 * - Verified: A (analysis), T (test), I (inspection), R (review), D (demonstration)
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useUIStore } from '../stores/uiStore'
import { SUGGESTED_REQS } from './suggestedReqs'
import { fs } from '../theme/tokens'
import { askText, showAlert } from '../components/ui/Dialog'

const API = '/api'

// English text is the i18n key
const REQ_TYPE_LABELS: Record<string, string> = {
  functional: 'Functional', performance: 'Performance', interface: 'Interface', regulatory: 'Regulatory', process: 'Process',
}

const REQ_TYPES = [
  { value: 'functional', label: REQ_TYPE_LABELS.functional, color: 'var(--interactive)' },
  { value: 'performance', label: REQ_TYPE_LABELS.performance, color: 'var(--status-ok)' },
  { value: 'interface', label: REQ_TYPE_LABELS.interface, color: 'var(--status-caution)' },
  { value: 'regulatory', label: REQ_TYPE_LABELS.regulatory, color: 'var(--status-alarm)' },
  { value: 'process', label: REQ_TYPE_LABELS.process, color: 'var(--cat-2)' },
]

const VERIFICATION_METHODS: Record<string, string> = {
  A: 'Analysis', T: 'Test', I: 'Inspection', R: 'Review', D: 'Demonstration',
}

const STATUS_COLORS: Record<string, string> = {
  draft: 'var(--text-secondary)',
  approved: 'var(--accent)',
  verified: 'var(--success)',
  violated: 'var(--danger)',
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
    enabled: !!studyId, structuralSharing: false, refetchInterval: 3000,
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
    enabled: !!studyId, structuralSharing: false, refetchInterval: 3000,
  })

  // Filter to requirements relevant to current view
  const relevantElementIds = new Set<string>()
  if (focusElementId) relevantElementIds.add(focusElementId)
  for (const child of children) relevantElementIds.add(child.id)

  const requirements = allRequirements.filter((r: any) =>
    !r.element_id || relevantElementIds.has(r.element_id)
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

  const LEVEL_TO_REQ: Record<number, string> = { 0: 'mission', 1: 'system', 2: 'subsystem', 3: 'subsystem', 4: 'subsystem' }
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
            rationale: newReqType,
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
          level: levelName,
          code: newCode || undefined,
          text: newText,
          rationale: newReqType,
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
    setNewReqType(parentReq.rationale || 'performance')
    setNewMethod(parentReq.verification_method || 'A')
    setNewElementId(focusElementId || '')
    // Store parent ID for the derive API call
    setDeriveFromId(parentReq.id)
    setShowAdd(true)
  }
  const [deriveFromId, setDeriveFromId] = useState<string | null>(null)

  // Group requirements by element
  const grouped = new Map<string, any[]>()
  for (const req of requirements) {
    const key = req.element_id || '_mission'
    if (!grouped.has(key)) grouped.set(key, [])
    grouped.get(key)!.push(req)
  }

  return (
    <div style={{ padding: '0.5rem 1rem', fontSize: fs.label }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem' }}>
        <span style={{ fontWeight: 600, fontSize: fs.label }}>
          {t('Requirements ({{n}})', { n: requirements.length })}
        </span>
        <span style={{ flex: 1 }} />

        {/* SMART verify button */}
        <SmartVerifyButton studyId={studyId} />

        {/* Type legend */}
        <div style={{ display: 'flex', gap: '0.3rem', marginLeft: '0.5rem' }}>
          {REQ_TYPES.map(rt => (
            <span key={rt.value} style={{
              fontSize: fs.label, padding: '0.1rem 0.3rem', borderRadius: '2px',
              background: `color-mix(in srgb, ${rt.color} 8%, transparent)`, color: rt.color, fontWeight: 600,
            }}>
              {t(rt.label)[0]}
            </span>
          ))}
        </div>
      </div>

      {/* Grouped requirement list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '0.5rem', maxHeight: 300, overflow: 'auto' }}>
        {requirements.length === 0 && !showAdd && (
          <div style={{ color: 'var(--text-secondary)', padding: '0.5rem 0' }}>
            {t('No requirements at this level.')}
          </div>
        )}

        {Array.from(grouped.entries()).map(([elementKey, reqs]) => (
          <div key={elementKey}>
            {/* Element header */}
            <div style={{
              fontSize: fs.label, fontWeight: 600, color: 'var(--text-secondary)',
              padding: '0.15rem 0.4rem', background: 'var(--bg-secondary)', borderRadius: '3px 3px 0 0',
              textTransform: 'uppercase',
            }}>
              {elementKey === '_mission' ? (focusElement?.name || t('Mission Level')) : nameOf(elementKey)}
            </div>

            {reqs.map((req: any) => {
              const reqType = REQ_TYPES.find(rt => rt.value === req.rationale) || REQ_TYPES[0]
              return (
                <div key={req.id} style={{
                  display: 'flex', alignItems: 'center', gap: '0.3rem',
                  padding: '0.3rem 0.4rem',
                  background: 'var(--bg-card)', borderBottom: '1px solid color-mix(in srgb, var(--text) 3%, transparent)',
                }}>
                  {/* Code */}
                  <span style={{ fontSize: fs.label, fontFamily: 'monospace', color: 'var(--accent)', fontWeight: 600, minWidth: 65, flexShrink: 0 }}>
                    {req.code}
                  </span>

                  {/* Type badge */}
                  <span style={{
                    fontSize: fs.label, padding: '0.05rem 0.2rem', borderRadius: '2px',
                    background: `color-mix(in srgb, ${reqType.color} 13%, transparent)`, color: reqType.color,
                    fontWeight: 600, flexShrink: 0,
                  }}>
                    {t(reqType.label)[0]}
                  </span>

                  {/* Text */}
                  <span style={{ flex: 1, fontSize: fs.label, lineHeight: 1.3 }}>{req.text}</span>

                  {/* Verification method */}
                  {req.verification_method && (
                    <span style={{
                      fontSize: fs.label, padding: '0.05rem 0.2rem', borderRadius: '2px',
                      background: 'rgba(16,185,129,0.15)', color: 'var(--success)',
                      fontWeight: 600, flexShrink: 0,
                    }}>
                      {req.verification_method}
                    </span>
                  )}

                  {/* Status */}
                  <select
                    value={req.status}
                    onChange={e => updateStatus.mutate({ reqId: req.id, status: e.target.value })}
                    style={{
                      fontSize: fs.label, padding: '0.05rem', borderRadius: '2px',
                      background: 'var(--bg-primary)', border: '1px solid var(--border)',
                      color: STATUS_COLORS[req.status] || 'var(--text-secondary)', flexShrink: 0,
                    }}
                  >
                    <option value="draft">{t('Draft', { context: 'requirement' })}</option>
                    <option value="approved">{t('Approved', { context: 'requirement' })}</option>
                    <option value="verified">{t('Verified', { context: 'requirement' })}</option>
                    <option value="violated">{t('Violated', { context: 'requirement' })}</option>
                  </select>

                  {/* Traceability badge — click to link/unlink */}
                  {req.derived_from_requirement_id ? (
                    <button style={{ fontSize: fs.label, padding: '0.05rem 0.2rem', borderRadius: '2px', background: 'rgba(16,185,129,0.15)', color: 'var(--success)', fontWeight: 600, flexShrink: 0, border: 'none', cursor: 'pointer' }}
                      title={t('Derived from {{id}} — click to change', { id: req.derived_from_requirement_id })}
                      onClick={async () => {
                        const parentCode = (await askText(t('Enter parent requirement code to link to (or leave empty to unlink):')))
                        if (parentCode === null) return
                        const parentReq = parentCode ? allRequirements.find((r: any) => r.code === parentCode) : null
                        fetch(`${API}/requirements/${req.id}`, {
                          method: 'PATCH', headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ derived_from_requirement_id: parentReq?.id || null }),
                        }).then(() => qc.invalidateQueries({ queryKey: ['requirements', studyId] }))
                      }}>
                      ↑ {allRequirements.find((r: any) => r.id === req.derived_from_requirement_id)?.code || t('traced')}
                    </button>
                  ) : (
                    <button style={{ fontSize: fs.label, padding: '0.05rem 0.2rem', borderRadius: '2px', background: req.level !== 'mission' ? 'rgba(245,158,11,0.15)' : 'rgba(59,130,246,0.1)', color: req.level !== 'mission' ? 'var(--warning)' : 'var(--accent)', fontWeight: 600, flexShrink: 0, border: 'none', cursor: 'pointer' }}
                      title={t('Click to link to a parent requirement')}
                      onClick={async () => {
                        const parentCode = (await askText(t('Enter parent requirement code to derive from:')))
                        if (!parentCode) return
                        const parentReq = allRequirements.find((r: any) => r.code === parentCode)
                        if (!parentReq) { void showAlert(t('Requirement "{{code}}" not found', { code: parentCode })); return }
                        fetch(`${API}/requirements/${req.id}`, {
                          method: 'PATCH', headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ derived_from_requirement_id: parentReq.id }),
                        }).then(() => qc.invalidateQueries({ queryKey: ['requirements', studyId] }))
                      }}>
                      {req.level !== 'mission' ? t('orphan — link ↑') : t('link ↑')}
                    </button>
                  )}

                  <button onClick={() => startDerive(req)} title={t('Flow down — derive a child requirement')}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--info)', fontSize: fs.label, flexShrink: 0 }}>
                    {t('flow ↓')}
                  </button>

                  <button onClick={() => deleteMutation.mutate(req.id)}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--danger)', fontSize: fs.label, flexShrink: 0 }}>
                    ×
                  </button>
                </div>
              )
            })}
          </div>
        ))}
      </div>

      {/* Add form */}
      {showAdd ? (
        <div style={{
          display: 'flex', gap: '0.3rem', alignItems: 'center', flexWrap: 'wrap',
          padding: '0.4rem', background: 'var(--bg-card)', borderRadius: '4px', border: '1px solid var(--accent)',
        }}>
          {/* Element picker */}
          <select
            value={newElementId}
            onChange={e => setNewElementId(e.target.value)}
            style={{
              padding: '0.25rem', fontSize: fs.label, borderRadius: '3px',
              background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)',
            }}
          >
            <option value={focusElementId || ''}>{focusElement?.name || t('Mission Level')}</option>
            {children.map((el: any) => (
              <option key={el.id} value={el.id}>{el.name}</option>
            ))}
          </select>

          {/* Requirement type */}
          <select
            value={newReqType}
            onChange={e => setNewReqType(e.target.value)}
            style={{
              padding: '0.25rem', fontSize: fs.label, borderRadius: '3px',
              background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)',
            }}
          >
            {REQ_TYPES.map(rt => <option key={rt.value} value={rt.value}>{t(rt.label)}</option>)}
          </select>

          {/* Code */}
          <input value={newCode} onChange={e => setNewCode(e.target.value)} placeholder={t('Code')}
            style={{ width: 75, padding: '0.25rem 0.3rem', fontSize: fs.value, borderRadius: '3px', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)', fontFamily: 'monospace' }}
          />

          {/* Text */}
          <input value={newText} onChange={e => setNewText(e.target.value)} placeholder={t('Requirement text')} autoFocus
            style={{ flex: 1, minWidth: 180, padding: '0.25rem 0.3rem', fontSize: fs.label, borderRadius: '3px', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}
            onKeyDown={e => e.key === 'Enter' && newText && addMutation.mutate()}
          />

          {/* Verification */}
          <select value={newMethod} onChange={e => setNewMethod(e.target.value)}
            style={{ padding: '0.25rem', fontSize: fs.label, borderRadius: '3px', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}>
            {Object.keys(VERIFICATION_METHODS).map((k) => <option key={k} value={k}>{k}</option>)}
          </select>

          <button onClick={() => newText && addMutation.mutate()} disabled={!newText}
            style={{ padding: '0.25rem 0.5rem', fontSize: fs.label, fontWeight: 600, borderRadius: '3px', background: 'var(--accent)', color: 'white', border: 'none', cursor: 'pointer' }}>
            {t('Add')}
          </button>
          <button onClick={() => setShowAdd(false)}
            style={{ padding: '0.25rem 0.5rem', fontSize: fs.label, borderRadius: '3px', background: 'var(--bg-secondary)', color: 'var(--text-secondary)', border: 'none', cursor: 'pointer' }}>
            {t('Cancel')}
          </button>
        </div>
      ) : (
        <button onClick={() => { setNewElementId(focusElementId || ''); setShowAdd(true) }}
          style={{ padding: '0.35rem 0.75rem', fontSize: fs.label, fontWeight: 600, borderRadius: '4px', background: 'var(--accent)', color: 'white', border: 'none', cursor: 'pointer' }}>
          {t('+ Add Requirement')}
        </button>
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

function SmartVerifyButton({ studyId }: { studyId: string | null }) {
  const { t } = useTranslation()
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const verify = async () => {
    if (!studyId) return
    setLoading(true)
    try {
      const res = await fetch(`${API}/requirements/verify?study_id=${studyId}`)
      if (res.ok) setResult(await res.json())
    } finally { setLoading(false) }
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
      <button onClick={verify} disabled={loading} style={{
        padding: '0.15rem 0.5rem', fontSize: fs.label, fontWeight: 600, borderRadius: '3px',
        background: result ? (result.smart_fail > 0 || result.orphans > 0 ? 'rgba(245,158,11,0.15)' : 'rgba(16,185,129,0.15)') : 'var(--bg-card)',
        color: result ? (result.smart_fail > 0 || result.orphans > 0 ? 'var(--warning)' : 'var(--success)') : 'var(--text-secondary)',
        border: 'none', cursor: 'pointer',
      }}>
        {loading ? '...' : t('SMART Check')}
      </button>
      {result && (
        <>
          <span style={{ fontSize: fs.label, color: 'var(--success)' }}>{t('{{count}} ok', { count: result.smart_pass })}</span>
          {result.smart_fail > 0 && <span style={{ fontSize: fs.label, color: 'var(--warning)' }}>{t('{{count}} issues', { count: result.smart_fail })}</span>}
          {result.orphans > 0 && <span style={{ fontSize: fs.label, color: 'var(--danger)' }}>{t('{{count}} orphans', { count: result.orphans })}</span>}
        </>
      )}
      {result?.issues?.length > 0 && (
        <span title={result.issues.map((i: any) => `${i.code}: ${i.issues.join('; ')}`).join('\n')}
          style={{ fontSize: fs.label, color: 'var(--warning)', cursor: 'help', textDecoration: 'underline dotted' }}>
          {t('details')}
        </span>
      )}
    </div>
  )
}

const REQ_TYPE_COLORS: Record<string, string> = {
  functional: 'var(--interactive)', performance: 'var(--status-ok)', interface: 'var(--status-caution)',
  regulatory: 'var(--status-alarm)', process: 'var(--cat-2)',
}

function SuggestedTemplates({ currentLevel, onUseTemplate }: {
  currentLevel: number
  onUseTemplate: (t: { type: string; text: string; method: string }) => void
}) {
  const { t } = useTranslation()
  const [expanded, setExpanded] = useState(false)
  const templates = SUGGESTED_REQS[currentLevel] || []
  if (templates.length === 0) return null

  return (
    <div style={{ marginTop: '0.5rem', borderTop: '1px solid var(--border)', paddingTop: '0.4rem' }}>
      <button onClick={() => setExpanded(!expanded)}
        style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: fs.label, color: 'var(--cat-2)', fontWeight: 600, padding: 0 }}>
        {expanded ? '▾' : '▸'} {t('Suggested Templates ({{n}})', { n: templates.length })}
      </button>
      {expanded && (
        <div style={{ marginTop: '0.3rem', display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
          <div style={{ fontSize: fs.label, color: 'var(--text-secondary)', marginBottom: '0.1rem' }}>
            {t('Click a template to pre-fill the add form — edit the [placeholders] before adding.')}
          </div>
          {templates.map((tpl, i) => {
            const color = REQ_TYPE_COLORS[tpl.type] || 'var(--text-3)'
            return (
              // The stored template stays English (it becomes requirement text); only the list shows t(text).
              <button key={i} onClick={() => onUseTemplate(tpl)}
                style={{
                  display: 'flex', alignItems: 'center', gap: '0.3rem',
                  padding: '0.2rem 0.4rem', borderRadius: '3px', textAlign: 'left',
                  background: 'var(--bg-card)', border: '1px solid var(--border)',
                  color: 'var(--text-primary)', cursor: 'pointer', fontSize: fs.label,
                }}>
                <span style={{
                  fontSize: fs.label, padding: '0.05rem 0.2rem', borderRadius: '2px',
                  background: `color-mix(in srgb, ${color} 13%, transparent)`, color, fontWeight: 600, flexShrink: 0,
                }}>
                  {t(REQ_TYPE_LABELS[tpl.type] ?? tpl.type).slice(0, 4).toUpperCase()}
                </span>
                <span style={{ flex: 1 }}>{t(tpl.text)}</span>
                <span style={{ fontSize: fs.label, color: 'var(--success)', flexShrink: 0 }}>{tpl.method}</span>
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
