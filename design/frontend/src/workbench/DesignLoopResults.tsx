/**
 * Analyses › Design loop: the key results of the last design-loop run (Nov 2026
 * worksheet/screen audit). The design agents computed these (orbit, power sizing,
 * link and data, delta-v, cost split) but no screen showed them, so Worksheets 2.3,
 * 3.1, 3.3, 3.4 and 4.4 asked students to "compare with SpaceCDF" against nothing.
 *
 * Read-only: these are the agents' estimates from the run's series
 * (GET /api/analyses/runs/{run_id}/series → series.parameters), not approved design
 * values. Two rows are derived here from the run's own numbers and say so:
 * semi-major axis a = R⊕ + h and the sun-synchronous inclination for that altitude.
 * Each group carries a data-where anchor for the logbook's "Where in SpaceCDF" links.
 */
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import type { AnalysisRun } from '../types/analyses'
import { fmtDate } from '../i18n'
import './designLoop.css'
import { R_EARTH_KM, ssoInclinationDeg } from './orbitMath'

const API = '/api'

type Params = Record<string, { value: unknown; unit?: string | null }>

interface Row { key: string; label: string; value: string; unit?: string; how?: string }

function num(p: Params, id: string): number | null {
  const v = p[id]?.value
  return typeof v === 'number' && Number.isFinite(v) ? v : null
}
function f(v: number | null, digits = 1): string {
  if (v == null || !Number.isFinite(v)) return '—'
  return v.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits })
}

function groups(p: Params, t: TFunction): { id: string; title: string; rows: Row[] }[] {
  const h = num(p, 'orbit.altitude_km')
  const a = h != null ? R_EARTH_KM + h : null
  const sso = h != null ? ssoInclinationDeg(h) : null
  const v = num(p, 'orbit.velocity_ms')
  const contact = num(p, 'orbit.contact_time_per_day_s')
  const rate = num(p, 'link.downlink_rate_bps')
  const cost = ['cost.hardware_keur', 'cost.nre_keur', 'cost.launch_keur', 'cost.operations_keur'] as const
  const total = num(p, 'cost.total_keur')
  const share = (id: string) => {
    const x = num(p, id)
    return x != null && total ? t('{{pct}} % of total', { pct: f((100 * x) / total, 0) }) : undefined
  }
  const ptype = p['propulsion.type']?.value
  return [
    {
      id: 'dl-orbit', title: t('Orbit'), rows: [
        { key: 'h', label: t('Altitude'), value: f(h, 0), unit: 'km' },
        { key: 'a', label: t('Semi-major axis'), value: f(a, 1), unit: 'km', how: t('derived here: a = R⊕ + h, R⊕ = 6378.137 km') },
        { key: 'i', label: t('Inclination'), value: f(num(p, 'orbit.inclination_deg'), 1), unit: '°' },
        { key: 'sso', label: t('Sun-synchronous inclination at this altitude'), value: f(sso, 2), unit: '°', how: t('derived here: cos i = −(2π/1 yr) / (1.5 J2 (R⊕/a)² n)') },
        { key: 'T', label: t('Orbital period'), value: f(num(p, 'orbit.period_min'), 2), unit: 'min', how: 'T = 2π √(a³/μ)' },
        { key: 'v', label: t('Orbital velocity'), value: f(v != null ? v / 1000 : null, 3), unit: 'km/s', how: 'v = √(μ/a)' },
        { key: 'ecl', label: t('Longest eclipse'), value: f(num(p, 'orbit.eclipse_duration_min'), 1), unit: 'min' },
        { key: 'sun', label: t('Sunlight per orbit'), value: f(num(p, 'orbit.sunlight_duration_min'), 1), unit: 'min' },
        { key: 'ef', label: t('Eclipse fraction'), value: f((num(p, 'orbit.eclipse_fraction') ?? NaN) * 100, 1), unit: '%', how: t('cylindrical Earth shadow, Sun in the orbit plane (worst case)') },
        { key: 'opd', label: t('Orbits per day'), value: f(num(p, 'orbit.orbits_per_day'), 2) },
        { key: 'raan', label: t('Node drift (RAAN)'), value: f(num(p, 'orbit.raan_drift_deg_day'), 3), unit: '°/d', how: t('J2 precession; 0.986 °/d is sun-synchronous') },
      ],
    },
    {
      id: 'dl-power', title: t('Power sizing'), rows: [
        { key: 'ps', label: t('Load in sunlight'), value: f(num(p, 'power.total_sunlight_w'), 1), unit: 'W' },
        { key: 'pe', label: t('Load in eclipse'), value: f(num(p, 'power.total_eclipse_w'), 1), unit: 'W' },
        { key: 'eol', label: t('Array power, end of life'), value: f(num(p, 'power.sa_power_eol_w'), 1), unit: 'W', how: t('covers the sunlit load and recharges the battery for the eclipse') },
        { key: 'bol', label: t('Array power, beginning of life'), value: f(num(p, 'power.sa_power_bol_w'), 1), unit: 'W', how: t('EOL power divided by the lifetime degradation factor') },
        { key: 'area', label: t('Array area'), value: f(num(p, 'power.sa_area_m2'), 3), unit: 'm²' },
        { key: 'sam', label: t('Array mass'), value: f(num(p, 'power.sa_mass_kg'), 2), unit: 'kg' },
        { key: 'bat', label: t('Battery capacity'), value: f(num(p, 'power.battery_capacity_wh'), 1), unit: 'Wh', how: t('eclipse energy divided by depth of discharge and efficiency') },
        { key: 'dod', label: t('Depth of discharge'), value: f(num(p, 'power.battery_dod_pct'), 0), unit: '%' },
        { key: 'batm', label: t('Battery mass'), value: f(num(p, 'power.battery_mass_kg'), 2), unit: 'kg' },
        { key: 'pm', label: t('Power margin'), value: f(num(p, 'systems.power_margin_percent'), 1), unit: '%' },
        { key: 'rad', label: t('Radiator area'), value: f(num(p, 'thermal.radiator_area_m2'), 3), unit: 'm²' },
        { key: 'heat', label: t('Heater power'), value: f(num(p, 'thermal.heater_power_w'), 1), unit: 'W' },
      ],
    },
    {
      id: 'dl-link', title: t('Link and data'), rows: [
        { key: 'rate', label: t('Payload downlink rate'), value: f(rate != null ? rate / 1e6 : null, 2), unit: 'Mbit/s' },
        { key: 'dlm', label: t('Payload downlink margin'), value: f(num(p, 'link.downlink_margin_db'), 1), unit: 'dB', how: t('Eb/N0 received minus Eb/N0 required; 3 dB is the usual minimum') },
        { key: 'ttc', label: t('TT&C downlink margin'), value: f(num(p, 'link.ttc_margin_db'), 1), unit: 'dB' },
        { key: 'ul', label: t('Uplink margin'), value: f(num(p, 'link.uplink_margin_db'), 1), unit: 'dB' },
        { key: 'ct', label: t('Contact time per day'), value: f(contact != null ? contact / 60 : null, 1), unit: 'min/d' },
        { key: 'gen', label: t('Data generated per day'), value: f(num(p, 'data.generated_per_day_gb'), 2), unit: 'GB' },
        { key: 'dl', label: t('Data downlinked per day'), value: f(num(p, 'data.downlinked_per_day_gb') ?? num(p, 'link.data_per_day_gb'), 2), unit: 'GB' },
        { key: 'sto', label: t('On-board storage needed'), value: f(num(p, 'data.storage_required_gb'), 1), unit: 'GB' },
      ],
    },
    {
      id: 'dl-dv', title: t('Delta-v and propulsion'), rows: [
        { key: 'deo', label: t('Delta-v to deorbit'), value: f(num(p, 'orbit.delta_v_deorbit_ms'), 1), unit: 'm/s', how: t('to lower perigee for a prompt re-entry; compare with the natural lifetime (Decide › Orbit Trade Study) before sizing propulsion') },
        { key: 'sk', label: t('Delta-v for orbit maintenance'), value: f(num(p, 'orbit.delta_v_sk_ms'), 2), unit: 'm/s' },
        { key: 'tot', label: t('Delta-v total (mission analysis)'), value: f(num(p, 'orbit.delta_v_total_ms'), 1), unit: 'm/s' },
        { key: 'type', label: t('Propulsion type'), value: typeof ptype === 'string' && ptype ? ptype : '—' },
        { key: 'pdv', label: t('Delta-v provided'), value: f(num(p, 'propulsion.delta_v_total_ms'), 1), unit: 'm/s' },
        { key: 'isp', label: t('Specific impulse'), value: f(num(p, 'propulsion.isp_s'), 0), unit: 's' },
        { key: 'prop', label: t('Propellant mass'), value: f(num(p, 'propulsion.propellant_mass_kg'), 3), unit: 'kg', how: 'Δv = Isp g₀ ln(m₀/m_f)' },
      ],
    },
    {
      id: 'dl-cost', title: t('Cost by element'), rows: [
        ...cost.map(id => ({
          key: id,
          label: id === 'cost.hardware_keur' ? t('Hardware') : id === 'cost.nre_keur' ? t('Development (non-recurring)')
            : id === 'cost.launch_keur' ? t('Launch') : t('Operations'),
          value: f(num(p, id), 0), unit: 'kEUR', how: share(id),
        })),
        { key: 'total', label: t('Total'), value: f(total, 0), unit: 'kEUR', how: t('parametric estimate (rough order of magnitude)') },
      ],
    },
  ]
}

export function DesignLoopResults({ studyId, optionId, run }: { studyId: string; optionId: string | null; run?: AnalysisRun }) {
  const { t } = useTranslation()
  const { data, isLoading, error } = useQuery<{ series?: { parameters?: Params } }>({
    queryKey: ['analysis-series', run?.id],
    queryFn: () => fetch(`${API}/analyses/runs/${run!.id}/series`).then(r => (r.ok ? r.json() : {})),
    enabled: !!run?.id,
    staleTime: 60_000,
  })
  void studyId; void optionId
  if (!run) return <p className="t-12 c-2 m-0" data-testid="dl-results">{t('Run the design loop (Run on its card, or Run Analysis in the toolbar) to see its key results here.')}</p>
  if (isLoading) return <p className="t-12 c-2 m-0">{t('Loading…')}</p>
  const params = data?.series?.parameters
  if (error || !params) return <p className="t-12 c-2 m-0" data-testid="dl-results">{t('The results of this run are not stored; run the design loop again.')}</p>
  return (
    <div className="c2o-dlr" data-testid="dl-results">
      <p className="t-12 c-2 m-0 mb-2 measure">
        {t('Key results of the last design loop ({{when}}): the values the worksheets ask you to check against your hand calculation. They are the design agents’ estimates for this study, not approved design values.', { when: run.finished_at ? fmtDate(run.finished_at, { dateStyle: 'medium', timeStyle: 'short' }) : '—' })}
      </p>
      <div className="c2o-dlr__grid">
        {groups(params, t).map(g => (
          <section key={g.id} className="c2o-dlr__group" data-where={g.id} aria-labelledby={`${g.id}-h`}>
            <h4 id={`${g.id}-h`} className="c2o-dlr__h">{g.title}</h4>
            <table className="c2o-table c2o-table--dense c2o-dlr__table">
              <tbody>
                {g.rows.map(r => (
                  <tr key={r.key}>
                    <th scope="row" className="c2o-dlr__label">
                      {r.label}
                      {r.how && <span className="c2o-dlr__how">{r.how}</span>}
                    </th>
                    <td className="num mono c2o-dlr__val">{r.value}{r.unit && r.value !== '—' ? <span className="c2o-dlr__unit"> {r.unit}</span> : null}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        ))}
      </div>
    </div>
  )
}
