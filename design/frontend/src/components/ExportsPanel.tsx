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
import { useModelStore } from '../stores/modelStore'
import { useEquipmentView } from '../hooks/useEquipmentView'
import { SEMPQuestionnaire } from './SEMPQuestionnaire'
import { DocumentPreview } from './DocumentPreview'

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
  const [showSEMP, setShowSEMP] = useState(false)
  const { requirements } = useDesignStore()
  const sempAnswers = useDesignStore(s => s.sempAnswers)
  const setSempAnswers = useDesignStore(s => s.setSempAnswers)
  const modelElements = useModelStore(s => s.elements)
  const modelInterfaces = useModelStore(s => s.interfaces)
  const equipment = useEquipmentView()

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

      // Enrich POST body with element tree data for richer document generation
      if (item.method === 'POST' && modelElements.size > 0) {
        // Build subsystem summary from element tree
        const subsystems = Array.from(modelElements.values())
          .filter(e => e.element_type === 'subsystem')
          .map(e => ({ id: e.id, name: e.name, domain: e.subsystem_domain, segment: e.segment, mass_kg: e.mass_kg, power_w: e.power_avg_w }))
        body.subsystems = subsystems

        // Build equipment BOM from element tree + flat store
        body.equipment_bom = equipment.map(e => ({
          name: e.name, category: e.category, component_id: e.componentId,
          mass_kg: e.mass_kg, power_w: e.power_w, cost_keur: e.cost_keur, quantity: e.quantity,
        }))

        // Build interface summary
        body.interfaces = Array.from(modelInterfaces.values()).map(i => ({
          name: i.name, type: i.interface_type, from: i.from_element_id, to: i.to_element_id,
        }))
      }

      if (item.category === 'regulatory') {
        // Pass full design parameters for deep auto-population
        const result = useDesignStore.getState().result
        const params = result?.parameters || {}
        const getP = (id: string) => { const p = (params as any)[id]; return p && typeof p.value === 'number' ? p.value : undefined }
        body.study_name = requirements.name
        body.mission_type = requirements.mission_type
        body.orbit_altitude_km = requirements.orbit.altitude_km
        body.orbit_inclination_deg = requirements.orbit.inclination_deg
        body.orbit_type = requirements.orbit.orbit_type
        body.design_lifetime_years = requirements.design_lifetime_years
        body.operator_name = ''
        body.has_imaging = requirements.mission_type === 'earth_observation'
        body.country_of_origin = 'Canada'
        body.mission_id = useDesignStore.getState().missionId
        // Design parameters for auto-computation
        body.design_params = {
          mass_kg: getP('mass.dry_mass_kg') || getP('systems.total_mass_kg'),
          power_w: getP('power.sa_power_eol_w'),
          tx_power_w: getP('link.ttc_power_w'),
          antenna_gain_dbi: getP('link.antenna_gain_dbi'),
          data_rate_mbps: requirements.payloads?.[0]?.data_rate_mbps,
          pointing_accuracy_deg: getP('aocs.pointing_accuracy_deg'),
          isp_s: getP('propulsion.isp_s'),
          battery_capacity_wh: getP('power.battery_capacity_wh'),
          delta_v_ms: getP('propulsion.delta_v_total_ms'),
        }
        // Ground stations from element tree
        const allElements = useModelStore.getState().elements
        body.ground_stations = Array.from(allElements.values())
          .filter(el => el.segment === 'ground' && el.element_type === 'component' && el.performance?.latitude != null)
          .map(el => ({ name: el.name, latitude: el.performance.latitude, longitude: el.performance.longitude, bands: el.performance.bands || [] }))
        // Payload info
        if (requirements.payloads?.[0]) {
          body.payload = {
            name: requirements.payloads[0].name,
            mass_kg: requirements.payloads[0].mass_kg,
            power_w: requirements.payloads[0].power_w,
            data_rate_mbps: requirements.payloads[0].data_rate_mbps,
            pointing_accuracy_deg: requirements.payloads[0].pointing_accuracy_deg,
          }
        }
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
      <p style={{ fontSize: '0.78rem', color: '#9ca3af', marginBottom: '0.5rem' }}>
        Generate ECSS documents, regulatory filings, spectrum analysis, and design data exports.
      </p>

      {/* Quick action buttons */}
      <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
        <button className="btn btn-sm" onClick={() => setShowSEMP(true)}
          style={{ fontSize: '0.72rem', background: Object.keys(sempAnswers).length > 0 ? '#10b981' : '#3b82f6' }}>
          {Object.keys(sempAnswers).length > 0 ? 'Update SEMP Inputs' : 'Configure SEMP'}
        </button>
        {studyId && (
          <button className="btn btn-sm" onClick={() => window.open(`/api/lifecycle/bom/${studyId}?fmt=csv`, '_blank')}
            style={{ fontSize: '0.72rem', background: '#8b5cf6' }}>
            Export BOM (CSV)
          </button>
        )}
      </div>

      {/* Full design export — element tree + all state */}
      {modelElements.size > 0 && (
        <button className="btn btn-sm" onClick={() => {
          const exportData = {
            exported_at: new Date().toISOString(),
            study_id: studyId,
            requirements,
            elements: Array.from(modelElements.values()),
            interfaces: Array.from(modelInterfaces.values()),
            equipment_bom: equipment,
            design_result: useDesignStore.getState().result,
            budget_allocations: useDesignStore.getState().budgetAllocations,
          }
          const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
          const url = URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url; a.download = `spacecdf-full-${new Date().toISOString().slice(0, 10)}.json`
          a.click(); URL.revokeObjectURL(url)
        }} style={{ fontSize: '0.72rem', marginBottom: '0.75rem', background: '#10b981' }}>
          Export Full Design (Element Tree + BOM + Budgets)
        </button>
      )}

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
              {generating === item.id ? 'Generating...' : 'JSON'}
            </button>
            {/* .docx download — available for ECSS, regulatory, and engineering docs */}
            {(item.category === 'ecss' || item.category === 'regulatory' || item.category === 'engineering') && (
              <button className="btn btn-sm" onClick={() => {
                const docxMap: Record<string, string> = {
                  mrd: 'mrd', conops_doc: 'conops', test_plan: 'testplan',
                  ts: 'ts', ird: 'ird', semp: 'semp', rmp: 'rmp', vp: 'vp',
                  // Regulatory — mapped to docx generator or falls back to JSON download
                  itu_api: 'itu_api', iaru: 'iaru', rsssa: 'rsssa', export: 'export',
                  copuos: 'copuos', eol: 'eol',
                  // Engineering
                  srr_docs: 'srr', pdr_docs: 'pdr', cdr_docs: 'cdr',
                }
                const docType = docxMap[item.id] || item.id
                const url = `/api/exports/docx/${docType}${studyId ? `?study_id=${studyId}` : ''}`
                window.open(url, '_blank')
              }} style={{ fontSize: '0.7rem', whiteSpace: 'nowrap', background: item.category === 'ecss' ? '#3b82f6' : item.category === 'regulatory' ? '#f59e0b' : '#8b5cf6' }}>
                .docx
              </button>
            )}
          </div>
        ))}
      </div>

      {/* Generated document viewer — renders sections, tables, and diagrams */}
      {generatedDoc && (
        <DocumentPreview
          title={generatedDoc.title}
          content={generatedDoc.content}
          onClose={() => setGeneratedDoc(null)}
        />
      )}
      {/* SEMP Questionnaire wizard */}
      <SEMPQuestionnaire
        isOpen={showSEMP}
        onClose={() => setShowSEMP(false)}
        onSubmit={(answers) => {
          setSempAnswers(answers)
          setShowSEMP(false)
        }}
        subsystemTRLs={(() => {
          // Read actual TRLs from element tree subsystems
          const trls: Record<string, number> = {}
          for (const el of modelElements.values()) {
            if (el.element_type === 'subsystem' && el.subsystem_domain && el.trl) {
              trls[el.subsystem_domain] = el.trl
            } else if (el.element_type === 'component' && el.subsystem_domain && el.trl) {
              // Use min TRL of components in each subsystem (weakest link)
              const current = trls[el.subsystem_domain]
              if (!current || el.trl < current) trls[el.subsystem_domain] = el.trl
            }
          }
          // Default fallback for domains without elements
          const defaults: Record<string, number> = { power: 9, aocs: 8, ttc: 9, thermal: 9, structure: 9, propulsion: 7, obc: 9, payload: 6 }
          return { ...defaults, ...trls }
        })()}
        orbitAltitude={requirements?.orbit?.altitude_km || 500}
        missionDurationYears={requirements?.design_lifetime_years || 3}
      />
    </div>
  )
}
