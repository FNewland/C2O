/**
 * Mission definition draft (Nov 2026) — the orbit, payload, class, lifetime, launch /
 * disposal and link a team enters in the wizard (step 4) and edits afterwards
 * (Traceability › Mission need › Edit). Pure helpers, no React: the wizard POSTs
 * `toRequirements(draft)` to /api/studies/, the editor PATCHes `toPatch(draft)` to
 * /api/studies/{id}/mission (services/mission_definition.py validates it again).
 *
 * Inputs are kept as strings so a half-typed number is not turned into 0 while typing.
 */

export interface PayloadDraft {
  name: string
  type: string
  mass_kg: string
  power_w: string
  power_peak_w: string
  data_rate_mbps: string
  duty_cycle_percent: string
  pointing_accuracy_deg: string
  gsd_m: string
  swath_km: string
  /** comma-separated band centres, e.g. "865, 1610" */
  wavelengths_nm: string
  data_per_image_mb: string
}

export interface LinkDraft {
  band: string
  downlink_frequency_mhz: string
  uplink_frequency_mhz: string
  downlink_rate_bps: string
  uplink_rate_bps: string
  tx_power_w: string
  tx_antenna_gain_dbi: string
}

export interface MissionDefDraft {
  spacecraft_class: string
  design_lifetime_years: string
  target_mass_kg: string
  orbit_type: string
  altitude_km: string
  inclination_deg: string
  /** SSO: inclination follows the altitude (J2) */
  inclination_auto: boolean
  ltan: string
  launch_vehicle: string
  disposal_method: string
  payloads: PayloadDraft[]
  link: LinkDraft
}

export const SPACECRAFT_CLASSES = ['nano', 'micro', 'small', 'medium', 'large', 'flagship'] as const
export const ORBIT_TYPES = ['sso', 'leo', 'meo', 'geo', 'heo', 'gto'] as const
export const DISPOSAL_METHODS = ['natural_decay', 'drag_sail', 'propulsive', 'graveyard', 'none'] as const

// English text is the i18n key (value → label)
export const CLASS_LABELS: Record<string, string> = {
  nano: 'Nano (CubeSat, < 10 kg)', micro: 'Micro (10–100 kg)', small: 'Small (100–500 kg)',
  medium: 'Medium (500–1000 kg)', large: 'Large (> 1000 kg)', flagship: 'Flagship',
}
// English text is the i18n key
export const ORBIT_LABELS: Record<string, string> = {
  sso: 'Sun-synchronous (SSO)', leo: 'Low Earth orbit (LEO)', meo: 'Medium Earth orbit (MEO)',
  geo: 'Geostationary (GEO)', heo: 'Highly elliptical (HEO)', gto: 'Geostationary transfer (GTO)',
}
// English text is the i18n key
export const DISPOSAL_LABELS: Record<string, string> = {
  natural_decay: 'Natural decay', drag_sail: 'Drag sail', propulsive: 'Propulsive de-orbit',
  graveyard: 'Graveyard orbit', none: 'None',
}

const R_EARTH_M = 6371.0e3   // the server's physics constant (spacecdf_common.physics.orbit)
const MU_EARTH = 3.986004418e14
const J2 = 1.08263e-3

/** Sun-synchronous inclination (deg) at a circular altitude (km), J2 only. */
export function ssoInclination(altitudeKm: number): number {
  const a = R_EARTH_M + altitudeKm * 1e3
  const n = Math.sqrt(MU_EARTH / a ** 3)
  const target = 0.9856 * Math.PI / 180 / 86400
  const cosI = Math.max(-1, Math.min(1, -target / (1.5 * n * J2 * (R_EARTH_M / a) ** 2)))
  return Math.round(Math.acos(cosI) * 180 / Math.PI * 100) / 100
}

/** Circular-orbit period (min). */
export function orbitPeriodMin(altitudeKm: number): number {
  const a = R_EARTH_M + altitudeKm * 1e3
  return 2 * Math.PI * Math.sqrt(a ** 3 / MU_EARTH) / 60
}

export function emptyPayload(name = 'Payload'): PayloadDraft {
  return {
    name, type: 'optical_imager', mass_kg: '1', power_w: '10', power_peak_w: '', data_rate_mbps: '10',
    duty_cycle_percent: '25', pointing_accuracy_deg: '1', gsd_m: '', swath_km: '', wavelengths_nm: '', data_per_image_mb: '',
  }
}

export function defaultMissionDef(): MissionDefDraft {
  return {
    spacecraft_class: 'nano', design_lifetime_years: '3', target_mass_kg: '6',
    orbit_type: 'sso', altitude_km: '500', inclination_deg: String(ssoInclination(500)), inclination_auto: true,
    ltan: '10:30', launch_vehicle: '', disposal_method: 'natural_decay',
    payloads: [emptyPayload()],
    link: { band: '', downlink_frequency_mhz: '', uplink_frequency_mhz: '', downlink_rate_bps: '', uplink_rate_bps: '', tx_power_w: '', tx_antenna_gain_dbi: '' },
  }
}

const str = (v: unknown): string => (v === null || v === undefined ? '' : String(v))
const num = (s: string): number | null => {
  if (s.trim() === '') return null
  const v = Number(s.replace(',', '.'))
  return Number.isFinite(v) ? v : null
}

/** Draft from a study's `requirements` (GET /api/studies/{id}). */
export function fromRequirements(req: any): MissionDefDraft {
  const d = defaultMissionDef()
  if (!req) return d
  const o = req.orbit || {}
  const alt = typeof o.altitude_km === 'number' ? o.altitude_km : 500
  const inc = typeof o.inclination_deg === 'number' ? o.inclination_deg : ssoInclination(alt)
  const type = str(o.orbit_type || 'sso')
  return {
    spacecraft_class: str(req.spacecraft_class || d.spacecraft_class),
    design_lifetime_years: str(req.design_lifetime_years ?? d.design_lifetime_years),
    target_mass_kg: str(req.target_mass_kg ?? ''),
    orbit_type: type,
    altitude_km: str(alt),
    inclination_deg: str(inc),
    inclination_auto: type === 'sso' && Math.abs(inc - ssoInclination(alt)) < 0.005,
    ltan: str(o.ltan ?? ''),
    launch_vehicle: str(req.launch_vehicle ?? ''),
    disposal_method: str(req.disposal_method ?? ''),
    payloads: (req.payloads || []).map((p: any) => ({
      name: str(p.name), type: str(p.type || 'optical_imager'), mass_kg: str(p.mass_kg), power_w: str(p.power_w),
      power_peak_w: str(p.power_peak_w), data_rate_mbps: str(p.data_rate_mbps), duty_cycle_percent: str(p.duty_cycle_percent),
      pointing_accuracy_deg: str(p.pointing_accuracy_deg), gsd_m: str(p.gsd_m), swath_km: str(p.swath_km),
      wavelengths_nm: (p.wavelengths_nm || []).join(', '), data_per_image_mb: str(p.data_per_image_mb),
    })),
    link: {
      band: str(req.link?.band), downlink_frequency_mhz: str(req.link?.downlink_frequency_mhz),
      uplink_frequency_mhz: str(req.link?.uplink_frequency_mhz), downlink_rate_bps: str(req.link?.downlink_rate_bps),
      uplink_rate_bps: str(req.link?.uplink_rate_bps), tx_power_w: str(req.link?.tx_power_w),
      tx_antenna_gain_dbi: str(req.link?.tx_antenna_gain_dbi),
    },
  }
}

/** The inclination the draft stands for (auto SSO → J2 value). */
export function effectiveInclination(d: MissionDefDraft): number | null {
  const alt = num(d.altitude_km)
  if (d.orbit_type === 'sso' && d.inclination_auto && alt !== null) return ssoInclination(alt)
  return num(d.inclination_deg)
}

// English text is the i18n key (validateDraft messages, shown with t())
export const DRAFT_ERRORS = {
  altitude: 'Altitude must be a positive number',
  inclination: 'Inclination must be between 0 and 180°',
  ltan: 'LTAN must be HH:MM',
  lifetime: 'Lifetime must be a positive number',
  payload: 'Payload values must be non-negative numbers',
}

/** English messages (i18n keys, DRAFT_ERRORS) for what is wrong; [] = valid. */
export function validateDraft(d: MissionDefDraft): string[] {
  const errs: string[] = []
  const alt = num(d.altitude_km)
  if (alt === null || alt <= 0) errs.push(DRAFT_ERRORS.altitude)
  const inc = effectiveInclination(d)
  if (inc === null || inc < 0 || inc > 180) errs.push(DRAFT_ERRORS.inclination)
  if (d.ltan.trim() && !/^([01]?\d|2[0-3]):[0-5]\d$/.test(d.ltan.trim())) errs.push(DRAFT_ERRORS.ltan)
  const life = num(d.design_lifetime_years)
  if (life === null || life <= 0) errs.push(DRAFT_ERRORS.lifetime)
  for (const p of d.payloads) {
    for (const k of ['mass_kg', 'power_w', 'power_peak_w', 'data_rate_mbps', 'gsd_m', 'swath_km', 'data_per_image_mb'] as const) {
      const v = num(p[k])
      if (p[k].trim() && (v === null || v < 0)) { errs.push(DRAFT_ERRORS.payload); break }
    }
  }
  return [...new Set(errs)]
}

function payloadOut(p: PayloadDraft): Record<string, unknown> {
  const out: Record<string, unknown> = { name: p.name.trim() || 'Payload', type: p.type || 'optical_imager' }
  const put = (k: keyof PayloadDraft, target = k as string) => { const v = num(p[k]); if (v !== null) out[target] = v }
  put('mass_kg'); put('power_w'); put('power_peak_w'); put('data_rate_mbps'); put('duty_cycle_percent')
  put('pointing_accuracy_deg'); put('gsd_m'); put('swath_km'); put('data_per_image_mb')
  if (out.power_peak_w === undefined && typeof out.power_w === 'number') out.power_peak_w = out.power_w
  out.wavelengths_nm = p.wavelengths_nm.split(/[,;\s]+/).map(Number).filter(v => Number.isFinite(v) && v > 0)
  return out
}

function linkOut(l: LinkDraft): Record<string, unknown> {
  const out: Record<string, unknown> = { band: l.band.trim() || null }
  for (const k of ['downlink_frequency_mhz', 'uplink_frequency_mhz', 'downlink_rate_bps', 'uplink_rate_bps', 'tx_power_w', 'tx_antenna_gain_dbi'] as const) {
    out[k] = num(l[k])
  }
  return out
}

function orbitOut(d: MissionDefDraft): Record<string, unknown> {
  const life = num(d.design_lifetime_years)
  return {
    orbit_type: d.orbit_type,
    altitude_km: num(d.altitude_km),
    inclination_deg: effectiveInclination(d),
    ltan: d.ltan.trim() || null,
    ...(life !== null ? { mission_duration_years: life } : {}),
    deorbit_required: d.disposal_method !== 'none',
  }
}

/** `requirements` fields for POST /api/studies/ (the wizard; name, type and stations added by the caller). */
export function toRequirements(d: MissionDefDraft): Record<string, unknown> {
  const mass = num(d.target_mass_kg)
  return {
    spacecraft_class: d.spacecraft_class,
    orbit: orbitOut(d),
    payloads: d.payloads.map(payloadOut),
    design_lifetime_years: num(d.design_lifetime_years) ?? 3,
    target_mass_kg: mass,
    launch_vehicle: d.launch_vehicle.trim() || null,
    disposal_method: d.disposal_method || null,
    link: linkOut(d.link),
  }
}

/** Body for PATCH /api/studies/{id}/mission. */
export function toPatch(d: MissionDefDraft): Record<string, unknown> {
  const r = toRequirements(d)
  // An explicit inclination: the server only recomputes it when asked (auto_inclination)
  return { ...r, orbit: { ...(r.orbit as object), auto_inclination: d.orbit_type === 'sso' && d.inclination_auto } }
}

/** "SSO 590 km · 97.75° · LTAN 10:30" */
export function orbitSummary(req: any): string {
  const o = req?.orbit
  if (!o) return ''
  const parts = [`${String(o.orbit_type || '').toUpperCase()} ${o.altitude_km} km`, `${Number(o.inclination_deg).toFixed(2)}°`]
  if (o.ltan) parts.push(`LTAN ${o.ltan}`)
  return parts.join(' · ')
}
