/**
 * Phase 5: Verification & Operations
 */
import { GateReviewPanel } from '../components/GateReviewPanel'
import { ComplianceMatrix } from '../components/ComplianceMatrix'
import { EcssCompliancePanel } from '../components/EcssCompliancePanel'
import { ExportsPanel } from '../components/ExportsPanel'
import { MaturityOverview } from '../components/MaturityOverview'
import { BOMView } from '../components/BOMView'
import { useDesignStore } from '../stores/designStore'
import { useState } from 'react'

type SubView = 'gate_review' | 'maturity' | 'bom' | 'compliance' | 'ecss' | 'exports'

export function Phase5Verification() {
  const studyId = useDesignStore(s => s.studyId)
  const [subView, setSubView] = useState<SubView>('gate_review')

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ display: 'flex', gap: '0.25rem', padding: '0.4rem 1rem', borderBottom: '1px solid var(--border, #374151)' }}>
        {(['gate_review', 'maturity', 'bom', 'compliance', 'ecss', 'exports'] as SubView[]).map(v => {
          const labels: Record<string, string> = { gate_review: 'Gate Review', maturity: 'Maturity', bom: 'BOM', ecss: 'ECSS', compliance: 'Compliance', exports: 'Exports' }
          return (
          <button key={v} onClick={() => setSubView(v)} style={{
            padding: '0.25rem 0.6rem', fontSize: '0.72rem', borderRadius: '3px', cursor: 'pointer',
            background: subView === v ? 'rgba(239,68,68,0.15)' : 'transparent',
            color: subView === v ? '#fca5a5' : '#6b7280',
            border: 'none',
          }}>{labels[v] || v}</button>
          )
        })}
      </div>
      <div style={{ flex: 1, overflow: 'auto' }}>
        {(!studyId || !useDesignStore(s => s.result)) && (subView === 'compliance' || subView === 'ecss') && (
          <div style={{ padding: '2rem', color: '#6b7280' }}>
            <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem', color: '#9ca3af' }}>
              {subView === 'compliance' ? 'Compliance Matrix' : 'ECSS Standards'}
            </h3>
            <p style={{ fontSize: '0.78rem', marginBottom: '0.5rem' }}>
              This view requires a completed design run. Click "Run Design" in the sidebar to execute
              the parametric design loop, then return here.
            </p>
            <p style={{ fontSize: '0.72rem', color: '#6b7280' }}>
              The design loop runs 20 engineering agents that compute mass, power, link, thermal,
              AOCS, propulsion, and cost budgets. These results are then checked against requirements
              and ECSS margin policies.
            </p>
          </div>
        )}
        {subView === 'gate_review' && <GateReviewPanel studyId={studyId} />}
        {subView === 'maturity' && <MaturityOverview />}
        {subView === 'bom' && <BOMView />}
        {subView === 'compliance' && studyId && useDesignStore.getState().result && <ComplianceMatrix studyId={studyId} />}
        {subView === 'ecss' && studyId && useDesignStore.getState().result && <EcssCompliancePanel studyId={studyId} />}
        {subView === 'exports' && <ExportsPanel studyId={studyId} />}
      </div>
    </div>
  )
}
