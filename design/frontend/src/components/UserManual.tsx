import { useState } from 'react'

type Section =
  | 'getting-started'
  | 'templates'
  | 'sessions'
  | 'design'
  | 'compliance'
  | 'ecss'
  | 'cost'
  | 'trade'
  | 'snapshots'
  | 'optimizer'
  | 'exports'
  | 'validation'
  | 'positions'

const SECTIONS: { id: Section; label: string }[] = [
  { id: 'getting-started', label: 'Getting started' },
  { id: 'templates',       label: 'Templates' },
  { id: 'sessions',        label: 'Sessions & positions' },
  { id: 'design',          label: 'Design workspace' },
  { id: 'positions',       label: 'Position panel' },
  { id: 'compliance',      label: 'Requirements compliance' },
  { id: 'ecss',            label: 'ECSS review gate' },
  { id: 'cost',            label: 'Cost breakdown' },
  { id: 'trade',           label: 'Trade studies' },
  { id: 'snapshots',       label: 'Snapshots & diff' },
  { id: 'optimizer',       label: 'Optimizer' },
  { id: 'exports',         label: 'Exports (SMO / MBSE / FSW / Docs)' },
  { id: 'validation',      label: 'Validation harness' },
]

export function UserManual() {
  const [current, setCurrent] = useState<Section>('getting-started')

  return (
    <div style={{ display: 'flex', height: '100%', gap: '1rem', padding: '1rem', overflow: 'hidden' }}>
      {/* Sidebar */}
      <div style={{
        minWidth: '200px',
        background: 'var(--bg-secondary, #1f2937)',
        border: '1px solid var(--border, #374151)',
        borderRadius: '6px',
        padding: '0.5rem',
        overflowY: 'auto',
      }}>
        <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary, #9ca3af)', padding: '0.4rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          User manual
        </div>
        {SECTIONS.map(s => (
          <button
            key={s.id}
            onClick={() => setCurrent(s.id)}
            style={{
              display: 'block',
              width: '100%',
              textAlign: 'left',
              padding: '0.4rem 0.6rem',
              background: current === s.id ? 'var(--accent, #3b82f6)' : 'transparent',
              color: current === s.id ? 'white' : 'var(--text-secondary, #d1d5db)',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '0.82rem',
              marginBottom: '0.15rem',
            }}
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        background: 'var(--bg-secondary, #1f2937)',
        border: '1px solid var(--border, #374151)',
        borderRadius: '6px',
        padding: '1.25rem 1.5rem',
        lineHeight: 1.55,
        fontSize: '0.88rem',
      }}>
        {current === 'getting-started' && <GettingStarted />}
        {current === 'templates'       && <Templates />}
        {current === 'sessions'        && <Sessions />}
        {current === 'design'          && <Design />}
        {current === 'positions'       && <Positions />}
        {current === 'compliance'      && <Compliance />}
        {current === 'ecss'            && <Ecss />}
        {current === 'cost'            && <Cost />}
        {current === 'trade'           && <Trade />}
        {current === 'snapshots'       && <Snapshots />}
        {current === 'optimizer'       && <Optimizer />}
        {current === 'exports'         && <Exports />}
        {current === 'validation'      && <Validation />}
      </div>
    </div>
  )
}

// --- Re-usable helpers -----------------------------------------------------

const H1 = ({ children }: any) => <h2 style={{ marginTop: 0 }}>{children}</h2>
const H2 = ({ children }: any) => <h3 style={{ marginTop: '1.25rem', borderBottom: '1px solid var(--border, #374151)', paddingBottom: '0.3rem' }}>{children}</h3>
const P  = ({ children }: any) => <p>{children}</p>
const UL = ({ children }: any) => <ul style={{ paddingLeft: '1.3rem' }}>{children}</ul>
const OL = ({ children }: any) => <ol style={{ paddingLeft: '1.3rem' }}>{children}</ol>
const C  = ({ children }: any) => <code style={{
  background: 'var(--bg-primary, #111827)',
  border: '1px solid var(--border, #374151)',
  padding: '0.05rem 0.25rem',
  borderRadius: '3px',
  fontSize: '0.82em',
}}>{children}</code>
const Box = ({ tone = 'info', children }: any) => (
  <div style={{
    borderLeft: `3px solid ${tone === 'warn' ? '#f59e0b' : tone === 'tip' ? '#10b981' : '#3b82f6'}`,
    background: 'var(--bg-primary, #111827)',
    padding: '0.5rem 0.8rem',
    margin: '0.75rem 0',
    borderRadius: '4px',
    fontSize: '0.82em',
  }}>{children}</div>
)

// --- Content sections ------------------------------------------------------

function GettingStarted() {
  return <>
    <H1>Getting started</H1>
    <P>SpaceCDF is a concurrent design facility for space missions. You work with up to 14 engineering "positions" (mission analyst, power, AOCS, thermal, comms, propulsion, structures, OBDH, cost, etc.) that collaborate in real time on a single converged design.</P>

    <H2>Your first 5 minutes</H2>
    <OL>
      <li><strong>Click "New from Template"</strong> (top right). Pick an archetype close to your target mission — e.g. <C>6U EO CubeSat</C> or <C>Lunar Orbiter</C>.</li>
      <li><strong>Click "Join Session"</strong> (top strip) and pick your position. You can only edit parameters your position owns — this is by design.</li>
      <li><strong>Open the Design tab</strong> to see converged budgets (mass, power, data, cost, link margin).</li>
      <li><strong>Open the ECSS Gate tab</strong> to see which review deliverables your current phase requires and how many SpaceCDF already auto-produces.</li>
      <li><strong>Save a snapshot</strong> (Snapshots tab) before making any trade. Diffing two snapshots is how you document a trade study.</li>
    </OL>

    <Box tone="tip">
      <strong>Sticky parameters.</strong> Values you set manually (or select from the equipment browser) are marked sticky — they survive re-convergence. The design agents can only write non-sticky parameters. This is what keeps your decisions from being silently overwritten.
    </Box>

    <H2>Why the tool is built this way</H2>
    <UL>
      <li><strong>Offline-first.</strong> No API keys, no external services. Runs entirely on your machine.</li>
      <li><strong>Honest provenance.</strong> Every parameter carries its source (computed, selected, override, requirement). The MBSE export preserves this.</li>
      <li><strong>Aligned with ECSS.</strong> Templates declare their applicable standards. The Gate tab cites clause-level DRDs from ECSS-E-ST-10C Annex A, E-ST-10-24 (interfaces), M-ST-10 (phases), etc.</li>
      <li><strong>Traceable.</strong> Snapshots + diff give you a time-reversible audit trail. The validation harness lets a reviewer re-run your study and compare against references.</li>
    </UL>
  </>
}

function Templates() {
  return <>
    <H1>Mission Templates</H1>
    <P>Templates seed a new study from a canonical archetype so you don't start from an empty form. Each template carries its mission requirements, recommended margin policy, target ECSS phase, and a list of applicable ECSS standards.</P>

    <H2>Shipped templates</H2>
    <UL>
      <li><C>3u_tech_demo</C> — 3U CubeSat, 1-year LEO demonstrator, Phase 0</li>
      <li><C>6u_eo_cubesat</C> — 6U Earth-observation imager, 3-year SSO, Phase A</li>
      <li><C>100kg_smallsat_eo</C> — 100 kg commercial EO smallsat, 5-year, Phase A</li>
      <li><C>lunar_orbiter</C> — Small lunar orbiter (~300 kg), Phase 0</li>
    </UL>

    <H2>Using a template</H2>
    <OL>
      <li>Click <strong>New from Template</strong> in the top bar.</li>
      <li>Filter by archetype using the chips if needed.</li>
      <li>Click a card to see its full detail pane on the right: applicable ECSS list, equipment hints, typical use cases.</li>
      <li>Click <strong>Create study from …</strong> — a new study is created and the Design tab opens.</li>
    </OL>

    <H2>Customising a template</H2>
    <P>Templates live in <C>configs/templates/*.yaml</C>. Copy one, edit the <C>requirements</C> block and <C>applicable_ecss</C> list, restart the server, and it shows up in the gallery. The schema is defined in <C>packages/spacecdf-common/.../models/template.py</C>.</P>
  </>
}

function Sessions() {
  return <>
    <H1>Sessions & positions</H1>
    <P>A <strong>session</strong> is a live collaborative working copy of a study. A <strong>position</strong> is the role you play in that session (e.g. <C>power_engineer</C>). Up to 14 positions can join the same session and edit in real time over WebSocket.</P>

    <H2>Join flow</H2>
    <OL>
      <li>Click <strong>Join Session</strong> in the session bar.</li>
      <li>Pick a position from the dropdown — this decides which parameters you're allowed to edit.</li>
      <li>Type a display name (optional). Your edits will be labelled with it in the live-edit toast and history drawer.</li>
      <li>Click <strong>Join</strong>.</li>
    </OL>

    <H2>Edit scoping</H2>
    <P>Each position owns a set of parameters (e.g. power_engineer owns <C>power.*</C>, aocs_engineer owns <C>aocs.*</C>). Attempting to edit outside your scope returns an <C>edit_rejected</C> message and nothing changes. Systems engineer has cross-cutting edit rights.</P>

    <Box tone="tip">Multiple engineers in the same session see each other's edits live and get a toast notification per change, with rationale.</Box>
  </>
}

function Design() {
  return <>
    <H1>Design workspace</H1>
    <P>The Design tab is the main convergence view. It shows all ~85 design parameters grouped by engineering domain, with the current converged value, unit, source, and margin. Click a parameter name to expand rationale and dependencies.</P>

    <H2>Inline editing</H2>
    <OL>
      <li>Click a value. If your position owns the parameter, an input field appears.</li>
      <li>Type the new value and press Enter.</li>
      <li>An edit message goes over WebSocket; the server runs selective re-convergence (only affected agents); all connected positions see the result in 3-15 ms.</li>
    </OL>

    <H2>Equipment browser</H2>
    <P>Click <strong>Browse Equipment</strong> (top bar, appears when in a session) to pick from the Knowledge Base catalogue — real components (batteries, reaction wheels, star trackers, etc.) with published mass/power/performance data. Selecting a component sets the relevant parameter and marks it <strong>sticky</strong> so later convergence can't overwrite it.</P>
  </>
}

function Positions() {
  return <>
    <H1>Position panel</H1>
    <P>A single-pane view of every parameter your current position owns, with direct edit fields and convergence status per parameter.</P>
    <UL>
      <li><strong>Green dot</strong> — parameter is current and converged.</li>
      <li><strong>Amber dot</strong> — parameter changed in the last cascade round and still propagating.</li>
      <li><strong>Red dot</strong> — parameter is blocked by a cross-domain conflict (see Conflicts tab on the right).</li>
    </UL>
    <P>Use this panel as your "workbench" — it filters out parameters you don't own so you can focus.</P>
  </>
}

function Compliance() {
  return <>
    <H1>Requirements Compliance</H1>
    <P>Auto-generated formal requirements (of the form <em>"The spacecraft shall …"</em>) derived from the template's MissionRequirements, evaluated against the current converged state. Follows the ECSS-E-ST-10-06 requirements pattern.</P>
    <H2>Status codes</H2>
    <UL>
      <li><strong>COMPLIANT</strong> — margin ≥ policy threshold (20% by default in Phase 0/A).</li>
      <li><strong>MARGINAL</strong> — margin positive but below policy. Acceptable at PDR if documented.</li>
      <li><strong>NON_COMPLIANT</strong> — negative margin. Must be resolved before the gate.</li>
      <li><strong>NOT_VERIFIED</strong> — the linked parameter hasn't converged or is missing.</li>
    </UL>
    <P>This panel populates the VCD (Verification Control Document) section of the ECSS review-gate deliverables (see ECSS Gate tab).</P>
  </>
}

function Ecss() {
  return <>
    <H1>ECSS Review Gate</H1>
    <P>Tells you, for the study's current phase, which <strong>DRDs</strong> (Document Requirements Descriptions) are expected at the next review and how many SpaceCDF currently auto-produces.</P>

    <H2>Status categories</H2>
    <UL>
      <li><strong>Auto-produced</strong> (green) — SpaceCDF generates this deliverable from the design state.</li>
      <li><strong>Partial</strong> (amber) — SpaceCDF covers part of the content; human authoring still required.</li>
      <li><strong>Planned</strong> (blue) — road-map feature, not yet generated.</li>
      <li><strong>External</strong> (grey) — document authored outside SpaceCDF (SEMP, PAP, etc.).</li>
    </UL>

    <H2>Phase → Gate mapping</H2>
    <UL>
      <li><C>phase_0</C> → MDR (Mission Definition Review)</li>
      <li><C>phase_a</C> → PRR (Preliminary Requirements Review)</li>
      <li><C>phase_b1</C> → SRR (System Requirements Review)</li>
    </UL>
    <P>Each DRD in the list cites the owning ECSS standard and annex. The data lives in <C>configs/ecss_review_gates.yaml</C> — edit to tailor per ECSS-S-ST-00-02.</P>
  </>
}

function Cost() {
  return <>
    <H1>Cost breakdown</H1>
    <P>NASA-CEH-aligned cost estimate: analogy + parametric rollup with ECSS-style margin, Monte Carlo for 80% confidence level (CL80). Each subsystem contributes a cost in kEUR; the totals are aggregated in MEUR.</P>
    <P>The Monte Carlo uses triangular distributions per subsystem (min / most-likely / max) calibrated against historical data. See <C>services/cost_engine.py</C> for the distribution parameters and CEH Appendix G for the method.</P>
  </>
}

function Trade() {
  return <>
    <H1>Trade studies</H1>
    <P>Lightweight what-if sweeps on a small set of parameters. For formal multi-variable optimisation use the <strong>Optimizer</strong> tab instead.</P>
    <P>Pick a parameter, a range, and a step; the tool runs each value through the full cascade and plots the effect on your chosen objective. Useful for quick altitude-vs-link-margin or payload-duty-cycle-vs-cost explorations before a full optimiser run.</P>
  </>
}

function Snapshots() {
  return <>
    <H1>Snapshots & diff</H1>
    <P>Named, tagged snapshots of the session's DesignState. Two snapshots can be diffed parameter-by-parameter — this is how you document a trade study.</P>

    <H2>Workflow</H2>
    <OL>
      <li>In the <strong>Snapshots</strong> tab, type a name (e.g. <C>baseline</C>) and click <strong>Save snapshot</strong>.</li>
      <li>Make your trade change (e.g. override <C>payload.power_w</C>).</li>
      <li>Save another snapshot (e.g. <C>heavy-payload</C>).</li>
      <li>Click the first snapshot — it's marked <strong>A</strong>. Click the second — it's marked <strong>B</strong>.</li>
      <li>The diff table appears above the list: Δ values and % change for every parameter that differs.</li>
    </OL>

    <Box tone="tip">
      Tag snapshots for provenance. <C>pre-pdr</C>, <C>margin-check</C>, <C>optimised</C> are common conventions.
    </Box>
  </>
}

function Optimizer() {
  return <>
    <H1>Optimizer</H1>
    <P>Single-objective design optimisation using scipy <C>differential_evolution</C>. Uses the Candidate Evaluator so that sticky parameters on the base state are never mutated.</P>

    <H2>Available objectives</H2>
    <UL>
      <li><strong>Minimise wet mass</strong> — <C>mass.wet_mass_kg</C></li>
      <li><strong>Minimise dry mass</strong> — <C>mass.dry_mass_kg</C></li>
      <li><strong>Minimise total cost with margin</strong> — <C>cost.total_with_margin_meur</C></li>
      <li><strong>Maximise downlink margin</strong> — <C>link.downlink_margin_db</C></li>
    </UL>

    <H2>Workflow</H2>
    <OL>
      <li>Tick 1–3 design variables; adjust lower/upper bounds.</li>
      <li>Pick an objective and a max-evaluations budget (120 is a reasonable default).</li>
      <li>Click <strong>Run</strong>. Each evaluation runs a full reconvergence cascade (~80 ms), so 120 evals ≈ 10 s wall-clock.</li>
      <li>Progress polls every 500 ms. Critical conflicts in candidates get a 10⁶ penalty, so the optimiser naturally avoids infeasible regions.</li>
      <li>When done, the best-x parameters are shown. Apply them manually via the Design tab, or save a snapshot before/after to document the improvement.</li>
    </OL>

    <Box tone="warn">
      The optimiser only mutates its own deep-copied state — your live session is never touched. The progress bar reflects scipy internals and may not move linearly.
    </Box>
  </>
}

function Exports() {
  return <>
    <H1>Exports</H1>
    <P>The <strong>Exports</strong> panel (right column) generates artefacts from the current design:</P>
    <H2>SMO configs</H2>
    <P>~20 YAML files for the SpaceMissionSimulation platform: subsystems, telemetry, FDIR, monitoring. Use this to drive a simulator from your concept design.</P>
    <H2>MBSE JSON (ECSS-E-TM-10-25A-like)</H2>
    <P>SysML-like model: blocks (Spacecraft → subsystems), parameters with units + sources, requirements, traceability links, applicable ECSS standards. Diff-friendly JSON — suitable for version control and downstream import into Cameo or Capella.</P>
    <H2>Design review documents (SRR / PDR / CDR)</H2>
    <P>Markdown + DOCX + XLSX bundle with auto-filled budget tables, equipment lists, compliance matrix. Sections requiring human input are highlighted.</P>
    <H2>Flight software architecture</H2>
    <P>cFS-style C scaffolding: parameter database, telemetry packets, mode tables, FDIR rules, 10 application skeletons. For FSW architects transitioning concept to code.</P>
  </>
}

function Validation() {
  return <>
    <H1>Validation harness</H1>
    <P>A reproducibility anchor. Compares a converged template output against a reference set with tolerances and citations.</P>

    <H2>Running</H2>
    <Box>
      <C>python3 scripts/validate_template.py</C>
    </Box>
    <P>Default reference: <C>configs/validation/eosat_6u_reference.yaml</C> (6U EO CubeSat against SMAD4, Fortescue, and SMO-EOSAT). Exit codes: 0 = all PASS, 1 = any WARN, 2 = any FAIL. Use the <C>--json</C> flag in CI.</P>

    <H2>Adding a reference</H2>
    <OL>
      <li>Create a YAML in <C>configs/validation/</C> with a <C>template_id</C> and a <C>parameters</C> block.</li>
      <li>For each anchor parameter, provide <C>reference_value</C>, <C>tolerance_percent</C>, and — this matters — a <C>citation</C>.</li>
      <li>Run the harness against the new file.</li>
    </OL>

    <Box tone="tip">
      Citations should be specific: <em>"SMAD4 Table 14-1"</em> not <em>"some book"</em>. A reviewer should be able to chase the reference.
    </Box>
  </>
}
