/**
 * ExportPanel — Comprehensive document export.
 *
 * Generates all standard space mission deliverables using existing backend endpoints.
 * Organized by category: Design Reviews, Systems Engineering, Compliance,
 * Technical Models, Operations, and Data.
 */
import { useState } from 'react'
import { useUIStore } from '../stores/uiStore'

const API = '/api'

interface ExportItem {
  id: string
  label: string
  description: string
  format: string
  action: (studyId: string) => Promise<void>
}

interface ExportCategory {
  name: string
  color: string
  items: ExportItem[]
}

// ─── Helpers ───

async function downloadBlob(url: string, filename: string, method = 'POST') {
  const res = await fetch(url, { method })
  if (!res.ok) throw new Error(`Export failed: ${res.status} ${res.statusText}`)
  const blob = await res.blob()
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = filename
  a.click()
  URL.revokeObjectURL(a.href)
}

async function downloadJson(url: string, filename: string, method = 'POST') {
  const res = await fetch(url, { method })
  if (!res.ok) throw new Error(`Export failed: ${res.status}`)
  const data = await res.json()
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = filename
  a.click()
  URL.revokeObjectURL(a.href)
}

async function downloadCsv(headers: string[], rows: string[][], filename: string) {
  const csv = [headers.join(','), ...rows.map(r => r.map(c => `"${(c || '').replace(/"/g, '""')}"`).join(','))].join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = filename
  a.click()
  URL.revokeObjectURL(a.href)
}

// ─── Build export categories from element tree ───

function buildClientExports(studyId: string): ExportCategory[] {
  return [
    {
      name: 'Design Reviews',
      color: '#3b82f6',
      items: [
        { id: 'srr', label: 'SRR Document Pack', description: 'System Requirements Review — ZIP with Markdown, DOCX, XLSX', format: 'ZIP',
          action: (sid) => downloadBlob(`${API}/exports/docs/${sid}?review=srr&fmt=zip`, `SRR_${sid}.zip`) },
        { id: 'pdr', label: 'PDR Document Pack', description: 'Preliminary Design Review', format: 'ZIP',
          action: (sid) => downloadBlob(`${API}/exports/docs/${sid}?review=pdr&fmt=zip`, `PDR_${sid}.zip`) },
        { id: 'cdr', label: 'CDR Document Pack', description: 'Critical Design Review', format: 'ZIP',
          action: (sid) => downloadBlob(`${API}/exports/docs/${sid}?review=cdr&fmt=zip`, `CDR_${sid}.zip`) },
      ],
    },
    {
      name: 'Systems Engineering',
      color: '#8b5cf6',
      items: [
        { id: 'semp', label: 'SEMP', description: 'Systems Engineering Management Plan (ECSS-E-ST-10C)', format: 'JSON',
          action: async (sid) => downloadJson(`${API}/ecss/dids/semp/generate?study_id=${sid}`, `SEMP_${sid}.json`) },
        { id: 'mrd', label: 'Mission Requirements Document', description: 'MRD with mission needs, objectives, requirements', format: 'DOCX',
          action: (sid) => downloadBlob(`${API}/exports/docx/mrd?study_id=${sid}`, `MRD_${sid}.docx`) },
        { id: 'conops', label: 'Concept of Operations', description: 'ConOps with modes, phases, data flow', format: 'DOCX',
          action: (sid) => downloadBlob(`${API}/exports/docx/conops?study_id=${sid}`, `ConOps_${sid}.docx`) },
        { id: 'bom', label: 'Bill of Materials', description: 'All components with mass, power, cost, TRL, manufacturer', format: 'CSV',
          action: async (sid) => {
            const elements = await fetch(`${API}/studies/${sid}/elements`).then(r => r.json())
            const components = elements.filter((e: any) => e.element_type === 'component')
            downloadCsv(
              ['Name', 'Domain', 'Mass (kg)', 'Power (W)', 'Cost (kEUR)', 'TRL', 'Manufacturer', 'Qty', 'KB ID'],
              components.map((c: any) => [c.name, c.subsystem_domain || '', String(c.mass_kg || ''), String(c.power_avg_w || ''), String(c.cost_recurring_keur || ''), String(c.trl || ''), c.manufacturer || '', String(c.quantity || 1), c.kb_component_id || '']),
              `BOM_${sid}.csv`,
            )
          },
        },
      ],
    },
    {
      name: 'Verification & Compliance',
      color: '#10b981',
      items: [
        { id: 'vv-matrix', label: 'V&V Matrix', description: 'Requirements verification matrix with methods and status', format: 'CSV',
          action: async (sid) => {
            const reqs = await fetch(`${API}/requirements/tree?study_id=${sid}`).then(r => r.json())
            downloadCsv(
              ['Code', 'Level', 'Text', 'Type', 'V&V Method', 'Status', 'Element'],
              reqs.map((r: any) => [r.code || '', r.level, r.text, r.rationale || '', r.verification_method || '', r.status, r.element_id || '']),
              `VV_Matrix_${sid}.csv`,
            )
          },
        },
        { id: 'compliance', label: 'ECSS Compliance Matrix', description: 'Standard-by-standard compliance status', format: 'JSON',
          action: (sid) => downloadJson(`${API}/compliance/${sid}`, `ECSS_Compliance_${sid}.json`, 'GET') },
        { id: 'verification', label: 'Verification Plan', description: 'Verification approach per requirement', format: 'JSON',
          action: (sid) => downloadJson(`${API}/compliance/${sid}/verification`, `Verification_Plan_${sid}.json`, 'GET') },
        { id: 'tailoring', label: 'ECSS Tailoring', description: 'Standards tailoring rationale', format: 'JSON',
          action: (sid) => downloadJson(`${API}/compliance/${sid}/tailoring`, `ECSS_Tailoring_${sid}.json`, 'GET') },
        { id: 'margins', label: 'Margin Status Report', description: 'Mass, power, cost, link margins vs ECSS thresholds', format: 'JSON',
          action: (sid) => downloadJson(`${API}/ecss/margins/${sid}`, `Margins_${sid}.json`, 'GET') },
        { id: 'regulatory', label: 'Regulatory Filing Data', description: 'ISED/ITU frequency coordination inputs', format: 'JSON',
          action: async (sid) => {
            const elements = await fetch(`${API}/studies/${sid}/elements`).then(r => r.json())
            const gsElements = elements.filter((e: any) => e.segment === 'ground' && e.performance?.latitude)
            const ttcElements = elements.filter((e: any) => e.subsystem_domain === 'ttc')
            const data = { ground_stations: gsElements.map((e: any) => ({ name: e.name, ...e.performance })), ttc_systems: ttcElements.map((e: any) => ({ name: e.name, ...e.performance })) }
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
            const a = document.createElement('a'); a.href = URL.createObjectURL(blob)
            a.download = `Regulatory_${sid}.json`; a.click(); URL.revokeObjectURL(a.href)
          },
        },
        { id: 'rsssa', label: 'RSSSA Licence Application', description: 'Remote Sensing Space Systems Act filing data (UOttawa branded)', format: 'JSON',
          action: (sid) => downloadJson(`${API}/exports/rsssa/${sid}`, `RSSSA_${sid}.json`) },
        { id: 'launch-icd', label: 'Launch ICD', description: 'Launch Interface Control Document — mechanical, electrical, environmental', format: 'JSON',
          action: (sid) => downloadJson(`${API}/exports/launch-icd/${sid}`, `Launch_ICD_${sid}.json`) },
        { id: 'deorbit', label: 'Deorbit Analysis', description: 'Debris compliance report — orbital lifetime, casualty risk, mitigation options', format: 'JSON',
          action: (sid) => downloadJson(`${API}/exports/deorbit/${sid}`, `Deorbit_Analysis_${sid}.json`) },
      ],
    },
    {
      name: 'Technical Models',
      color: '#f59e0b',
      items: [
        { id: 'fsw', label: 'Flight Software Architecture', description: 'FSW module structure, interfaces, task scheduling', format: 'JSON',
          action: (sid) => downloadJson(`${API}/exports/fsw/${sid}`, `FSW_Architecture_${sid}.json`) },
        { id: 'mbse', label: 'MBSE Model Export', description: 'SysML-compatible model data (elements, interfaces, requirements)', format: 'JSON',
          action: (sid) => downloadJson(`${API}/exports/mbse/${sid}`, `MBSE_Model_${sid}.json`) },
        { id: 'smo', label: 'Simulator Model Inputs', description: 'Orbit, attitude, power, thermal parameters for simulation', format: 'JSON',
          action: (sid) => downloadJson(`${API}/exports/smo/${sid}`, `Simulator_Inputs_${sid}.json`) },
        { id: 'thermal-report', label: 'Thermal Design Report', description: 'Thermal environment, power dissipation, design notes (UOttawa branded)', format: 'JSON',
          action: (sid) => downloadJson(`${API}/exports/thermal-report/${sid}`, `Thermal_Report_${sid}.json`) },
        { id: 'thermal-model', label: 'Thermal Model Data', description: 'Node temperatures, power dissipation, radiator areas per element', format: 'CSV',
          action: async (sid) => {
            const elements = await fetch(`${API}/studies/${sid}/elements`).then(r => r.json())
            const rows = elements.filter((e: any) => e.power_avg_w || e.subsystem_domain === 'thermal')
            downloadCsv(
              ['Name', 'Type', 'Domain', 'Power Avg (W)', 'Power Peak (W)', 'Mass (kg)', 'Notes'],
              rows.map((e: any) => [e.name, e.element_type, e.subsystem_domain || '', String(e.power_avg_w || 0), String(e.power_peak_w || 0), String(e.mass_kg || 0), '']),
              `Thermal_Model_${sid}.csv`,
            )
          },
        },
        { id: 'structural-model', label: 'Structural Model Data', description: 'Mass breakdown, dimensions, CoG inputs', format: 'CSV',
          action: async (sid) => {
            const elements = await fetch(`${API}/studies/${sid}/elements`).then(r => r.json())
            const rows = elements.filter((e: any) => e.mass_kg)
            downloadCsv(
              ['Name', 'Type', 'Domain', 'Mass (kg)', 'Qty', 'Total Mass (kg)', 'Dimensions (mm)'],
              rows.map((e: any) => [e.name, e.element_type, e.subsystem_domain || '', String(e.mass_kg), String(e.quantity || 1), String((e.mass_kg || 0) * (e.quantity || 1)), JSON.stringify(e.dimensions_mm || [])]),
              `Structural_Model_${sid}.csv`,
            )
          },
        },
        { id: 'wiring', label: 'Wiring Diagram Data', description: 'Electrical interfaces: voltage, current, connector types', format: 'CSV',
          action: async (sid) => {
            const interfaces = await fetch(`${API}/studies/${sid}/interfaces`).then(r => r.json())
            const elements = await fetch(`${API}/studies/${sid}/elements`).then(r => r.json())
            const nameOf = (id: string) => elements.find((e: any) => e.id === id)?.name || id
            const electrical = interfaces.filter((i: any) => i.interface_type === 'electrical' || i.interface_type === 'data')
            downloadCsv(
              ['From', 'To', 'Type', 'Direction', 'Label', 'Properties'],
              electrical.map((i: any) => [nameOf(i.from_element_id), nameOf(i.to_element_id), i.interface_type, i.direction || '', i.name || '', JSON.stringify(i.properties || {})]),
              `Wiring_${sid}.csv`,
            )
          },
        },
      ],
    },
    {
      name: 'Operations & Test',
      color: '#06b6d4',
      items: [
        { id: 'test-plan', label: 'Test Plan Matrix', description: 'AIT/AIV test cases derived from requirements', format: 'CSV',
          action: async (sid) => {
            const reqs = await fetch(`${API}/requirements/tree?study_id=${sid}`).then(r => r.json())
            const testReqs = reqs.filter((r: any) => r.verification_method === 'T')
            downloadCsv(
              ['Test ID', 'Requirement', 'Requirement Text', 'Level', 'Status', 'Test Description', 'Pass Criteria'],
              testReqs.map((r: any, i: number) => [`TC-${String(i + 1).padStart(3, '0')}`, r.code || r.id, r.text, r.level, r.status, `Test for: ${r.text}`, `Verify ${r.code || ''} is met`]),
              `Test_Plan_${sid}.csv`,
            )
          },
        },
        { id: 'test-plan-branded', label: 'Test Plan (Branded)', description: 'AIT/AIV test plan with UOttawa/SEDTI branding', format: 'JSON',
          action: (sid) => downloadJson(`${API}/exports/test-plan/${sid}`, `Test_Plan_Branded_${sid}.json`) },
        { id: 'ops-concept', label: 'Operations Concept Data', description: 'Ground stations, contact windows, data flow', format: 'JSON',
          action: async (sid) => {
            const elements = await fetch(`${API}/studies/${sid}/elements`).then(r => r.json())
            const opsData = {
              ground_stations: elements.filter((e: any) => e.segment === 'ground' && e.performance?.latitude).map((e: any) => ({ name: e.name, ...e.performance })),
              operations_elements: elements.filter((e: any) => e.segment === 'operations').map((e: any) => ({ name: e.name, type: e.element_type })),
              spacecraft: elements.filter((e: any) => e.segment === 'space' && e.element_type === 'system').map((e: any) => ({ name: e.name, quantity: e.quantity || 1 })),
            }
            const blob = new Blob([JSON.stringify(opsData, null, 2)], { type: 'application/json' })
            const a = document.createElement('a'); a.href = URL.createObjectURL(blob)
            a.download = `Ops_Concept_${sid}.json`; a.click(); URL.revokeObjectURL(a.href)
          },
        },
      ],
    },
    {
      name: 'Data Export',
      color: '#6b7280',
      items: [
        { id: 'full-tree', label: 'Full Element Tree', description: 'Complete design tree with all properties', format: 'JSON',
          action: async (sid) => {
            const [elements, interfaces, requirements] = await Promise.all([
              fetch(`${API}/studies/${sid}/elements`).then(r => r.json()),
              fetch(`${API}/studies/${sid}/interfaces`).then(r => r.json()),
              fetch(`${API}/requirements/tree?study_id=${sid}`).then(r => r.json()),
            ])
            const blob = new Blob([JSON.stringify({ studyId: sid, elements, interfaces, requirements }, null, 2)], { type: 'application/json' })
            const a = document.createElement('a'); a.href = URL.createObjectURL(blob)
            a.download = `SpaceCDF_Full_${sid}.json`; a.click(); URL.revokeObjectURL(a.href)
          },
        },
        { id: 'interfaces-csv', label: 'Interface Control Document', description: 'All interfaces with types, properties, endpoints', format: 'CSV',
          action: async (sid) => {
            const interfaces = await fetch(`${API}/studies/${sid}/interfaces`).then(r => r.json())
            const elements = await fetch(`${API}/studies/${sid}/elements`).then(r => r.json())
            const nameOf = (id: string) => elements.find((e: any) => e.id === id)?.name || id
            downloadCsv(
              ['Name', 'Type', 'Direction', 'From', 'To', 'Status', 'Label', 'Properties'],
              interfaces.map((i: any) => [i.name, i.interface_type, i.direction || '', nameOf(i.from_element_id), nameOf(i.to_element_id), i.status || '', i.diagram_label || '', JSON.stringify(i.properties || {})]),
              `ICD_${sid}.csv`,
            )
          },
        },
      ],
    },
  ]
}

// ─── Export Panel Component ───

export function ExportPanel({ onClose }: { onClose: () => void }) {
  const studyId = useUIStore(s => s.studyId)
  const [running, setRunning] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const categories = studyId ? buildClientExports(studyId) : []

  const handleExport = async (item: ExportItem) => {
    if (!studyId) return
    setRunning(item.id)
    setError(null)
    setSuccess(null)
    try {
      await item.action(studyId)
      setSuccess(`${item.label} exported`)
      setTimeout(() => setSuccess(null), 3000)
    } catch (e: any) {
      setError(`${item.label}: ${e.message || 'Failed'}`)
    } finally {
      setRunning(null)
    }
  }

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000,
    }}>
      <div style={{
        background: 'var(--bg-secondary)', borderRadius: '8px', border: '1px solid var(--border)',
        padding: '1.5rem', width: 650, maxHeight: '85vh', overflow: 'auto',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem' }}>
          <h2 style={{ fontSize: '1rem', margin: 0 }}>Export Documents & Data</h2>
          <span style={{ flex: 1 }} />
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '1.2rem' }}>×</button>
        </div>
        <div style={{
          display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem',
          padding: '0.3rem 0.5rem', borderRadius: '4px',
          background: 'linear-gradient(90deg, #8B000015, transparent)',
          borderLeft: '3px solid #8B0000',
        }}>
          <span style={{ fontSize: '0.68rem', fontWeight: 600, color: '#8B0000' }}>University of Ottawa</span>
          <span style={{ fontSize: '0.6rem', color: 'var(--text-secondary)' }}>|</span>
          <span style={{ fontSize: '0.6rem', color: 'var(--text-secondary)' }}>SEDTI — Space Exploration & Design Technology Initiative</span>
          <span style={{ flex: 1 }} />
          <span style={{ fontSize: '0.55rem', color: '#CC0000' }}>All documents branded</span>
        </div>

        {error && <div style={{ padding: '0.3rem 0.5rem', background: 'rgba(239,68,68,0.15)', borderRadius: '4px', color: 'var(--danger)', fontSize: '0.72rem', marginBottom: '0.5rem' }}>{error}</div>}
        {success && <div style={{ padding: '0.3rem 0.5rem', background: 'rgba(16,185,129,0.15)', borderRadius: '4px', color: 'var(--success)', fontSize: '0.72rem', marginBottom: '0.5rem' }}>{success}</div>}

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {categories.map(cat => (
            <div key={cat.name}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: cat.color, marginBottom: '0.3rem', textTransform: 'uppercase' }}>
                {cat.name}
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.3rem' }}>
                {cat.items.map(item => (
                  <button
                    key={item.id}
                    onClick={() => handleExport(item)}
                    disabled={running !== null}
                    style={{
                      display: 'flex', flexDirection: 'column', gap: '0.1rem',
                      padding: '0.4rem 0.5rem', borderRadius: '4px', textAlign: 'left',
                      background: 'var(--bg-card)', border: '1px solid var(--border)',
                      color: 'var(--text-primary)', cursor: running ? 'wait' : 'pointer',
                      opacity: running && running !== item.id ? 0.5 : 1,
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                      <span style={{ fontWeight: 600, fontSize: '0.72rem' }}>
                        {running === item.id ? 'Generating...' : item.label}
                      </span>
                      <span style={{
                        fontSize: '0.5rem', padding: '0.05rem 0.2rem', borderRadius: '2px',
                        background: `${cat.color}20`, color: cat.color, fontWeight: 600,
                      }}>
                        {item.format}
                      </span>
                    </div>
                    <span style={{ fontSize: '0.6rem', color: 'var(--text-secondary)' }}>{item.description}</span>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
