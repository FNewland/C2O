/**
 * LinkBudgetTool — Interactive link budget calculator.
 *
 * Computes EIRP, FSPL, received power, C/N0, Eb/N0, margin per ECSS-E-ST-50-05C.
 * Shows each term as a cascade with the final margin.
 *
 * Nov 2026 (W1.04 / W4.04): both directions start from the study (GET
 * /api/studies/{id}/link-budgets → ``start``: the band preset of the study's link overlaid with
 * ``requirements.link``), so a UHF mission opens at 401.5 MHz and its uplink at 450 MHz and
 * 9.6 kbit/s, not the S-band telecommand values. A band selector loads the UHF / VHF / S / X
 * presets. Apply writes the fields of the direction shown (the uplink writes ``link.uplink_*``).
 * Named cases (direction, station, elevation, rate tier) are saved on the server, listed with
 * their margin, loaded back, and one per direction can be made the design case.
 */
import { useState, useMemo, useRef, useCallback, useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useDesignStore } from '../stores/designStore'
import { useUIStore } from '../stores/uiStore'
import { useApplyToDesign } from '../hooks/useApplyToDesign'
import { fs } from '../theme/tokens'
import { useTranslation } from 'react-i18next'

interface LinkBudgetLine {
  label: string
  value: number
  unit: string
  notes: string
  type: 'gain' | 'loss' | 'result'
  key?: string
}

export function LinkBudgetTool() {
  const { t } = useTranslation()
  const reqs = useDesignStore(s => s.requirements)
  const setParam = useDesignStore(s => s.setParameter)
  // Nov 2026: the study's mission definition (orbit, link) — not the legacy browser store
  const studyId = useUIStore(s => s.studyId)
  const qc = useQueryClient()
  const { data: study } = useQuery<any>({
    queryKey: ['study', studyId],
    queryFn: () => fetch(`/api/studies/${studyId}`).then(r => (r.ok ? r.json() : null)),
    enabled: !!studyId,
  })
  const alt = study?.requirements?.orbit?.altitude_km ?? reqs.orbit.altitude_km

  // Helper: set local state immediately, debounce designStore write to avoid render storms
  const timersRef = useRef<Record<string, ReturnType<typeof setTimeout>>>({})
  const writeStoreRef = useRef(true)
  const useLinkedState = (initial: number, paramId: string): [number, (v: number) => void] => {
    const [val, setVal] = useState(initial)
    const setter = useCallback((v: number) => {
      setVal(v)
      // The uplink is a what-if: only the downlink writes the design's link parameters
      if (!writeStoreRef.current) return
      // Debounce the store write — only fires after 500ms of no changes
      if (timersRef.current[paramId]) clearTimeout(timersRef.current[paramId])
      timersRef.current[paramId] = setTimeout(() => setParam(paramId, v, 'link-budget'), 500)
    }, [paramId])
    return [val, setter]
  }

  const [linkDirection, setLinkDirection] = useState<'downlink' | 'uplink'>('downlink')
  const [band, setBand] = useState<string>('UHF')
  const [elevation, setElevation] = useState(10)
  const [rxLosses, setRxLosses] = useState(0)
  const [caseName, setCaseName] = useState('')
  const [station, setStation] = useState('')
  const [rateTier, setRateTier] = useState('')
  const [caseError, setCaseError] = useState<string | null>(null)
  const { data: lb } = useQuery<LinkBudgetsResponse>({
    queryKey: ['link-budgets', studyId],
    queryFn: () => fetch(`/api/studies/${studyId}/link-budgets`).then(r => (r.ok ? r.json() : null)),
    enabled: !!studyId,
  })
  const { data: presetData } = useQuery<{ bands: Record<string, Record<'downlink' | 'uplink', LinkInputs>> }>({
    queryKey: ['link-budget-presets'],
    queryFn: () => fetch('/api/link-budgets/presets').then(r => (r.ok ? r.json() : { bands: {} })),
    staleTime: 3_600_000,
  })

  // Inputs with defaults from design state — every change writes to parameterOverrides
  const [txPower, setTxPower] = useLinkedState(2.0, 'link.tx_power_w')
  const [txGain, setTxGain] = useLinkedState(linkDirection === 'downlink' ? 6.0 : 35.0, 'link.tx_antenna_gain_db')
  const [txLosses, setTxLosses] = useLinkedState(1.5, 'link.tx_losses_db')
  const [frequency, setFrequency] = useLinkedState(linkDirection === 'downlink' ? 2250 : 2050, 'link.frequency_mhz')
  // Worst case: the slant range at the lowest usable elevation (10°), textbook § 11.4.1
  const slantAt = (h: number, elDeg: number) => {
    const re = 6378.137, e = elDeg * Math.PI / 180
    return Math.round(Math.sqrt((re + h) ** 2 - (re * Math.cos(e)) ** 2) - re * Math.sin(e))
  }
  const [slantRange, setSlantRange] = useLinkedState(slantAt(alt || 500, 10), 'link.slant_range_km')
  const [atmosphericLoss, setAtmosphericLoss] = useLinkedState(0.5, 'link.atmospheric_loss_db')
  const [pointingLoss, setPointingLoss] = useLinkedState(1.0, 'link.pointing_loss_db')
  const [polLoss, setPolLoss] = useLinkedState(0.3, 'link.polarisation_loss_db')
  const [rxGain, setRxGain] = useLinkedState(35.0, 'link.rx_antenna_gain_db')
  const [rxTemp, setRxTemp] = useLinkedState(150, 'link.system_noise_temp_k')
  const [dataRate, setDataRate] = useLinkedState(1e6, 'link.data_rate_bps')
  const [reqEbN0, setReqEbN0] = useState(4.0)
  const [implMargin, setImplMargin] = useState(2.0)

  // Start from the study (W1.04): the server's starting values for each direction — the band
  // preset of the study's link overlaid with what the study chose (requirements.link)
  const values = (): LinkInputs => ({
    tx_power_w: txPower, tx_antenna_gain_dbi: txGain, tx_losses_db: txLosses, frequency_mhz: frequency,
    rx_antenna_gain_dbi: rxGain, rx_losses_db: rxLosses, system_noise_temp_k: rxTemp, data_rate_bps: dataRate,
    required_ebn0_db: reqEbN0, implementation_loss_db: implMargin, atmospheric_loss_db: atmosphericLoss,
    pointing_loss_db: pointingLoss, polarisation_loss_db: polLoss, elevation_deg: elevation,
  })
  const load = (v: Partial<LinkInputs>, alt0?: number | null) => {
    const num = (x: unknown) => (typeof x === 'number' && Number.isFinite(x) ? x : null)
    const set = <K extends keyof LinkInputs>(k: K, f: (x: number) => void) => { const x = num(v[k]); if (x !== null) f(x) }
    set('tx_power_w', setTxPower); set('tx_antenna_gain_dbi', setTxGain); set('tx_losses_db', setTxLosses)
    set('frequency_mhz', setFrequency); set('rx_antenna_gain_dbi', setRxGain); set('rx_losses_db', setRxLosses)
    set('system_noise_temp_k', setRxTemp); set('data_rate_bps', setDataRate); set('required_ebn0_db', setReqEbN0)
    set('implementation_loss_db', setImplMargin); set('atmospheric_loss_db', setAtmosphericLoss)
    set('pointing_loss_db', setPointingLoss); set('polarisation_loss_db', setPolLoss)
    const el = num(v.elevation_deg) ?? elevation
    setElevation(el)
    const sr = num(v.slant_range_km)
    const a = alt0 ?? lb?.altitude_km ?? alt
    setSlantRange(sr && sr > 0 ? sr : slantAt(typeof a === 'number' ? a : 500, el))
  }
  const seededFor = useRef<string | null>(null)
  useEffect(() => {
    if (!lb || !studyId || seededFor.current === studyId) return
    seededFor.current = studyId
    savedDir.current = {}
    if (lb.start?.downlink?.band) setBand(lb.start.downlink.band)
    load(lb.start?.downlink ?? {}, lb.altitude_km)
  }, [lb, studyId])  // eslint-disable-line react-hooks/exhaustive-deps

  // Switching direction swaps the station and spacecraft ends: each direction keeps its own
  // values; the first time, the uplink starts from the study's uplink (band preset + link).
  const savedDir = useRef<Partial<Record<'downlink' | 'uplink', LinkInputs>>>({})
  const switchDirection = (dir: 'downlink' | 'uplink') => {
    if (dir === linkDirection) return
    savedDir.current[linkDirection] = values()
    writeStoreRef.current = dir === 'downlink'
    const next = savedDir.current[dir] ?? lb?.start?.[dir] ?? presetData?.bands?.[band]?.[dir] ?? {}
    load(next)
    setLinkDirection(dir)
  }
  const changeBand = (b: string) => {
    setBand(b)
    savedDir.current = {}
    const p = presetData?.bands?.[b]?.[linkDirection]
    if (p) load(p)
  }
  const changeElevation = (el: number) => {
    setElevation(el)
    const a = lb?.altitude_km ?? alt
    if (el >= 0 && el <= 90) setSlantRange(slantAt(typeof a === 'number' ? a : 500, el))
  }

  const budget = useMemo<LinkBudgetLine[]>(() => {
    const c = 3e8
    const k = -228.6 // Boltzmann dBW/K/Hz
    const wavelength = c / (frequency * 1e6)

    const eirp = 10 * Math.log10(txPower) + txGain - txLosses
    const fspl = 20 * Math.log10(4 * Math.PI * slantRange * 1000 / wavelength)
    const gt = rxGain - rxLosses - 10 * Math.log10(rxTemp)
    const cn0 = eirp - fspl - atmosphericLoss - pointingLoss - polLoss + gt - k
    const ebN0 = cn0 - 10 * Math.log10(dataRate)
    const margin = ebN0 - reqEbN0 - implMargin

    return [
      { label: t('TX Power'), value: round(10 * Math.log10(txPower)), unit: 'dBW', notes: `${txPower} W`, type: 'gain' },
      { label: t('TX Antenna Gain'), value: round(txGain), unit: 'dBi', notes: linkDirection === 'downlink' ? t('Spacecraft antenna') : t('Ground station antenna'), type: 'gain' },
      { label: t('TX Losses'), value: round(-txLosses), unit: 'dB', notes: t('Cable, filter, mismatch'), type: 'loss' },
      { label: 'EIRP', value: round(eirp), unit: 'dBW', notes: t('Effective Isotropic Radiated Power'), type: 'result' },
      { label: t('Free Space Path Loss'), value: round(-fspl), unit: 'dB', notes: t('{{km}} km at {{mhz}} MHz', { km: slantRange, mhz: frequency }), type: 'loss' },
      { label: t('Atmospheric Loss'), value: round(-atmosphericLoss), unit: 'dB', notes: t('Rain, gas absorption'), type: 'loss' },
      { label: t('Pointing Loss'), value: round(-pointingLoss), unit: 'dB', notes: t('Antenna misalignment'), type: 'loss' },
      { label: t('Polarisation Loss'), value: round(-polLoss), unit: 'dB', notes: t('Pol mismatch'), type: 'loss' },
      { label: t('RX Antenna Gain'), value: round(rxGain), unit: 'dBi', notes: linkDirection === 'downlink' ? t('Ground station antenna') : t('Spacecraft antenna'), type: 'gain' },
      { label: t('RX Losses'), value: round(-rxLosses), unit: 'dB', notes: t('Cable before the low-noise amplifier'), type: 'loss' },
      { label: t('System G/T'), value: round(gt), unit: 'dB/K', notes: `Tsys = ${rxTemp} K`, type: 'result' },
      { label: 'C/N₀', value: round(cn0), unit: 'dBHz', notes: t('Carrier-to-noise density'), type: 'result' },
      { label: t('Eb/N₀ (available)'), value: round(ebN0), unit: 'dB', notes: dataRate >= 1e5 ? t('Data rate: {{v}} Mbps', { v: (dataRate / 1e6).toFixed(1) }) : t('Data rate: {{v}} kbps', { v: (dataRate / 1e3).toFixed(1) }), type: 'result' },
      { label: t('Eb/N₀ (required)'), value: round(-reqEbN0), unit: 'dB', notes: t('Modulation + coding threshold'), type: 'loss' },
      { label: t('Implementation Margin'), value: round(-implMargin), unit: 'dB', notes: 'ECSS-E-ST-50-05C', type: 'loss' },
      { label: t('LINK MARGIN'), key: 'margin', value: round(margin), unit: 'dB', notes: margin >= 3 ? t('Closes with margin') : margin >= 0 ? t('Marginal') : t('DOES NOT CLOSE'), type: 'result' },
    ]
  }, [txPower, txGain, txLosses, frequency, slantRange, atmosphericLoss, pointingLoss, polLoss, rxGain, rxLosses, rxTemp, dataRate, reqEbN0, implMargin, linkDirection])

  const margin = budget[budget.length - 1]?.value || 0
  const [applied, setApplied] = useState(false)
  const [applyError, setApplyError] = useState<string | null>(null)

  /** Save the link on the study (PATCH /studies/{id}/mission ``link``): the design loop's
   *  link agent and the ground / simulation closures read it. Uplink values only set the
   *  uplink fields. */
  const persist = async () => {
    if (!studyId) return
    const link = linkDirection === 'downlink'
      ? {
          band, downlink_frequency_mhz: frequency, downlink_rate_bps: dataRate, tx_power_w: txPower, tx_antenna_gain_dbi: txGain,
          tx_losses_db: txLosses, rx_antenna_gain_dbi: rxGain, system_noise_temp_k: rxTemp, slant_range_km: slantRange,
          required_ebn0_db: reqEbN0, margin_db: margin, source: 'link_budget_tool',
        }
      : { band, uplink_frequency_mhz: frequency, uplink_rate_bps: dataRate, source: 'link_budget_tool' }
    const res = await fetch(`/api/studies/${encodeURIComponent(studyId)}/mission`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ link }),
    })
    if (!res.ok) {
      const d = (await res.json().catch(() => ({})))?.detail
      throw new Error(typeof d === 'string' ? d : t('Could not save the mission definition'))
    }
    for (const k of ['study', 'analyses', 'analysis', 'link-budgets']) qc.invalidateQueries({ queryKey: [k] })
  }

  /** Save the values shown as a named case (W4.04); the server recomputes the margin. */
  const saveCase = async () => {
    if (!studyId) return
    setCaseError(null)
    const res = await fetch(`/api/studies/${encodeURIComponent(studyId)}/link-budgets`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...values(), slant_range_km: slantRange, direction: linkDirection, band, station, rate_tier: rateTier,
        name: caseName.trim() || undefined, source: 'link_budget_tool' }),
    })
    if (!res.ok) { setCaseError(t('The case could not be saved ({{code}}).', { code: res.status })); return }
    setCaseName('')
    qc.invalidateQueries({ queryKey: ['link-budgets', studyId] })
  }
  const caseAction = async (id: string, action: 'apply' | 'delete') => {
    if (!studyId) return
    setCaseError(null)
    const url = `/api/studies/${encodeURIComponent(studyId)}/link-budgets/${encodeURIComponent(id)}${action === 'apply' ? '/apply' : ''}`
    const res = await fetch(url, { method: action === 'apply' ? 'POST' : 'DELETE' })
    if (!res.ok) { setCaseError(t('The case could not be changed ({{code}}).', { code: res.status })); return }
    for (const k of ['study', 'analyses', 'analysis', 'link-budgets']) qc.invalidateQueries({ queryKey: [k] })
  }
  const loadCase = (c: LinkCase) => {
    savedDir.current = {}
    setBand(c.band || band)
    setLinkDirection(c.direction)
    writeStoreRef.current = c.direction === 'downlink'
    setStation(c.station || '')
    setRateTier(c.rate_tier || '')
    load(c)
  }

  const apply = useApplyToDesign({
    events: [
      { kind: 'parameter_override', target_id: 'link.tx_power_w', new_value: txPower },
      { kind: 'parameter_override', target_id: 'link.tx_antenna_gain_db', new_value: txGain },
      { kind: 'parameter_override', target_id: 'link.frequency_mhz', new_value: frequency },
      { kind: 'parameter_override', target_id: 'link.rx_antenna_gain_db', new_value: rxGain },
      { kind: 'parameter_override', target_id: 'link.data_rate_bps', new_value: dataRate },
      { kind: 'parameter_override', target_id: 'link.slant_range_km', new_value: slantRange },
      { kind: 'parameter_override', target_id: 'link.system_noise_temp_k', new_value: rxTemp },
    ],
    correlation_id: 'linkbudget-tool',
    rationale: 'Manual link-budget tuning',
  })

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ marginBottom: '0.25rem' }}>{t('Link Budget Calculator')}</h2>
      <p style={{ fontSize: fs.label, color: 'var(--text-2)', marginBottom: '0.75rem' }}>
        {t('Per ECSS-E-ST-50-05C. Edit any parameter to see the impact on link margin.')}
      </p>

      {/* Uplink / Downlink toggle */}
      <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.75rem' }}>
        <button onClick={() => switchDirection('downlink')} style={{
          padding: '0.25rem 0.75rem', fontSize: fs.label, borderRadius: '4px', cursor: 'pointer',
          background: linkDirection === 'downlink' ? 'var(--interactive)' : 'var(--bg-secondary, var(--surface-2))',
          color: linkDirection === 'downlink' ? 'white' : 'var(--text-2)',
          border: `1px solid ${linkDirection === 'downlink' ? 'var(--interactive)' : 'var(--line)'}`,
        }}>{t('Downlink (Space→Ground)')}</button>
        <button onClick={() => switchDirection('uplink')} style={{
          padding: '0.25rem 0.75rem', fontSize: fs.label, borderRadius: '4px', cursor: 'pointer',
          background: linkDirection === 'uplink' ? 'var(--cat-2)' : 'var(--bg-secondary, var(--surface-2))',
          color: linkDirection === 'uplink' ? 'white' : 'var(--text-2)',
          border: `1px solid ${linkDirection === 'uplink' ? 'var(--cat-2)' : 'var(--line)'}`,
        }}>{t('Uplink (Ground→Space)')}</button>
        <label style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: fs.label }}>
          <span>{t('Band preset')}</span>
          <select className="c2o-select c2o-select--sm" aria-label={t('Band preset')} value={band} onChange={e => changeBand(e.target.value)}>
            {Object.keys(presetData?.bands ?? { UHF: {}, VHF: {}, S: {}, X: {} }).map(b => <option key={b} value={b}>{b}</option>)}
          </select>
        </label>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        {/* Input column */}
        <div>
          <div className="card">
            <h3 style={{ fontSize: fs.body, marginBottom: '0.4rem' }}>
              {linkDirection === 'downlink' ? t('Transmitter (Spacecraft)') : t('Transmitter (Ground Station)')}
            </h3>
            <InputRow label={t('TX Power (W)')} value={txPower} onChange={setTxPower} step={0.5} />
            <InputRow label={t('TX Antenna Gain (dBi)')} value={txGain} onChange={setTxGain} step={1} />
            <InputRow label={t('TX Losses (dB)')} value={txLosses} onChange={setTxLosses} step={0.1} />
            <InputRow label={t('Frequency (MHz)')} value={frequency} onChange={setFrequency} step={100} />
          </div>
          <div className="card">
            <h3 style={{ fontSize: fs.body, marginBottom: '0.4rem' }}>{t('Path')}</h3>
            <InputRow label={t('Elevation (deg)')} value={elevation} onChange={changeElevation} step={5} />
            <InputRow label={t('Slant Range (km)')} value={slantRange} onChange={setSlantRange} step={50} />
            <InputRow label={t('Atmospheric Loss (dB)')} value={atmosphericLoss} onChange={setAtmosphericLoss} step={0.1} />
            <InputRow label={t('Pointing Loss (dB)')} value={pointingLoss} onChange={setPointingLoss} step={0.1} />
            <InputRow label={t('Polarisation Loss (dB)')} value={polLoss} onChange={setPolLoss} step={0.1} />
          </div>
          <div className="card">
            <h3 style={{ fontSize: fs.body, marginBottom: '0.4rem' }}>{linkDirection === 'downlink' ? t('Receiver (Ground)') : t('Receiver (Spacecraft)')}</h3>
            <InputRow label={t('RX Antenna Gain (dBi)')} value={rxGain} onChange={setRxGain} step={1} />
            <InputRow label={t('RX Losses (dB)')} value={rxLosses} onChange={setRxLosses} step={0.1} />
            <InputRow label={t('System Temp (K)')} value={rxTemp} onChange={setRxTemp} step={10} />
            <InputRow label={t('Data Rate (bps)')} value={dataRate} onChange={setDataRate} step={100000} />
            <InputRow label={t('Required Eb/N₀ (dB)')} value={reqEbN0} onChange={setReqEbN0} step={0.5} />
            <InputRow label={t('Implementation Margin (dB)')} value={implMargin} onChange={setImplMargin} step={0.5} />
          </div>
        </div>

        {/* Budget cascade column */}
        <div className="card">
          <h3 style={{ fontSize: fs.body, marginBottom: '0.4rem' }}>{t('Link Budget Cascade')}</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: fs.label }}>
            <thead>
              <tr style={{ background: 'var(--bg-primary, var(--surface-0))' }}>
                <th style={th}>{t('Parameter')}</th>
                <th style={thR}>{t('Value')}</th>
                <th style={th}>{t('Notes')}</th>
              </tr>
            </thead>
            <tbody>
              {budget.map((line, i) => (
                <tr key={i} style={{
                  borderBottom: line.type === 'result' ? '2px solid var(--line)' : '1px solid color-mix(in srgb, var(--text) 5%, transparent)',
                  background: line.key === 'margin' ? (margin >= 3 ? 'rgba(16,185,129,0.1)' : margin >= 0 ? 'rgba(245,158,11,0.1)' : 'rgba(239,68,68,0.1)') : 'transparent',
                }}>
                  <td style={{ ...td, fontWeight: line.type === 'result' ? 700 : 400 }}>{line.label}</td>
                  <td style={{
                    ...tdR, fontWeight: line.type === 'result' ? 700 : 400,
                    color: line.type === 'gain' ? 'var(--status-ok)' : line.type === 'loss' ? 'var(--status-alarm)' : line.key === 'margin' ? (margin >= 3 ? 'var(--status-ok)' : margin >= 0 ? 'var(--status-caution)' : 'var(--status-alarm)') : 'var(--text)',
                  }}>
                    {line.value >= 0 ? '+' : ''}{line.value.toFixed(1)} {line.unit}
                  </td>
                  <td style={{ ...td, fontSize: fs.label, color: 'var(--text-3)' }}>{line.notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Apply to design */}
      {applyError && <div role="alert" style={{ color: 'var(--status-alarm)', fontSize: fs.label, marginTop: '0.5rem' }}>{applyError}</div>}
      <button className="btn" onClick={async () => {
        setApplyError(null)
        try { await persist() } catch (e) { setApplyError((e as Error).message); return }
        await apply(); setApplied(true); setTimeout(() => setApplied(false), 2000)
      }}
        style={{ marginTop: '0.75rem', width: '100%', background: applied ? 'var(--status-ok)' : 'var(--interactive)', fontSize: fs.body }}>
        {applied ? t('Saved to the mission definition — re-run the analyses') : linkDirection === 'uplink' ? t('Apply the uplink to the design') : t('Apply to Design')}
      </button>

      {/* Named link cases (W4.04) */}
      <div className="card" style={{ marginTop: '0.75rem' }} data-testid="link-cases">
        <h3 style={{ fontSize: fs.body, marginBottom: '0.4rem' }}>{t('Link cases')}</h3>
        <p style={{ fontSize: fs.label, color: 'var(--text-2)', margin: '0 0 0.4rem' }}>
          {t('Save the values shown as a named case (one direction, station, elevation and rate tier). The master budget, the review packs and the licensing documents list the saved cases; the design case is the one the analyses use.')}
        </p>
        <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap', marginBottom: '0.4rem' }}>
          <input className="c2o-input c2o-input--sm" aria-label={t('Case name')} placeholder={t('Case name')} value={caseName} onChange={e => setCaseName(e.target.value)} />
          <input className="c2o-input c2o-input--sm" aria-label={t('Ground station')} placeholder={t('Ground station')} value={station} onChange={e => setStation(e.target.value)} />
          <input className="c2o-input c2o-input--sm" aria-label={t('Rate tier')} placeholder={t('Rate tier')} value={rateTier} onChange={e => setRateTier(e.target.value)} />
          <button className="c2o-btn c2o-btn--sm" disabled={!studyId} onClick={() => void saveCase()}>{t('Save as a case')}</button>
        </div>
        {caseError && <div role="alert" style={{ color: 'var(--status-alarm)', fontSize: fs.label }}>{caseError}</div>}
        {(lb?.items?.length ?? 0) > 0 ? (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: fs.label }}>
            <thead>
              <tr><th style={th}>{t('Case')}</th><th style={th}>{t('Direction')}</th><th style={th}>{t('Station')}</th>
                <th style={thR}>{t('Elevation')}</th><th style={thR}>{t('Margin')}</th><th style={th} /></tr>
            </thead>
            <tbody>
              {lb!.items.map(c => (
                <tr key={c.id} style={{ borderBottom: '1px solid color-mix(in srgb, var(--text) 5%, transparent)' }}>
                  <td style={td}>{c.name}{c.is_design_case ? ` · ${t('design case')}` : ''}</td>
                  <td style={td}>{c.direction === 'uplink' ? t('Uplink') : t('Downlink')} · {c.band}</td>
                  <td style={td}>{c.station}</td>
                  <td style={tdR}>{c.elevation_deg}°</td>
                  <td style={{ ...tdR, color: (c.margin_db ?? -99) >= 3 ? 'var(--status-ok)' : (c.margin_db ?? -99) >= 0 ? 'var(--status-caution)' : 'var(--status-alarm)' }}>
                    {c.margin_db == null ? '' : `${c.margin_db >= 0 ? '+' : ''}${c.margin_db.toFixed(1)} dB`}
                  </td>
                  <td style={{ ...td, whiteSpace: 'nowrap' }}>
                    <button className="c2o-btn c2o-btn--sm" onClick={() => loadCase(c)}>{t('Load')}</button>{' '}
                    {!c.is_design_case && <button className="c2o-btn c2o-btn--sm" onClick={() => void caseAction(c.id, 'apply')}>{t('Use as design case')}</button>}{' '}
                    <button className="c2o-btn c2o-btn--sm" aria-label={t('Delete case {{name}}', { name: c.name })} onClick={() => void caseAction(c.id, 'delete')}>×</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : <p style={{ fontSize: fs.label, color: 'var(--text-3)', margin: 0 }}>{t('No saved case yet.')}</p>}
      </div>
    </div>
  )
}

interface LinkInputs {
  frequency_mhz: number; data_rate_bps: number; tx_power_w: number; tx_antenna_gain_dbi: number; tx_losses_db: number
  elevation_deg: number; slant_range_km?: number; polarisation_loss_db: number; atmospheric_loss_db: number
  pointing_loss_db: number; rx_antenna_gain_dbi: number; rx_losses_db: number; system_noise_temp_k: number
  required_ebn0_db: number; implementation_loss_db: number; band?: string
}
interface LinkCase extends LinkInputs {
  id: string; name: string; direction: 'downlink' | 'uplink'; band: string; station: string; rate_tier: string
  margin_db: number | null; is_design_case: boolean
}
interface LinkBudgetsResponse {
  design_case: Record<string, unknown>; altitude_km: number | null
  start: Record<'downlink' | 'uplink', LinkInputs & { band?: string }>
  items: LinkCase[]
}

function InputRow({ label, value, onChange, step }: { label: string; value: number; onChange: (v: number) => void; step: number }) {
  return (
    <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem' }}>
      <span style={{ flex: 1, fontSize: fs.label, color: 'var(--text-2)' }}>{label}</span>
      <input className="input" type="number" value={value} step={step} aria-label={label}
        onChange={e => onChange(Number(e.target.value))}
        style={{ width: '80px', fontSize: fs.label, textAlign: 'right' }} />
    </label>
  )
}

function round(v: number): number { return Math.round(v * 10) / 10 }

const th: React.CSSProperties = { padding: '0.3rem 0.5rem', textAlign: 'left', fontSize: fs.label, color: 'var(--text-2)', textTransform: 'uppercase' }
const thR: React.CSSProperties = { ...th, textAlign: 'right' }
const td: React.CSSProperties = { padding: '0.25rem 0.5rem' }
const tdR: React.CSSProperties = { ...td, textAlign: 'right', fontFamily: 'monospace' }
