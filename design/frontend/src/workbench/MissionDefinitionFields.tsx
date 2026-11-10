/**
 * MissionDefinitionFields (Nov 2026) — the form for the mission definition: spacecraft
 * class, lifetime, orbit (type, altitude, SSO inclination computed from the altitude or
 * typed, LTAN), launch and disposal, payloads and the link. Used by the Mission Wizard
 * (step 4) and by the editor in Traceability › Mission need. State lives in the parent
 * (`MissionDefDraft`, workbench/missionDef.ts).
 */
import { useTranslation } from 'react-i18next'
import {
  CLASS_LABELS, DISPOSAL_LABELS, ORBIT_LABELS, DISPOSAL_METHODS, ORBIT_TYPES, SPACECRAFT_CLASSES, emptyPayload, effectiveInclination, orbitPeriodMin, ssoInclination,
  type LinkDraft, type MissionDefDraft, type PayloadDraft,
} from './missionDef'

function F({ label, hint, children, wide }: { label: string; hint?: string; children: React.ReactNode; wide?: boolean }) {
  return (
    <label className="c2o-wfield" style={wide ? { minWidth: '16rem', flex: 1 } : undefined}>
      <span className="c2o-wfield__label">{label}</span>
      {hint && <span className="c2o-wfield__hint">{hint}</span>}
      {children}
    </label>
  )
}

export function MissionDefinitionFields({ value, onChange, showLink = true }: {
  value: MissionDefDraft; onChange: (d: MissionDefDraft) => void; showLink?: boolean
}) {
  const { t } = useTranslation()
  const d = value
  const set = (patch: Partial<MissionDefDraft>) => onChange({ ...d, ...patch })
  const setPayload = (i: number, patch: Partial<PayloadDraft>) =>
    set({ payloads: d.payloads.map((p, j) => (j === i ? { ...p, ...patch } : p)) })
  const setLink = (patch: Partial<LinkDraft>) => set({ link: { ...d.link, ...patch } })
  const alt = Number(d.altitude_km)
  const inc = effectiveInclination(d)
  const sso = d.orbit_type === 'sso'
  const num = 'c2o-input c2o-input--num c2o-w-num'

  return (
    <div className="stack gap-2" data-testid="mission-definition-fields">
      {/* Spacecraft and lifetime */}
      <fieldset className="c2o-wfield">
        <legend className="c2o-wfield__label">{t('Spacecraft')}</legend>
        <div className="flex wrap gap-2">
          <F label={t('Spacecraft class')}>
            <select className="c2o-select" value={d.spacecraft_class} onChange={e => set({ spacecraft_class: e.target.value })}>
              {SPACECRAFT_CLASSES.map(c => <option key={c} value={c}>{t(CLASS_LABELS[c])}</option>)}
            </select>
          </F>
          <F label={t('Design Lifetime (years)')}>
            <input type="number" min={0} step={0.5} className={num} value={d.design_lifetime_years}
              onChange={e => set({ design_lifetime_years: e.target.value })} />
          </F>
          <F label={t('Target Mass (kg)')}>
            <input type="number" min={0} step={0.1} className={num} value={d.target_mass_kg}
              onChange={e => set({ target_mass_kg: e.target.value })} />
          </F>
        </div>
      </fieldset>

      {/* Orbit */}
      <fieldset className="c2o-wfield">
        <legend className="c2o-wfield__label">{t('Orbit')}</legend>
        <div className="flex wrap gap-2 ai-e">
          <F label={t('Orbit type')}>
            <select className="c2o-select" value={d.orbit_type}
              onChange={e => set({ orbit_type: e.target.value, inclination_auto: e.target.value === 'sso' ? d.inclination_auto : false })}>
              {ORBIT_TYPES.map(o => <option key={o} value={o}>{t(ORBIT_LABELS[o])}</option>)}
            </select>
          </F>
          <F label={t('Altitude (km)')}>
            <input type="number" min={150} step={10} className={num} value={d.altitude_km}
              onChange={e => set({ altitude_km: e.target.value })} />
          </F>
          <F label={t('Inclination (°)')} hint={sso && d.inclination_auto ? t('computed for a sun-synchronous orbit') : undefined}>
            <input type="number" min={0} max={180} step={0.01} className={num}
              value={sso && d.inclination_auto ? String(inc ?? '') : d.inclination_deg}
              disabled={sso && d.inclination_auto}
              onChange={e => set({ inclination_deg: e.target.value })} />
          </F>
          {sso && (
            <label className="c2o-check t-12">
              <input type="checkbox" checked={d.inclination_auto}
                onChange={e => set({ inclination_auto: e.target.checked, inclination_deg: e.target.checked ? d.inclination_deg : String(inc ?? d.inclination_deg) })} />
              {t('Compute the SSO inclination from the altitude')}
            </label>
          )}
          <F label={sso ? t('LTAN (hh:mm)') : t('LTAN (hh:mm, SSO only)')}>
            <input type="text" inputMode="numeric" placeholder="10:30" className="c2o-input c2o-w-num" value={d.ltan}
              onChange={e => set({ ltan: e.target.value })} />
          </F>
        </div>
        {Number.isFinite(alt) && alt > 0 && (
          <div className="t-12 c-2 mt-1">
            {t('Period {{min}} min', { min: orbitPeriodMin(alt).toFixed(1) })}
            {sso && !d.inclination_auto && inc !== null && Math.abs(inc - ssoInclination(alt)) > 0.5 && (
              <span className="c-caution"> · {t('not sun-synchronous at this altitude (SSO: {{inc}}°)', { inc: ssoInclination(alt) })}</span>
            )}
          </div>
        )}
      </fieldset>

      {/* Launch and disposal */}
      <fieldset className="c2o-wfield">
        <legend className="c2o-wfield__label">{t('Launch and disposal')}</legend>
        <div className="flex wrap gap-2">
          <F label={t('Launch / deployer')} wide>
            <input type="text" className="c2o-input" placeholder={t('e.g. rideshare to SSO, 3U deployer')} value={d.launch_vehicle}
              onChange={e => set({ launch_vehicle: e.target.value })} />
          </F>
          <F label={t('Disposal')}>
            <select className="c2o-select" value={d.disposal_method} onChange={e => set({ disposal_method: e.target.value })}>
              <option value="">{t('not chosen')}</option>
              {DISPOSAL_METHODS.map(m => <option key={m} value={m}>{t(DISPOSAL_LABELS[m])}</option>)}
            </select>
          </F>
        </div>
      </fieldset>

      {/* Payloads */}
      <fieldset className="c2o-wfield">
        <legend className="c2o-wfield__label">{t('Payload')}</legend>
        {d.payloads.map((p, i) => (
          <div key={i} className="c2o-card mb-1" data-testid={`payload-${i}`}>
            <div className="flex wrap gap-2 ai-e">
              <F label={t('Payload name')} wide>
                <input type="text" className="c2o-input" value={p.name} onChange={e => setPayload(i, { name: e.target.value })} />
              </F>
              <F label={t('Mass (kg)')}>
                <input type="number" min={0} step={0.1} className={num} value={p.mass_kg} onChange={e => setPayload(i, { mass_kg: e.target.value })} />
              </F>
              <F label={t('Average power (W)')}>
                <input type="number" min={0} step={0.5} className={num} value={p.power_w} onChange={e => setPayload(i, { power_w: e.target.value })} />
              </F>
              <F label={t('Peak power (W)')}>
                <input type="number" min={0} step={0.5} className={num} value={p.power_peak_w} onChange={e => setPayload(i, { power_peak_w: e.target.value })} />
              </F>
              <F label={t('Data rate (Mbit/s)')}>
                <input type="number" min={0} step={0.1} className={num} value={p.data_rate_mbps} onChange={e => setPayload(i, { data_rate_mbps: e.target.value })} />
              </F>
              <F label={t('Duty cycle (%)')}>
                <input type="number" min={0} max={100} step={1} className={num} value={p.duty_cycle_percent} onChange={e => setPayload(i, { duty_cycle_percent: e.target.value })} />
              </F>
            </div>
            <div className="flex wrap gap-2 ai-e mt-1">
              <F label={t('GSD (m)')}>
                <input type="number" min={0} step={1} className={num} value={p.gsd_m} onChange={e => setPayload(i, { gsd_m: e.target.value })} />
              </F>
              <F label={t('Swath (km)')}>
                <input type="number" min={0} step={1} className={num} value={p.swath_km} onChange={e => setPayload(i, { swath_km: e.target.value })} />
              </F>
              <F label={t('Wavelengths (nm)')} hint={t('band centres, comma-separated')}>
                <input type="text" className="c2o-input" placeholder="865, 1610" value={p.wavelengths_nm} onChange={e => setPayload(i, { wavelengths_nm: e.target.value })} />
              </F>
              <F label={t('Data per image (MB)')}>
                <input type="number" min={0} step={1} className={num} value={p.data_per_image_mb} onChange={e => setPayload(i, { data_per_image_mb: e.target.value })} />
              </F>
              <F label={t('Pointing accuracy (°)')}>
                <input type="number" min={0} step={0.01} className={num} value={p.pointing_accuracy_deg} onChange={e => setPayload(i, { pointing_accuracy_deg: e.target.value })} />
              </F>
              {d.payloads.length > 1 && (
                <button type="button" className="c2o-btn c2o-btn--sm c2o-btn--danger" aria-label={t('Remove payload {{name}}', { name: p.name || i + 1 })}
                  onClick={() => set({ payloads: d.payloads.filter((_, j) => j !== i) })}>×</button>
              )}
            </div>
          </div>
        ))}
        <button type="button" className="c2o-btn c2o-btn--sm" onClick={() => set({ payloads: [...d.payloads, emptyPayload(`Payload ${d.payloads.length + 1}`)] })}>
          {t('+ Add payload')}
        </button>
      </fieldset>

      {/* Link */}
      {showLink && (
        <fieldset className="c2o-wfield">
          <legend className="c2o-wfield__label">{t('Communication link')}</legend>
          <span className="c2o-wfield__hint">{t('Leave empty to let the design loop choose from the spacecraft class.')}</span>
          <div className="flex wrap gap-2 ai-e">
            <F label={t('Band')}>
              <input type="text" className="c2o-input c2o-w-num" placeholder="UHF" value={d.link.band} onChange={e => setLink({ band: e.target.value })} />
            </F>
            <F label={t('Downlink frequency (MHz)')}>
              <input type="number" min={0} step={0.01} className={num} value={d.link.downlink_frequency_mhz} onChange={e => setLink({ downlink_frequency_mhz: e.target.value })} />
            </F>
            <F label={t('Downlink rate (bit/s)')}>
              <input type="number" min={0} step={100} className={num} value={d.link.downlink_rate_bps} onChange={e => setLink({ downlink_rate_bps: e.target.value })} />
            </F>
            <F label={t('Uplink frequency (MHz)')}>
              <input type="number" min={0} step={0.01} className={num} value={d.link.uplink_frequency_mhz} onChange={e => setLink({ uplink_frequency_mhz: e.target.value })} />
            </F>
            <F label={t('Uplink rate (bit/s)')}>
              <input type="number" min={0} step={100} className={num} value={d.link.uplink_rate_bps} onChange={e => setLink({ uplink_rate_bps: e.target.value })} />
            </F>
            <F label={t('TX power (W)')}>
              <input type="number" min={0} step={0.1} className={num} value={d.link.tx_power_w} onChange={e => setLink({ tx_power_w: e.target.value })} />
            </F>
            <F label={t('TX antenna gain (dBi)')}>
              <input type="number" step={0.5} className={num} value={d.link.tx_antenna_gain_dbi} onChange={e => setLink({ tx_antenna_gain_dbi: e.target.value })} />
            </F>
          </div>
        </fieldset>
      )}
    </div>
  )
}
