/**
 * LinkBudgetTool — Interactive link budget calculator.
 *
 * Computes EIRP, FSPL, received power, C/N0, Eb/N0, margin per ECSS-E-ST-50-05C.
 * Shows each term as a cascade with the final margin.
 */
import { useState, useMemo, useRef, useCallback } from 'react'
import { useDesignStore } from '../stores/designStore'
import { useApplyToDesign } from '../hooks/useApplyToDesign'

interface LinkBudgetLine {
  label: string
  value: number
  unit: string
  notes: string
  type: 'gain' | 'loss' | 'result'
}

export function LinkBudgetTool() {
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
    const totalPathLoss = fspl + atmosphericLoss + pointingLoss + polLoss
    const receivedPower = eirp - totalPathLoss + rxGain
    const gt = rxGain - 10 * Math.log10(rxTemp)
    const cn0 = eirp - fspl - atmosphericLoss - pointingLoss - polLoss + gt - k
    const ebN0 = cn0 - 10 * Math.log10(dataRate)
    const margin = ebN0 - reqEbN0 - implMargin

    return [
      { label: 'TX Power', value: round(10 * Math.log10(txPower)), unit: 'dBW', notes: `${txPower} W`, type: 'gain' },
      { label: 'TX Antenna Gain', value: round(txGain), unit: 'dBi', notes: 'Spacecraft antenna', type: 'gain' },
      { label: 'TX Losses', value: round(-txLosses), unit: 'dB', notes: 'Cable, filter, mismatch', type: 'loss' },
      { label: 'EIRP', value: round(eirp), unit: 'dBW', notes: 'Effective Isotropic Radiated Power', type: 'result' },
      { label: 'Free Space Path Loss', value: round(-fspl), unit: 'dB', notes: `${slantRange} km at ${frequency} MHz`, type: 'loss' },
      { label: 'Atmospheric Loss', value: round(-atmosphericLoss), unit: 'dB', notes: 'Rain, gas absorption', type: 'loss' },
      { label: 'Pointing Loss', value: round(-pointingLoss), unit: 'dB', notes: 'Antenna misalignment', type: 'loss' },
      { label: 'Polarisation Loss', value: round(-polLoss), unit: 'dB', notes: 'Pol mismatch', type: 'loss' },
      { label: 'RX Antenna Gain', value: round(rxGain), unit: 'dBi', notes: 'Ground station antenna', type: 'gain' },
      { label: 'System G/T', value: round(gt), unit: 'dB/K', notes: `Tsys = ${rxTemp} K`, type: 'result' },
      { label: 'C/N₀', value: round(cn0), unit: 'dBHz', notes: 'Carrier-to-noise density', type: 'result' },
      { label: 'Eb/N₀ (available)', value: round(ebN0), unit: 'dB', notes: `Data rate: ${(dataRate / 1e6).toFixed(1)} Mbps`, type: 'result' },
      { label: 'Eb/N₀ (required)', value: round(-reqEbN0), unit: 'dB', notes: 'Modulation + coding threshold', type: 'loss' },
      { label: 'Implementation Margin', value: round(-implMargin), unit: 'dB', notes: 'ECSS-E-ST-50-05C', type: 'loss' },
      { label: 'LINK MARGIN', value: round(margin), unit: 'dB', notes: margin >= 3 ? 'Closes with margin' : margin >= 0 ? 'Marginal' : 'DOES NOT CLOSE', type: 'result' },
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
      <h2 style={{ marginBottom: '0.25rem' }}>Link Budget Calculator</h2>
      <p style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.75rem' }}>
        Per ECSS-E-ST-50-05C. Edit any parameter to see the impact on link margin.
      </p>

      {/* Uplink / Downlink toggle */}
      <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.75rem' }}>
        <button onClick={() => setLinkDirection('downlink')} style={{
          padding: '0.25rem 0.75rem', fontSize: '0.78rem', borderRadius: '4px', cursor: 'pointer',
          background: linkDirection === 'downlink' ? '#3b82f6' : 'var(--bg-secondary, #1f2937)',
          color: linkDirection === 'downlink' ? 'white' : '#9ca3af',
          border: `1px solid ${linkDirection === 'downlink' ? '#3b82f6' : '#374151'}`,
        }}>Downlink (Space→Ground)</button>
        <button onClick={() => setLinkDirection('uplink')} style={{
          padding: '0.25rem 0.75rem', fontSize: '0.78rem', borderRadius: '4px', cursor: 'pointer',
          background: linkDirection === 'uplink' ? '#8b5cf6' : 'var(--bg-secondary, #1f2937)',
          color: linkDirection === 'uplink' ? 'white' : '#9ca3af',
          border: `1px solid ${linkDirection === 'uplink' ? '#8b5cf6' : '#374151'}`,
        }}>Uplink (Ground→Space)</button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        {/* Input column */}
        <div>
          <div className="card">
            <h3 style={{ fontSize: '0.85rem', marginBottom: '0.4rem' }}>
              Transmitter ({linkDirection === 'downlink' ? 'Spacecraft' : 'Ground Station'})
            </h3>
            <InputRow label="TX Power (W)" value={txPower} onChange={setTxPower} step={0.5} />
            <InputRow label="TX Antenna Gain (dBi)" value={txGain} onChange={setTxGain} step={1} />
            <InputRow label="TX Losses (dB)" value={txLosses} onChange={setTxLosses} step={0.1} />
            <InputRow label="Frequency (MHz)" value={frequency} onChange={setFrequency} step={100} />
          </div>
          <div className="card">
            <h3 style={{ fontSize: '0.85rem', marginBottom: '0.4rem' }}>Path</h3>
            <InputRow label="Slant Range (km)" value={slantRange} onChange={setSlantRange} step={50} />
            <InputRow label="Atmospheric Loss (dB)" value={atmosphericLoss} onChange={setAtmosphericLoss} step={0.1} />
            <InputRow label="Pointing Loss (dB)" value={pointingLoss} onChange={setPointingLoss} step={0.1} />
            <InputRow label="Polarisation Loss (dB)" value={polLoss} onChange={setPolLoss} step={0.1} />
          </div>
          <div className="card">
            <h3 style={{ fontSize: '0.85rem', marginBottom: '0.4rem' }}>Receiver (Ground)</h3>
            <InputRow label="RX Antenna Gain (dBi)" value={rxGain} onChange={setRxGain} step={1} />
            <InputRow label="System Temp (K)" value={rxTemp} onChange={setRxTemp} step={10} />
            <InputRow label="Data Rate (bps)" value={dataRate} onChange={setDataRate} step={100000} />
            <InputRow label="Required Eb/N₀ (dB)" value={reqEbN0} onChange={setReqEbN0} step={0.5} />
            <InputRow label="Implementation Margin (dB)" value={implMargin} onChange={setImplMargin} step={0.5} />
          </div>
        </div>

        {/* Budget cascade column */}
        <div className="card">
          <h3 style={{ fontSize: '0.85rem', marginBottom: '0.4rem' }}>Link Budget Cascade</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
            <thead>
              <tr style={{ background: 'var(--bg-primary, #0a0e1a)' }}>
                <th style={th}>Parameter</th>
                <th style={thR}>Value</th>
                <th style={th}>Notes</th>
              </tr>
            </thead>
            <tbody>
              {budget.map((line, i) => (
                <tr key={i} style={{
                  borderBottom: line.type === 'result' ? '2px solid #374151' : '1px solid rgba(255,255,255,0.05)',
                  background: line.label === 'LINK MARGIN' ? (margin >= 3 ? 'rgba(16,185,129,0.1)' : margin >= 0 ? 'rgba(245,158,11,0.1)' : 'rgba(239,68,68,0.1)') : 'transparent',
                }}>
                  <td style={{ ...td, fontWeight: line.type === 'result' ? 700 : 400 }}>{line.label}</td>
                  <td style={{
                    ...tdR, fontWeight: line.type === 'result' ? 700 : 400,
                    color: line.type === 'gain' ? '#10b981' : line.type === 'loss' ? '#ef4444' : line.label === 'LINK MARGIN' ? (margin >= 3 ? '#10b981' : margin >= 0 ? '#f59e0b' : '#ef4444') : '#d1d5db',
                  }}>
                    {line.value >= 0 ? '+' : ''}{line.value.toFixed(1)} {line.unit}
                  </td>
                  <td style={{ ...td, fontSize: '0.68rem', color: '#6b7280' }}>{line.notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Apply to design */}
      <button className="btn" onClick={async () => { await apply(); setApplied(true); setTimeout(() => setApplied(false), 2000) }}
        style={{ marginTop: '0.75rem', width: '100%', background: applied ? '#10b981' : '#3b82f6', fontSize: '0.82rem' }}>
        {applied ? 'Applied — reconverging...' : 'Apply to Design'}
      </button>
    </div>
  )
}

function InputRow({ label, value, onChange, step }: { label: string; value: number; onChange: (v: number) => void; step: number }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem' }}>
      <span style={{ flex: 1, fontSize: '0.72rem', color: '#9ca3af' }}>{label}</span>
      <input className="input" type="number" value={value} step={step}
        onChange={e => onChange(Number(e.target.value))}
        style={{ width: '80px', fontSize: '0.72rem', textAlign: 'right' }} />
    </div>
  )
}

function round(v: number): number { return Math.round(v * 10) / 10 }

const th: React.CSSProperties = { padding: '0.3rem 0.5rem', textAlign: 'left', fontSize: '0.65rem', color: '#9ca3af', textTransform: 'uppercase' }
const thR: React.CSSProperties = { ...th, textAlign: 'right' }
const td: React.CSSProperties = { padding: '0.25rem 0.5rem' }
const tdR: React.CSSProperties = { ...td, textAlign: 'right', fontFamily: 'monospace' }
