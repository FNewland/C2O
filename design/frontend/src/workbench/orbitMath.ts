/**
 * Small orbit formulas the screens show next to the design loop's own numbers
 * (pure; runs under plain Node in tests).
 */
export const R_EARTH_KM = 6378.137
export const MU_KM3_S2 = 398600.4418
export const J2 = 1.08262668e-3
/** Earth's mean motion around the Sun (rad/s): the node rate a sun-synchronous orbit needs. */
export const SSO_RATE = (2 * Math.PI) / (365.2422 * 86400)

/** Inclination (deg) of a circular sun-synchronous orbit at altitude h, or null when none exists. */
export function ssoInclinationDeg(altitudeKm: number): number | null {
  const a = R_EARTH_KM + altitudeKm
  const n = Math.sqrt(MU_KM3_S2 / (a * a * a))
  const cosI = -SSO_RATE / (1.5 * J2 * (R_EARTH_KM / a) ** 2 * n)
  if (cosI < -1 || cosI > 1) return null
  return (Math.acos(cosI) * 180) / Math.PI
}

