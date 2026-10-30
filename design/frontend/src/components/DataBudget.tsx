/**
 * DataBudget — Data pipeline budget from generation to user delivery.
 *
 * Two tabs: "Payload Data" and "TMTC".
 * Payload Data: generation rate, onboard storage, downlink capacity, balance.
 * TMTC: HK telemetry, TC uplink, CCSDS overhead, Reed-Solomon framing.
 * Mission profile selector for different acquisition patterns.
 *
 * All quantities in bits/bytes/MB/GB — no power/energy references.
 */
import { useMemo, useState } from 'react'
import { useDesignStore } from '../stores/designStore'
import { useActiveParameters } from '../hooks/useActiveParameters'
import { useApplyToDesign } from '../hooks/useApplyToDesign'

type DataTab = 'payload' | 'tmtc'
type MissionProfile = 'leo_imaging' | '24_7_rf' | 'wide_fov'

const PROFILE_LABELS: Record<MissionProfile, string> = {
  leo_imaging: 'LEO Imaging (slew-based)',
  '24_7_rf': '24/7 RF (continuous acquisition)',
  wide_fov: 'Wide FOV (continuous, no slew)',
}

const PROFILE_DUTY: Record<MissionProfile, number> = {
  leo_imaging: 25,   // 25% duty cycle per orbit
  '24_7_rf': 100,    // 100% duty cycle
  wide_fov: 100,     // continuous
}

// CCSDS packet overhead constants
const CCSDS_PRIMARY_HEADER_BYTES = 6
const CCSDS_SECONDARY_HEADER_BYTES = 10
const CCSDS_TOTAL_HEADER_BYTES = CCSDS_PRIMARY_HEADER_BYTES + CCSDS_SECONDARY_HEADER_BYTES

// Reed-Solomon coding overhead
const RS_CODED = 255
const RS_DATA = 223
const RS_OVERHEAD_RATIO = RS_CODED / RS_DATA  // ~1.143

export function DataBudget() {
  const reqs = useDesignStore(s => s.requirements)
  const params = useActiveParameters()
  const get = (id: string) => { const p = params[id]; return p && typeof p.value === 'number' ? p.value : 0 }

  const [activeTab, setActiveTab] = useState<DataTab>('payload')
  const [profile, setProfile] = useState<MissionProfile>('leo_imaging')
  const [hkRate_kbps, setHkRate] = useState(1)  // default 1 kbps continuous HK
  const [tcRate_kbps, setTcRate] = useState(4)   // default 4 kbps uplink
  const [packetDataBytes, setPacketDataBytes] = useState(440)  // typical CCSDS packet data field
  const [useReedSolomon, setUseReedSolomon] = useState(true)

  const pipeline = useMemo(() => {
    const pl = reqs.payloads?.[0]
    const dataRateMbps = pl?.data_rate_mbps || 10
    const dutyCyclePct = profile === 'leo_imaging' ? (pl?.duty_cycle_percent || 25) : PROFILE_DUTY[profile]
    const orbitPeriodMin = 95 // ~500km LEO
    const orbitsPerDay = (24 * 60) / orbitPeriodMin  // ~15.16

    // Generation: data rate * duty cycle * active time per day
    const activeTimePerOrbitSec = orbitPeriodMin * 60 * (dutyCyclePct / 100)
    const genBitsPerOrbit = dataRateMbps * 1e6 * activeTimePerOrbitSec
    const genBitsPerDay = genBitsPerOrbit * orbitsPerDay
    const genMBPerDay = genBitsPerDay / (8 * 1e6)
    const genGBPerDay = genMBPerDay / 1000

    // Storage
    const storageGB = get('data.storage_gb') || 32
    const storageMB = storageGB * 1000
    const fillTimeDays = storageMB / Math.max(genMBPerDay, 0.01)

    // Downlink
    const contactMinPerDay = get('link.contact_min_per_day') || 30
    const dlRateMbps = get('link.downlink_data_rate_mbps') || dataRateMbps
    const dlBitsPerDay = dlRateMbps * 1e6 * contactMinPerDay * 60
    const dlMBPerDay = dlBitsPerDay / (8 * 1e6)
    const dlGBPerDay = dlMBPerDay / 1000

    // Balance
    const balanceMBPerDay = dlMBPerDay - genMBPerDay

    return {
      generation: {
        rate_mbps: dataRateMbps,
        duty_pct: dutyCyclePct,
        daily_bits: genBitsPerDay,
        daily_mb: genMBPerDay,
        daily_gb: genGBPerDay,
      },
      storage: {
        capacity_gb: storageGB,
        capacity_mb: storageMB,
        fill_time_days: fillTimeDays,
      },
      downlink: {
        rate_mbps: dlRateMbps,
        contact_min: contactMinPerDay,
        daily_bits: dlBitsPerDay,
        daily_mb: dlMBPerDay,
        daily_gb: dlGBPerDay,
      },
      balance: {
        surplus_mb: balanceMBPerDay,
        balanced: balanceMBPerDay >= 0,
      },
    }
  }, [reqs, params, profile])

  // TMTC calculations
  const tmtc = useMemo(() => {
    const hkBitsPerDay = hkRate_kbps * 1000 * 86400  // continuous
    const hkMBPerDay = hkBitsPerDay / (8 * 1e6)
    const tcBitsPerPass = tcRate_kbps * 1000 * (get('link.contact_min_per_day') || 30) * 60
    const tcMBPerDay = tcBitsPerPass / (8 * 1e6)

    // Packet overhead
    const totalPacketBytes = CCSDS_TOTAL_HEADER_BYTES + packetDataBytes
    const overheadPct = (CCSDS_TOTAL_HEADER_BYTES / totalPacketBytes) * 100

    // Frame overhead with/without RS
    const frameOverheadPct = useReedSolomon ? ((RS_OVERHEAD_RATIO - 1) * 100) : 0
    const totalOverheadPct = overheadPct + frameOverheadPct

    // Effective data after overhead
    const effectiveRatio = (1 - totalOverheadPct / 100)

    return {
      hk_rate_kbps: hkRate_kbps,
      hk_daily_mb: hkMBPerDay,
      tc_rate_kbps: tcRate_kbps,
      tc_daily_mb: tcMBPerDay,
      packet_header_bytes: CCSDS_TOTAL_HEADER_BYTES,
      packet_data_bytes: packetDataBytes,
      packet_total_bytes: CCSDS_TOTAL_HEADER_BYTES + packetDataBytes,
      packet_overhead_pct: overheadPct,
      rs_overhead_pct: frameOverheadPct,
      total_overhead_pct: totalOverheadPct,
      effective_ratio: effectiveRatio,
    }
  }, [hkRate_kbps, tcRate_kbps, packetDataBytes, useReedSolomon, params])

  const p = pipeline
  const [applied, setApplied] = useState(false)

  const apply = useApplyToDesign({
    events: [
      { kind: 'parameter_override', target_id: 'data.storage_gb', new_value: p.storage.capacity_gb },
      { kind: 'parameter_override', target_id: 'link.downlink_data_rate_mbps', new_value: p.downlink.rate_mbps },
      { kind: 'parameter_override', target_id: 'link.contact_min_per_day', new_value: p.downlink.contact_min },
    ],
    correlation_id: 'data-budget',
    rationale: 'Apply data pipeline budget parameters',
  })

  return (
    <div className="card">
      <h3 style={{ fontSize: '0.9rem', marginBottom: '0.3rem' }}>Data Budget</h3>
      <p style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.5rem' }}>
        Data volume analysis in bits/bytes. Payload data and TMTC overhead.
      </p>

      {/* Mission profile selector */}
      <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <span style={{ fontSize: '0.72rem', color: '#9ca3af', fontWeight: 600 }}>Mission Profile:</span>
        {(Object.entries(PROFILE_LABELS) as [MissionProfile, string][]).map(([id, label]) => (
          <button key={id} onClick={() => setProfile(id)} style={{
            padding: '0.25rem 0.6rem', fontSize: '0.7rem', borderRadius: '4px', cursor: 'pointer',
            background: profile === id ? '#3b82f6' : 'var(--bg-secondary, #1f2937)',
            color: profile === id ? 'white' : '#9ca3af',
            border: `1px solid ${profile === id ? '#3b82f6' : '#374151'}`,
          }}>{label}</button>
        ))}
      </div>

      {/* Tab selector */}
      <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.75rem' }}>
        {([
          { id: 'payload' as DataTab, label: 'Payload Data' },
          { id: 'tmtc' as DataTab, label: 'TM/TC' },
        ]).map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
            padding: '0.3rem 0.75rem', fontSize: '0.78rem', borderRadius: '4px', cursor: 'pointer',
            background: activeTab === t.id ? '#8b5cf6' : 'var(--bg-secondary, #1f2937)',
            color: activeTab === t.id ? 'white' : '#9ca3af',
            border: `1px solid ${activeTab === t.id ? '#8b5cf6' : '#374151'}`,
          }}>{t.label}</button>
        ))}
      </div>

      {/* Payload Data tab */}
      {activeTab === 'payload' && (
        <>
          {/* Flow diagram */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.2rem', marginBottom: '0.75rem', fontSize: '0.72rem', flexWrap: 'wrap' }}>
            <FlowBox label="Generate" value={`${p.generation.daily_mb.toFixed(1)} MB/day`} sub={`${p.generation.rate_mbps} Mbps × ${p.generation.duty_pct}% duty`} color="#8b5cf6" />
            <Arrow />
            <FlowBox label="Store" value={`${p.storage.capacity_gb} GB capacity`} sub={`fills in ${p.storage.fill_time_days.toFixed(1)} days`} color="#3b82f6" />
            <Arrow />
            <FlowBox label="Downlink" value={`${p.downlink.daily_mb.toFixed(1)} MB/day`} sub={`${p.downlink.rate_mbps} Mbps × ${p.downlink.contact_min} min/day`} color="#10b981" />
          </div>

          {/* Detailed numbers table */}
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem', marginBottom: '0.75rem' }}>
            <thead>
              <tr style={{ background: 'var(--bg-primary, #0a0e1a)' }}>
                <th style={th}>Parameter</th>
                <th style={{ ...th, textAlign: 'right' }}>Value</th>
                <th style={{ ...th, textAlign: 'right' }}>Unit</th>
              </tr>
            </thead>
            <tbody>
              <tr style={trBorder}><td style={tdL} colSpan={3}><strong style={{ color: '#8b5cf6' }}>Generation</strong></td></tr>
              <tr style={trBorder}><td style={tdL}>Payload data rate</td><td style={tdR}>{p.generation.rate_mbps}</td><td style={tdR}>Mbps</td></tr>
              <tr style={trBorder}><td style={tdL}>Duty cycle</td><td style={tdR}>{p.generation.duty_pct}</td><td style={tdR}>%</td></tr>
              <tr style={trBorder}><td style={tdL}>Daily generation</td><td style={tdR}>{p.generation.daily_mb.toFixed(1)}</td><td style={tdR}>MB/day</td></tr>
              <tr style={trBorder}><td style={tdL}>Daily generation</td><td style={tdR}>{(p.generation.daily_bits / 1e9).toFixed(2)}</td><td style={tdR}>Gbit/day</td></tr>

              <tr style={trBorder}><td style={tdL} colSpan={3}><strong style={{ color: '#3b82f6' }}>Onboard Storage</strong></td></tr>
              <tr style={trBorder}><td style={tdL}>Capacity</td><td style={tdR}>{p.storage.capacity_gb}</td><td style={tdR}>GB</td></tr>
              <tr style={trBorder}><td style={tdL}>Capacity</td><td style={tdR}>{p.storage.capacity_mb.toFixed(0)}</td><td style={tdR}>MB</td></tr>
              <tr style={trBorder}><td style={tdL}>Time to fill</td><td style={tdR}>{p.storage.fill_time_days.toFixed(1)}</td><td style={tdR}>days</td></tr>

              <tr style={trBorder}><td style={tdL} colSpan={3}><strong style={{ color: '#10b981' }}>Downlink</strong></td></tr>
              <tr style={trBorder}><td style={tdL}>Link data rate</td><td style={tdR}>{p.downlink.rate_mbps}</td><td style={tdR}>Mbps</td></tr>
              <tr style={trBorder}><td style={tdL}>Contact time / day</td><td style={tdR}>{p.downlink.contact_min}</td><td style={tdR}>min</td></tr>
              <tr style={trBorder}><td style={tdL}>Daily downlink capacity</td><td style={tdR}>{p.downlink.daily_mb.toFixed(1)}</td><td style={tdR}>MB/day</td></tr>
              <tr style={trBorder}><td style={tdL}>Daily downlink capacity</td><td style={tdR}>{(p.downlink.daily_bits / 1e9).toFixed(2)}</td><td style={tdR}>Gbit/day</td></tr>
            </tbody>
          </table>

          {/* Balance indicator */}
          <div style={{
            padding: '0.4rem 0.6rem', borderRadius: '4px', fontSize: '0.78rem',
            background: p.balance.balanced ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
            border: `1px solid ${p.balance.balanced ? '#10b981' : '#ef4444'}`,
            display: 'flex', alignItems: 'center', gap: '0.5rem',
          }}>
            <span style={{ fontWeight: 700, color: p.balance.balanced ? '#10b981' : '#ef4444' }}>
              {p.balance.balanced ? 'BALANCED' : 'OVERFLOW'}
            </span>
            <span style={{ color: '#9ca3af' }}>
              {p.balance.balanced ? 'Surplus' : 'Deficit'}: {Math.abs(p.balance.surplus_mb).toFixed(1)} MB/day
            </span>
            {!p.balance.balanced && (
              <span style={{ color: '#ef4444', fontSize: '0.72rem' }}>
                — need higher data rate, more contact time, or reduced duty cycle
              </span>
            )}
          </div>
        </>
      )}

      {/* TMTC tab */}
      {activeTab === 'tmtc' && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '0.75rem' }}>
            {/* HK Telemetry */}
            <div style={{ background: 'var(--bg-primary, #111827)', padding: '0.6rem', borderRadius: '6px', border: '1px solid #374151' }}>
              <h4 style={{ fontSize: '0.78rem', color: '#06b6d4', marginBottom: '0.3rem' }}>HK Telemetry (Downlink)</h4>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', marginBottom: '0.3rem' }}>
                <label style={{ fontSize: '0.68rem', color: '#9ca3af' }}>Rate:</label>
                <input type="number" min={0.1} max={100} step={0.1} value={hkRate_kbps}
                  onChange={e => setHkRate(Number(e.target.value))}
                  style={{ width: '50px', fontSize: '0.72rem', textAlign: 'center', background: 'var(--bg-secondary, #1f2937)', border: '1px solid #374151', borderRadius: '3px', color: '#d1d5db' }} />
                <span style={{ fontSize: '0.68rem', color: '#6b7280' }}>kbps (continuous)</span>
              </div>
              <div style={{ fontSize: '0.72rem', color: '#d1d5db' }}>
                Daily HK volume: <strong>{tmtc.hk_daily_mb.toFixed(2)} MB/day</strong>
              </div>
              <div style={{ fontSize: '0.65rem', color: '#6b7280' }}>
                = {(tmtc.hk_daily_mb * 8).toFixed(1)} Mbit/day
              </div>
            </div>

            {/* TC Uplink */}
            <div style={{ background: 'var(--bg-primary, #111827)', padding: '0.6rem', borderRadius: '6px', border: '1px solid #374151' }}>
              <h4 style={{ fontSize: '0.78rem', color: '#f59e0b', marginBottom: '0.3rem' }}>TC Uplink</h4>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', marginBottom: '0.3rem' }}>
                <label style={{ fontSize: '0.68rem', color: '#9ca3af' }}>Rate:</label>
                <input type="number" min={0.1} max={100} step={0.1} value={tcRate_kbps}
                  onChange={e => setTcRate(Number(e.target.value))}
                  style={{ width: '50px', fontSize: '0.72rem', textAlign: 'center', background: 'var(--bg-secondary, #1f2937)', border: '1px solid #374151', borderRadius: '3px', color: '#d1d5db' }} />
                <span style={{ fontSize: '0.68rem', color: '#6b7280' }}>kbps</span>
              </div>
              <div style={{ fontSize: '0.72rem', color: '#d1d5db' }}>
                Daily TC volume: <strong>{tmtc.tc_daily_mb.toFixed(3)} MB/day</strong>
              </div>
              <div style={{ fontSize: '0.65rem', color: '#6b7280' }}>
                (during {get('link.contact_min_per_day') || 30} min contact)
              </div>
            </div>
          </div>

          {/* Packet overhead */}
          <div style={{ background: 'var(--bg-primary, #111827)', padding: '0.6rem', borderRadius: '6px', border: '1px solid #374151', marginBottom: '0.75rem' }}>
            <h4 style={{ fontSize: '0.78rem', color: '#8b5cf6', marginBottom: '0.3rem' }}>CCSDS Packet Overhead</h4>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem' }}>
              <tbody>
                <tr style={trBorder}>
                  <td style={tdL}>Primary header</td>
                  <td style={tdR}>{CCSDS_PRIMARY_HEADER_BYTES} bytes</td>
                </tr>
                <tr style={trBorder}>
                  <td style={tdL}>Secondary header</td>
                  <td style={tdR}>{CCSDS_SECONDARY_HEADER_BYTES} bytes</td>
                </tr>
                <tr style={trBorder}>
                  <td style={tdL}>
                    Data field
                    <input type="number" min={1} max={65536} step={1} value={packetDataBytes}
                      onChange={e => setPacketDataBytes(Number(e.target.value))}
                      style={{ width: '60px', fontSize: '0.68rem', textAlign: 'center', marginLeft: '0.3rem', background: 'var(--bg-secondary, #1f2937)', border: '1px solid #374151', borderRadius: '3px', color: '#d1d5db' }} />
                    <span style={{ fontSize: '0.6rem', color: '#6b7280', marginLeft: '0.2rem' }}>bytes</span>
                  </td>
                  <td style={tdR}>{packetDataBytes} bytes</td>
                </tr>
                <tr style={{ ...trBorder, fontWeight: 700 }}>
                  <td style={tdL}>Total packet size</td>
                  <td style={tdR}>{tmtc.packet_total_bytes} bytes</td>
                </tr>
                <tr style={trBorder}>
                  <td style={tdL}>Packet overhead</td>
                  <td style={{ ...tdR, color: '#f59e0b' }}>{tmtc.packet_overhead_pct.toFixed(1)}%</td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Frame overhead */}
          <div style={{ background: 'var(--bg-primary, #111827)', padding: '0.6rem', borderRadius: '6px', border: '1px solid #374151', marginBottom: '0.75rem' }}>
            <h4 style={{ fontSize: '0.78rem', color: '#10b981', marginBottom: '0.3rem' }}>Frame Coding Overhead</h4>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.72rem', color: '#d1d5db', cursor: 'pointer' }}>
                <input type="checkbox" checked={useReedSolomon} onChange={e => setUseReedSolomon(e.target.checked)}
                  style={{ accentColor: '#10b981' }} />
                Reed-Solomon ({RS_CODED}/{RS_DATA})
              </label>
            </div>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem' }}>
              <tbody>
                <tr style={trBorder}>
                  <td style={tdL}>RS overhead</td>
                  <td style={tdR}>{useReedSolomon ? `${tmtc.rs_overhead_pct.toFixed(1)}%` : 'N/A (no RS)'}</td>
                </tr>
                <tr style={{ ...trBorder, fontWeight: 700 }}>
                  <td style={tdL}>Total protocol overhead (packet + frame)</td>
                  <td style={{ ...tdR, color: '#f59e0b' }}>{tmtc.total_overhead_pct.toFixed(1)}%</td>
                </tr>
                <tr style={trBorder}>
                  <td style={tdL}>Effective user data ratio</td>
                  <td style={{ ...tdR, color: '#10b981' }}>{(tmtc.effective_ratio * 100).toFixed(1)}%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </>
      )}

      <button className="btn" onClick={async () => { await apply(); setApplied(true); setTimeout(() => setApplied(false), 2000) }}
        style={{ marginTop: '0.5rem', width: '100%', background: applied ? '#10b981' : '#3b82f6', fontSize: '0.78rem' }}>
        {applied ? 'Applied — reconverging...' : 'Apply to Design'}
      </button>
    </div>
  )
}

function FlowBox({ label, value, sub, color }: { label: string; value: string; sub: string; color: string }) {
  return (
    <div style={{
      padding: '0.3rem 0.5rem', borderRadius: '4px', minWidth: '100px', textAlign: 'center',
      background: `${color}11`, border: `1px solid ${color}40`,
    }}>
      <div style={{ fontSize: '0.65rem', color, fontWeight: 600, textTransform: 'uppercase' }}>{label}</div>
      <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#d1d5db' }}>{value}</div>
      <div style={{ fontSize: '0.6rem', color: '#6b7280' }}>{sub}</div>
    </div>
  )
}

function Arrow() {
  return <span style={{ fontSize: '1rem', color: '#6b7280' }}>→</span>
}

const th: React.CSSProperties = { padding: '0.3rem 0.5rem', textAlign: 'left', fontSize: '0.65rem', textTransform: 'uppercase', color: '#9ca3af' }
const tdL: React.CSSProperties = { padding: '0.25rem 0.5rem', color: '#d1d5db' }
const tdR: React.CSSProperties = { padding: '0.25rem 0.5rem', textAlign: 'right', fontFamily: 'monospace', color: '#d1d5db' }
const trBorder: React.CSSProperties = { borderBottom: '1px solid rgba(255,255,255,0.05)' }
