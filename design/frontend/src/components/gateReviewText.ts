/**
 * Gate Review (ruling Q23) — English texts the backend sends, listed here so
 * the i18n tool extracts them and the panel can render them with t().
 *
 * GATE_QUESTIONS must match the `question:` strings in
 * configs/gate_exit_criteria.yaml, and EVIDENCE_KEYS the EVIDENCE_KEYS tuple
 * in spacecdf_server/services/gate_evaluator.py, character for character
 * (tests/test_services/test_gate_evaluator.py checks both). A text missing
 * here still renders, in English.
 */
import type { TFunction } from 'i18next'
import type { GateCriterion } from './useGateReview'

// English text is the i18n key
export const GATE_QUESTIONS = [
  'Is the mission need clearly defined and justified?',
  'Are the key stakeholders identified with their needs and constraints?',
  'Are mission objectives defined with measurable success criteria?',
  'Have alternative solutions been considered, including non-space options?',
  'Is the selected concept justified against the alternatives?',
  'Is a preliminary Concept of Operations documented?',
  'Has a feasible system concept been identified?',
  'Are preliminary cost and schedule estimates within constraints?',
  'Have initial technical risks been identified?',
  'Is the mission concept compatible with debris mitigation requirements?',
  'Are all mission objectives traced to system requirements?',
  'Are system requirements complete, verifiable, and non-conflicting?',
  'Is the requirements compliance matrix populated?',
  'Have all engineering positions answered their key questions?',
  'Are cross-position conflicts identified and resolved or accepted?',
  'Does the design close within mass, power, and cost budgets?',
  'Is the Verification and Validation approach defined?',
  'Are technology readiness levels acceptable for the target phase?',
  'Has the Systems Engineering Management Plan been baselined?',
  'Is the mission sustainable (debris, EOL, casualty risk)?',
  'Does the preliminary design satisfy all system requirements?',
  'Are interface requirements defined between all subsystems?',
  'Are all subsystem mass, power, and data margins positive?',
  'Has equipment been selected for all critical subsystems?',
  'Is the reliability analysis acceptable?',
]

// English text is the i18n key
export const EVIDENCE_KEYS = [
  'Requires manual assessment',
  'Auto-evaluation not implemented for this criterion',
  'Run the design loop first: {{params}} not available',
  'Problem statement defined',
  'Problem statement is empty',
  '{{n}} stakeholder(s) identified',
  '{{n}} primary objective(s) with measurable criteria',
  '{{n}} alternative(s), including a non-space option',
  '{{n}} alternative(s), no non-space option',
  'Concept selected with rationale',
  'Concept selected, rationale missing',
  'No concept selected',
  'ConOps summary documented',
  'ConOps summary is empty',
  'Mass margin {{mass}}%, power margin {{power}}%',
  'No cost target set',
  'Cost {{cost}} MEUR vs target {{target}} MEUR',
  'Risk analysis run: {{n}} risk(s) identified',
  'Debris compliance score {{score}}/100',
  'No objectives defined',
  '{{traced}}/{{total}} objectives traced to requirements',
  'No requirements defined',
  '{{ok}}/{{total}} requirements have a verification method and a threshold',
  'No requirement threshold can be checked against the design yet',
  '{{met}}/{{total}} checkable requirements met ({{pct}}%)',
  'Mass margin {{mass}}%, power margin {{power}}% (required ≥ {{min}}%)',
  'Sustainability score {{score}}/100; casualty risk compliant',
  'Sustainability score {{score}}/100; casualty risk not compliant',
  '{{n}} requirement(s) not met: {{codes}}',
  'All {{n}} checkable requirements met',
  'No subsystem elements defined',
  '{{ok}}/{{total}} subsystems have at least one component',
  'Reliability {{rel}} vs target {{target}}',
  'All {{required}} expected subsystem links present and reviewed',
  '{{met}}/{{required}} expected subsystem links present; {{suggested}} suggested link(s) not reviewed',
  'Interface rules are invalid',
]

/** Where "Go fix" goes, and what it says, for a criterion. */
export interface FixTarget { tab: string; action: string }

// Navigation tab per criterion id / category (values are tab ids, not text).
const TAB_BY_ID: Record<string, string> = {
  'MCR-EC-01': 'need', 'MCR-EC-02': 'need', 'MCR-EC-03': 'need',
  'MCR-EC-04': 'concept', 'MCR-EC-05': 'concept', 'MCR-EC-06': 'conops', 'MCR-EC-07': 'design',
}
const TAB_BY_CATEGORY: Record<string, string> = {
  mission_need: 'need', alternatives: 'concept', conops: 'conops',
  feasibility: 'design', budgets: 'design', risk: 'design', sustainability: 'design',
  reliability: 'design', equipment: 'design',
  traceability: 'requirements', requirements: 'requirements', verification: 'requirements', design: 'requirements',
  interfaces: 'interfaces',
}

// English text is the i18n key
const ACTION_BY_ID: Record<string, string> = {
  'MCR-EC-01': 'Define the problem statement in the Mission Need step',
  'MCR-EC-02': 'Add stakeholders in the Mission Need step',
  'MCR-EC-03': 'Add measurable criteria to primary objectives',
  'MCR-EC-04': 'Run the Mission Trade analysis in the Concept step',
  'MCR-EC-05': 'Select a preferred alternative in the Concept step',
  'MCR-EC-06': 'Document the ConOps in the ConOps tab',
  'MCR-EC-07': 'Run the design loop to check feasibility, then adjust requirements if margin is negative',
}

// English text is the i18n key
const ACTION_BY_CATEGORY: Record<string, string> = {
  mission_need: 'Complete the Mission Need step',
  alternatives: 'Compare the alternatives in the Concept step',
  conops: 'Document the ConOps in the ConOps tab',
  feasibility: 'Run the design loop and check the budgets',
  budgets: 'Run the design loop and check the budgets',
  risk: 'Run the design loop to update the risk analysis',
  sustainability: 'Run the design loop to evaluate sustainability, check orbit altitude and deorbit plan',
  reliability: 'Run the design loop to update the reliability analysis',
  equipment: 'Select equipment for each subsystem',
  traceability: 'Trace each objective to at least one requirement in the Requirements tab',
  requirements: 'Give each requirement a verification method and a threshold in the Requirements tab',
  verification: 'Review requirement compliance in the Requirements tab',
  design: 'Review requirement compliance in the Requirements tab',
  interfaces: 'Review the Interface Matrix tab and resolve open conflicts',
}

/** Fix target (English action = i18n key) for a criterion, or null when it
 *  maps to no tab: the criterion is then shown without a "Go fix" link. */
export function fixTargetFor(id: string, category: string): FixTarget | null {
  const tab = TAB_BY_ID[id] ?? TAB_BY_CATEGORY[category]
  if (!tab) return null
  return { tab, action: ACTION_BY_ID[id] ?? ACTION_BY_CATEGORY[category] }
}

// English text is the i18n key
export const STATUS_LABEL: Record<string, string> = {
  pass: 'PASS', fail: 'FAIL', advisory: 'ADVISORY', manual: 'REVIEW', not_evaluated: 'N/A',
}

/** Badge kind: a not-met should-pass item reads "advisory"; manual / N/A keep their own badge. */
export function badgeKind(c: GateCriterion): string {
  if (c.status === 'fail' && c.verdict === 'advisory') return 'advisory'
  return c.status
}

/** Backend evidence in the UI language: the English template + params when known. */
export function evidenceText(c: GateCriterion, t: TFunction): string {
  return c.evidence_key ? String(t(c.evidence_key, c.evidence_params || {})) : c.evidence_found
}
