/**
 * ExportPanel — All documents, one entry each, multiple format options.
 */
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import { useUIStore } from '../stores/uiStore'
import { ExchangePanel } from '../components/ExchangePanel'
import { getLang } from '../i18n'
import { Button, Dialog, Note } from '../components/ui'
import { SimConfigExportDialog } from './SimConfigExportDialog'
import { saveProjectFile } from './projectFile'
import { LicensingDialog, licensingExportCategory } from './LicensingPanel'

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

/** A review pack the study can export (GET /api/studies/{id}/review-packs). */
export interface ReviewPack { id: string; short: string; name: Record<string, string> | null; covers: string[]; complete: boolean }

const FALLBACK_PACKS: ReviewPack[] = [
  { id: 'mdr', short: 'MDR', name: null, covers: ['mdr'], complete: true },
  { id: 'prr', short: 'PRR', name: null, covers: ['prr'], complete: true },
  { id: 'srr', short: 'SRR', name: null, covers: ['srr'], complete: true },
  { id: 'pdr', short: 'PDR', name: null, covers: ['pdr'], complete: true },
  { id: 'cdr', short: 'CDR', name: null, covers: ['cdr'], complete: false },
  { id: 'qr', short: 'QR', name: null, covers: ['qr'], complete: false },
  { id: 'ar', short: 'AR', name: null, covers: ['ar'], complete: false },
  { id: 'frr', short: 'FRR', name: null, covers: ['frr'], complete: false },
]

function reviewPackDocs(sid: string, t: TFunction, packs: ReviewPack[], docLang: string): DocExport[] {
  const lang = getLang() === 'fr' ? 'fr' : 'en'
  return packs.map(p => {
    const name = p.name ? (p.name[lang] || p.name.en || p.short) : p.short
    const covers = p.covers.map(c => c.toUpperCase()).join(' + ')
    return {
      id: `pack-${p.id}`,
      label: t('{{gate}} review data pack', { gate: p.short }),
      description: p.complete
        ? t('{{name}} ({{covers}}): the documents this review expects, built from the study, with an index of what is still missing', { name, covers })
        : t('{{name}} ({{covers}}): skeleton pack filled from the study; the index lists what later work adds', { name, covers }),
      formats: [
        { fmt: 'ZIP', label: 'ZIP', action: () => dl(`${API}/exports/docs/${sid}?review=${encodeURIComponent(p.id)}&fmt=zip${docLang}`, `${p.short.replace(/[^A-Za-z0-9]+/g, '_')}_${sid}.zip`) },
      ],
    }
  })
}

// Labels and descriptions are display-only (translated); file names and CSV content stay English.
function buildExports(sid: string, t: TFunction, openSimConfig: () => void, packs: ReviewPack[], openLicensing: () => void = () => {}): DocCategory[] {
  // Review packs: headings of the review data package in French when the UI is in French.
  const docLang = getLang() === 'fr' ? '&lang=fr' : ''
  return [
    { name: t('Design Reviews'), color: 'var(--interactive)', docs: [
      ...reviewPackDocs(sid, t, packs, docLang),
      { id: 'review-report', label: t('Review report'), description: t('Criteria with results and evidence, RIDs and actions, chair note, go / no-go and the baseline diff of one review'),
        formats: packs.map(p => ({ fmt: p.short, label: p.short, action: () => dl(`${API}/studies/${sid}/gates/${encodeURIComponent(p.id)}/report?lang=${docLang ? 'fr' : 'en'}`, `Review_report_${p.short.replace(/[^A-Za-z0-9]+/g, '_')}_${sid}.docx`) })) },
      { id: 'trades', label: t('Trade-off report'), description: t('Every trade study with its options, criteria, weights, scores and decision (ECSS-E-ST-10C Annex K)'), formats: [
        { fmt: 'DOCX', label: 'DOCX', action: () => dl(`${API}/studies/${sid}/trades/report?lang=${docLang ? 'fr' : 'en'}`, `Trade_off_report_${sid}.docx`) },
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
      { id: 'ird', label: t('Interface Requirements Document'), description: t('Link cases, power rails and lines, buses and addresses, ICDs and interface requirements, with the diagrams'), formats: [
        { fmt: 'DOCX', label: 'DOCX', action: () => dl(`${API}/exports/docx/ird?study_id=${sid}${docLang}`, `IRD_${sid}.docx`) },
      ]},
      { id: 'ts', label: t('Technical requirements specification'), description: t('Every requirement by type, with its environment section, verification and parents (ECSS-E-ST-10-06C)'), formats: [
        { fmt: 'DOCX', label: 'DOCX', action: () => dl(`${API}/exports/docx/ts?study_id=${sid}${docLang}`, `TS_${sid}.docx`) },
      ]},
      { id: 'mrd', label: t('Mission Requirements Document'), description: t('Mission needs, stakeholders, objectives, requirements'), formats: [
        { fmt: 'DOCX', label: 'DOCX', action: () => dl(`${API}/exports/docx/mrd?study_id=${sid}${docLang}`, `MRD_${sid}.docx`) },
      ]},
      { id: 'conops', label: t('Concept of Operations'), description: t('Modes, phases, contacts, data flow, typical day, flight rules, end-of-life operations'), formats: [
        { fmt: 'DOCX', label: 'DOCX', action: () => dl(`${API}/studies/${sid}/conops/document?lang=${docLang ? 'fr' : 'en'}`, `ConOps_${sid}.docx`) },
      ]},
      { id: 'bom', label: t('Bill of Materials'), description: t('All components with mass, power, cost, TRL'), formats: [
        { fmt: 'XLSX', label: 'XLSX', action: () => dl(`${API}/studies/${sid}/export/bom.xlsx`, `BOM_${sid}.xlsx`, 'GET') },
        { fmt: 'JSON', label: 'JSON', action: async () => {
          const elements = await fetch(`${API}/studies/${sid}/elements`).then(r => r.json())
          const blob = new Blob([JSON.stringify(elements.filter((e: any) => e.element_type === 'component'), null, 2)], { type: 'application/json' })
          const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `BOM_${sid}.json`; a.click()
        }},
      ]},
    ]},
    { name: t('Verification & Compliance'), color: 'var(--status-ok)', docs: [
      { id: 'vv', label: t('V&V Matrix'), description: t('Requirements verification matrix'), formats: [
        { fmt: 'XLSX', label: 'XLSX', action: () => dl(`${API}/studies/${sid}/export/vv.xlsx`, `VV_Matrix_${sid}.xlsx`, 'GET') },
      ]},
      { id: 'vp', label: t('Verification Plan'), description: t('Model philosophy, test matrix, environmental test levels and the verification items by stage'), formats: [
        { fmt: 'DOCX', label: 'DOCX', action: () => dl(`${API}/exports/docx/vp?study_id=${sid}${docLang}`, `VP_${sid}.docx`) },
      ]},
      { id: 'vcd', label: t('Verification Control Document'), description: t('Every verification item by level, with the close-out status (ECSS-E-ST-10-02C)'), formats: [
        { fmt: 'DOCX', label: 'DOCX', action: () => dl(`${API}/studies/${sid}/export/vcd.docx`, `VCD_${sid}.docx`, 'GET') },
      ]},
      { id: 'rtm', label: t('Requirement Traceability Matrix'), description: t('Requirement, method, stage, status and linked elements and functions'), formats: [
        { fmt: 'CSV', label: 'CSV', action: () => dl(`${API}/studies/${sid}/export/rtm.csv`, `RTM_${sid}.csv`, 'GET') },
      ]},
      { id: 'compliance', label: t('ECSS Compliance Matrix'), description: t('Standard-by-standard compliance'), formats: [
        { fmt: 'JSON', label: 'JSON', action: () => dlJson(`${API}/compliance/${sid}`, `ECSS_Compliance_${sid}.json`, 'GET') },
      ]},
      { id: 'margins', label: t('Margin Status Report'), description: t('Mass, power, cost margins vs ECSS thresholds'), formats: [
        { fmt: 'JSON', label: 'JSON', action: () => dlJson(`${API}/ecss/margins/${sid}`, `Margins_${sid}.json`, 'GET') },
      ]},
      { id: 'launch-icd', label: t('Launch ICD'), description: t('Launch Interface Control Document'), formats: [
        { fmt: 'DOCX', label: 'DOCX', action: () => dl(`${API}/exports/launch-icd/${sid}?fmt=docx`, `Launch_ICD_${sid}.docx`) },
        { fmt: 'JSON', label: 'JSON', action: () => dlJson(`${API}/exports/launch-icd/${sid}`, `Launch_ICD_${sid}.json`) },
      ]},
    ]},
    // Regulatory group (agent L, W5.04): licensing inputs, the study-linked licence documents, deorbit
    licensingExportCategory(sid, t, openLicensing),
    { name: t('Technical Models'), color: 'var(--status-caution)', docs: [
      { id: 'thermal', label: t('Thermal Design Report'), description: t('Thermal balance, radiator sizing, component temps'), formats: [
        { fmt: 'DOCX', label: 'DOCX', action: () => dl(`${API}/exports/thermal-report/${sid}?fmt=docx`, `Thermal_${sid}.docx`) },
        { fmt: 'CSV', label: 'CSV', action: async () => {
          const elements = await fetch(`${API}/studies/${sid}/elements`).then(r => r.json())
          const rows = elements.filter((e: any) => e.power_avg_w || e.subsystem_domain === 'thermal')
          dlCsv(['Name','Type','Domain','Power Avg (W)','Power Peak (W)','Mass (kg)'],
            rows.map((e: any) => [e.name,e.element_type,e.subsystem_domain||'',String(e.power_avg_w||0),String(e.power_peak_w||0),String(e.mass_kg||0)]),
            `Thermal_Model_${sid}.csv`)
        }},
        { fmt: 'JSON', label: 'JSON', action: () => dlJson(`${API}/exports/thermal-report/${sid}`, `Thermal_${sid}.json`) },
      ]},
      { id: 'structural', label: t('Structural Model Data'), description: t('Mass breakdown, dimensions, CoG inputs'), formats: [
        { fmt: 'CSV', label: 'CSV', action: async () => {
          const elements = await fetch(`${API}/studies/${sid}/elements`).then(r => r.json())
          dlCsv(['Name','Type','Domain','Mass (kg)','Qty','Total Mass (kg)','Dimensions'],
            elements.filter((e: any) => e.mass_kg).map((e: any) => [e.name,e.element_type,e.subsystem_domain||'',String(e.mass_kg),String(e.quantity||1),String((e.mass_kg||0)*(e.quantity||1)),JSON.stringify(e.dimensions_mm||[])]),
            `Structural_${sid}.csv`)
        }},
      ]},
      { id: 'wiring', label: t('Wiring & Interface Data'), description: t('All interfaces with properties'), formats: [
        { fmt: 'CSV', label: 'CSV', action: async () => {
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
      { id: 'full', label: t('Project file'), description: t('The whole study in one file (the file Load opens): every table, layout, seats, gates, results and your logbook entries'), formats: [
        { fmt: 'JSON', label: 'JSON', action: async () => saveProjectFile(sid) },
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
  const [licensing, setLicensing] = useState(false)
  const [packs, setPacks] = useState<ReviewPack[]>(FALLBACK_PACKS)
  useEffect(() => {
    if (!studyId) return
    let live = true
    fetch(`${API}/studies/${studyId}/review-packs`).then(r => (r.ok ? r.json() : null))
      .then(d => { if (live && d && Array.isArray(d.packs) && d.packs.length) setPacks(d.packs) })
      .catch(() => { /* keep the default list */ })
    return () => { live = false }
  }, [studyId])
  const categories = studyId ? buildExports(studyId, t, () => setSimConfig(true), packs, () => setLicensing(true)) : []

  const run = async (docId: string, label: string, action: (sid: string) => Promise<void>) => {
    if (!studyId) return
    setRunning(docId); setError(null); setSuccess(null)
    try { await action(studyId); setSuccess(t('{{label}} exported', { label })); setTimeout(() => setSuccess(null), 3000) }
    catch (e: any) { setError(t('{{label}}: {{message}}', { label, message: e.message })) }
    finally { setRunning(null) }
  }

  if (simConfig && studyId) return <SimConfigExportDialog studyId={studyId} onClose={() => setSimConfig(false)} />
  if (licensing && studyId) return <LicensingDialog studyId={studyId} onClose={() => setLicensing(false)} />
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
