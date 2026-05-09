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
        {!studyId && subView !== 'exports' && subView !== 'gate_review' && subView !== 'maturity' && subView !== 'bom' && (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#6b7280' }}>
            <p>Run a design first to generate compliance and ECSS data.</p>
            <p style={{ fontSize: '0.72rem', color: '#374151' }}>Use the "Run Design" button in the header.</p>
          </div>
        )}
        {subView === 'gate_review' && <GateReviewPanel studyId={studyId} />}
        {subView === 'maturity' && <MaturityOverview />}
        {subView === 'bom' && <BOMView />}
        {subView === 'compliance' && studyId && <ComplianceMatrix studyId={studyId} />}
        {subView === 'ecss' && studyId && <EcssCompliancePanel studyId={studyId} />}
        {subView === 'exports' && <ExportsPanel studyId={studyId} />}
      </div>
    </div>
  )
}
