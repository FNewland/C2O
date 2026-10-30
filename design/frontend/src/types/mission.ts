/**
 * Domain types for ground stations, constellation, and budget cascade.
 */

export interface GroundStation {
  id: string
  name: string
  latitude_deg: number
  longitude_deg: number
  antenna_diameter_m: number
  frequency_bands: string[]  // e.g., ['S', 'X']
  min_elevation_deg: number
  cost_keur: number
  owned: boolean  // true = build/own, false = lease
}

export interface SpacecraftVariant {
  id: string
  name: string  // e.g., "Comms primary", "Spare", "Gateway"
  quantity: number
  mass_delta_kg: number  // offset from reference design
  payload_config: string  // description of payload differences
  cost_modifier: number  // multiplier (1.0 = same as reference)
}

export interface FleetConfig {
  variants: SpacecraftVariant[]
  learning_curve_factor: number  // typically 0.85-0.95
  total_spacecraft: number  // computed from variants
}

export interface BudgetAllocation {
  domain: string  // e.g., 'aocs', 'eps', 'comms', 'payload', 'thermal', 'structure', 'propulsion'
  allocation: number  // budget bucket assigned at system level
  unit: string  // 'kg', 'W', 'kEUR'
}

export interface BudgetEnvelope {
  mass_kg: number
  power_w: number
  cost_keur: number
  data_rate_mbps: number
}
