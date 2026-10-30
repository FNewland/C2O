/**
 * TraceabilityTree — V-model bidirectional traceability view (SCDF-133, SCDF-160).
 *
 * Server path (SCDF-160): GET /api/studies/{id}/traceability/tree —
 * objectives → requirement chain → linked elements/functions → verification,
 * with status pills. Falls back to the store-based view (SCDF-133) when the
 * endpoint returns nothing (no objectives and no requirements).
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useDesignStore } from '../stores/designStore'
import { useUIStore } from '../stores/uiStore'
import type { TraceabilityTreeResponse, TraceRequirementNode } from '../types/arcadia'

const API = '/api'

const STATUS_COLORS: Record<string, string> = {
  accepted: '#10b981', approved: '#10b981', verified: '#10b981', passed: '#10b981', compliant: '#10b981',
  draft: '#6b7280', proposed: '#3b82f6', planned: '#3b82f6', in_progress: '#f59e0b', pending: '#f59e0b',
  partial: '#f59e0b', rejected: '#ef4444', failed: '#ef4444', non_compliant: '#ef4444', retired: '#6b7280',
}
// English text is the i18n key
const LEVEL_LABEL: Record<string, string> = {
  mission: 'mission', system: 'system', subsystem: 'subsystem', equipment: 'equipment', component: 'component',
}
const LEVEL_COLORS: Record<string, string> = {
  mission: '#8b5cf6', system: '#3b82f6', subsystem: '#06b6d4', equipment: '#10b981', component: '#10b981',
}

export function StatusPill({ value, prefix }: { value: string | null | undefined; prefix?: string }) {
  if (!value) return null
  const c = STATUS_COLORS[value] || '#6b7280'
  return (
    <span style={{ fontSize: '0.56rem', padding: '0 0.3rem', borderRadius: '999px', background: `${c}22`, color: c, border: `1px solid ${c}55`, whiteSpace: 'nowrap' }}>
      {prefix ? `${prefix} ` : ''}{value.replace(/_/g, ' ')}
    </span>
  )
}

function ReqNode({ node, depth, collapsed, toggle }: { node: TraceRequirementNode; depth: number; collapsed: Set<string>; toggle: (id: string) => void }) {
  const { t } = useTranslation()
  const lc = LEVEL_COLORS[node.level || ''] || '#3b82f6'
  const isCollapsed = collapsed.has(node.id)
  const kids = node.children || []
  const v = node.verification
  return (
    <div style={{ marginLeft: depth ? '0.75rem' : 0, marginTop: '0.15rem', borderLeft: `2px solid ${lc}`, paddingLeft: '0.4rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', flexWrap: 'wrap', fontSize: '0.7rem' }}>
        {kids.length > 0 && (
          <button onClick={() => toggle(node.id)} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', padding: 0, width: 12, fontSize: '0.65rem' }}>
            {isCollapsed ? '▸' : '▾'}
          </button>
        )}
        <span style={{ color: '#93c5fd', fontWeight: 600 }}>{node.code || node.id.slice(0, 8)}</span>
        {node.level && <span style={{ fontSize: '0.56rem', color: lc }}>{LEVEL_LABEL[node.level] ? t(LEVEL_LABEL[node.level]) : node.level}</span>}
        <StatusPill value={node.status} />
        <span style={{ color: 'var(--text-primary)' }} title={node.text || ''}>
          {(node.text || '').slice(0, 100)}{(node.text || '').length > 100 ? '…' : ''}
        </span>
      </div>
      {(node.elements.length > 0 || node.functions.length > 0 || v?.method || v?.status) && (
        <div style={{ marginLeft: '0.75rem', display: 'flex', gap: '0.3rem', flexWrap: 'wrap', alignItems: 'center', marginTop: '0.1rem', fontSize: '0.62rem' }}>
          {node.elements.map(e => (
            <span key={e.id} title={`${e.relation}${e.element_type ? ` · ${e.element_type}` : ''}`} style={{ color: '#6ee7b7', border: '1px solid rgba(16,185,129,0.4)', borderRadius: '3px', padding: '0 0.3rem', background: 'rgba(16,185,129,0.1)' }}>
              E: {e.name || e.id.slice(0, 8)}
            </span>
          ))}
          {node.functions.map(f => (
            <span key={f.id} title={f.relation} style={{ color: '#fcd34d', border: '1px solid rgba(245,158,11,0.4)', borderRadius: '3px', padding: '0 0.3rem', background: 'rgba(245,158,11,0.1)' }}>
              F: {f.name || f.id.slice(0, 8)}{f.layer ? ` [${f.layer}]` : ''}
            </span>
          ))}
          {(v?.method || v?.status || v?.phase) && (
            <span style={{ color: 'var(--text-secondary)' }}>
              V&V: {v.method || '—'}{v.phase ? ` @ ${v.phase}` : ''} <StatusPill value={v.status} />
            </span>
          )}
        </div>
      )}
      {!isCollapsed && kids.map(c => <ReqNode key={c.id} node={c} depth={depth + 1} collapsed={collapsed} toggle={toggle} />)}
    </div>
  )
}

export function TraceabilityTree({ studyId: studyIdProp }: { studyId?: string | null } = {}) {
  const { t } = useTranslation()
  const uiStudyId = useUIStore(s => s.studyId)
  const designStudyId = useDesignStore(s => s.studyId)
  const studyId = studyIdProp ?? uiStudyId ?? designStudyId
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set())
  const toggle = (id: string) => setCollapsed(prev => { const n = new Set(prev); if (n.has(id)) n.delete(id); else n.add(id); return n })

  const { data, isLoading, isError } = useQuery<TraceabilityTreeResponse>({
    queryKey: ['traceability-tree', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/traceability/tree`).then(r => { if (!r.ok) throw new Error(`${r.status}`); return r.json() }),
    enabled: !!studyId, structuralSharing: false,
  })

  const serverEmpty = !data || (data.objectives.length === 0 && data.unlinked_requirements.length === 0)
  if (!studyId || isError || (!isLoading && serverEmpty)) {
    return <LegacyTraceabilityTree />
  }
  if (isLoading || !data) {
    return <div className="card"><p style={{ fontSize: '0.72rem', color: '#6b7280' }}>{t('Loading traceability…')}</p></div>
  }

  const s = data.summary
  const levels = Object.entries(s.requirements_by_level || {}).map(([k, v]) => `${v} ${LEVEL_LABEL[k] ? t(LEVEL_LABEL[k]) : k}`).join(', ')
  return (
    <div className="card">
      <h3 style={{ fontSize: '0.85rem', marginBottom: '0.3rem' }}>{t('V-Model Traceability')}</h3>
      <p style={{ fontSize: '0.68rem', color: '#9ca3af', marginBottom: '0.5rem' }}>
        {t('Objective → Requirement chain → Element / Function → Verification. {{objectives}} objectives, {{requirements}} requirements ({{levels}}), {{traced}} traced to objectives, {{relations}} relations.', {
          objectives: s.objectives, requirements: s.requirements, levels: levels || t('none'),
          traced: s.requirements_traced_to_objectives, relations: s.relations,
        })}
      </p>

      {data.objectives.map((obj, i) => (
        <div key={obj.id || i} style={{ marginBottom: '0.5rem', borderLeft: '2px solid #8b5cf6', paddingLeft: '0.5rem' }}>
          <div style={{ display: 'flex', gap: '0.3rem', alignItems: 'center', flexWrap: 'wrap', fontSize: '0.75rem', fontWeight: 600, color: '#a78bfa' }}>
            <span>OBJ-{i + 1}: {obj.text}</span>
            {obj.priority && <span style={{ fontSize: '0.58rem', color: '#f59e0b' }}>{obj.priority}</span>}
            <StatusPill value={obj.status} />
          </div>
          {obj.measurable_criterion && <div style={{ fontSize: '0.62rem', color: '#9ca3af' }}>{t('criterion: {{criterion}}', { criterion: obj.measurable_criterion })}</div>}
          {obj.requirements.length > 0 ? (
            obj.requirements.map(r => <ReqNode key={r.id} node={r} depth={1} collapsed={collapsed} toggle={toggle} />)
          ) : (
            <div style={{ marginLeft: '0.75rem', fontSize: '0.65rem', color: '#6b7280', fontStyle: 'italic' }}>{t('No requirements linked to this objective')}</div>
          )}
        </div>
      ))}

      {data.unlinked_requirements.length > 0 && (
        <div style={{ marginTop: '0.5rem', borderTop: '1px solid #374151', paddingTop: '0.4rem' }}>
          <div style={{ fontSize: '0.68rem', color: '#f59e0b', marginBottom: '0.2rem' }}>
            {t('{{count}} top-level requirements not linked to an objective', { count: data.unlinked_requirements.length, defaultValue_one: '{{count}} top-level requirement not linked to an objective' })}
          </div>
          {data.unlinked_requirements.map(r => <ReqNode key={r.id} node={r} depth={0} collapsed={collapsed} toggle={toggle} />)}
        </div>
      )}
    </div>
  )
}

/** SCDF-133 store-based view; kept as the fallback when the server tree is empty. */
export function LegacyTraceabilityTree() {
  const { t } = useTranslation()
  const missionNeed = useDesignStore(s => s.missionNeed)
  const rawReqs = useDesignStore(s => s.generatedRequirements)
  const reqs = Array.isArray(rawReqs) ? rawReqs : []
  const functionsList = useDesignStore(s => s.functionsList)
  const objectives = missionNeed?.objectives || []

  const acceptedReqs = reqs.filter(r => r.status === 'accepted')

  if (objectives.length === 0 && acceptedReqs.length === 0) {
    return (
      <div className="card" style={{ borderLeft: '3px solid #6b7280' }}>
        <h3 style={{ fontSize: '0.85rem', color: '#6b7280' }}>{t('Traceability')}</h3>
        <p style={{ fontSize: '0.72rem', color: '#6b7280' }}>{t('Define objectives and requirements to see traceability.')}</p>
      </div>
    )
  }

  return (
    <div className="card">
      <h3 style={{ fontSize: '0.85rem', marginBottom: '0.3rem' }}>{t('V-Model Traceability')}</h3>
      <p style={{ fontSize: '0.68rem', color: '#9ca3af', marginBottom: '0.5rem' }}>
        {t('Need → Objective → Requirement → Function → Design. {{objectives}} objectives, {{requirements}} requirements, {{functions}} functions.', { objectives: objectives.length, requirements: acceptedReqs.length, functions: functionsList.length })}
      </p>

      {objectives.map((obj: any, i: number) => {
        const linkedReqs = acceptedReqs.filter(r => r.objective_id === obj.id)
        return (
          <div key={obj.id || i} style={{ marginBottom: '0.5rem', borderLeft: '2px solid #8b5cf6', paddingLeft: '0.5rem' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#a78bfa' }}>
              OBJ-{i + 1}: {obj.text}
            </div>
            {linkedReqs.length > 0 ? (
              linkedReqs.map(req => {
                const linkedFn = functionsList.find(f => f.id === req.function_id)
                return (
                  <div key={req.id} style={{ marginLeft: '0.75rem', marginTop: '0.15rem', borderLeft: '2px solid #3b82f6', paddingLeft: '0.4rem' }}>
                    <div style={{ fontSize: '0.7rem', color: '#93c5fd' }}>
                      {req.id}: {req.text?.slice(0, 80)}{req.text?.length > 80 ? '...' : ''}
                    </div>
                    {linkedFn && (
                      <div style={{ marginLeft: '0.75rem', fontSize: '0.65rem', color: '#6ee7b7', borderLeft: '2px solid #10b981', paddingLeft: '0.3rem', marginTop: '0.1rem' }}>
                        F: {linkedFn.name} → [{linkedFn.allocated_to?.join(', ')}]
                      </div>
                    )}
                  </div>
                )
              })
            ) : (
              <div style={{ marginLeft: '0.75rem', fontSize: '0.65rem', color: '#6b7280', fontStyle: 'italic' }}>
                {t('No requirements linked to this objective')}
              </div>
            )}
          </div>
        )
      })}

      {/* Orphan requirements (no objective link) */}
      {(() => {
        const orphans = acceptedReqs.filter(r => !r.objective_id || !objectives.find((o: any) => o.id === r.objective_id))
        if (orphans.length === 0) return null
        return (
          <div style={{ marginTop: '0.5rem', borderTop: '1px solid #374151', paddingTop: '0.4rem' }}>
            <div style={{ fontSize: '0.68rem', color: '#f59e0b', marginBottom: '0.2rem' }}>
              {t('{{count}} requirements not linked to an objective', { count: orphans.length, defaultValue_one: '{{count}} requirement not linked to an objective' })}
            </div>
            {orphans.slice(0, 5).map(r => (
              <div key={r.id} style={{ fontSize: '0.65rem', color: '#6b7280', marginLeft: '0.5rem' }}>
                {r.id}: {r.text?.slice(0, 60)}...
              </div>
            ))}
          </div>
        )
      })()}
    </div>
  )
}
