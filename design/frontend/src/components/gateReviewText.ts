/**
 * Gate Review (ruling Q23; profiles and states WP6, Nov 2026) — English texts
 * the backend sends, listed here so the i18n tool extracts them and the panel
 * can render them with t().
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

// English text is the i18n key — PRR (Nov 2026). Kept as a separate table: the i18n
// extractor reads at most 2000 characters of one table literal.
export const GATE_QUESTIONS_PRR = [
  'Is one system concept selected and justified against at least two alternatives?',
  'Is the mission analysis baselined (orbit, lifetime)?',
  'Is the function tree defined?',
  'Is the product tree defined down to subsystems?',
  'Do the mass and power budgets close with the Phase A system margin?',
  'Are the preliminary technical requirements written, with a verification method each?',
  'Is the technology readiness of the selected equipment listed?',
  'Is the model philosophy and verification approach defined?',
  'Is the ground segment identified?',
  'Is the risk register updated for the selected concept?',
  'Is the cost estimate within the target?',
  'Does the orbit meet the debris-mitigation lifetime rules?',
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

// English text is the i18n key — PRR and margin-ladder evidence (Nov 2026; separate table,
// see GATE_QUESTIONS_PRR)
export const EVIDENCE_KEYS_PRR = [
  'Concept selected with rationale; {{n}} alternative(s) considered',
  'Orbit baseline: {{orbit}} {{alt}} km, {{inc}}°, {{life}} year(s)',
  'No orbit baseline',
  '{{n}} function(s) in the function tree',
  '{{systems}} system(s), {{subsystems}} subsystem(s) in the product tree',
  'Mass {{mass}} kg + {{margin}}% system margin = {{total}} kg vs {{limit}} kg; power {{power}} W + {{margin}}% = {{ptotal}} W vs {{avail}} W',
  'No mass target or form factor to check the mass budget against',
  '{{mission}} mission and {{system}} system requirement(s); {{nomethod}} without a verification method',
  '{{rated}}/{{total}} components have a TRL',
  'No components selected yet',
  '{{n}} ground station(s) identified',
  '{{n}} risk(s) in the risk register',
]

// English text is the i18n key — what the Fix link opens (criterion `fix` in
// configs/gate_exit_criteria.yaml: a workbench panel id, or vv:<section>).
export const FIX_LABEL: Record<string, string> = {
  analyses: 'Open Analyses',
  budget: 'Open Budget',
  blocks: 'Open Blocks',
  requirements: 'Open Requirements',
  functions: 'Open Functions',
  interfaces: 'Open Interfaces',
  decide: 'Open Decide',
  'vv:risks': 'Open the risk register',
}

// English text is the i18n key — gate states (services/gate_reviews.py)
export const STATE_LABEL: Record<string, string> = {
  not_ready: 'Not ready', ready: 'Ready for review', under_review: 'Under review',
  passed: 'Passed', reopened: 'Reopened',
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
