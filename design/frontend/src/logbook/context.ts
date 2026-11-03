/**
 * The context captured automatically with an entry: study, wizard step or
 * workbench tab, product-tree level, element in focus, review gate.
 * Keys follow LOGBOOK_SPEC.md §2 (study_id, step) plus SpaceCDF's own
 * (study_name, tab, level, element, gate, decision).
 */
import { useQuery } from '@tanstack/react-query'
import type { TFunction } from 'i18next'
import { useUIStore } from '../stores/uiStore'
import { useLogbookUI } from './store'
import type { Context } from './api'

export function useAutoContext(): Context {
  const studyId = useUIStore(s => s.studyId)
  const breadcrumb = useUIStore(s => s.breadcrumb)
  const level = useUIStore(s => s.currentLevel)
  const panel = useUIStore(s => s.activePanel)
  const wizardStep = useLogbookUI(s => s.wizardStep)
  const gate = useLogbookUI(s => s.gate)
  const { data: study } = useQuery<{ name?: string; requirements?: { name?: string } } | null>({
    queryKey: ['study', studyId],
    queryFn: () => fetch(`/api/studies/${studyId}`).then(r => (r.ok ? r.json() : null)),
    enabled: !!studyId, staleTime: 30_000,
  })
  const ctx: Context = {}
  if (!studyId) {
    if (wizardStep) ctx.step = `wizard:${wizardStep}`
    return ctx
  }
  ctx.study_id = studyId
  const name = study?.name || study?.requirements?.name
  if (name) ctx.study_name = String(name)
  ctx.level = level
  ctx.tab = level === 4 ? 'vv' : panel
  const el = breadcrumb[breadcrumb.length - 1]
  if (el && level < 4) ctx.element = el.name
  if (gate && level === 4) ctx.gate = gate
  return ctx
}

/** The subset the worksheet matcher uses. */
export function matchContext(ctx: Context): Context {
  const out: Context = {}
  for (const k of ['step', 'tab', 'level', 'gate'] as const) if (ctx[k] != null) out[k] = ctx[k]
  return out
}

// English text is the i18n key: chip labels and values, translated at render time.
const CHIP_LABEL: Record<string, string> = {
  study_name: 'Study', step: 'Step', tab: 'Tab', level: 'Level', element: 'Element', gate: 'Gate', decision: 'On',
  page: 'Page', procedure: 'Procedure', position: 'Position', scenario: 'Scenario',
}
const TAB_LABEL: Record<string, string> = {
  blocks: 'Blocks', spacecraft: 'Spacecraft', budget: 'Budget', requirements: 'Requirements', functions: 'Functions',
  interfaces: 'Interfaces', icd: 'ICD', trace: 'Traceability', decide: 'Decide', analyses: 'Analyses', vv: 'V&V',
}
const STEP_LABEL: Record<string, string> = {
  'wizard:home': 'Start', 'wizard:problem': 'Problem', 'wizard:stakeholders': 'Stakeholders',
  'wizard:alternatives': 'Alternatives', 'wizard:architecture': 'Architecture',
}
/** Keys that are ids for software, shown only through their readable twin. */
export const HIDDEN_KEYS = new Set(['study_id'])

export function chipLabel(key: string, t: TFunction): string {
  return CHIP_LABEL[key] ? t(CHIP_LABEL[key]) : key
}

export function chipValue(key: string, value: Context[string], t: TFunction): string {
  const v = String(value)
  if (key === 'tab' && TAB_LABEL[v]) return t(TAB_LABEL[v])
  if (key === 'step' && STEP_LABEL[v]) return t(STEP_LABEL[v])
  if (key === 'gate') return v.toUpperCase()
  if (key === 'level') return v === '4' ? 'V&V' : v
  return v
}
