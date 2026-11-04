/**
 * DiagramsView — the Diagrams tab: the SEMP / ECSS diagram set read from the design model
 * (design rules §3). A catalogue on the left (grouped, with the gates that expect each
 * diagram and how much the model still lacks), the selected diagram on the right. The
 * same models go into the SEMP and IRD Word exports and the diagram document.
 */
import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useUIStore } from '../stores/uiStore'
import { Button, Select, StatusBadge } from '../components/ui'
import { diagramDocUrl, useDiagram, useDiagramCatalogue, useDiagramNav, type CatalogueEntry } from './api'
import { DiagramFigure, GateChips } from './DiagramFigure'
import { useTx } from './DiagramCanvas'
import * as S3 from '../viz/stack3d.js'
import './diagrams.css'

// English text is the i18n key: catalogue filter.
const GATE_FILTERS: Record<string, string> = { '': 'All gates', mdr: 'MDR', prr: 'PRR', srr: 'SRR', pdr: 'PDR' }

function Stack3D({ studyId }: { studyId: string }) {
  const { t } = useTranslation()
  const host = useRef<HTMLDivElement>(null)
  const [err, setErr] = useState<string | null>(null)
  useEffect(() => {
    let view: { destroy(): void } | null = null
    let dead = false
    fetch(`/api/studies/${encodeURIComponent(studyId)}/stack/geometry?which=current`)
      .then(r => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then(geometry => {
        if (dead || !host.current) return
        view = S3.mount(host.current, {
          t: (en: string, vars?: Record<string, unknown>) => t(en, vars as Record<string, string>) as string,
          geometry, mode: 'deployed', exploded: 0.35, height: 460, onFallback: () => setErr(t('3D view needs WebGL.')),
        })
      })
      .catch(() => setErr(t('No stack layout to show in 3D yet.')))
    return () => { dead = true; view?.destroy() }
  }, [studyId, t])
  return err ? <p className="t-12 c-3">{err}</p> : <div ref={host} className="c2o-dgm__3d" />
}

function EntryRow({ e, active, onPick }: { e: CatalogueEntry; active: boolean; onPick: () => void }) {
  const f = useTx()
  const { t } = useTranslation()
  const status = e.link ? 'neutral' : e.empty || e.gap_alarm ? 'alarm' : e.gaps ? 'caution' : 'ok'
  return (
    <li>
      <button type="button" className={active ? 'c2o-dgm__entry is-active' : 'c2o-dgm__entry'} aria-current={active || undefined}
        onClick={onPick} data-testid={`dgm-entry-${e.kind}`}>
        <span className="c2o-dgm__entry-title">{f(e.title)}</span>
        <span className="row gap-2 ai-c wrap">
          <GateChips gates={e.gates} />
          {e.link ? <span className="t-12 c-3">{t('linked view')}</span>
            : <StatusBadge status={status}>{e.empty ? t('empty') : e.gaps ? t('Gaps: {{n}}', { n: e.gaps }) : t('complete')}</StatusBadge>}
        </span>
      </button>
    </li>
  )
}

export function DiagramsView() {
  const { t, i18n } = useTranslation()
  const f = useTx()
  const studyId = useUIStore(s => s.studyId)
  const setActivePanel = useUIStore(s => s.setActivePanel)
  const kind = useDiagramNav(s => s.kind)
  const open = useDiagramNav(s => s.open)
  const [gate, setGate] = useState('')
  const [level, setLevel] = useState<'unit' | 'system'>('unit')
  const [focus, setFocus] = useState('')
  const [allTypes, setAllTypes] = useState(false)
  const { data: cat } = useDiagramCatalogue(studyId, gate || null)
  const { data: blockModel } = useDiagram(studyId, kind === 'block' ? 'block' : null, { level: 'system' })
  if (!studyId) return null
  const lang = i18n.language?.startsWith('fr') ? 'fr' : 'en'
  const entries = cat?.diagrams ?? []
  const groups: { id: string; label: string; items: CatalogueEntry[] }[] = []
  for (const e of entries) {
    let g = groups.find(x => x.id === e.group)
    if (!g) { g = { id: e.group, label: f(e.group_label), items: [] }; groups.push(g) }
    g.items.push(e)
  }
  const current = entries.find(e => e.kind === kind)
  const opts = kind === 'block' ? { level, focus: focus || undefined, types: allTypes ? 'all' : undefined }
    : kind === 'n2' ? { level } : {}
  const subsystems = blockModel?.options?.subsystems ?? []
  const pick = (k: string) => { open(k); document.getElementById('act-panel')?.scrollTo({ top: 0 }) }
  return (
    <div className="c2o-dgmv">
      <nav className="c2o-dgmv__cat" aria-label={t('Diagram catalogue')}>
        <label className="t-12 c-3 stack gap-1">
          {t('Expected at')}
          <Select dense value={gate} onChange={e => setGate(e.target.value)}>
            {Object.entries(GATE_FILTERS).map(([k, v]) => <option key={k} value={k}>{t(v)}</option>)}
          </Select>
        </label>
        {groups.map(g => (
          <section key={g.id}>
            <h3 className="c2o-dgmv__group">{g.label}</h3>
            <ul className="list-reset stack gap-1">
              {g.items.map(e => <EntryRow key={e.kind} e={e} active={e.kind === kind} onPick={() => pick(e.kind)} />)}
            </ul>
          </section>
        ))}
        <div className="stack gap-1 mt-3">
          <span className="t-12 c-3">{t('Word documents with these diagrams')}</span>
          <a className="c2o-btn c2o-btn--sm" href={diagramDocUrl(studyId, 'all', lang)} download>{t('All diagrams (DOCX)')}</a>
          <a className="c2o-btn c2o-btn--sm" href={`/api/exports/docx/semp?study_id=${encodeURIComponent(studyId)}`} target="_blank" rel="noreferrer"
            onClick={e => { e.preventDefault(); void download(`/api/exports/docx/semp?study_id=${encodeURIComponent(studyId)}`, `SEMP_${studyId}.docx`) }}>
            {t('SEMP (DOCX)')}</a>
          <a className="c2o-btn c2o-btn--sm" href={`/api/exports/docx/ird?study_id=${encodeURIComponent(studyId)}`}
            onClick={e => { e.preventDefault(); void download(`/api/exports/docx/ird?study_id=${encodeURIComponent(studyId)}`, `IRD_${studyId}.docx`) }}>
            {t('Interface document (DOCX)')}</a>
        </div>
      </nav>
      <div className="c2o-dgmv__main">
        {current?.link ? (
          <div className="stack gap-2 c2o-dgm">
            <h3 className="c2o-dgm__title m-0">{f(current.title)}</h3>
            <GateChips gates={current.gates} />
            <p className="t-12 c-2 m-0">{t('These charts already exist in the Budget tab and in the design-review packs; open them there.')}</p>
            <span><Button size="sm" onClick={() => setActivePanel('budget')}>{t('Open Budget')}</Button></span>
          </div>
        ) : (
          <DiagramFigure key={kind} studyId={studyId} kind={kind} opts={opts}
            extraView={kind === 'stack' ? { label: t('3D'), render: () => <Stack3D studyId={studyId} /> } : undefined}
            toolbar={(kind === 'block' || kind === 'n2') ? (
              <span className="row gap-2 ai-c wrap">
                <Select dense aria-label={t('Level')} value={level} onChange={e => { setLevel(e.target.value as 'unit' | 'system'); setFocus('') }}>
                  <option value="unit">{t('Equipment level')}</option>
                  <option value="system">{t('Subsystem level')}</option>
                </Select>
                {kind === 'block' && level === 'unit' && (
                  <>
                    <Select dense aria-label={t('Drill down')} value={focus} onChange={e => setFocus(e.target.value)}>
                      <option value="">{t('Whole spacecraft')}</option>
                      {subsystems.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                    </Select>
                    <label className="row gap-1 ai-c t-12">
                      <input type="checkbox" checked={allTypes} onChange={e => setAllTypes(e.target.checked)} />
                      {t('Show mechanical and thermal links')}
                    </label>
                  </>
                )}
              </span>
            ) : undefined}
          />
        )}
      </div>
    </div>
  )
}

async function download(url: string, name: string) {
  const r = await fetch(url, { method: 'POST' })
  if (!r.ok) return
  const blob = await r.blob()
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = name
  a.click()
  setTimeout(() => URL.revokeObjectURL(a.href), 2000)
}
