// Labels of the mode vocabulary, translated with t() at render time.
// English text is the i18n key
export const KIND_LABELS: Record<string, string> = {
  leop: 'LEOP', commissioning: 'Commissioning', nominal: 'Nominal', imaging: 'Imaging', downlink: 'Downlink',
  safe: 'Safe', survival: 'Survival', custom: 'Custom',
}
// English text is the i18n key
export const POINTING_LABELS: Record<string, string> = {
  tumbling: 'Tumbling', sun: 'Sun-pointing', nadir: 'Nadir-pointing', target: 'Target-pointing',
  station: 'Station-pointing', inertial: 'Inertial',
}
// English text is the i18n key
export const TRIGGER_LABELS: Record<string, string> = {
  ground_tc: 'Ground command', autonomous: 'Autonomous (monitor)', timer: 'Timer / time-tag', event: 'Event',
}
// English text is the i18n key
export const STATE_LABELS: Record<string, string> = { off: 'Off', standby: 'Standby', nominal: 'On', peak: 'Peak' }
// English text is the i18n key
export const STATUS_LABELS: Record<string, string> = {
  suggested: 'Suggested', accepted: 'Accepted', edited: 'Edited', rejected: 'Rejected', stale: 'Stale, review',
}
// English text is the i18n key
export const PROPOSAL_KIND_LABELS: Record<string, string> = {
  monitor: 'Monitors (ST[12]-like)', action: 'Event-actions (ST[19]-like)', risk: 'Risk register entries', heater: 'Heaters',
}
// English text is the i18n key
export const PHASE_LABELS: Record<string, string> = {
  leop: 'LEOP', commissioning: 'Commissioning', nominal: 'Operations', any: 'Any phase',
}
