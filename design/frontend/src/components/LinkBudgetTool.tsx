/**
 * LinkBudgetTool — Interactive link budget calculator.
 *
 * Computes EIRP, FSPL, received power, C/N0, Eb/N0, margin per ECSS-E-ST-50-05C.
 * Shows each term as a cascade with the final margin.
 */
import { useState, useMemo, useRef, useCallback } from 'react'
import { useDesignStore } from '../stores/designStore'
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
  const alt = reqs.orbit.altitude_km

  // Helper: set local state immediately, debounce designStore write to avoid render storms
  const timersRef = useRef<Record<string, ReturnType<typeof setTimeout>>>({})
  const useLinkedState = (initial: number, paramId: string): [number, (v: number) => void] => {
    const [val, setVal] = useState(initial)
    const setter = useCallback((v: number) => {
      setVal(v)
      // Debounce the store write — only fires after 500ms of no changes
      if (timersRef.current[paramId]) clearTimeout(timersRef.current[paramId])
      timersRef.current[paramId] = setTimeout(() => setParam(paramId, v, 'link-budget'), 500)
    }, [paramId])
    return [val, setter]
  }

  const [linkDirection, setLinkDirection] = useState<'downlink' | 'uplink'>('downlink')

  // Inputs with defaults from design state — every change writes to parameterOverrides
  const [txPower, setTxPower] = useLinkedState(2.0, 'link.tx_power_w')
  const [txGain, setTxGain] = useLinkedState(linkDirection === 'downlink' ? 6.0 : 35.0, 'link.tx_antenna_gain_db')
  const [txLosses, setTxLosses] = useLinkedState(1.5, 'link.tx_losses_db')
  const [frequency, setFrequency] = useLinkedState(linkDirection === 'downlink' ? 2250 : 2050, 'link.frequency_mhz')
  const [slantRange, setSlantRange] = useLinkedState(alt * 1.15 || 575, 'link.slant_range_km')
  const [atmosphericLoss, setAtmosphericLoss] = useLinkedState(0.5, 'link.atmospheric_loss_db')
  const [pointingLoss, setPointingLoss] = useLinkedState(1.0, 'link.pointing_loss_db')
  const [polLoss, setPolLoss] = useLinkedState(0.3, 'link.polarisation_loss_db')
  const [rxGain, setRxGain] = useLinkedState(35.0, 'link.rx_antenna_gain_db')
  const [rxTemp, setRxTemp] = useLinkedState(150, 'link.system_noise_temp_k')
  const [dataRate, setDataRate] = useLinkedState(1e6, 'link.data_rate_bps')
  const [reqEbN0, setReqEbN0] = useState(4.0)
  const [implMargin, setImplMargin] = useState(2.0)

  const budget = useMemo<LinkBudgetLine[]>(() => {
    const c = 3e8
    const k = -228.6 // Boltzmann dBW/K/Hz
    const wavelength = c / (frequency * 1e6)

    const eirp = 10 * Math.log10(txPower) + txGain - txLosses
    const fspl = 20 * Math.log10(4 * Math.PI * slantRange * 1000 / wavelength)
    const gt = rxGain - 10 * Math.log10(rxTemp)
    const cn0 = eirp - fspl - atmosphericLoss - pointingLoss - polLoss + gt - k
    const ebN0 = cn0 - 10 * Math.log10(dataRate)
    const margin = ebN0 - reqEbN0 - implMargin

    return [
      { label: t('TX Power'), value: round(10 * Math.log10(txPower)), unit: 'dBW', notes: `${txPower} W`, type: 'gain' },
      { label: t('TX Antenna Gain'), value: round(txGain), unit: 'dBi', notes: t('Spacecraft antenna'), type: 'gain' },
      { label: t('TX Losses'), value: round(-txLosses), unit: 'dB', notes: t('Cable, filter, mismatch'), type: 'loss' },
      { label: 'EIRP', value: round(eirp), unit: 'dBW', notes: t('Effective Isotropic Radiated Power'), type: 'result' },
      { label: t('Free Space Path Loss'), value: round(-fspl), unit: 'dB', notes: t('{{km}} km at {{mhz}} MHz', { km: slantRange, mhz: frequency }), type: 'loss' },
      { label: t('Atmospheric Loss'), value: round(-atmosphericLoss), unit: 'dB', notes: t('Rain, gas absorption'), type: 'loss' },
      { label: t('Pointing Loss'), value: round(-pointingLoss), unit: 'dB', notes: t('Antenna misalignment'), type: 'loss' },
      { label: t('Polarisation Loss'), value: round(-polLoss), unit: 'dB', notes: t('Pol mismatch'), type: 'loss' },
      { label: t('RX Antenna Gain'), value: round(rxGain), unit: 'dBi', notes: t('Ground station antenna'), type: 'gain' },
      { label: t('System G/T'), value: round(gt), unit: 'dB/K', notes: `Tsys = ${rxTemp} K`, type: 'result' },
      { label: 'C/N₀', value: round(cn0), unit: 'dBHz', notes: t('Carrier-to-noise density'), type: 'result' },
      { label: t('Eb/N₀ (available)'), value: round(ebN0), unit: 'dB', notes: t('Data rate: {{v}} Mbps', { v: (dataRate / 1e6).toFixed(1) }), type: 'result' },
      { label: t('Eb/N₀ (required)'), value: round(-reqEbN0), unit: 'dB', notes: t('Modulation + coding threshold'), type: 'loss' },
      { label: t('Implementation Margin'), value: round(-implMargin), unit: 'dB', notes: 'ECSS-E-ST-50-05C', type: 'loss' },
      { label: t('LINK MARGIN'), key: 'margin', value: round(margin), unit: 'dB', notes: margin >= 3 ? t('Closes with margin') : margin >= 0 ? t('Marginal') : t('DOES NOT CLOSE'), type: 'result' },
    ]
  }, [txPower, txGain, txLosses, frequency, slantRange, atmosphericLoss, pointingLoss, polLoss, rxGain, rxTemp, dataRate, reqEbN0, implMargin])

  const margin = budget[budget.length - 1]?.value || 0
  const [applied, setApplied] = useState(false)

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
        <button onClick={() => setLinkDirection('downlink')} style={{
          padding: '0.25rem 0.75rem', fontSize: fs.label, borderRadius: '4px', cursor: 'pointer',
          background: linkDirection === 'downlink' ? 'var(--interactive)' : 'var(--bg-secondary, var(--surface-2))',
          color: linkDirection === 'downlink' ? 'white' : 'var(--text-2)',
          border: `1px solid ${linkDirection === 'downlink' ? 'var(--interactive)' : 'var(--line)'}`,
        }}>{t('Downlink (Space→Ground)')}</button>
        <button onClick={() => setLinkDirection('uplink')} style={{
          padding: '0.25rem 0.75rem', fontSize: fs.label, borderRadius: '4px', cursor: 'pointer',
          background: linkDirection === 'uplink' ? 'var(--cat-2)' : 'var(--bg-secondary, var(--surface-2))',
          color: linkDirection === 'uplink' ? 'white' : 'var(--text-2)',
          border: `1px solid ${linkDirection === 'uplink' ? 'var(--cat-2)' : 'var(--line)'}`,
        }}>{t('Uplink (Ground→Space)')}</button>
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
            <InputRow label={t('Slant Range (km)')} value={slantRange} onChange={setSlantRange} step={50} />
            <InputRow label={t('Atmospheric Loss (dB)')} value={atmosphericLoss} onChange={setAtmosphericLoss} step={0.1} />
            <InputRow label={t('Pointing Loss (dB)')} value={pointingLoss} onChange={setPointingLoss} step={0.1} />
            <InputRow label={t('Polarisation Loss (dB)')} value={polLoss} onChange={setPolLoss} step={0.1} />
          </div>
          <div className="card">
            <h3 style={{ fontSize: fs.body, marginBottom: '0.4rem' }}>{t('Receiver (Ground)')}</h3>
            <InputRow label={t('RX Antenna Gain (dBi)')} value={rxGain} onChange={setRxGain} step={1} />
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
      <button className="btn" onClick={async () => { await apply(); setApplied(true); setTimeout(() => setApplied(false), 2000) }}
        style={{ marginTop: '0.75rem', width: '100%', background: applied ? 'var(--status-ok)' : 'var(--interactive)', fontSize: fs.body }}>
        {applied ? t('Applied — reconverging...') : t('Apply to Design')}
      </button>
    </div>
  )
}

function InputRow({ label, value, onChange, step }: { label: string; value: number; onChange: (v: number) => void; step: number }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem' }}>
      <span style={{ flex: 1, fontSize: fs.label, color: 'var(--text-2)' }}>{label}</span>
      <input className="input" type="number" value={value} step={step}
        onChange={e => onChange(Number(e.target.value))}
        style={{ width: '80px', fontSize: fs.label, textAlign: 'right' }} />
    </div>
  )
}

function round(v: number): number { return Math.round(v * 10) / 10 }

const th: React.CSSProperties = { padding: '0.3rem 0.5rem', textAlign: 'left', fontSize: fs.label, color: 'var(--text-2)', textTransform: 'uppercase' }
const thR: React.CSSProperties = { ...th, textAlign: 'right' }
const td: React.CSSProperties = { padding: '0.25rem 0.5rem' }
const tdR: React.CSSProperties = { ...td, textAlign: 'right', fontFamily: 'monospace' }
