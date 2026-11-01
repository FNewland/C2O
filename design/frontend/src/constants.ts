/** Shared constants for SpaceCDF frontend. */

export const POSITION_COLOR: Record<string, string> = {
  systems_engineer: 'var(--cat-2)',
  mission_analyst: 'var(--interactive)',
  payload_lead: 'var(--status-ok)',
  power_engineer: 'var(--status-caution)',
  aocs_engineer: 'var(--interactive)',
  thermal_engineer: 'var(--status-alarm)',
  comms_engineer: 'var(--cat-6)',
  propulsion_engineer: 'var(--status-caution)',
  structures_engineer: 'var(--cat-7)',
  cost_engineer: 'var(--cat-2)',
  compliance_engineer: 'var(--cat-3)',
  user_representative: 'var(--status-caution)',
  mission_ops: 'var(--text-3)',
  ground_segment: 'var(--interactive)',
  software_engineer: 'var(--cat-2)',
}

export const POSITION_OPTIONS = [
  { id: 'systems_engineer', label: 'Systems Engineer' },
  { id: 'mission_analyst', label: 'Mission Analyst' },
  { id: 'payload_lead', label: 'Payload Lead' },
  { id: 'power_engineer', label: 'Power Engineer' },
  { id: 'aocs_engineer', label: 'AOCS Engineer' },
  { id: 'thermal_engineer', label: 'Thermal Engineer' },
  { id: 'comms_engineer', label: 'Comms Engineer' },
  { id: 'propulsion_engineer', label: 'Propulsion Engineer' },
  { id: 'structures_engineer', label: 'Structures Engineer' },
  { id: 'cost_engineer', label: 'Cost Engineer' },
  { id: 'compliance_engineer', label: 'Compliance / Regulatory' },
  { id: 'user_representative', label: 'User Representative' },
  { id: 'mission_ops', label: 'Mission Operations' },
  { id: 'ground_segment', label: 'Ground Segment' },
  { id: 'software_engineer', label: 'Software Engineer' },
  { id: 'project_manager', label: 'Project Manager' },
] as const
