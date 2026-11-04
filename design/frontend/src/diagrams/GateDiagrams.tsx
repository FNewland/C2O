/**
 * GateDiagrams — on the gate checklist: the diagrams this gate expects (ECSS product
 * maturity per gate, services/diagrams KINDS) as evidence links, each with what the model
 * still lacks for it. "Open" shows the diagram in the Diagrams tab.
 */
import { useTranslation } from 'react-i18next'
import { useUIStore } from '../stores/uiStore'
import { workbenchLevel } from '../workbench/blockLevels'
import { Button, StatusBadge } from '../components/ui'
import { useDiagramCatalogue, useDiagramNav } from './api'
import { useTx } from './DiagramCanvas'

export function openDiagram(kind: string) {
  useDiagramNav.getState().open(kind)
  const ui = useUIStore.getState()
  if (ui.currentLevel === 4) useUIStore.setState({ currentLevel: workbenchLevel(ui.breadcrumb) })
  ui.setActivePanel(kind === 'budgets' ? 'budget' : 'diagrams')
}

export function GateDiagrams({ studyId, gate }: { studyId: string | null; gate: string }) {
  const { t } = useTranslation()
  const f = useTx()
  const { data } = useDiagramCatalogue(studyId, gate)
  if (!data) return null
  const covers = data.covers ?? [gate]
  const mat: Record<string, string> = { D: t('draft'), B: t('baselined'), U: t('updated') }
  return (
    <section className="mt-3" aria-labelledby={`gd-${gate}`} data-testid="gate-diagrams">
      <h4 id={`gd-${gate}`} className="c2o-reqs__group">{t('Diagrams expected at this gate')}</h4>
      <ul className="list-reset c2o-criteria">
        {data.diagrams.map(d => {
          const m = d.gates.filter(g => covers.includes(g.gate)).map(g => `${g.gate.toUpperCase()} ${mat[g.maturity] ?? g.maturity}`).join(', ')
          const status = d.link ? 'neutral' : d.empty || d.gap_alarm ? 'alarm' : d.gaps ? 'caution' : 'ok'
          return (
            <li key={d.kind} className="c2o-criteria__row">
              <StatusBadge status={status}>{d.link ? t('linked view') : d.empty ? t('empty') : d.gaps ? t('Gaps: {{n}}', { n: d.gaps }) : t('complete')}</StatusBadge>
              <span className="c2o-criteria__q">{f(d.title)}</span>
              <span className="t-12 c-2">{d.top_gaps.map(f).join(' · ')}</span>
              <span className="t-12 c-3 row gap-2 wrap ai-c">
                <span>{t('Expected: {{m}}', { m })}</span>
                <span className="mono">{d.ref}</span>
                <Button size="sm" variant="quiet" onClick={() => openDiagram(d.kind)}>{t('Open diagram')}</Button>
              </span>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
