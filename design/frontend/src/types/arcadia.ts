/**
 * Arcadia spine types (SCDF-160) — mirrors the server routers
 * functions.py / exchange_items.py / relations.py / parameters.py / exchange.py.
 */

export type ArcadiaLayer = 'OA' | 'SA' | 'LA' | 'PA'
export const ARCADIA_LAYERS: ArcadiaLayer[] = ['OA', 'SA', 'LA', 'PA']
export const LAYER_LABELS: Record<ArcadiaLayer, string> = {
  OA: 'Operational', SA: 'System', LA: 'Logical', PA: 'Physical',
}
export const LAYER_COLORS: Record<ArcadiaLayer, string> = {
  OA: '#f59e0b', SA: '#3b82f6', LA: '#8b5cf6', PA: '#10b981',
}

export interface ElementSummary {
  id: string
  name: string | null
  element_type?: string | null
  subsystem_domain?: string | null
}

export interface FunctionPort {
  id: string
  function_id: string
  name: string
  direction: 'in' | 'out' | string
  exchange_item_ids: string[]
}

export interface FunctionAllocation {
  id: string
  study_id: string
  function_id: string
  element_id: string
  layer: ArcadiaLayer | string
  element: ElementSummary | null
}

export interface FunctionRow {
  id: string
  study_id: string
  parent_id: string | null
  name: string
  description: string
  layer: ArcadiaLayer | string
  function_type: string | null
  level: number
  is_leaf: boolean
  position_responsible: string | null
  external_id: string | null
  external_ids: Record<string, unknown> | null
  version: number
  created_at?: string
  updated_at?: string
}

export interface FunctionNode extends FunctionRow {
  ports: FunctionPort[]
  allocations: FunctionAllocation[]
  children: FunctionNode[]
}

export interface FunctionCreate {
  name: string
  description?: string
  parent_id?: string | null
  layer?: ArcadiaLayer | string
  function_type?: string | null
  level?: number
  is_leaf?: boolean
}

export interface FunctionUpdate {
  version: number
  name?: string
  description?: string
  parent_id?: string | null
  layer?: ArcadiaLayer | string
  function_type?: string | null
  level?: number
  is_leaf?: boolean
}

export interface FunctionalExchange {
  id: string
  study_id: string
  name: string
  from_port_id: string
  to_port_id: string
  exchange_item_ids: string[]
  realized_by_interface_id: string | null
  external_id: string | null
  version: number
}

export interface MigrateLegacyResult {
  study_id: string
  legacy_functions: number
  [count: string]: number | string
}

// ─── Exchange items / ICD ───

export type ExchangeItemKind = 'data' | 'command' | 'power' | 'signal' | 'fluid' | 'mechanical' | 'thermal' | string
export const EXCHANGE_ITEM_KINDS = ['data', 'command', 'power', 'signal', 'fluid', 'mechanical', 'thermal']

export interface ExchangeItem {
  id: string
  study_id: string
  name: string
  kind: ExchangeItemKind
  description: string
  properties: Record<string, unknown>
  external_id: string | null
  external_ids: Record<string, unknown> | null
  version: number
}

export interface ExchangeItemCreate {
  name: string
  kind?: ExchangeItemKind
  description?: string
  properties?: Record<string, unknown>
}

export interface ExchangeItemUpdate {
  version?: number
  name?: string
  kind?: ExchangeItemKind
  description?: string
  properties?: Record<string, unknown>
}

export interface ICDRow {
  interface_id: string
  name: string
  interface_type: string | null
  direction: string | null
  from_element: { id: string | null; name: string | null }
  to_element: { id: string | null; name: string | null }
  interface_properties: Record<string, unknown>
  exchange_item: { id: string; name: string | null; kind: string | null; properties: Record<string, unknown> } | null
}

// ─── Parameters / equations ───

export type ValueSwitch = 'manual' | 'computed' | 'reference'
export const VALUE_SWITCHES: ValueSwitch[] = ['manual', 'computed', 'reference']
export type FormulaKind = 'ref' | 'calc'
export type Provenance = 'manual' | 'formula' | 'column' | 'agent'

export interface ParameterView {
  id: string
  element_id: string
  element_name: string | null
  name: string
  unit: string
  quantity_kind: string
  manual_value: number | null
  computed_value: number | null
  reference_value: number | null
  value_switch: ValueSwitch
  effective_value: number | null
  formula: string | null
  formula_kind: FormulaKind | null
  errors: string[]
  owner_domain: string | null
  provenance: Provenance
  version: number | null
  updated_at: string | null
  /** SCDF-172: set when this row is an override belonging to that option (null = baseline row). */
  option_id?: string | null
}

export interface ParameterUpsert {
  manual_value?: number | null
  reference_value?: number | null
  formula?: string | null
  formula_kind?: FormulaKind | null
  value_switch?: ValueSwitch | null
  owner_domain?: string | null
  unit?: string | null
  quantity_kind?: string | null
  description?: string | null
}

export interface RecomputeResult {
  study_id: string
  parameters: ParameterView[]
  errors: Array<{ element_id: string; name: string; errors: string[] }>
  cycles: Array<Array<{ element_id: string; name: string }>>
}

// ─── Traceability ───

export interface TraceVerification {
  method: string | null
  phase: string | null
  status: string | null
}

export interface TraceElementRef extends ElementSummary {
  relation: string
}

export interface TraceFunctionRef {
  id: string
  name: string | null
  layer: string | null
  relation: string
}

export interface TraceRequirementNode {
  id: string
  code: string | null
  text: string | null
  level: string | null
  status: string | null
  parent_id: string | null
  element_id: string | null
  verification: TraceVerification
  elements: TraceElementRef[]
  functions: TraceFunctionRef[]
  children: TraceRequirementNode[]
}

export interface TraceObjectiveNode {
  id: string
  text: string | null
  priority: string | null
  type: string | null
  measurable_criterion: string | null
  status: string | null
  requirements: TraceRequirementNode[]
}

export interface TraceabilityTreeResponse {
  study_id: string
  objectives: TraceObjectiveNode[]
  unlinked_requirements: TraceRequirementNode[]
  summary: {
    objectives: number
    requirements: number
    requirements_by_level: Record<string, number>
    relations: number
    requirements_traced_to_objectives: number
  }
}

// ─── Exchange (import/export) ───

export interface CapellaImportResult {
  format: 'capella'
  filename: string | null
  study_id: string
  created: Record<string, number>
  updated: Record<string, number>
  warnings: string[]
}

export interface ReqIFImportResult {
  format: 'reqif'
  filename: string | null
  study_id: string
  created: number
  updated: number
  relations_created: number
  warnings: string[]
}

export type ImportResult = CapellaImportResult | ReqIFImportResult

/** WS ChangeEvent types emitted by the spine routers. */
export const ARCADIA_WS_PREFIXES = ['option_', 'function_', 'functions_', 'functional_exchange_', 'exchange_item_', 'interface_exchange_items_', 'relation_', 'realization_', 'parameter_', 'parameters_recomputed', 'model_imported', 'element_updated'] as const

/** WS ChangeEvent types emitted by the SCDF-170 analyses / options / V&V / ground / physics routers (SCDF-178). */
export const ANALYSIS_WS_PREFIXES = ['analysis_started', 'analysis_completed', 'conflict_resolved', 'option_', 'verification_item_', 'ground_station_', 'element_position_'] as const
/** Query keys to invalidate on an ANALYSIS_WS_PREFIXES event. */
export const ANALYSIS_QUERY_KEYS = ['analyses', 'analysis', 'conflicts', 'options', 'option-compare', 'study-parameters', 'element-parameters', 'verification-items', 'ground-stations', 'physics-placement', 'budget', 'escalation'] as const
