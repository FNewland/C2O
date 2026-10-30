/** Shared constants for SpaceCDF frontend. */

export const POSITION_COLOR: Record<string, string> = {
  systems_engineer: '#8b5cf6',
  mission_analyst: '#3b82f6',
  payload_lead: '#10b981',
  power_engineer: '#f59e0b',
  aocs_engineer: '#06b6d4',
  thermal_engineer: '#ef4444',
  comms_engineer: '#ec4899',
  propulsion_engineer: '#f97316',
  structures_engineer: '#84cc16',
  cost_engineer: '#a855f7',
  compliance_engineer: '#14b8a6',
  user_representative: '#fb923c',
  mission_ops: '#64748b',
  ground_segment: '#0ea5e9',
  software_engineer: '#d946ef',
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
