/**
 * Text the shared 3D stack module (src/viz/stack3d.js, generated from shared/ui-viz)
 * passes to our t(). The module is plain JS outside the SpaceCDF i18n scanner, so its
 * English keys are listed here; French in locales/fr.u13.json (and, for mission
 * control, smo_common/ui/i18n/fr.json — the same words).
 */
// i18n-keys
const STACK3D_KEYS_1 = [
  "+Z zenith",
  "3D view unavailable: {{reason}}. The elevation and face map show the same layout.",
  "Body frame: +X velocity, +Y orbit normal, +Z zenith (−Z nadir); origin at the envelope centre",
  "Centre (mm)",
  "CoG",
  "Configuration",
  "Deployed",
  "Drag to orbit, wheel or +/− to zoom, arrow keys to rotate.",
  "Exploded view",
  "Mass (kg)",
  "Mount",
  "No stack layout yet",
  "Reset view",
  "Stack in 3D",
  "Stack layout values",
  "Stowed",
  "Unit",
  "WebGL could not start",
  "WebGL is not available in this browser",
  "Where",
  "column {{c}}, slot {{s}}",
  "face {{f}}",
  "nadir",
  "the WebGL context was lost",
  "{{n}} units, {{m}} kg, centre of gravity {{x}}, {{y}}, {{z}} mm from the envelope centre.",
]
// i18n-keys
const STACK3D_KEYS_2 = [
  "PC/104 board", "PC/104 module", "U module", "face panel", "deployable", "bracket", "structure", "distributed",
  "Payload", "Data handling", "AOCS", "Power", "Thermal", "TT&C", "Propulsion", "Structure", "Other",
]

export const STACK3D_KEYS: readonly string[] = [...STACK3D_KEYS_1, ...STACK3D_KEYS_2]
