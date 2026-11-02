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
import { fs } from '../theme/tokens'

const API = '/api'

const STATUS_COLORS: Record<string, string> = {
  accepted: 'var(--status-ok)', approved: 'var(--status-ok)', verified: 'var(--status-ok)', passed: 'var(--status-ok)', compliant: 'var(--status-ok)',
  draft: 'var(--text-3)', proposed: 'var(--interactive)', planned: 'var(--interactive)', in_progress: 'var(--status-caution)', pending: 'var(--status-caution)',
  partial: 'var(--status-caution)', rejected: 'var(--status-alarm)', failed: 'var(--status-alarm)', non_compliant: 'var(--status-alarm)', retired: 'var(--text-3)',
}
// English text is the i18n key
const LEVEL_LABEL: Record<string, string> = {
  mission: 'mission', system: 'system', subsystem: 'subsystem', equipment: 'equipment', component: 'component',
}
const LEVEL_COLORS: Record<string, string> = {
  mission: 'var(--cat-2)', system: 'var(--interactive)', subsystem: 'var(--interactive)', equipment: 'var(--status-ok)', component: 'var(--status-ok)',
}

export function StatusPill({ value, prefix }: { value: string | null | undefined; prefix?: string }) {
  if (!value) return null
  const c = STATUS_COLORS[value] || 'var(--text-3)'
  return (
    <span style={{ fontSize: fs.label, padding: '0 0.3rem', borderRadius: '999px', background: `color-mix(in srgb, ${c} 13%, transparent)`, color: c, border: `1px solid color-mix(in srgb, ${c} 33%, transparent)`, whiteSpace: 'nowrap' }}>
      {prefix ? `${prefix} ` : ''}{value.replace(/_/g, ' ')}
    </span>
  )
}

function ReqNode({ node, depth, collapsed, toggle }: { node: TraceRequirementNode; depth: number; collapsed: Set<string>; toggle: (id: string) => void }) {
  const { t } = useTranslation()
  const lc = LEVEL_COLORS[node.level || ''] || 'var(--interactive)'
  const isCollapsed = collapsed.has(node.id)
  const kids = node.children || []
  const v = node.verification
  return (
    <div style={{ marginLeft: depth ? '0.75rem' : 0, marginTop: '0.15rem', borderLeft: `2px solid ${lc}`, paddingLeft: '0.4rem' }}>
      <div className="flex ai-c gap-1 wrap t-12">
        {kids.length > 0 && (
          <button onClick={() => toggle(node.id)} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', padding: 0, width: 12, fontSize: fs.label }}>
            {isCollapsed ? '▸' : '▾'}
          </button>
        )}
        <span className="c-accent w-600">{node.code || node.id.slice(0, 8)}</span>
        {node.level && <span style={{ fontSize: fs.label, color: lc }}>{LEVEL_LABEL[node.level] ? t(LEVEL_LABEL[node.level]) : node.level}</span>}
        <StatusPill value={node.status} />
        <span className="c-1" title={node.text || ''}>
          {(node.text || '').slice(0, 100)}{(node.text || '').length > 100 ? '…' : ''}
        </span>
      </div>
      {(node.elements.length > 0 || node.functions.length > 0 || v?.method || v?.status) && (
        <div className="ml-3 flex gap-1 wrap ai-c mt-1 t-12">
          {node.elements.map(e => (
            <span key={e.id} title={`${e.relation}${e.element_type ? ` · ${e.element_type}` : ''}`} style={{ color: 'var(--status-ok)', border: '1px solid rgba(16,185,129,0.4)', borderRadius: '3px', padding: '0 0.3rem', background: 'rgba(16,185,129,0.1)' }}>
              E: {e.name || e.id.slice(0, 8)}
            </span>
          ))}
          {node.functions.map(f => (
            <span key={f.id} title={f.relation} style={{ color: 'var(--status-caution)', border: '1px solid rgba(245,158,11,0.4)', borderRadius: '3px', padding: '0 0.3rem', background: 'rgba(245,158,11,0.1)' }}>
              F: {f.name || f.id.slice(0, 8)}{f.layer ? ` [${f.layer}]` : ''}
            </span>
          ))}
          {(v?.method || v?.status || v?.phase) && (
            <span className="c-2">
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
    return <div className="card"><p className="t-12 c-3">{t('Loading traceability…')}</p></div>
  }

  const s = data.summary
  const levels = Object.entries(s.requirements_by_level || {}).map(([k, v]) => `${v} ${LEVEL_LABEL[k] ? t(LEVEL_LABEL[k]) : k}`).join(', ')
  return (
    <div className="card">
      <h3 className="t-13 mb-1">{t('V-Model Traceability')}</h3>
      <p className="t-12 c-2 mb-2">
        {t('Objective → Requirement chain → Element / Function → Verification. {{objectives}} objectives, {{requirements}} requirements ({{levels}}), {{traced}} traced to objectives, {{relations}} relations.', {
          objectives: s.objectives, requirements: s.requirements, levels: levels || t('none'),
          traced: s.requirements_traced_to_objectives, relations: s.relations,
        })}
      </p>

      {data.objectives.map((obj, i) => (
        <div key={obj.id || i} style={{ marginBottom: '0.5rem', borderLeft: '2px solid var(--cat-2)', paddingLeft: '0.5rem' }}>
          <div style={{ display: 'flex', gap: '0.3rem', alignItems: 'center', flexWrap: 'wrap', fontSize: fs.label, fontWeight: 600, color: 'var(--cat-2)' }}>
            <span>OBJ-{i + 1}: {obj.text}</span>
            {obj.priority && <span className="t-12 c-caution">{obj.priority}</span>}
            <StatusPill value={obj.status} />
          </div>
          {obj.measurable_criterion && <div className="t-12 c-2">{t('criterion: {{criterion}}', { criterion: obj.measurable_criterion })}</div>}
          {obj.requirements.length > 0 ? (
            obj.requirements.map(r => <ReqNode key={r.id} node={r} depth={1} collapsed={collapsed} toggle={toggle} />)
          ) : (
            <div className="ml-3 t-12 c-3 ital">{t('No requirements linked to this objective')}</div>
          )}
        </div>
      ))}

      {data.unlinked_requirements.length > 0 && (
        <div className="mt-2 bt pt-2">
          <div className="t-12 c-caution mb-1">
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
      <div className="card" style={{ borderLeft: '3px solid var(--text-3)' }}>
        <h3 className="t-13 c-3">{t('Traceability')}</h3>
        <p className="t-12 c-3">{t('Define objectives and requirements to see traceability.')}</p>
      </div>
    )
  }

  return (
    <div className="card">
      <h3 className="t-13 mb-1">{t('V-Model Traceability')}</h3>
      <p className="t-12 c-2 mb-2">
        {t('Need → Objective → Requirement → Function → Design. {{objectives}} objectives, {{requirements}} requirements, {{functions}} functions.', { objectives: objectives.length, requirements: acceptedReqs.length, functions: functionsList.length })}
      </p>

      {objectives.map((obj: any, i: number) => {
        const linkedReqs = acceptedReqs.filter(r => r.objective_id === obj.id)
        return (
          <div key={obj.id || i} style={{ marginBottom: '0.5rem', borderLeft: '2px solid var(--cat-2)', paddingLeft: '0.5rem' }}>
            <div style={{ fontSize: fs.label, fontWeight: 600, color: 'var(--cat-2)' }}>
              OBJ-{i + 1}: {obj.text}
            </div>
            {linkedReqs.length > 0 ? (
              linkedReqs.map(req => {
                const linkedFn = functionsList.find(f => f.id === req.function_id)
                return (
                  <div key={req.id} className="ml-3 mt-1 bl-accent pl-2">
                    <div className="t-12 c-accent">
                      {req.id}: {req.text?.slice(0, 80)}{req.text?.length > 80 ? '...' : ''}
                    </div>
                    {linkedFn && (
                      <div className="ml-3 t-12 c-ok bl-ok pl-1 mt-1">
                        F: {linkedFn.name} → [{linkedFn.allocated_to?.join(', ')}]
                      </div>
                    )}
                  </div>
                )
              })
            ) : (
              <div className="ml-3 t-12 c-3 ital">
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
          <div className="mt-2 bt pt-2">
            <div className="t-12 c-caution mb-1">
              {t('{{count}} requirements not linked to an objective', { count: orphans.length, defaultValue_one: '{{count}} requirement not linked to an objective' })}
            </div>
            {orphans.slice(0, 5).map(r => (
              <div key={r.id} className="t-12 c-3 ml-2">
                {r.id}: {r.text?.slice(0, 60)}...
              </div>
            ))}
          </div>
        )
      })()}
    </div>
  )
}
