/**
 * ExportPanel — All documents, one entry each, multiple format options.
 */
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import { useUIStore } from '../stores/uiStore'
import { ExchangePanel } from '../components/ExchangePanel'
import { getLang } from '../i18n'
import { Button, Dialog, Note } from '../components/ui'
import { SimConfigExportDialog } from './SimConfigExportDialog'

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

// Labels and descriptions are display-only (translated); file names and CSV content stay English.
function buildExports(sid: string, t: TFunction, openSimConfig: () => void): DocCategory[] {
  // ECSS review packs: French Markdown templates (templates/fr/) when the UI is in French.
  const docLang = getLang() === 'fr' ? '&lang=fr' : ''
  return [
    { name: t('Design Reviews'), color: 'var(--interactive)', docs: [
      { id: 'srr', label: t('SRR Document Pack'), description: t('System Requirements Review'), formats: [
        { fmt: 'ZIP', label: 'ZIP', action: () => dl(`${API}/exports/docs/${sid}?review=srr&fmt=zip${docLang}`, `SRR_${sid}.zip`) },
      ]},
      { id: 'pdr', label: t('PDR Document Pack'), description: t('Preliminary Design Review'), formats: [
        { fmt: 'ZIP', label: 'ZIP', action: () => dl(`${API}/exports/docs/${sid}?review=pdr&fmt=zip${docLang}`, `PDR_${sid}.zip`) },
      ]},
      { id: 'cdr', label: t('CDR Document Pack'), description: t('Critical Design Review'), formats: [
        { fmt: 'ZIP', label: 'ZIP', action: () => dl(`${API}/exports/docs/${sid}?review=cdr&fmt=zip${docLang}`, `CDR_${sid}.zip`) },
      ]},
    ]},
    { name: t('Systems Engineering'), color: 'var(--cat-2)', docs: [
      { id: 'semp', label: 'SEMP', description: t('Systems Engineering Management Plan'), formats: [
        { fmt: 'DOCX', label: 'DOCX', action: () => dl(`${API}/exports/docx/semp?study_id=${sid}`, `SEMP_${sid}.docx`) },
        { fmt: 'JSON', label: 'JSON', action: () => dlJson(`${API}/ecss/dids/semp/generate?study_id=${sid}`, `SEMP_${sid}.json`) },
      ]},
      { id: 'diagrams', label: t('SEMP / ECSS diagram set'), description: t('Every diagram with its gaps and data table (same as the Diagrams tab)'), formats: [
        { fmt: 'DOCX', label: 'DOCX', action: () => dl(`${API}/studies/${sid}/diagrams-document.docx?set=all${docLang}`, `Diagrams_${sid}.docx`, 'GET') },
      ]},
      { id: 'ird', label: t('Interface Requirements Document'), description: t('Interfaces with the block, N², power, data-bus and RF diagrams'), formats: [
        { fmt: 'DOCX', label: 'DOCX', action: () => dl(`${API}/exports/docx/ird?study_id=${sid}`, `IRD_${sid}.docx`) },
      ]},
      { id: 'mrd', label: t('Mission Requirements Document'), description: t('Mission needs, stakeholders, objectives, requirements'), formats: [
        { fmt: 'DOCX', label: 'DOCX', action: () => dl(`${API}/exports/docx/mrd?study_id=${sid}`, `MRD_${sid}.docx`) },
      ]},
      { id: 'conops', label: t('Concept of Operations'), description: t('Modes, phases, orbit, ground stations, data flow'), formats: [
        { fmt: 'DOCX', label: 'DOCX', action: () => dl(`${API}/exports/docx/conops?study_id=${sid}`, `ConOps_${sid}.docx`) },
      ]},
      { id: 'bom', label: t('Bill of Materials'), description: t('All components with mass, power, cost, TRL'), formats: [
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
    { name: t('Verification & Compliance'), color: 'var(--status-ok)', docs: [
      { id: 'vv', label: t('V&V Matrix'), description: t('Requirements verification matrix'), formats: [
        { fmt: 'XLSX', label: 'XLSX', action: async () => {
          const reqs = await fetch(`${API}/requirements/tree?study_id=${sid}`).then(r => r.json())
          dlCsv(['Code','Level','Text','Type','V&V Method','Status','Element'],
            reqs.map((r: any) => [r.code||'',r.level,r.text,r.rationale||'',r.verification_method||'',r.status,r.element_id||'']),
            `VV_Matrix_${sid}.csv`)
        }},
      ]},
      { id: 'compliance', label: t('ECSS Compliance Matrix'), description: t('Standard-by-standard compliance'), formats: [
        { fmt: 'JSON', label: 'JSON', action: () => dlJson(`${API}/compliance/${sid}`, `ECSS_Compliance_${sid}.json`, 'GET') },
      ]},
      { id: 'margins', label: t('Margin Status Report'), description: t('Mass, power, cost margins vs ECSS thresholds'), formats: [
        { fmt: 'JSON', label: 'JSON', action: () => dlJson(`${API}/ecss/margins/${sid}`, `Margins_${sid}.json`, 'GET') },
      ]},
      { id: 'rsssa', label: t('RSSSA Licence Application'), description: t('Remote Sensing Space Systems Act filing'), formats: [
        { fmt: 'DOCX', label: 'DOCX', action: () => dl(`${API}/exports/rsssa/${sid}?fmt=docx`, `RSSSA_${sid}.docx`) },
        { fmt: 'JSON', label: 'JSON', action: () => dlJson(`${API}/exports/rsssa/${sid}`, `RSSSA_${sid}.json`) },
      ]},
      { id: 'launch-icd', label: t('Launch ICD'), description: t('Launch Interface Control Document'), formats: [
        { fmt: 'DOCX', label: 'DOCX', action: () => dl(`${API}/exports/launch-icd/${sid}?fmt=docx`, `Launch_ICD_${sid}.docx`) },
        { fmt: 'JSON', label: 'JSON', action: () => dlJson(`${API}/exports/launch-icd/${sid}`, `Launch_ICD_${sid}.json`) },
      ]},
      { id: 'deorbit', label: t('Deorbit & Debris Compliance'), description: t('Orbital lifetime, casualty risk, passivation'), formats: [
        { fmt: 'DOCX', label: 'DOCX', action: () => dl(`${API}/exports/deorbit/${sid}?fmt=docx`, `Deorbit_${sid}.docx`) },
        { fmt: 'JSON', label: 'JSON', action: () => dlJson(`${API}/exports/deorbit/${sid}`, `Deorbit_${sid}.json`) },
      ]},
    ]},
    { name: t('Technical Models'), color: 'var(--status-caution)', docs: [
      { id: 'thermal', label: t('Thermal Design Report'), description: t('Thermal balance, radiator sizing, component temps'), formats: [
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
      { id: 'structural', label: t('Structural Model Data'), description: t('Mass breakdown, dimensions, CoG inputs'), formats: [
        { fmt: 'XLSX', label: 'XLSX', action: async () => {
          const elements = await fetch(`${API}/studies/${sid}/elements`).then(r => r.json())
          dlCsv(['Name','Type','Domain','Mass (kg)','Qty','Total Mass (kg)','Dimensions'],
            elements.filter((e: any) => e.mass_kg).map((e: any) => [e.name,e.element_type,e.subsystem_domain||'',String(e.mass_kg),String(e.quantity||1),String((e.mass_kg||0)*(e.quantity||1)),JSON.stringify(e.dimensions_mm||[])]),
            `Structural_${sid}.csv`)
        }},
      ]},
      { id: 'wiring', label: t('Wiring & Interface Data'), description: t('All interfaces with properties'), formats: [
        { fmt: 'XLSX', label: 'XLSX', action: async () => {
          const [interfaces, elements] = await Promise.all([fetch(`${API}/studies/${sid}/interfaces`).then(r=>r.json()), fetch(`${API}/studies/${sid}/elements`).then(r=>r.json())])
          const n = (id: string) => elements.find((e: any) => e.id === id)?.name || id
          dlCsv(['Name','Type','Direction','From','To','Status','Properties'],
            interfaces.map((i: any) => [i.name,i.interface_type,i.direction||'',n(i.from_element_id),n(i.to_element_id),i.status||'',JSON.stringify(i.properties||{})]),
            `ICD_${sid}.csv`)
        }},
      ]},
      { id: 'fsw', label: t('Flight Software Architecture'), description: t('State machine, tasks, memory, TM/TC, FDIR'), formats: [
        { fmt: 'JSON', label: 'JSON', action: () => dlJson(`${API}/exports/fsw/${sid}`, `FSW_${sid}.json`) },
      ]},
      { id: 'mbse', label: t('MBSE Model Export'), description: t('Functional, logical, physical architecture + traceability'), formats: [
        { fmt: 'JSON', label: 'JSON', action: () => dlJson(`${API}/exports/mbse/${sid}`, `MBSE_${sid}.json`) },
      ]},
      { id: 'smo', label: t('Simulator configuration'), description: t('Configuration directory for the EOSAT-1-class simulator, with a readiness checklist'), formats: [
        { fmt: 'ZIP', label: 'ZIP', action: async () => openSimConfig() },
      ]},
    ]},
    { name: t('Operations & Test'), color: 'var(--interactive)', docs: [
      { id: 'test-plan', label: t('Test Plan'), description: t('AIT/AIV test cases, environmental profile, integration matrix'), formats: [
        { fmt: 'DOCX', label: 'DOCX', action: () => dl(`${API}/exports/test-plan/${sid}?fmt=docx`, `Test_Plan_${sid}.docx`) },
        { fmt: 'XLSX', label: 'XLSX', action: () => dl(`${API}/exports/test-plan/${sid}?fmt=xlsx`, `Test_Plan_${sid}.xlsx`) },
        { fmt: 'JSON', label: 'JSON', action: () => dlJson(`${API}/exports/test-plan/${sid}`, `Test_Plan_${sid}.json`) },
      ]},
      { id: 'ops', label: t('Operations Concept'), description: t('Ground stations, contact windows, spacecraft fleet'), formats: [
        { fmt: 'JSON', label: 'JSON', action: async () => {
          const elements = await fetch(`${API}/studies/${sid}/elements`).then(r => r.json())
          const d = { ground_stations: elements.filter((e: any) => e.segment==='ground' && e.performance?.latitude).map((e: any) => ({name: e.name, ...e.performance})), spacecraft: elements.filter((e: any) => e.segment==='space' && e.element_type==='system').map((e: any) => ({name: e.name, quantity: e.quantity||1})) }
          const blob = new Blob([JSON.stringify(d, null, 2)], {type: 'application/json'})
          const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `Ops_${sid}.json`; a.click()
        }},
      ]},
    ]},
    { name: t('Data Export'), color: 'var(--text-3)', docs: [
      { id: 'full', label: t('Full Study Export'), description: t('Elements, interfaces, requirements — complete backup'), formats: [
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

  const { t } = useTranslation()
  const [simConfig, setSimConfig] = useState(false)
  const categories = studyId ? buildExports(studyId, t, () => setSimConfig(true)) : []

  const run = async (docId: string, label: string, action: (sid: string) => Promise<void>) => {
    if (!studyId) return
    setRunning(docId); setError(null); setSuccess(null)
    try { await action(studyId); setSuccess(t('{{label}} exported', { label })); setTimeout(() => setSuccess(null), 3000) }
    catch (e: any) { setError(t('{{label}}: {{message}}', { label, message: e.message })) }
    finally { setRunning(null) }
  }

  if (simConfig && studyId) return <SimConfigExportDialog studyId={studyId} onClose={() => setSimConfig(false)} />
  return (
    <Dialog open title={t('Export Documents & Data')} onClose={onClose} width={680}
      actions={<button type="button" className="c2o-btn" onClick={onClose}>{t('Close')}</button>}>
      <div>
        <p className="t-12 c-2 m-0 mb-3"><span className="w-600 c-1">C2O</span> {t('— from Concept to Orbit. All documents carry the C2O branding.')}</p>

        {error && <Note tone="alarm" role="alert" className="mb-2">{error}</Note>}
        {success && <Note tone="ok" role="status" className="mb-2">{success}</Note>}

        <div className="mb-4">
          <ExchangePanel studyId={studyId} title={t('Model exchange (Capella / ECSS-E-TM-10-25 / ReqIF / SysML v2)')} />
        </div>

        <div className="stack gap-3">
          {categories.map(cat => (
            <div key={cat.name}>
              <h3 className="c2o-panel__title mb-1">{cat.name}</h3>
              <div className="stack gap-0 bt">
                {cat.docs.map(doc => (
                  <div key={doc.id} className="flex ai-c gap-2 py-2 px-2 bb">
                    <div className="grow min0">
                      <div className="w-600 t-12">{doc.label}</div>
                      <div className="t-12 c-2">{doc.description}</div>
                    </div>
                    <div className="flex gap-1 shrink-0">
                      {doc.formats.map(f => (
                        <Button key={f.fmt} size="sm" onClick={() => run(doc.id + f.fmt, doc.label, f.action)}
                          busy={running === doc.id + f.fmt}
                          disabledReason={running !== null && running !== doc.id + f.fmt ? t('Another export is running') : undefined}
                          aria-label={`${doc.label}: ${f.label}`}>
                          <span className="mono">{running === doc.id + f.fmt ? t('Exporting…') : f.label}</span>
                        </Button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </Dialog>
  )
}
