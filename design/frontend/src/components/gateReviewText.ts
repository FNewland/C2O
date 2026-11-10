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
  'Does every requirement below mission level flow down from a parent requirement?',
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
  'No spacecraft mass limit set: enter the target mass in the mission brief',
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

// English text is the i18n key — PDR-EC-02 / SRR-EC-02 interface requirement evidence (design
// rules IF-01, IF-05; separate table, the i18n scanner reads 2000 characters per table)
export const EVIDENCE_KEYS_IRD = [
  'All {{total}} accepted links have approved interface requirements agreed by both parties',
  '{{complete}}/{{total}} accepted links have approved interface requirements agreed by both parties; {{approved}} approved, {{agreed}} agreed',
  '{{n}} interface requirement(s) name no accepted interface',
]

// English text is the i18n key — CDR (Nov 2026, phase 2): questions of gate_exit_criteria.yaml
// phase_c (separate table: the i18n extractor reads at most 2000 characters of one literal)
export const GATE_QUESTIONS_CDR = [
  'Does the detailed design meet every requirement, with its justification?',
  'Are the interface control documents baselined?',
  'Is the TM/TC database complete and consistent?',
  'Does the housekeeping fit the downlink in every mode?',
  'Is every critical failure mode detected and recovered on board?',
  'Are the safe mode and the load-shed table defined?',
  'Are the AOCS mode machine and control parameters defined?',
  'Are the TT&C rate ladder, beacon and command-loss recovery defined?',
  'Are the operations products drafted (organisation, GO/NO-GO, flight rules)?',
  'Do the budgets close with the CDR system margin?',
  'Is the AIV programme ready (test specifications, facilities, model philosophy)?',
]

// English text is the i18n key — CDR evidence (gate_evaluator.py EVIDENCE_KEYS, CDR block)
export const EVIDENCE_KEYS_CDR = [
  'The CDR model is not available',
  'No TM/TC database yet: propose it from the design (CDR model)',
  '{{params}} parameters, {{hk}} HK structures, {{tc}} telecommands, {{events}} events; {{suggested}} suggestion(s) to review, {{alarms}} alarm finding(s)',
  'No rate tier or HK structure to check the downlink budget',
  'Housekeeping fits the downlink in {{ok}}/{{total}} regimes',
  '{{recovered}}/{{critical}} critical failure modes detected and recovered; {{alarms}} FDIR alarm finding(s)',
  'Safe mode and load-shed table defined; {{alarms}} alarm finding(s)',
  'Safe mode or load-shed table missing',
  'No AOCS mode table yet',
]
// English text is the i18n key — CDR evidence, continued (2000-character table limit)
export const EVIDENCE_KEYS_CDR2 = [
  '{{modes}} AOCS mode(s), {{transitions}} transition(s); {{alarms}} alarm and {{cautions}} caution finding(s)',
  'No rate ladder yet',
  '{{tiers}} rate tier(s), command-loss timer {{hours}} h; {{alarms}} alarm finding(s)',
  '{{positions}} position(s), {{gonogo}} GO/NO-GO situation(s), {{rules}} flight rule(s); {{uncovered}} critical telecommand(s) without a GO/NO-GO entry',
  '{{ok}}/{{total}} requirements have a verification method',
]
// English text is the i18n key — requirement baseline evidence (W2.03, W2.05, W1.08: new fields, the one roll-up)
export const EVIDENCE_KEYS_REQ = [
  '{{ok}}/{{total}} requirements have a verification method and a threshold or an acceptance criterion',
  '{{n}} requirement(s) below mission level without a parent',
  'Mass {{mass}} kg + {{margin}}% system margin = {{total}} kg vs {{limit}} kg; orbit-average power {{power}} W ({{ptotal}} W with {{margin}}% margin) vs {{avail}} W generated at end of life',
  'Orbit-average power {{power}} W ({{ptotal}} W with {{pmargin}}% margin) vs {{avail}} W generated at end of life; mass margin {{mass}}%',
]

// English text is the i18n key — W3.05 daily data budget (PDR-EC-06, CDR-EC-04; gate_evaluator.py EVIDENCE_KEYS)
export const GATE_QUESTIONS_HK = [
  'Does the daily data budget (housekeeping + science) close with margin, and do the stores hold the required days?',
  'Does the housekeeping fit the downlink in every mode, does the daily budget close with margin and do the stores hold the required days?',
]
// English text is the i18n key — W3.05 data-budget evidence
export const EVIDENCE_KEYS_HK = [
  'No data budget yet: no mode, no contact plan or no link rate',
  'Daily budget case {{case}}: margin {{margin}} % (required {{required}} %); no HK store sized yet',
  'Daily budget case {{case}}: margin {{margin}} % (required {{required}} %); the stores hold {{days}} days at the worst rate (required {{need}})',
  'Housekeeping fits the downlink in {{ok}}/{{total}} regimes; daily budget case {{case}}: margin {{margin}} % (required {{required}} %); the stores hold {{days}} days (required {{need}})',
]
// English text is the i18n key — QR, AR and FRR (wave 2, W4.09): questions of
// gate_exit_criteria.yaml phase_d_qr, phase_d_ar and phase_e_frr
export const GATE_QUESTIONS_POST_CDR = [
  'Are the RIDs and actions of the earlier reviews closed?',
  'Have the qualification test results been reviewed and accepted by the board?',
  'Are the non-conformances of the qualification campaign closed or waived?',
  'Are the deviations and waivers against the requirements accepted?',
  'Does every requirement have a verification method and a close-out stage?',
  'Has the flight model passed its acceptance tests?',
  'Is the acceptance data package complete (as-built configuration, logbook, waivers)?',
  'Are the non-conformances of the acceptance campaign closed or waived?',
  'Is every verification item closed, or waived with a recorded justification?',
  'Are the licences granted (spectrum, space station, earth stations, remote sensing)?',
  'Are operations ready (procedures validated, team trained, ground segment tested end to end)?',
  'Are the as-built mass properties within the launch interface limits?',
  'Is the spacecraft ready for delivery (launch provider documents accepted, delivery configuration recorded)?',
]
// English text is the i18n key — QR-EC-01 evidence (wave 2, W4.09)
export const EVIDENCE_KEYS_QR = [
  '{{ok}}/{{total}} requirements have a verification method and a close-out stage; without: {{codes}}',
  'All {{total}} requirements have a verification method and a close-out stage',
]

// English text is the i18n key — SRR-EC-04/05/07/08 and the PDR-EC-04 harness allowance (wave 2 integration)
export const EVIDENCE_KEYS_W2B = [
  '{{answered}}/{{total}} must-answer position questions answered by the design; open: {{open}}',
  'All {{total}} must-answer position questions answered by the design',
  'No position questions to check',
  '{{critical}} critical conflict(s) unresolved: {{codes}}',
  'No critical conflict unresolved ({{major}} major, {{other}} other open)',
  'No model philosophy yet: propose the AIT models and test matrix',
  '{{philosophy}} model philosophy: {{models}} model(s), {{tests}} test(s) covering {{reqs}} requirement(s)',
  '{{philosophy}} model philosophy with {{models}} model(s) but no test in the test matrix',
  'Lowest subsystem TRL {{trl}} ({{subsystem}}); {{low}} subsystem(s) below TRL {{min}}: {{names}}',
  'Every subsystem at TRL {{min}} or above (lowest: {{subsystem}} at TRL {{trl}})',
  'No component has a TRL yet',
  '{{ok}}/{{total}} subsystems have at least one component or a mass allowance',
]

// English text is the i18n key — wave 3 (3.R4/3.R5) criteria questions
export const GATE_QUESTIONS_W3 = [
  'Are the systems-engineering deliverables of this phase ready?',
  'Is every leaf function covered by a requirement, and does every space subsystem have requirements?',
  'Does every primary objective have a validation activity performed by a stakeholder?',
  'Are the mass and power allocations agreed by their owners, covered by requirements and within the limits with the system margin?',
  'Are the in-orbit validation activities planned?',
]

// English text is the i18n key — wave 3 evidence (1/4)
export const EVIDENCE_KEYS_W3_1 = [
  'All {{total}} ICDs under issue control at Issue A and signed by both seats',
  '{{agreed}}/{{total}} ICDs under issue control at Issue A and signed by both seats; not agreed: {{unsigned}}',
  'All {{total}} trades due by the SRR decided in the Decide panel',
  '{{recorded}}/{{total}} trades due by the SRR decided in the Decide panel; open: {{open}}',
  'No trade due by the SRR recorded in the Decide panel',
  'All {{total}} deliverables of the gate ready',
  '{{ok}}/{{total}} deliverables of the gate ready; missing: {{names}}',
  'No deliverables listed for this gate',
]

// English text is the i18n key — wave 3 evidence (2/4)
export const EVIDENCE_KEYS_W3_2 = [
  'The deliverables check is not available yet',
  'All {{total}} primary objectives have a validation activity performed by a stakeholder',
  '{{ok}}/{{total}} primary objectives have a validation activity performed by a stakeholder; without: {{ids}}',
  'All {{total}} primary objectives have an in-orbit validation activity planned',
  '{{ok}}/{{total}} primary objectives have an in-orbit validation activity planned; without: {{ids}}',
  'No in-orbit validation activity planned',
  'The validation plan is not available yet',
]

// English text is the i18n key — wave 3 evidence (3/4)
export const EVIDENCE_KEYS_W3_3 = [
  'Allocations with the system margin exceed the limit: {{mass}} kg vs {{mlimit}} kg; {{power}} W vs {{plimit}} W',
  'Lines not agreed by their owner: {{names}}; {{mass}} kg vs {{mlimit}} kg; {{power}} W vs {{plimit}} W',
  'Mass and power lines agreed for {{n}} subsystem(s); {{mass}} ≤ {{mlimit}} kg; {{power}} ≤ {{plimit}} W',
  'No allocation ledger lines yet',
  'No mass or power line for: {{names}}',
  '{{n}} allocation line(s) without a covering requirement: {{names}}',
  'No function tree yet',
]

// English text is the i18n key — wave 3 evidence (4/4)
export const EVIDENCE_KEYS_W3_4 = [
  '{{leaves}} leaf function(s) covered by requirements; {{subs}} space subsystem(s) with requirements',
  '{{uncovered}}/{{leaves}} leaf function(s) without a requirement: {{codes}}; {{nosubs}} space subsystem(s) without one: {{names}}',
  '{{n}} function(s); {{allocated}}/{{leaves}} leaf function(s) allocated',
  '{{n}} function(s); {{allocated}}/{{leaves}} leaf function(s) allocated; unallocated: {{codes}}',
  'Reliability {{rel}} over {{horizon}} vs target {{target}}',
]

// English text is the i18n key — wave 3 integration evidence (1/2)
export const EVIDENCE_KEYS_W3_5 = [
  'ConOps summary documented; {{n}} operational scenario(s) with requirements',
  '{{n}} operational scenario(s) with requirements',
  'SEMP issue {{issue}} recorded',
  'SEMP content ready ({{parts}}/{{of}} parts): review it and record its issue',
  'The SEMP generator has no content yet ({{parts}}/{{of}} parts)',
  'No debris assessment has been run',
]

// English text is the i18n key — wave 3 integration evidence (2/2)
export const EVIDENCE_KEYS_W3_6 = [
  'Debris assessment v{{version}} not accepted yet',
  'Debris assessment v{{version}} accepted, but the design changed since the run: run it again',
  'Debris assessment v{{version}} accepted, not compliant and no deviation recorded',
  'Debris assessment v{{version}} accepted at {{gate}}',
  'Reliability {{rel}} over {{horizon}} vs target {{target}}; FMEA {{rows}} line(s), {{critical}} critical, all linked',
  'Reliability analysis not acceptable: {{reasons}}',
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
  tmtc: 'Open TM/TC',
  fdir: 'Open FDIR',
  aocs: 'Open AOCS modes',
  ops: 'Open Operations',
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
