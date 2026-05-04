/**
 * ExportsPanel — Unified document and data export interface.
 *
 * Connects ALL backend generators to the UI:
 * - ECSS DID documents (MRD, TS, IRD, SEMP, RMP, ConOps, Test Plan)
 * - Regulatory filings (ITU API, IARU coordination, RSSSA, COPUOS, EOL)
 * - Export control assessment
 * - BOM generator
 * - Parametric data viewer
 * - Spectrum allocation viewer
 * - Launch provider options
 */
import { useState } from 'react'
import { useDesignStore } from '../stores/designStore'

type ExportCategory = 'ecss' | 'regulatory' | 'spectrum' | 'launch' | 'data' | 'engineering'

interface GeneratedDoc {
  title: string
  content: any
}

const EXPORT_ITEMS: { category: ExportCategory; id: string; name: string; endpoint: string; method: string; description: string }[] = [
  // ECSS Documents
  { category: 'ecss', id: 'mrd', name: 'Mission Requirements Document', endpoint: '/api/ecss/dids/mrd/generate', method: 'POST', description: 'ECSS-E-ST-10C Annex A' },
  { category: 'ecss', id: 'ts', name: 'Technical Specification', endpoint: '/api/ecss/dids/ts/generate', method: 'POST', description: 'ECSS-E-ST-10-06C' },
  { category: 'ecss', id: 'ird', name: 'Interface Requirements Document', endpoint: '/api/ecss/dids/ird/generate', method: 'POST', description: 'ECSS-E-ST-10-24C' },
  { category: 'ecss', id: 'semp', name: 'SE Management Plan', endpoint: '/api/ecss/dids/semp/generate', method: 'POST', description: 'NASA SEH Appendix J' },
  { category: 'ecss', id: 'rmp', name: 'Risk Management Plan', endpoint: '/api/ecss/dids/rmp/generate', method: 'POST', description: 'ECSS-M-ST-80C' },
  { category: 'ecss', id: 'conops_doc', name: 'Concept of Operations', endpoint: '/api/ecss/dids/conops/generate', method: 'POST', description: 'NASA SEH Appendix S' },
  { category: 'ecss', id: 'test_plan', name: 'Test Plan', endpoint: '/api/ecss/dids/test_plan/generate', method: 'POST', description: 'ECSS-E-ST-10-03C' },
  // Regulatory
  { category: 'regulatory', id: 'itu_api', name: 'ITU API Filing Template', endpoint: '/api/lifecycle/spectrum/itu-api-template', method: 'POST', description: 'ITU RR Appendix 4 Section I' },
  { category: 'regulatory', id: 'iaru', name: 'IARU Coordination Request', endpoint: '/api/lifecycle/spectrum/iaru-template', method: 'POST', description: 'IARU Form Version 40' },
  { category: 'regulatory', id: 'rsssa', name: 'RSSSA Filing (Canada)', endpoint: '/api/lifecycle/regulatory/rsssa', method: 'POST', description: 'Remote Sensing Space Systems Act' },
  { category: 'regulatory', id: 'export', name: 'Export Control Assessment', endpoint: '/api/lifecycle/regulatory/export-assessment', method: 'POST', description: 'ITAR/EAR/CGP classification' },
  { category: 'regulatory', id: 'copuos', name: 'UN Registration (COPUOS)', endpoint: '/api/lifecycle/regulatory/copuos-registration', method: 'POST', description: 'Registration Convention Art IV' },
  { category: 'regulatory', id: 'eol', name: 'End-of-Life Analysis', endpoint: '/api/lifecycle/regulatory/eol-report', method: 'POST', description: 'ECSS-U-AS-10C / NASA-STD-8719.14' },
  // Spectrum
  { category: 'spectrum', id: 'bands', name: 'Available Frequency Bands', endpoint: '/api/lifecycle/spectrum/bands', method: 'GET', description: 'Filtered by mission type and license' },
  // Launch
  { category: 'launch', id: 'providers', name: 'Launch Provider Options', endpoint: '/api/lifecycle/parametric-data', method: 'GET', description: 'Pricing, capacity, lead times' },
  // Data
  { category: 'data', id: 'parametric', name: 'Parametric Model Data', endpoint: '/api/lifecycle/parametric-data', method: 'GET', description: 'Mass/cost/power fractions (editable)' },
  { category: 'data', id: 'duty_cycles', name: 'Power Duty Cycles', endpoint: '/api/lifecycle/duty-cycles', method: 'POST', description: 'Per-mode power and duty cycle estimate' },
  { category: 'data', id: 'consistency', name: 'Consistency Check', endpoint: '/api/lifecycle/consistency/', method: 'GET', description: 'Full design consistency validation' },
  { category: 'data', id: 'margins', name: 'ECSS Margin Enforcement', endpoint: '/api/ecss/margins/', method: 'GET', description: 'Budget margins vs ECSS policy' },
  // Engineering outputs (from right panel ExportPanel)
  { category: 'engineering', id: 'smo', name: 'SMO Simulator Config', endpoint: '/api/exports/smo/', method: 'POST', description: 'Simulator configuration (YAML)' },
  { category: 'engineering', id: 'srr_docs', name: 'SRR Design Review Package', endpoint: '/api/exports/docs/srr', method: 'POST', description: 'System Requirements Review documents' },
  { category: 'engineering', id: 'pdr_docs', name: 'PDR Design Review Package', endpoint: '/api/exports/docs/pdr', method: 'POST', description: 'Preliminary Design Review documents' },
  { category: 'engineering', id: 'cdr_docs', name: 'CDR Design Review Package', endpoint: '/api/exports/docs/cdr', method: 'POST', description: 'Critical Design Review documents' },
  { category: 'engineering', id: 'mbse', name: 'MBSE Export (SysML JSON)', endpoint: '/api/exports/mbse/', method: 'POST', description: 'ECSS-E-TM-10-25A-style model exchange' },
  { category: 'engineering', id: 'fsw', name: 'Flight Software Architecture', endpoint: '/api/exports/fsw/', method: 'POST', description: 'Mode manager, FDIR, TC/TM (C headers)' },
]

const CATEGORY_LABELS: Record<ExportCategory, { name: string; color: string }> = {
  ecss: { name: 'ECSS Documents', color: '#3b82f6' },
  regulatory: { name: 'Regulatory Filings', color: '#f59e0b' },
  engineering: { name: 'Engineering Outputs', color: '#8b5cf6' },
  spectrum: { name: 'Spectrum & Licensing', color: '#ec4899' },
  launch: { name: 'Launch', color: '#f97316' },
  data: { name: 'Design Data', color: '#10b981' },
}

export function ExportsPanel({ studyId }: { studyId: string | null }) {
  const [activeCategory, setActiveCategory] = useState<ExportCategory>('ecss')
  const [generating, setGenerating] = useState<string | null>(null)
  const [generatedDoc, setGeneratedDoc] = useState<GeneratedDoc | null>(null)
  const { requirements } = useDesignStore()

  const generateExport = async (item: typeof EXPORT_ITEMS[0]) => {
    setGenerating(item.id)
    setGeneratedDoc(null)
    try {
      let url = item.endpoint
      if (studyId) {
        if (url.endsWith('/')) {
          url += studyId
        } else if (item.method === 'GET') {
          url += (url.includes('?') ? '&' : '?') + `study_id=${studyId}`
        }
      }

      const body: any = {}
      if (item.category === 'regulatory') {
        body.study_name = requirements.name
        body.orbit_altitude_km = requirements.orbit.altitude_km
        body.orbit_inclination_deg = requirements.orbit.inclination_deg
        body.operator_name = ''
        body.has_imaging = requirements.mission_type === 'earth_observation'
        body.country_of_origin = 'Canada'
      }
      if (item.id === 'duty_cycles') {
        body.spacecraft_class = requirements.spacecraft_class
        body.mission_type = requirements.mission_type
        body.comms_band = 'S'
        body.eclipse_fraction = 0.35
      }
      if (item.id === 'itu_api') {
        body.network_name = requirements.name
        body.orbit_altitude_km = requirements.orbit.altitude_km
        body.orbit_inclination_deg = requirements.orbit.inclination_deg
      }
      if (item.id === 'iaru') {
        body.mission_name = requirements.name
        body.orbit_altitude_km = requirements.orbit.altitude_km
        body.orbit_inclination_deg = requirements.orbit.inclination_deg
      }

      const res = await fetch(url, {
        method: item.method,
        headers: item.method === 'POST' ? { 'Content-Type': 'application/json' } : undefined,
        body: item.method === 'POST' ? JSON.stringify(body) : undefined,
      })

      if (res.ok) {
        const data = await res.json()
        setGeneratedDoc({ title: item.name, content: data })
      }
    } catch (e) {
      console.error('Export failed:', e)
    }
    setGenerating(null)
  }

  const filteredItems = EXPORT_ITEMS.filter(i => i.category === activeCategory)

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ marginBottom: '0.25rem' }}>Exports & Documents</h2>
      <p style={{ fontSize: '0.78rem', color: '#9ca3af', marginBottom: '0.75rem' }}>
        Generate ECSS documents, regulatory filings, spectrum analysis, and design data exports.
      </p>

      {/* Category tabs */}
      <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        {(Object.entries(CATEGORY_LABELS) as [ExportCategory, { name: string; color: string }][]).map(([cat, info]) => (
          <button key={cat} onClick={() => setActiveCategory(cat)}
            style={{
              padding: '0.3rem 0.75rem', fontSize: '0.78rem', borderRadius: '4px', cursor: 'pointer',
              background: activeCategory === cat ? info.color : 'var(--bg-secondary, #1f2937)',
              color: activeCategory === cat ? 'white' : '#9ca3af',
              border: `1px solid ${activeCategory === cat ? info.color : '#374151'}`,
            }}>{info.name}</button>
        ))}
      </div>

      {/* Export items */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', marginBottom: '1rem' }}>
        {filteredItems.map(item => (
          <div key={item.id} style={{
            display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 0.75rem',
            background: 'var(--bg-secondary, #1f2937)', borderRadius: '6px',
            border: '1px solid var(--border, #374151)',
          }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '0.82rem', fontWeight: 500 }}>{item.name}</div>
              <div style={{ fontSize: '0.68rem', color: '#6b7280' }}>{item.description}</div>
            </div>
            <button className="btn btn-sm" onClick={() => generateExport(item)}
              disabled={generating !== null}
              style={{ fontSize: '0.7rem', whiteSpace: 'nowrap' }}>
              {generating === item.id ? 'Generating...' : 'Generate'}
            </button>
          </div>
        ))}
      </div>

      {/* Generated document viewer */}
      {generatedDoc && (
        <div style={{
          padding: '0.75rem', borderRadius: '6px',
          background: 'var(--bg-primary, #0a0e1a)', border: '1px solid var(--border, #374151)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>{generatedDoc.title}</span>
            <button className="btn btn-sm" onClick={() => {
              const blob = new Blob([JSON.stringify(generatedDoc.content, null, 2)], { type: 'application/json' })
              const url = URL.createObjectURL(blob)
              const a = document.createElement('a')
              a.href = url
              a.download = `${generatedDoc.title.replace(/\s+/g, '_')}.json`
              a.click()
            }} style={{ fontSize: '0.68rem' }}>Download JSON</button>
          </div>
          <pre style={{
            fontSize: '0.72rem', color: '#d1d5db', overflow: 'auto', maxHeight: '400px',
            background: '#111827', padding: '0.5rem', borderRadius: '4px',
            whiteSpace: 'pre-wrap', wordBreak: 'break-word',
          }}>
            {JSON.stringify(generatedDoc.content, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}
