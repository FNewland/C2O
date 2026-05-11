/**
 * ExportPanel — All documents, one entry each, multiple format options.
 */
import { useState } from 'react'
import { useUIStore } from '../stores/uiStore'

const API = '/api'

interface DocExport {
  id: string
  label: string
  description: string
  formats: Array<{ fmt: string; label: string; action: (sid: string) => Promise<void> }>
}

interface DocCategory { name: string; color: string; docs: DocExport[] }

async function dl(url: string, filename: string, method = 'POST') {
  const res = await fetch(url, { method })
  if (!res.ok) throw new Error(`${res.status}`)
  const blob = await res.blob()
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = filename; a.click(); URL.revokeObjectURL(a.href)
}
async function dlJson(url: string, filename: string, method = 'POST') {
  const res = await fetch(url, { method })
  if (!res.ok) throw new Error(`${res.status}`)
  const data = await res.json()
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = filename; a.click(); URL.revokeObjectURL(a.href)
}
async function dlCsv(headers: string[], rows: string[][], filename: string) {
  const csv = [headers.join(','), ...rows.map(r => r.map(c => `"${(c||'').replace(/"/g,'""')}"`).join(','))].join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = filename; a.click(); URL.revokeObjectURL(a.href)
}

function buildExports(sid: string): DocCategory[] {
  return [
    { name: 'Design Reviews', color: '#3b82f6', docs: [
      { id: 'srr', label: 'SRR Document Pack', description: 'System Requirements Review', formats: [
        { fmt: 'ZIP', label: 'ZIP', action: () => dl(`${API}/exports/docs/${sid}?review=srr&fmt=zip`, `SRR_${sid}.zip`) },
      ]},
      { id: 'pdr', label: 'PDR Document Pack', description: 'Preliminary Design Review', formats: [
        { fmt: 'ZIP', label: 'ZIP', action: () => dl(`${API}/exports/docs/${sid}?review=pdr&fmt=zip`, `PDR_${sid}.zip`) },
      ]},
      { id: 'cdr', label: 'CDR Document Pack', description: 'Critical Design Review', formats: [
        { fmt: 'ZIP', label: 'ZIP', action: () => dl(`${API}/exports/docs/${sid}?review=cdr&fmt=zip`, `CDR_${sid}.zip`) },
      ]},
    ]},
    { name: 'Systems Engineering', color: '#8b5cf6', docs: [
      { id: 'semp', label: 'SEMP', description: 'Systems Engineering Management Plan', formats: [
        { fmt: 'DOCX', label: 'DOCX', action: () => dl(`${API}/exports/docx/semp?study_id=${sid}`, `SEMP_${sid}.docx`) },
        { fmt: 'JSON', label: 'JSON', action: () => dlJson(`${API}/ecss/dids/semp/generate?study_id=${sid}`, `SEMP_${sid}.json`) },
      ]},
      { id: 'mrd', label: 'Mission Requirements Document', description: 'Mission needs, stakeholders, objectives, requirements', formats: [
        { fmt: 'DOCX', label: 'DOCX', action: () => dl(`${API}/exports/docx/mrd?study_id=${sid}`, `MRD_${sid}.docx`) },
      ]},
      { id: 'conops', label: 'Concept of Operations', description: 'Modes, phases, orbit, ground stations, data flow', formats: [
        { fmt: 'DOCX', label: 'DOCX', action: () => dl(`${API}/exports/docx/conops?study_id=${sid}`, `ConOps_${sid}.docx`) },
      ]},
      { id: 'bom', label: 'Bill of Materials', description: 'All components with mass, power, cost, TRL', formats: [
        { fmt: 'XLSX', label: 'XLSX', action: async () => {
          const elements = await fetch(`${API}/studies/${sid}/elements`).then(r => r.json())
          const comps = elements.filter((e: any) => e.element_type === 'component')
          dlCsv(['Name','Domain','Mass (kg)','Power (W)','Cost (kEUR)','TRL','Manufacturer','Qty','KB ID'],
            comps.map((c: any) => [c.name,c.subsystem_domain||'',String(c.mass_kg||''),String(c.power_avg_w||''),String(c.cost_recurring_keur||''),String(c.trl||''),c.manufacturer||'',String(c.quantity||1),c.kb_component_id||'']),
            `BOM_${sid}.csv`)
        }},
        { fmt: 'JSON', label: 'JSON', action: async () => {
          const elements = await fetch(`${API}/studies/${sid}/elements`).then(r => r.json())
          const blob = new Blob([JSON.stringify(elements.filter((e: any) => e.element_type === 'component'), null, 2)], { type: 'application/json' })
          const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `BOM_${sid}.json`; a.click()
        }},
      ]},
    ]},
    { name: 'Verification & Compliance', color: '#10b981', docs: [
      { id: 'vv', label: 'V&V Matrix', description: 'Requirements verification matrix', formats: [
        { fmt: 'XLSX', label: 'XLSX', action: async () => {
          const reqs = await fetch(`${API}/requirements/tree?study_id=${sid}`).then(r => r.json())
          dlCsv(['Code','Level','Text','Type','V&V Method','Status','Element'],
            reqs.map((r: any) => [r.code||'',r.level,r.text,r.rationale||'',r.verification_method||'',r.status,r.element_id||'']),
            `VV_Matrix_${sid}.csv`)
        }},
      ]},
      { id: 'compliance', label: 'ECSS Compliance Matrix', description: 'Standard-by-standard compliance', formats: [
        { fmt: 'JSON', label: 'JSON', action: () => dlJson(`${API}/compliance/${sid}`, `ECSS_Compliance_${sid}.json`, 'GET') },
      ]},
      { id: 'margins', label: 'Margin Status Report', description: 'Mass, power, cost margins vs ECSS thresholds', formats: [
        { fmt: 'JSON', label: 'JSON', action: () => dlJson(`${API}/ecss/margins/${sid}`, `Margins_${sid}.json`, 'GET') },
      ]},
      { id: 'rsssa', label: 'RSSSA Licence Application', description: 'Remote Sensing Space Systems Act filing', formats: [
        { fmt: 'DOCX', label: 'DOCX', action: () => dl(`${API}/exports/rsssa/${sid}?fmt=docx`, `RSSSA_${sid}.docx`) },
        { fmt: 'JSON', label: 'JSON', action: () => dlJson(`${API}/exports/rsssa/${sid}`, `RSSSA_${sid}.json`) },
      ]},
      { id: 'launch-icd', label: 'Launch ICD', description: 'Launch Interface Control Document', formats: [
        { fmt: 'DOCX', label: 'DOCX', action: () => dl(`${API}/exports/launch-icd/${sid}?fmt=docx`, `Launch_ICD_${sid}.docx`) },
        { fmt: 'JSON', label: 'JSON', action: () => dlJson(`${API}/exports/launch-icd/${sid}`, `Launch_ICD_${sid}.json`) },
      ]},
      { id: 'deorbit', label: 'Deorbit & Debris Compliance', description: 'Orbital lifetime, casualty risk, passivation', formats: [
        { fmt: 'DOCX', label: 'DOCX', action: () => dl(`${API}/exports/deorbit/${sid}?fmt=docx`, `Deorbit_${sid}.docx`) },
        { fmt: 'JSON', label: 'JSON', action: () => dlJson(`${API}/exports/deorbit/${sid}`, `Deorbit_${sid}.json`) },
      ]},
    ]},
    { name: 'Technical Models', color: '#f59e0b', docs: [
      { id: 'thermal', label: 'Thermal Design Report', description: 'Thermal balance, radiator sizing, component temps', formats: [
        { fmt: 'DOCX', label: 'DOCX', action: () => dl(`${API}/exports/thermal-report/${sid}?fmt=docx`, `Thermal_${sid}.docx`) },
        { fmt: 'XLSX', label: 'XLSX', action: async () => {
          const elements = await fetch(`${API}/studies/${sid}/elements`).then(r => r.json())
          const rows = elements.filter((e: any) => e.power_avg_w || e.subsystem_domain === 'thermal')
          dlCsv(['Name','Type','Domain','Power Avg (W)','Power Peak (W)','Mass (kg)'],
            rows.map((e: any) => [e.name,e.element_type,e.subsystem_domain||'',String(e.power_avg_w||0),String(e.power_peak_w||0),String(e.mass_kg||0)]),
            `Thermal_Model_${sid}.csv`)
        }},
        { fmt: 'JSON', label: 'JSON', action: () => dlJson(`${API}/exports/thermal-report/${sid}`, `Thermal_${sid}.json`) },
      ]},
      { id: 'structural', label: 'Structural Model Data', description: 'Mass breakdown, dimensions, CoG inputs', formats: [
        { fmt: 'XLSX', label: 'XLSX', action: async () => {
          const elements = await fetch(`${API}/studies/${sid}/elements`).then(r => r.json())
          dlCsv(['Name','Type','Domain','Mass (kg)','Qty','Total Mass (kg)','Dimensions'],
            elements.filter((e: any) => e.mass_kg).map((e: any) => [e.name,e.element_type,e.subsystem_domain||'',String(e.mass_kg),String(e.quantity||1),String((e.mass_kg||0)*(e.quantity||1)),JSON.stringify(e.dimensions_mm||[])]),
            `Structural_${sid}.csv`)
        }},
      ]},
      { id: 'wiring', label: 'Wiring & Interface Data', description: 'All interfaces with properties', formats: [
        { fmt: 'XLSX', label: 'XLSX', action: async () => {
          const [interfaces, elements] = await Promise.all([fetch(`${API}/studies/${sid}/interfaces`).then(r=>r.json()), fetch(`${API}/studies/${sid}/elements`).then(r=>r.json())])
          const n = (id: string) => elements.find((e: any) => e.id === id)?.name || id
          dlCsv(['Name','Type','Direction','From','To','Status','Properties'],
            interfaces.map((i: any) => [i.name,i.interface_type,i.direction||'',n(i.from_element_id),n(i.to_element_id),i.status||'',JSON.stringify(i.properties||{})]),
            `ICD_${sid}.csv`)
        }},
      ]},
      { id: 'fsw', label: 'Flight Software Architecture', description: 'State machine, tasks, memory, TM/TC, FDIR', formats: [
        { fmt: 'JSON', label: 'JSON', action: () => dlJson(`${API}/exports/fsw/${sid}`, `FSW_${sid}.json`) },
      ]},
      { id: 'mbse', label: 'MBSE Model Export', description: 'Functional, logical, physical architecture + traceability', formats: [
        { fmt: 'JSON', label: 'JSON', action: () => dlJson(`${API}/exports/mbse/${sid}`, `MBSE_${sid}.json`) },
      ]},
      { id: 'smo', label: 'Simulator Model Inputs', description: 'Orbit, attitude, power, thermal simulation setup', formats: [
        { fmt: 'JSON', label: 'JSON', action: () => dlJson(`${API}/exports/smo/${sid}`, `Simulator_${sid}.json`) },
      ]},
    ]},
    { name: 'Operations & Test', color: '#06b6d4', docs: [
      { id: 'test-plan', label: 'Test Plan', description: 'AIT/AIV test cases, environmental profile, integration matrix', formats: [
        { fmt: 'DOCX', label: 'DOCX', action: () => dl(`${API}/exports/test-plan/${sid}?fmt=docx`, `Test_Plan_${sid}.docx`) },
        { fmt: 'XLSX', label: 'XLSX', action: () => dl(`${API}/exports/test-plan/${sid}?fmt=xlsx`, `Test_Plan_${sid}.xlsx`) },
        { fmt: 'JSON', label: 'JSON', action: () => dlJson(`${API}/exports/test-plan/${sid}`, `Test_Plan_${sid}.json`) },
      ]},
      { id: 'ops', label: 'Operations Concept', description: 'Ground stations, contact windows, spacecraft fleet', formats: [
        { fmt: 'JSON', label: 'JSON', action: async () => {
          const elements = await fetch(`${API}/studies/${sid}/elements`).then(r => r.json())
          const d = { ground_stations: elements.filter((e: any) => e.segment==='ground' && e.performance?.latitude).map((e: any) => ({name: e.name, ...e.performance})), spacecraft: elements.filter((e: any) => e.segment==='space' && e.element_type==='system').map((e: any) => ({name: e.name, quantity: e.quantity||1})) }
          const blob = new Blob([JSON.stringify(d, null, 2)], {type: 'application/json'})
          const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `Ops_${sid}.json`; a.click()
        }},
      ]},
    ]},
    { name: 'Data Export', color: '#6b7280', docs: [
      { id: 'full', label: 'Full Study Export', description: 'Elements, interfaces, requirements — complete backup', formats: [
        { fmt: 'JSON', label: 'JSON', action: async () => {
          const [elements, interfaces, requirements] = await Promise.all([fetch(`${API}/studies/${sid}/elements`).then(r=>r.json()), fetch(`${API}/studies/${sid}/interfaces`).then(r=>r.json()), fetch(`${API}/requirements/tree?study_id=${sid}`).then(r=>r.json())])
          const blob = new Blob([JSON.stringify({studyId: sid, elements, interfaces, requirements}, null, 2)], {type: 'application/json'})
          const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `SpaceCDF_Full_${sid}.json`; a.click()
        }},
      ]},
    ]},
  ]
}

export function ExportPanel({ onClose }: { onClose: () => void }) {
  const studyId = useUIStore(s => s.studyId)
  const [running, setRunning] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const categories = studyId ? buildExports(studyId) : []

  const run = async (docId: string, label: string, action: (sid: string) => Promise<void>) => {
    if (!studyId) return
    setRunning(docId); setError(null); setSuccess(null)
    try { await action(studyId); setSuccess(`${label} exported`); setTimeout(() => setSuccess(null), 3000) }
    catch (e: any) { setError(`${label}: ${e.message}`) }
    finally { setRunning(null) }
  }

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
      <div style={{ background: 'var(--bg-secondary)', borderRadius: '8px', border: '1px solid var(--border)', padding: '1.5rem', width: 650, maxHeight: '85vh', overflow: 'auto' }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem' }}>
          <h2 style={{ fontSize: '1rem', margin: 0 }}>Export Documents & Data</h2>
          <span style={{ flex: 1 }} />
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '1.2rem' }}>×</button>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', padding: '0.3rem 0.5rem', borderRadius: '4px', background: 'linear-gradient(90deg, #8B000015, transparent)', borderLeft: '3px solid #8B0000' }}>
          <span style={{ fontSize: '0.68rem', fontWeight: 600, color: '#8B0000' }}>University of Ottawa</span>
          <span style={{ fontSize: '0.6rem', color: 'var(--text-secondary)' }}>| SEDTI — All documents branded</span>
        </div>

        {error && <div style={{ padding: '0.3rem 0.5rem', background: 'rgba(239,68,68,0.15)', borderRadius: '4px', color: 'var(--danger)', fontSize: '0.72rem', marginBottom: '0.5rem' }}>{error}</div>}
        {success && <div style={{ padding: '0.3rem 0.5rem', background: 'rgba(16,185,129,0.15)', borderRadius: '4px', color: 'var(--success)', fontSize: '0.72rem', marginBottom: '0.5rem' }}>{success}</div>}

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {categories.map(cat => (
            <div key={cat.name}>
              <div style={{ fontSize: '0.7rem', fontWeight: 700, color: cat.color, marginBottom: '0.25rem', textTransform: 'uppercase' }}>{cat.name}</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                {cat.docs.map(doc => (
                  <div key={doc.id} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', padding: '0.35rem 0.5rem', borderRadius: '4px', background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 600, fontSize: '0.72rem' }}>{doc.label}</div>
                      <div style={{ fontSize: '0.58rem', color: 'var(--text-secondary)' }}>{doc.description}</div>
                    </div>
                    <div style={{ display: 'flex', gap: '0.2rem', flexShrink: 0 }}>
                      {doc.formats.map(f => (
                        <button key={f.fmt} onClick={() => run(doc.id + f.fmt, doc.label, f.action)}
                          disabled={running !== null}
                          style={{
                            padding: '0.2rem 0.4rem', fontSize: '0.55rem', fontWeight: 700, borderRadius: '3px',
                            background: f.fmt === 'DOCX' ? 'rgba(59,130,246,0.15)' : f.fmt === 'XLSX' ? 'rgba(16,185,129,0.15)' : f.fmt === 'ZIP' ? 'rgba(245,158,11,0.15)' : 'var(--bg-secondary)',
                            color: f.fmt === 'DOCX' ? 'var(--accent)' : f.fmt === 'XLSX' ? 'var(--success)' : f.fmt === 'ZIP' ? 'var(--warning)' : 'var(--text-secondary)',
                            border: 'none', cursor: running ? 'wait' : 'pointer',
                            opacity: running && running !== doc.id + f.fmt ? 0.4 : 1,
                          }}>
                          {running === doc.id + f.fmt ? '...' : f.label}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
