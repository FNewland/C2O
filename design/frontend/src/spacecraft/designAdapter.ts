/**
 * designAdapter — the CURRENT DESIGN as the models the shared pictorial
 * modules draw (shared/ui-viz, copied to src/viz). Mission control feeds the
 * same views from telemetry; here every quantity has verdict "design" and a
 * source that says which element or rule it came from.
 *
 *   designGeometry()  -> c2o.geometry/1, the shape sim/configs/eosat1/geometry.yaml uses
 *   designOverview()  -> overview.js model (subsystem synoptic)
 *   designPower()     -> powerflow.js model for a power case (sunlit / eclipse / peak)
 *   designAttitude()  -> attitude3d.js model (nominal nadir pointing in LVLH)
 *
 * Pure functions, no fetch, so they can move to shared/ui-viz as the shared
 * design adapter (requested from the module owner).
 *
 * What is a standard and what is a default:
 *   - CubeSat sizes and typical maximum mass: CubeSat Design Specification
 *     rev 14.1, 2.2.10 Table 1 (1U 2 kg, 1.5U 3, 2U 4, 3U 6, 6U 12, 12U 24).
 *   - 20 % system margin on dry mass: ESA "Margin philosophy for science
 *     assessment studies", issue 1.3.
 *   - Depth-of-discharge limit 25 %, star-tracker Earth-limb exclusion 25°,
 *     payload field of view 10° when none is given: C2O defaults, labelled so
 *     (the ESA margin philosophy gives no DoD figure).
 */
import { qty, periodFromAltS, eclipseFraction, betaCriticalDeg } from '../viz/derive.js'

// ─── Inputs ───

export interface El {
  id: string
  name: string
  parent_id: string | null
  element_type: string
  subsystem_domain?: string | null
  mass_kg?: number | null
  power_avg_w?: number | null
  power_peak_w?: number | null
  quantity?: number | null
  kb_component_id?: string | null
  performance?: Record<string, any> | null
  dimensions?: Record<string, any> | null
  deleted_at?: string | null
  in_scope?: boolean
}

export type PowerCase = 'sunlit' | 'eclipse' | 'peak'

const n = (x: unknown): number | null => (x === null || x === undefined || x === '' || !Number.isFinite(Number(x)) ? null : Number(x))
const q = (e: El) => Math.max(1, Number(e.quantity) || 1)

/** All live descendants of `rootId`. */
export function descendants(all: El[], rootId: string): El[] {
  const kids = new Map<string, El[]>()
  for (const e of all) if (!e.deleted_at && e.parent_id) kids.set(e.parent_id, [...(kids.get(e.parent_id) ?? []), e])
  const out: El[] = []
  const walk = (id: string) => { for (const c of kids.get(id) ?? []) { out.push(c); walk(c.id) } }
  walk(rootId)
  return out
}

/** The subsystem elements under a spacecraft and each one's leaf equipment. */
export function subsystemsOf(all: El[], scId: string): Array<{ el: El; parts: El[] }> {
  const subs = all.filter(e => e.parent_id === scId && !e.deleted_at && e.element_type === 'subsystem')
  return subs.map(el => {
    const d = descendants(all, el.id)
    const leaves = d.filter(x => !d.some(y => y.parent_id === x.id))
    return { el, parts: leaves }
  })
}

/** Mass and power of a subsystem: leaf roll-up (× quantity) when it has equipment, else its own values. */
export function rollup(s: { el: El; parts: El[] }, field: 'mass_kg' | 'power_avg_w' | 'power_peak_w'): number | null {
  if (s.parts.length) {
    const vals = s.parts.map(p => {
      const v = n(p[field]) ?? (field === 'power_peak_w' ? n(p.power_avg_w) : null)
      return v === null ? null : v * q(p)
    })
    return vals.some(v => v !== null) ? vals.reduce<number>((a, v) => a + (v ?? 0), 0) : null
  }
  return n(s.el[field]) ?? (field === 'power_peak_w' ? n(s.el.power_avg_w) : null)
}

const kbPrefix = (e: El) => String(e.kb_component_id ?? '').split('-')[0]
const isSolar = (e: El) => kbPrefix(e) === 'sp' || n(e.performance?.power_eol_w) !== null || n(e.performance?.power_bol_w) !== null
const isBattery = (e: El) => kbPrefix(e) === 'bat' || n(e.performance?.capacity_wh) !== null
const isStarTracker = (e: El) => kbPrefix(e) === 'st' || /star ?tracker/i.test(e.name)
const isAntenna = (e: El) => kbPrefix(e) === 'ant' || /antenna/i.test(e.name)
const isThruster = (e: El) => ['thr', 'prop', 'pps'].includes(kbPrefix(e)) || /thruster/i.test(e.name)

// ─── Form factor ───

/** CDS rev 14.1 2.2.10 Table 1 (typical maximum mass) and the standard envelopes, metres [X, Y, Z]. */
export const CUBESAT_SIZES = [
  { u: '1U', maxKg: 2.0, size: [0.100, 0.100, 0.1135] },
  { u: '1.5U', maxKg: 3.0, size: [0.100, 0.100, 0.1702] },
  { u: '2U', maxKg: 4.0, size: [0.100, 0.100, 0.227] },
  { u: '3U', maxKg: 6.0, size: [0.100, 0.100, 0.3405] },
  { u: '6U', maxKg: 12.0, size: [0.100, 0.2263, 0.366] },
  { u: '12U', maxKg: 24.0, size: [0.2263, 0.2263, 0.366] },
] as const
/** Fallback system margin when the study's margin-ladder step is not known yet. The live
 *  value is the C2O default ladder of margin_policy.yaml (25 / 20 / 20 / 10 % at
 *  MDR / PRR–SRR / PDR / CDR), served by GET /api/studies/{id}/rules/margin-ladder. */
export const SYSTEM_MARGIN = 0.20

export interface FormFactor {
  label: string
  size: [number, number, number]
  massKg: number | null
  /** where the size came from: 'design' (dimensions on the element) or 'mass' (CDS table) */
  how: 'design' | 'mass' | 'default'
  fits: boolean
  maxKg: number | null
}

export function formFactor(sc: El | null, massKg: number | null, systemMargin: number = SYSTEM_MARGIN): FormFactor {
  const dims = sc?.dimensions ?? null
  const dx = n(dims?.x_m ?? dims?.length_m), dy = n(dims?.y_m ?? dims?.width_m), dz = n(dims?.z_m ?? dims?.height_m)
  if (dx && dy && dz) return { label: `${Math.round(dx * 1000)} × ${Math.round(dy * 1000)} × ${Math.round(dz * 1000)} mm`, size: [dx, dy, dz], massKg, how: 'design', fits: true, maxKg: null }
  const named = String(sc?.performance?.form_factor ?? '').toUpperCase().replace(/\s/g, '')
  const byName = CUBESAT_SIZES.find(s => s.u === named)
  if (byName) return { label: byName.u, size: [...byName.size] as [number, number, number], massKg, how: 'design', fits: massKg === null || massKg <= byName.maxKg, maxKg: byName.maxKg }
  if (massKg === null) { const s = CUBESAT_SIZES[3]; return { label: s.u, size: [...s.size] as [number, number, number], massKg, how: 'default', fits: true, maxKg: s.maxKg } }
  const need = massKg * (1 + systemMargin)
  const s = CUBESAT_SIZES.find(c => c.maxKg >= need) ?? CUBESAT_SIZES[CUBESAT_SIZES.length - 1]
  return { label: s.u, size: [...s.size] as [number, number, number], massKg, how: 'mass', fits: need <= s.maxKg, maxKg: s.maxKg }
}

// ─── Geometry (c2o.geometry/1) ───

export interface DesignGeometry {
  schema: 'c2o.geometry/1'
  spacecraft: string
  quaternion: { order: 'xyzw'; maps: 'eci_to_body' }
  bus: { size_m: [number, number, number] }
  body_panels: Array<{ face: string; normal: number[]; cell_area_m2: number }>
  wings: Array<{ id: string; face: string; mount_axis: number[]; panel_size_m: [number, number]; panels: number; cell_area_m2: number; deployed_bit: number }>
  array_drive?: { axis: number[]; normal_at_0deg: number[]; normal_at_90deg: number[]; angle_param: string }
  payload?: { boresight: number[]; position_m: number[]; fov_deg: number }
  star_trackers: Array<{ id: string; boresight: number[]; position_m: number[]; fov_deg: number }>
  star_tracker_sun_exclusion_deg: number
  star_tracker_earth_exclusion_deg: number
  antennas: Array<{ id: string; kind: 'patch' | 'dipole'; position_m: number[]; boresight: number[]; length_m?: number }>
  thrusters: Array<{ id: string; position_m: number[]; thrust_axis: number[] }>
  /** where each part came from (not part of the c2o.geometry schema; views ignore it) */
  provenance: string[]
}

export function designGeometry(all: El[], sc: El | null, ff: FormFactor, study: any): DesignGeometry {
  const parts = sc ? descendants(all, sc.id) : []
  const [sx, sy, sz] = ff.size
  const prov: string[] = []
  // solar: deployable -> two wings on ±Y; body-mounted -> cells shared over ±X ±Y +Z by face area
  const solar = parts.filter(isSolar)
  const deploy = solar.filter(e => /deploy/i.test(String(e.performance?.deployment ?? '')) && !/body/i.test(String(e.performance?.deployment ?? '')))
  const body = solar.filter(e => !deploy.includes(e))
  const area = (list: El[]) => list.reduce((a, e) => a + (n(e.performance?.area_m2) ?? 0) * q(e), 0)
  const bodyArea = area(body)
  const faces = [
    { face: 'px', normal: [1, 0, 0], a: sy * sz }, { face: 'mx', normal: [-1, 0, 0], a: sy * sz },
    { face: 'py', normal: [0, 1, 0], a: sx * sz }, { face: 'my', normal: [0, -1, 0], a: sx * sz },
    { face: 'pz', normal: [0, 0, 1], a: sx * sy }, { face: 'mz', normal: [0, 0, -1], a: 0 },
  ]
  const faceSum = faces.reduce((a, f) => a + f.a, 0)
  const body_panels = faces.map(f => ({ face: f.face, normal: f.normal, cell_area_m2: bodyArea > 0 ? +(bodyArea * f.a / faceSum).toFixed(4) : 0 }))
  if (body.length) prov.push(`body cells: ${body.map(e => e.name).join(', ')}`)
  const wings: DesignGeometry['wings'] = []
  if (deploy.length) {
    const perWing = area(deploy) / 2 || 0.06
    const panels = 2
    const wid = sz * 0.93
    const len = Math.max(0.05, perWing / panels / wid)
    wings.push({ id: 'wing_py', face: 'py', mount_axis: [0, 1, 0], panel_size_m: [len, wid], panels, cell_area_m2: +perWing.toFixed(4), deployed_bit: 0 })
    wings.push({ id: 'wing_my', face: 'my', mount_axis: [0, -1, 0], panel_size_m: [len, wid], panels, cell_area_m2: +perWing.toFixed(4), deployed_bit: 1 })
    prov.push(`wings: ${deploy.map(e => e.name).join(', ')}`)
  }
  const sada = parts.find(e => /sada|array drive/i.test(e.name) || kbPrefix(e) === 'sada')
  // payload: imager boresight on the nadir face (-Z)
  const pl = all.find(e => e.parent_id === sc?.id && e.subsystem_domain === 'payload' && !e.deleted_at)
  const fovReq = n(study?.requirements?.payloads?.[0]?.fov_deg)
  const payload = pl ? { boresight: [0, 0, -1], position_m: [0, 0, -sz / 2], fov_deg: fovReq ?? 10 } : undefined
  if (pl) prov.push(fovReq !== null ? 'payload field of view: mission requirements' : 'payload field of view: C2O default 10°')
  // star trackers on +Z, canted alternately
  const sts = parts.filter(isStarTracker)
  const star_trackers = sts.flatMap((e, i) => Array.from({ length: q(e) }, (_, k) => {
    const j = i + k
    const fov = Math.max(...([] as number[]).concat(e.performance?.fov_deg ?? 12).map(Number).filter(Number.isFinite)) || 12
    const b = j === 0 ? [0, 0, 1] : [0, 0.70710678, 0.70710678]
    return { id: `st${j + 1}`, boresight: b, position_m: [sx / 4, (j === 0 ? -1 : 1) * sy / 4, sz / 2], fov_deg: fov }
  }))
  const stExcl = n(sts[0]?.performance?.sun_exclusion_deg) ?? 15
  if (sts.length) prov.push(`star trackers: ${sts.map(e => e.name).join(', ')} on +Z`)
  // antennas: dipoles deploy from -X near +Z, patches on the nadir face
  const ants = parts.filter(isAntenna)
  const antennas = ants.map((e, i) => {
    const type = String(e.performance?.type ?? e.name).toLowerCase()
    return /patch/.test(type)
      ? { id: `ant${i + 1}`, kind: 'patch' as const, position_m: [0, sy / 4, -sz / 2], boresight: [0, 0, -1] }
      : { id: `ant${i + 1}`, kind: 'dipole' as const, position_m: [-sx / 2, 0, sz * 0.4], boresight: [-1, 0, 0], length_m: 0.17 }
  })
  if (ants.length) prov.push(`antennas: ${ants.map(e => e.name).join(', ')}`)
  const thr = parts.filter(isThruster)
  const thrusters = thr.map((_, i) => ({ id: `thr${i + 1}`, position_m: [-sx / 2, 0, 0], thrust_axis: [1, 0, 0] }))
  return {
    schema: 'c2o.geometry/1', spacecraft: sc?.name ?? 'Spacecraft',
    quaternion: { order: 'xyzw', maps: 'eci_to_body' },
    bus: { size_m: [sx, sy, sz] }, body_panels, wings,
    ...(sada && wings.length ? { array_drive: { axis: [0, 1, 0], normal_at_0deg: [1, 0, 0], normal_at_90deg: [0, 0, 1], angle_param: 'design' } } : {}),
    ...(payload ? { payload } : {}),
    star_trackers, star_tracker_sun_exclusion_deg: stExcl, star_tracker_earth_exclusion_deg: 25,
    antennas, thrusters, provenance: prov,
  }
}

// ─── Power (powerflow.js model) ───

/** Load groups of the power-flow mimic (its translated DYNAMIC_KEYS) and the design domains feeding them. */
const GROUPS: Array<{ id: string; domains: string[]; overview: string }> = [
  { id: 'Platform', domains: ['obc', 'structure'], overview: 'obdh' },
  { id: 'Comms', domains: ['ttc'], overview: 'ttc' },
  { id: 'Payload', domains: ['payload'], overview: 'payload' },
  { id: 'Thermal', domains: ['thermal'], overview: 'tcs' },
  { id: 'AOCS', domains: ['aocs'], overview: 'aocs' },
  { id: 'Propulsion', domains: ['propulsion'], overview: 'prop' },
]
export const DOD_LIMIT_PCT = 25

export interface PowerAssumptions {
  altKm: number; periodS: number; eclipseS: number; betaDeg: number; arrayW: number | null; arrayHow: string
  capWh: number | null; busV: number | null; consW: number; peakW: number; dodPct: number | null
}

export function designPower(all: El[], sc: El | null, study: any, pc: PowerCase) {
  const subs = sc ? subsystemsOf(all, sc.id) : []
  const parts = sc ? descendants(all, sc.id) : []
  const design = (v: number | null, units: string, src: string) => qty(v, units, { verdict: 'design', src, ground: false })
  const altKm = n(study?.requirements?.orbit?.altitude_km) ?? 500
  const beta = 0
  const T = periodFromAltS(altKm)
  const Tecl = T * eclipseFraction(altKm, beta)
  // generation: end-of-life array power, sunlit (no cosine loss: arrays assumed sun-pointed in this case)
  const solar = parts.filter(isSolar)
  const arrayW = solar.length ? solar.reduce((a, e) => a + (n(e.performance?.power_eol_w) ?? n(e.performance?.power_bol_w) ?? 0) * q(e), 0) : null
  const eps = parts.find(e => n(e.performance?.max_solar_input_w) !== null || /^eps-/.test(String(e.kb_component_id ?? '')))
  const rails = ([] as unknown[]).concat(eps?.performance?.bus_voltage_v ?? []).map(Number).filter(Number.isFinite)
  const bat = parts.filter(isBattery)
  const capWh = bat.length ? bat.reduce((a, e) => a + (n(e.performance?.capacity_wh) ?? 0) * q(e), 0) : null
  const batV = bat.length ? n(bat[0].performance?.voltage_v?.nominal ?? bat[0].performance?.voltage_v) : null
  const busV = batV ?? (rails.length ? Math.max(...rails) : null)

  const loadW = (s: { el: El; parts: El[] }) => rollup(s, pc === 'peak' ? 'power_peak_w' : 'power_avg_w')
  const groups = GROUPS.map(g => {
    const ss = subs.filter(s => g.domains.includes(String(s.el.subsystem_domain)))
    const lines = ss.flatMap(s => s.parts
      .filter(p => (n(pc === 'peak' ? p.power_peak_w ?? p.power_avg_w : p.power_avg_w) ?? 0) > 0)
      .map(p => {
        const w = (n(pc === 'peak' ? p.power_peak_w ?? p.power_avg_w : p.power_avg_w) ?? 0) * q(p)
        return { id: p.id, label: p.name, group: g.id, on: true, onVerdict: 'design', w: design(w, 'W', `design: ${p.name}${q(p) > 1 ? ` × ${q(p)}` : ''}`) }
      }))
    const total = ss.length ? ss.reduce((a, s) => a + (loadW(s) ?? 0), 0) : null
    return { id: g.id, label: g.id, subsystem: g.overview, lines, w: design(total, 'W', 'design: Σ equipment power') }
  }).filter(g => g.w.v !== null)
  const consW = groups.reduce((a, g) => a + (g.w.v ?? 0), 0)
  const peakW = subs.reduce((a, s) => a + (rollup(s, 'power_peak_w') ?? 0), 0)

  const sunlit = pc !== 'eclipse'
  const genW = sunlit ? arrayW : 0
  const cons = design(consW, 'W', pc === 'peak' ? 'design: Σ peak power' : 'design: Σ average power')
  const gen = design(genW, 'W', sunlit ? 'design: Σ array EOL power' : 'eclipse: arrays dark')
  const batW = genW === null ? null : genW - consW
  const dodPct = capWh ? (consW * Tecl / 3600) / capWh * 100 : null
  // SoC: sunlit and peak start full; eclipse shows the end of the eclipse, the worst point of the orbit
  const socV = capWh ? (sunlit ? 100 : Math.max(0, 100 - (dodPct ?? 0))) : null
  const socMin = 100 - DOD_LIMIT_PCT
  const ein = arrayW === null ? null : arrayW * (T - Tecl) / 3600
  const eout = consW * T / 3600
  const balance = {
    periodS: T, eclipseS: Tecl, sunGenHow: 'design',
    inWh: design(ein, 'Wh', 'design: array EOL power × sunlit time'),
    outWh: design(eout, 'Wh', 'design: average consumption × period'),
    netWh: design(ein === null ? null : ein - eout, 'Wh', 'design: in − out (before charge efficiency)'),
  }
  const orbit = {
    alt: design(altKm, 'km', 'mission requirements: orbit altitude'),
    lat: qty(null), lon: qty(null),
    periodS: design(T, 's', 'Kepler period from altitude'),
    inEclipse: !sunlit, eclipseSource: 'design case',
    toEntryS: qty(null, 's'), toExitS: qty(null, 's'),
    eclipseS: design(Tecl, 's', 'cylindrical shadow, β = 0 (worst case)'),
    betaDeg: design(beta, '°', 'worst case'), betaCritDeg: betaCriticalDeg(altKm),
  }
  const sources = solar.slice(0, 4).map(e => ({
    id: e.id, label: e.name,
    w: design(sunlit ? (n(e.performance?.power_eol_w) ?? n(e.performance?.power_bol_w) ?? 0) * q(e) : 0, 'W', `design: ${e.name} EOL power${q(e) > 1 ? ` × ${q(e)}` : ''}`),
  }))
  const model = {
    busV: design(busV, 'V', batV !== null ? 'design: battery nominal voltage' : 'design: highest EPS rail'),
    gen, cons,
    margin: design(genW === null ? null : genW - consW, 'W', 'design: generation − consumption'),
    sources, loads: groups.flatMap(g => g.lines), groups,
    battery: {
      i: design(batW !== null && busV ? batW / busV : null, 'A', 'design: battery power ÷ bus voltage'),
      v: design(batV, 'V', 'design: battery nominal voltage'),
      w: design(batW, 'W', 'design: generation − consumption (+ = charging)'),
      soc: design(socV, '%', sunlit ? 'design: full at eclipse entry' : 'design: at eclipse exit'),
      dod: design(capWh ? (sunlit ? 0 : dodPct) : null, '%', 'design: eclipse energy ÷ capacity'),
      dir: batW === null ? null : batW > 0.05 ? 'charge' : batW < -0.05 ? 'discharge' : 'idle',
      capWh: capWh ?? 0, temp: qty(null, '°C'),
      socMin, socFloor: Math.max(0, socMin - 10), dodMax: DOD_LIMIT_PCT,
      capSrc: bat.length ? `design: ${bat.map(e => e.name).join(', ')}` : 'no battery in the design',
    },
    shedStage: qty(null),
    orbit, balance,
    pred: {
      socAtExit: design(capWh ? 100 - (dodPct ?? 0) : null, '%', 'design: full at entry − eclipse energy'),
      dodAtExit: design(dodPct, '%', 'design: eclipse energy ÷ capacity'),
      timeToMinSocS: qty(null, 's'),
      minReachedBeforeExit: dodPct === null ? null : dodPct > DOD_LIMIT_PCT,
    },
  }
  const assumptions: PowerAssumptions = {
    altKm, periodS: T, eclipseS: Tecl, betaDeg: beta, arrayW, arrayHow: solar.map(e => e.name).join(', '),
    capWh, busV, consW, peakW, dodPct,
  }
  return { model, assumptions }
}

// ─── Overview (overview.js model) ───

const OV_DOMAIN: Record<string, string> = { power: 'eps', eps: 'eps', aocs: 'aocs', obc: 'obdh', thermal: 'tcs', propulsion: 'prop', payload: 'payload', ttc: 'ttc' }
export const OVERVIEW_IDS = ['eps', 'aocs', 'obdh', 'tcs', 'prop', 'payload', 'ttc'] as const

export interface SubsystemFlags { state: 'nominal' | 'caution' | 'alarm'; note?: string }

export function designOverview(all: El[], sc: El | null, opts: {
  t: (k: string, o?: any) => string
  allocations: Array<{ element_id: string; budget_type: string; allocation_value: number }>
  flags: Record<string, SubsystemFlags>
  pc: PowerCase
  groundStation?: string | null
}) {
  const { t } = opts
  const subs = sc ? subsystemsOf(all, sc.id) : []
  const alloc = (id: string, type: string) => opts.allocations.find(a => a.element_id === id && a.budget_type === type)?.allocation_value ?? null
  const subsystems: Record<string, any> = {}
  for (const id of OVERVIEW_IDS) subsystems[id] = { hidden: true, state: 'nominal' }
  for (const s of subs) {
    const ov = OV_DOMAIN[String(s.el.subsystem_domain)]
    if (!ov) continue
    const mass = rollup(s, 'mass_kg')
    const pw = rollup(s, opts.pc === 'peak' ? 'power_peak_w' : 'power_avg_w')
    const row = (label: string, v: number | null, units: string, a: number | null, digits: number) => {
      const limits = a ? { yellow_high: a * 0.9, red_high: a, yellow_low: 0, red_low: 0 } : undefined
      const limitState = a && v !== null ? (v > a ? 'alarm' : v > a * 0.9 ? 'caution' : '') : ''
      return { label, digits, limits, limitState, q: qty(v, units, { verdict: 'design', src: a ? `design roll-up; allocation ${a} ${units}` : 'design roll-up' }) }
    }
    const f = opts.flags[s.el.id]
    const massRow = row(t('Mass'), mass, 'kg', alloc(s.el.id, 'mass'), 2)
    const powRow = row(opts.pc === 'peak' ? t('Peak power') : t('Power'), pw, 'W', alloc(s.el.id, opts.pc === 'peak' ? 'power_peak' : 'power'), 1)
    const worstRow = [massRow, powRow].some(r => r.limitState === 'alarm') ? 'alarm' : [massRow, powRow].some(r => r.limitState === 'caution') ? 'caution' : 'nominal'
    const rank = { nominal: 0, caution: 1, alarm: 2 } as const
    const st = rank[worstRow as keyof typeof rank] >= rank[f?.state ?? 'nominal'] ? worstRow : f!.state
    subsystems[ov] = {
      state: st, elementId: s.el.id, alarms: { a: st === 'alarm' ? 1 : 0, w: st === 'caution' ? 1 : 0 },
      rows: [massRow, powRow], mode: f?.note ?? '',
    }
  }
  return {
    mode: { label: opts.pc === 'peak' ? 'SCIENCE' : 'NOMINAL', contingency: false, src: 'design case' },
    aocsMode: null,
    eclipse: opts.pc === 'eclipse',
    contact: opts.pc === 'peak',
    gs: opts.groundStation ?? null,
    subsystems,
  }
}

// ─── Attitude (attitude3d.js model): nominal nadir pointing ───

/** LVLH = ECI for the picture (identity), body = BODY_FROM_LVLH: a 180° turn about X, q = [1 0 0 0]. */
export function designAttitude(pc: PowerCase) {
  const qNadir = [1, 0, 0, 0]
  const sunlit = pc !== 'eclipse'
  // sun above the orbit plane on the -Y side (beta about 45°), clear of the +Z star-tracker exclusion
  const sun = [0.5, -0.7, 0.5]
  const nrm = Math.hypot(...sun)
  return {
    q: { q: qNadir, valid: true, verdict: 'design', ageS: null },
    ref: { q: qNadir, valid: true },
    frame: 'LVLH_NADIR',
    lvlh: { q: [0, 0, 0, 1] },
    sun: { v: sun.map(c => c / nrm), valid: sunlit, reason: sunlit ? undefined : 'sun sensors not valid (eclipse or off)' },
    nadir: { v: [0, 0, -1], valid: true },
    illum: { sunFraction: sunlit ? 1 : 0, verdict: 'design' },
    errLimits: { warn: 1, alarm: 5 },
  }
}
