/**
 * Canonical interface vocabulary (SpaceCDF brief, 2 Nov 2026).
 *
 * One list for the whole frontend: the Interfaces panel, the block diagram,
 * the ICD and the Spacecraft view. It mirrors the backend enum
 * (spacecdf_common, served at GET /api/studies/{sid}/interfaces/types); the
 * server list wins when it is available, this table is the offline default
 * and the source of the glyph and colour.
 *
 * Natures follow ECSS-E-ST-10-24C Annex E where they apply (mechanical =
 * Structural + Mechanisms, data = Data representation + Software +
 * Communications protocol). The reference-data fields per type are the
 * Annex E attribute lists cut down to what a CubeSat design team fills in.
 */

export const INTERFACE_TYPES = [
  'power', 'data', 'rf', 'mechanical', 'thermal', 'timing', 'optical', 'fluid', 'electrical_signal',
] as const
export type InterfaceType = typeof INTERFACE_TYPES[number]

export type InterfaceStatus = 'suggested' | 'accepted' | 'rejected'
/** "user" | "import" | "rule:<rule_id>" */
export type InterfaceOrigin = string

export interface Bilingual { en: string; fr: string }

/** An interface as the frontend uses it (normalised from the API object). */
export interface DesignInterface {
  id: string
  study_id?: string
  name: string
  type: InterfaceType
  subtype: string | null
  direction: string
  from_element_id: string
  to_element_id: string
  properties: Record<string, unknown>
  diagram_label?: string | null
  exchange_item_ids_json?: string[]
  status: InterfaceStatus
  origin: InterfaceOrigin
  rationale: Bilingual | null
  standard_ref: string | null
  version?: number
  /** The type string the server sent, before normalisation. */
  raw_type: string
}

/** Old spellings still in saved studies and imports (codebase audit §2.6). */
const ALIASES: Record<string, InterfaceType> = {
  electrical: 'power', power: 'power', eps: 'power',
  data: 'data', command: 'data', software: 'data', tm_tc: 'data', tmtc: 'data', bus: 'data',
  rf: 'rf', radio: 'rf', link: 'rf', communications: 'rf',
  mechanical: 'mechanical', structural: 'mechanical', structure: 'mechanical', mechanisms: 'mechanical',
  thermal: 'thermal',
  timing: 'timing', pps: 'timing', clock: 'timing',
  optical: 'optical',
  fluid: 'fluid', propulsion: 'fluid', propellant: 'fluid', pressurant: 'fluid',
  electrical_signal: 'electrical_signal', signal: 'electrical_signal', discrete: 'electrical_signal',
}

export function canonicalType(raw: unknown): InterfaceType {
  const k = String(raw ?? '').trim().toLowerCase().replace(/[\s/-]+/g, '_')
  return ALIASES[k] ?? 'data'
}

export function isRuleOrigin(origin: string | null | undefined): boolean {
  return !!origin && origin.startsWith('rule:')
}
export function ruleId(origin: string | null | undefined): string | null {
  return isRuleOrigin(origin) ? origin!.slice(5) : null
}

function normStatus(s: unknown): InterfaceStatus {
  return s === 'suggested' || s === 'rejected' ? s : 'accepted'   // 'defined' and older values count as accepted
}

function normRationale(r: unknown): Bilingual | null {
  if (!r) return null
  if (typeof r === 'string') return { en: r, fr: r }
  if (typeof r === 'object') {
    const o = r as Record<string, unknown>
    const en = typeof o.en === 'string' ? o.en : ''
    const fr = typeof o.fr === 'string' && o.fr ? o.fr : en
    return en || fr ? { en: en || fr, fr } : null
  }
  return null
}

/** Normalise one API interface object. Unknown fields pass through untouched on the server. */
export function normaliseInterface(raw: any): DesignInterface {
  const rawType = String(raw?.type ?? raw?.interface_type ?? '')
  const props = (raw?.properties && typeof raw.properties === 'object') ? raw.properties : {}
  return {
    ...raw,
    name: raw?.name ?? '',
    type: canonicalType(rawType),
    raw_type: rawType,
    subtype: raw?.subtype ?? (props as any).subtype ?? null,
    direction: raw?.direction ?? 'bidirectional',
    properties: props,
    status: normStatus(raw?.status),
    origin: typeof raw?.origin === 'string' && raw.origin ? raw.origin : 'user',
    rationale: normRationale(raw?.rationale),
    standard_ref: raw?.standard_ref ?? null,
  }
}

/** Pick the text in the UI language (data from the server, so not an i18n key). */
export function pickLang(b: Bilingual | null | undefined, lang: string): string {
  if (!b) return ''
  return (lang.startsWith('fr') ? b.fr || b.en : b.en || b.fr) || ''
}

// ─── Per-type presentation ────────────────────────────────────────────────

export interface TypeField { key: string; label: string; placeholder?: string }
export interface TypeMeta {
  id: InterfaceType
  /** English text is the i18n key */
  label: string
  /** Short legend / edge label, also an i18n key */
  short: string
  color: string
  /** Annex E nature(s) this type maps to; standard titles are not translated. */
  annexE: string
  fields: TypeField[]
  subtypes: string[]
}

/** Type names. */
// English text is the i18n key
const TYPE_LABEL: Record<string, string> = {
  power: 'Power',
  data: 'Data (TM/TC)',
  rf: 'RF',
  mechanical: 'Mechanical',
  thermal: 'Thermal',
  timing: 'Timing (PPS)',
  optical: 'Optical',
  fluid: 'Fluid (propellant)',
  electrical_signal: 'Discrete signal',
}
/** Short names for the legend and edge labels. */
// English text is the i18n key
const TYPE_SHORT: Record<string, string> = {
  power: 'Power',
  data: 'Data',
  rf: 'RF',
  mechanical: 'Mech.',
  thermal: 'Thermal',
  timing: 'PPS',
  optical: 'Optical',
  fluid: 'Fluid',
  electrical_signal: 'Discrete',
}
/** Reference-data field labels. */
// English text is the i18n key
const FIELD_LABEL: Record<string, string> = {
  rail_voltage: 'Rail voltage (V)',
  current_a: 'Current (A)',
  power_w: 'Power (W)',
  switched: 'Switched (LCL)',
  connector: 'Connector',
  protocol: 'Protocol',
  data_rate_bps: 'Data rate (bit/s)',
  data_format: 'Data format',
  address: 'Bus address',
  band: 'Band',
  frequency_mhz: 'Frequency (MHz)',
  power_dbm: 'TX power (dBm)',
  polarisation: 'Polarisation',
  mount_type: 'Mount type',
  fastener: 'Fasteners',
  torque_nm: 'Torque (Nm)',
  material: 'Material',
  conductance_w_k: 'Conductance (W/K)',
  heat_flow_w: 'Heat flow (W)',
  interface_temp_c: 'Interface temp (°C)',
  strap_type: 'Thermal strap',
  signal: 'Signal',
  accuracy_us: 'Accuracy (µs)',
  boresight: 'Boresight',
  fov_deg: 'Field of view (°)',
  keep_out: 'Keep-out',
  medium: 'Medium',
  pressure_bar: 'Pressure (bar)',
  fitting: 'Fitting',
  inhibit_count: 'Inhibits',
  level: 'Level',
}

// Labels come from the tables above; placeholders are technical examples (not translated).
export const TYPE_META: Record<InterfaceType, TypeMeta> = {
  power: {
    id: 'power', label: TYPE_LABEL.power, short: TYPE_SHORT.power, color: 'var(--cat-4)', annexE: 'Electrical',
    subtypes: ['regulated', 'battery_bus', 'switched', 'array_input'],
    fields: [
      { key: 'rail_voltage', label: FIELD_LABEL.rail_voltage, placeholder: '3.3 / 5 / 12' },
      { key: 'current_a', label: FIELD_LABEL.current_a, placeholder: '0.5' },
      { key: 'power_w', label: FIELD_LABEL.power_w, placeholder: '2.5' },
      { key: 'switched', label: FIELD_LABEL.switched, placeholder: 'LCL' },
      { key: 'connector', label: FIELD_LABEL.connector, placeholder: 'Micro-D 9' },
    ],
  },
  data: {
    id: 'data', label: TYPE_LABEL.data, short: TYPE_SHORT.data, color: 'var(--cat-2)', annexE: 'Data representation; Software',
    subtypes: ['tm_tc', 'payload_data', 'bus'],
    fields: [
      { key: 'protocol', label: FIELD_LABEL.protocol, placeholder: 'I2C / UART / CAN / SpaceWire' },
      { key: 'data_rate_bps', label: FIELD_LABEL.data_rate_bps, placeholder: '115200' },
      { key: 'data_format', label: FIELD_LABEL.data_format, placeholder: 'CCSDS' },
      { key: 'address', label: FIELD_LABEL.address, placeholder: '0x20' },
      { key: 'connector', label: FIELD_LABEL.connector, placeholder: 'PC/104' },
    ],
  },
  rf: {
    id: 'rf', label: TYPE_LABEL.rf, short: TYPE_SHORT.rf, color: 'var(--cat-6)', annexE: 'Communications',
    subtypes: ['coax', 'space_ground'],
    fields: [
      { key: 'band', label: FIELD_LABEL.band, placeholder: 'UHF / S / X' },
      { key: 'frequency_mhz', label: FIELD_LABEL.frequency_mhz, placeholder: '437.5' },
      { key: 'power_dbm', label: FIELD_LABEL.power_dbm, placeholder: '30' },
      { key: 'polarisation', label: FIELD_LABEL.polarisation, placeholder: 'RHCP' },
      { key: 'connector', label: FIELD_LABEL.connector, placeholder: 'SMA / MMCX' },
    ],
  },
  mechanical: {
    id: 'mechanical', label: TYPE_LABEL.mechanical, short: TYPE_SHORT.mechanical, color: 'var(--cat-8)', annexE: 'Structural; Mechanisms',
    subtypes: ['mount', 'deployer', 'launcher'],
    fields: [
      { key: 'mount_type', label: FIELD_LABEL.mount_type, placeholder: 'PC/104' },
      { key: 'fastener', label: FIELD_LABEL.fastener, placeholder: 'M3 × 8 A4' },
      { key: 'torque_nm', label: FIELD_LABEL.torque_nm, placeholder: '0.5' },
      { key: 'material', label: FIELD_LABEL.material, placeholder: 'Al 6061-T6' },
    ],
  },
  thermal: {
    id: 'thermal', label: TYPE_LABEL.thermal, short: TYPE_SHORT.thermal, color: 'var(--cat-5)', annexE: 'Thermal control',
    subtypes: ['conductive', 'radiative', 'heater'],
    fields: [
      { key: 'conductance_w_k', label: FIELD_LABEL.conductance_w_k, placeholder: '0.5' },
      { key: 'heat_flow_w', label: FIELD_LABEL.heat_flow_w, placeholder: '2.0' },
      { key: 'interface_temp_c', label: FIELD_LABEL.interface_temp_c, placeholder: '20' },
      { key: 'strap_type', label: FIELD_LABEL.strap_type, placeholder: 'Cu / Al' },
    ],
  },
  timing: {
    id: 'timing', label: TYPE_LABEL.timing, short: TYPE_SHORT.timing, color: 'var(--cat-1)', annexE: 'Electrical (signal)',
    subtypes: ['pps', 'clock'],
    fields: [
      { key: 'signal', label: FIELD_LABEL.signal, placeholder: '1 PPS, 3.3 V CMOS' },
      { key: 'accuracy_us', label: FIELD_LABEL.accuracy_us, placeholder: '1' },
    ],
  },
  optical: {
    id: 'optical', label: TYPE_LABEL.optical, short: TYPE_SHORT.optical, color: 'var(--cat-1)', annexE: 'Optical',
    subtypes: ['boresight', 'fov'],
    fields: [
      { key: 'boresight', label: FIELD_LABEL.boresight, placeholder: '-Z' },
      { key: 'fov_deg', label: FIELD_LABEL.fov_deg, placeholder: '30' },
      { key: 'keep_out', label: FIELD_LABEL.keep_out, placeholder: '15°' },
    ],
  },
  fluid: {
    id: 'fluid', label: TYPE_LABEL.fluid, short: TYPE_SHORT.fluid, color: 'var(--cat-7)', annexE: 'Propulsion; Hydraulics',
    subtypes: ['propellant', 'pressurant'],
    fields: [
      { key: 'medium', label: FIELD_LABEL.medium, placeholder: 'ADN / xenon / N2' },
      { key: 'pressure_bar', label: FIELD_LABEL.pressure_bar, placeholder: '20' },
      { key: 'fitting', label: FIELD_LABEL.fitting, placeholder: '1/8" AN' },
    ],
  },
  electrical_signal: {
    id: 'electrical_signal', label: TYPE_LABEL.electrical_signal, short: TYPE_SHORT.electrical_signal, color: 'var(--cat-3)', annexE: 'Electrical (signal)',
    subtypes: ['deployment_switch', 'inhibit', 'rbf', 'release', 'umbilical'],
    fields: [
      { key: 'signal', label: FIELD_LABEL.signal, placeholder: 'NC, 3.3 V' },
      { key: 'inhibit_count', label: FIELD_LABEL.inhibit_count, placeholder: '3' },
      { key: 'level', label: FIELD_LABEL.level, placeholder: '3.3 V' },
    ],
  },
}

/** i18n keys of the subtype labels (enum values are not shown raw). */
// English text is the i18n key
export const SUBTYPE_LABELS: Record<string, string> = {
  regulated: 'Regulated rail', battery_bus: 'Battery bus', switched: 'Switched rail', array_input: 'Array input',
  tm_tc: 'TM/TC', payload_data: 'Payload data', bus: 'Bus',
  coax: 'Coax', space_ground: 'Space–ground link',
  mount: 'Mount', deployer: 'Deployer', launcher: 'Launcher',
  conductive: 'Conductive', radiative: 'Radiative', heater: 'Heater',
  pps: 'PPS', clock: 'Clock',
  boresight: 'Boresight', fov: 'Field of view',
  propellant: 'Propellant', pressurant: 'Pressurant',
  deployment_switch: 'Deployment switch', inhibit: 'Inhibit', rbf: 'Remove-before-flight', release: 'Release', umbilical: 'Umbilical',
}

/** Exchange-item kinds: the backend's EXCHANGE_ITEM_KINDS (db/exchange_item_repo.py). */
export const EXCHANGE_KINDS = ['data', 'power', 'rf', 'thermal', 'mechanical', 'optical', 'fluid'] as const
