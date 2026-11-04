/**
 * DiagramFigure — one SEMP / ECSS diagram: title, the gates that expect it, the picture
 * (or its table, the accessible alternative), legend, what the model still lacks (gaps,
 * with a button to the tab that closes each), provenance of the selected item, and
 * downloads (SVG / PNG drawn by the server from the same model, in the UI language).
 * Used by the Diagrams tab and embedded in the tabs a diagram belongs to (Electrical, Data).
 */
import { useState, type ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { useUIStore, type ActivityPanel } from '../stores/uiStore'
import { useSeatStore } from '../seats/api'
import { workbenchLevel } from '../workbench/blockLevels'
import { Button, Note, StatusBadge, Tabs, Tag } from '../components/ui'
import { diagramUrl, useDiagram, type DEdge, type DiagramModel, type DiagramOpts, type DNode, type DText } from './api'
import { DiagramCanvas, DiagramLegend, useTx, type Selection } from './DiagramCanvas'
import './diagrams.css'

// English text is the i18n key: provenance sources (services/diagrams/base.py prov()).
const SOURCE_LABEL: Record<string, string> = {
  element: 'Design element', interface: 'Interface (link)', rail: 'Power rail', line: 'Power line', bus: 'Data bus',
  node: 'Bus node', mode: 'Mode', transition: 'Mode transition', function: 'Function', requirement: 'Requirement',
  thermal_closure: 'Thermal closure (derived)', stack: 'Stack layout', kb: 'Knowledge base', conops: 'ConOps',
  template: 'C2O template', derived: 'Derived', parameter: 'Design parameter',
}
// English text is the i18n key: tabs a gap's fix opens.
const FIX_LABEL: Record<string, string> = {
  blocks: 'Open Blocks', interfaces: 'Open Interfaces', electrical: 'Open Electrical', data: 'Open Data',
  modes: 'Open Modes', functions: 'Open Functions', requirements: 'Open Requirements', spacecraft: 'Open Spacecraft',
  analyses: 'Open Analyses', ground: 'Open Analyses', conops: 'Open Modes', vv: 'Open V&V', risks: 'Open V&V',
}
const FIX_PANEL: Record<string, ActivityPanel> = {
  blocks: 'blocks', interfaces: 'interfaces', electrical: 'electrical', data: 'data', modes: 'modes', functions: 'functions',
  requirements: 'requirements', spacecraft: 'spacecraft', analyses: 'analyses', ground: 'analyses', conops: 'modes',
}

export function openFix(fix: string) {
  const ui = useUIStore.getState()
  if (fix === 'vv' || fix === 'risks') {
    useSeatStore.getState().openVV(fix === 'risks' ? 'risks' : null)
    ui.goToLevel(4)
    return
  }
  const p = FIX_PANEL[fix]
  if (!p) return
  if (ui.currentLevel === 4) useUIStore.setState({ currentLevel: workbenchLevel(ui.breadcrumb) })
  ui.setActivePanel(p)
}

const GAP_STATUS = { alarm: 'alarm', warn: 'caution', info: 'info' } as const

export function GateChips({ gates }: { gates: { gate: string; maturity: string }[] }) {
  const { t } = useTranslation()
  const mat: Record<string, string> = { D: t('draft'), B: t('baselined'), U: t('updated') }
  return (
    <span className="row gap-1 wrap">
      {gates.map(g => (
        <Tag key={g.gate} mono title={t('Expected at {{gate}}: {{m}}', { gate: g.gate.toUpperCase(), m: mat[g.maturity] ?? g.maturity })}>
          {g.gate.toUpperCase()} {g.maturity}
        </Tag>
      ))}
    </span>
  )
}

function Provenance({ sel, model }: { sel: Selection; model: DiagramModel }) {
  const { t } = useTranslation()
  const f = useTx()
  if (!sel) return <p className="t-12 c-3 m-0">{t('Select a block or a link to see where it comes from.')}</p>
  const it = sel.item as DNode & DEdge
  const p = it.prov
  const name = sel.kind === 'edge'
    ? `${f(model.nodes.find(n => n.id === it.from)?.label) || it.from} → ${f(model.nodes.find(n => n.id === it.to)?.label) || it.to}`
    : f(it.label) || f((it as DNode).title) || it.id
  return (
    <dl className="c2o-dgm__prov t-12">
      <dt>{t('Selected')}</dt><dd>{name}{it.type && sel.kind === 'edge' ? ` · ${t(it.type === 'electrical_signal' ? 'Discrete signal' : it.type.charAt(0).toUpperCase() + it.type.slice(1))}` : ''}</dd>
      <dt>{t('Source')}</dt><dd>{t(SOURCE_LABEL[p.source] ?? 'Derived')}{p.ref ? <span className="mono c-3"> {p.ref.length > 40 ? p.ref.slice(0, 40) + '…' : p.ref}</span> : null}</dd>
      {p.origin && <><dt>{t('Origin')}</dt><dd className="mono">{p.origin}</dd></>}
      {p.status && <><dt>{t('Status')}</dt><dd>{t(p.status)}</dd></>}
      {p.note && <><dt>{t('Note')}</dt><dd>{p.note}</dd></>}
    </dl>
  )
}

function DataTableView({ model }: { model: DiagramModel }) {
  const f = useTx()
  const { t } = useTranslation()
  if (!model.table.rows.length) return <p className="t-12 c-3">{t('No rows.')}</p>
  return (
    <div className="c2o-dgm__table-wrap">
      <table className="c2o-dgm__table">
        <caption className="sr-only">{f(model.title)}</caption>
        <thead><tr>{model.table.columns.map((c, i) => <th key={i} scope="col">{f(c)}</th>)}</tr></thead>
        <tbody>{model.table.rows.map((r, i) => <tr key={i}>{r.map((c, j) => <td key={j}>{f(c as DText)}</td>)}</tr>)}</tbody>
      </table>
    </div>
  )
}

export function GapList({ model, compact }: { model: DiagramModel; compact?: boolean }) {
  const { t } = useTranslation()
  const f = useTx()
  if (!model.gaps.length) return <p className="t-12 c-ok m-0">{t('Nothing missing for this diagram.')}</p>
  return (
    <ul className="list-reset stack gap-1 c2o-dgm__gaps">
      {model.gaps.map((g, i) => (
        <li key={i} className="row gap-2 ai-c wrap">
          <StatusBadge status={GAP_STATUS[g.severity] ?? 'info'}>{f(g.message)}</StatusBadge>
          {!compact && g.fix && FIX_LABEL[g.fix] && (
            <Button size="sm" variant="quiet" onClick={() => openFix(g.fix!)}>{t(FIX_LABEL[g.fix])}</Button>
          )}
        </li>
      ))}
    </ul>
  )
}

export function DiagramFigure({ studyId, kind, opts = {}, compact, toolbar, extraView }: {
  studyId: string | null; kind: string; opts?: DiagramOpts; compact?: boolean; toolbar?: ReactNode
  extraView?: { label: string; render: () => ReactNode }
}) {
  const { t, i18n } = useTranslation()
  const f = useTx()
  const { data: model, isLoading, isError } = useDiagram(studyId, kind, opts)
  const [view, setView] = useState<'diagram' | 'table' | 'extra'>('diagram')
  const [zoom, setZoom] = useState(1)
  const [sel, setSel] = useState<Selection>(null)
  if (!studyId) return null
  if (isLoading) return <p className="t-12 c-3">{t('Loading diagram…')}</p>
  if (isError || !model) return <Note tone="alarm">{t('The diagram could not be loaded.')}</Note>
  const lang = i18n.language?.startsWith('fr') ? 'fr' : 'en'
  const pct = Math.round(model.completeness.score * 100)
  const items: { id: 'diagram' | 'table' | 'extra'; label: string }[] = [
    { id: 'diagram', label: t('Diagram') }, { id: 'table', label: t('Table') },
  ]
  if (extraView) items.push({ id: 'extra', label: extraView.label })
  return (
    <figure className={compact ? 'c2o-dgm c2o-dgm--compact m-0' : 'c2o-dgm m-0'} data-testid={`diagram-${kind}`}>
      <header className="c2o-dgm__head">
        <div className="stack gap-1">
          <h3 className="c2o-dgm__title m-0">{f(model.title)}</h3>
          {model.subtitle && <p className="t-12 c-2 m-0">{f(model.subtitle)}</p>}
          <span className="row gap-2 ai-c wrap t-12 c-3">
            <GateChips gates={model.gates} />
            <span title={t('Share of the expected content the model provides')}>{t('{{p}} % complete', { p: pct })}</span>
            <span className="mono">{model.ref}</span>
          </span>
        </div>
        <div className="row gap-2 ai-c wrap c2o-dgm__tools">
          {toolbar}
          <Tabs idBase={`dgm-${kind}`} label={t('View')} value={view} onChange={setView} items={items} variant="segmented" />
          {view === 'diagram' && (
            <span className="row gap-1" role="group" aria-label={t('Zoom')}>
              <Button size="sm" variant="quiet" onClick={() => setZoom(z => Math.max(0.4, +(z - 0.2).toFixed(1)))} aria-label={t('Zoom out')}>−</Button>
              <Button size="sm" variant="quiet" onClick={() => setZoom(1)}>{Math.round(zoom * 100)} %</Button>
              <Button size="sm" variant="quiet" onClick={() => setZoom(z => Math.min(2.5, +(z + 0.2).toFixed(1)))} aria-label={t('Zoom in')}>+</Button>
            </span>
          )}
          <a className="c2o-btn c2o-btn--sm" href={diagramUrl(studyId, kind, 'svg', opts, lang)} download>{t('SVG')}</a>
          <a className="c2o-btn c2o-btn--sm" href={diagramUrl(studyId, kind, 'png', opts, lang)} download>{t('PNG')}</a>
        </div>
      </header>
      {model.notes?.map((n, i) => <p key={i} className="t-12 c-3 m-0">{f(n)}</p>)}
      {view === 'diagram' && (
        <>
          <div className="c2o-dgm__canvas" tabIndex={0} aria-label={t('Diagram, scrollable')}>
            <DiagramCanvas model={model} zoom={zoom} selectedId={(sel?.item as { id?: string } | undefined)?.id ?? null}
              onSelect={s => setSel(s)} />
          </div>
          <DiagramLegend items={model.legend} />
        </>
      )}
      {view === 'table' && <DataTableView model={model} />}
      {view === 'extra' && extraView?.render()}
      <div className={compact ? 'c2o-dgm__foot c2o-dgm__foot--compact' : 'c2o-dgm__foot'}>
        <section aria-label={t('What the model still lacks')}>
          <h4 className="c2o-dgm__h4">{t('What the model still lacks')}</h4>
          <GapList model={model} compact={compact} />
        </section>
        {!compact && (
          <section aria-label={t('Provenance')}>
            <h4 className="c2o-dgm__h4">{t('Provenance')}</h4>
            <Provenance sel={sel} model={model} />
            {model.sources.length > 0 && <p className="t-12 c-3 m-0 mt-2">{t('Sources: {{s}}', { s: model.sources.join(', ') })}</p>}
          </section>
        )}
      </div>
    </figure>
  )
}
