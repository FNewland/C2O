/**
 * ChangeEvent types — per SPINE_SPEC §2.2.
 *
 * Typed envelope for any mutation to the design state.
 * Used by useApplyToDesign hook and (in H2) the ChangeEventDispatcher.
 */

export type ChangeKind =
  | "parameter_override"
  | "equipment_selection"
  | "requirement_edit"
  | "requirement_delete"
  | "conops_edit"
  | "qa_answer"
  | "margin_phase_change"
  | "parametric_fraction_edit"
  | "launch_vehicle_selection"
  | "spectrum_band_selection"
  | "gate_criterion_toggle"

export interface ChangeEvent {
  id: string
  kind: ChangeKind
  session_id: string
  actor_id: string
  actor_label?: string
  target_id: string
  target_kind: "parameter" | "requirement" | "equipment" | "conops_mode" | string
  old_value?: unknown
  new_value?: unknown
  rationale?: string
  correlation_id?: string
  created_at: string
}
