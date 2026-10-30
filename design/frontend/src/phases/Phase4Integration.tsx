/**
 * Phase 4: Integration & Test
 */
import { VerificationMatrix } from '../components/VerificationMatrix'
import { ProjectManagement } from '../components/ProjectManagement'
import { useDesignStore } from '../stores/designStore'
import { useState } from 'react'

type SubView = 'vv_matrix' | 'project_mgmt'

export function Phase4Integration() {
  const studyId = useDesignStore(s => s.studyId)
  const [subView, setSubView] = useState<SubView>('vv_matrix')

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ display: 'flex', gap: '0.25rem', padding: '0.4rem 1rem', borderBottom: '1px solid var(--border, #374151)' }}>
        {(['vv_matrix', 'project_mgmt'] as SubView[]).map(v => (
          <button key={v} onClick={() => setSubView(v)} style={{
            padding: '0.25rem 0.6rem', fontSize: '0.72rem', borderRadius: '3px', cursor: 'pointer',
            background: subView === v ? 'rgba(245,158,11,0.15)' : 'transparent',
            color: subView === v ? '#fbbf24' : '#6b7280',
            border: 'none',
          }}>{v === 'vv_matrix' ? 'V&V Matrix' : 'Project Mgmt'}</button>
        ))}
      </div>
      <div style={{ flex: 1, overflow: 'auto' }}>
        {subView === 'vv_matrix' && <VerificationMatrix studyId={studyId} />}
        {subView === 'project_mgmt' && <ProjectManagement />}
      </div>
    </div>
  )
}
