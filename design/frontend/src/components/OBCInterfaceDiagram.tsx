import { fs } from '../theme/tokens'
/**
 * OBCInterfaceDiagram — shows OBC connections to all subsystems.
 *
 * Displays point-to-point interfaces, bus interfaces with addresses,
 * data rates, and protocols for each connection.
 */

interface OBCConnection {
  target: string
  protocol: string
  dataRate: string
  busType: 'p2p' | 'bus'
  address?: string
}

const DEFAULT_OBC_CONNECTIONS: OBCConnection[] = [
  { target: 'AOCS', protocol: 'I2C / UART', dataRate: '115.2 kbps', busType: 'bus', address: '0x20' },
  { target: 'EPS', protocol: 'I2C', dataRate: '100 kbps', busType: 'bus', address: '0x10' },
  { target: 'TTC (S-band)', protocol: 'UART / SPI', dataRate: '9.6-115.2 kbps', busType: 'p2p' },
  { target: 'TTC (X-band)', protocol: 'LVDS / SpaceWire', dataRate: '100+ Mbps', busType: 'p2p' },
  { target: 'Payload', protocol: 'SPI / LVDS', dataRate: '1-120 Mbps', busType: 'p2p' },
  { target: 'GPS Receiver', protocol: 'UART', dataRate: '9.6 kbps', busType: 'bus', address: '0x42' },
  { target: 'Magnetometer', protocol: 'I2C', dataRate: '100 kbps', busType: 'bus', address: '0x1E' },
  { target: 'Sun Sensors', protocol: 'I2C / Analog', dataRate: '10 kbps', busType: 'bus', address: '0x60' },
  { target: 'Thermal Sensors', protocol: 'OneWire / I2C', dataRate: '10 kbps', busType: 'bus', address: '0x48-0x4F' },
]

export function OBCInterfaceDiagram() {

  // Build connections from model if available, else use defaults
  const connections = DEFAULT_OBC_CONNECTIONS

  const busConnections = connections.filter(c => c.busType === 'bus')
  const p2pConnections = connections.filter(c => c.busType === 'p2p')

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ fontSize: fs.value, marginBottom: '0.25rem' }}>OBC Interface Architecture</h2>
      <p style={{ fontSize: fs.label, color: 'var(--text-2)', marginBottom: '0.75rem' }}>
        Data interfaces between the OBC and all subsystems. Shows protocols, data rates, and bus addresses.
      </p>

      {/* Visual diagram */}
      <div className="card" style={{ marginBottom: '0.75rem' }}>
        <svg width="100%" height="300" viewBox="0 0 600 300" style={{ background: 'var(--surface-0)', borderRadius: '4px' }}>
          {/* OBC central box */}
          <rect x="230" y="110" width="140" height="80" rx="8" fill="color-mix(in srgb, var(--cat-2) 13%, transparent)" stroke="var(--cat-2)" strokeWidth="2" />
          <text x="300" y="140" textAnchor="middle" fill="var(--cat-2)" fontSize={fs.label} fontWeight="700">OBC</text>
          <text x="300" y="158" textAnchor="middle" fill="var(--text-2)" fontSize={fs.label}>Command & Data Handling</text>
          <text x="300" y="172" textAnchor="middle" fill="var(--text-3)" fontSize={fs.label}>Flight Software | FDIR</text>

          {/* I2C Bus (left side) */}
          <line x1="230" y1="140" x2="30" y2="140" stroke="var(--interactive)" strokeWidth="2" />
          <text x="130" y="132" textAnchor="middle" fill="var(--interactive)" fontSize={fs.label} fontWeight="600">I2C Bus</text>

          {/* Bus devices */}
          {busConnections.map((c, i) => {
            const y = 30 + i * 35
            return (
              <g key={i}>
                <line x1="30" y1="140" x2="30" y2={y + 12} stroke="color-mix(in srgb, var(--interactive) 25%, transparent)" strokeWidth="1" />
                <rect x="5" y={y} width="100" height="24" rx="4" fill="var(--surface-2)" stroke="color-mix(in srgb, var(--interactive) 25%, transparent)" strokeWidth="1" />
                <text x="55" y={y + 10} textAnchor="middle" fill="var(--text)" fontSize={fs.label}>{c.target}</text>
                <text x="55" y={y + 20} textAnchor="middle" fill="var(--text-3)" fontSize={fs.label}>{c.address || ''} | {c.dataRate}</text>
              </g>
            )
          })}

          {/* Point-to-point connections (right side) */}
          {p2pConnections.map((c, i) => {
            const y = 50 + i * 50
            return (
              <g key={i}>
                <line x1="370" y1="150" x2="450" y2={y + 15} stroke="var(--status-caution)" strokeWidth="1.5" />
                <rect x="450" y={y} width="140" height="30" rx="4" fill="var(--surface-2)" stroke="color-mix(in srgb, var(--status-caution) 25%, transparent)" strokeWidth="1" />
                <text x="520" y={y + 12} textAnchor="middle" fill="var(--text)" fontSize={fs.label}>{c.target}</text>
                <text x="520" y={y + 24} textAnchor="middle" fill="var(--text-3)" fontSize={fs.label}>{c.protocol} | {c.dataRate}</text>
              </g>
            )
          })}

          {/* Legend */}
          <text x="10" y="290" fill="var(--text-3)" fontSize={fs.label} fontWeight="600">LEGEND:</text>
          <line x1="60" y1="288" x2="80" y2="288" stroke="var(--interactive)" strokeWidth="2" />
          <text x="85" y="291" fill="var(--text-3)" fontSize={fs.label}>I2C/SPI Bus</text>
          <line x1="160" y1="288" x2="180" y2="288" stroke="var(--status-caution)" strokeWidth="1.5" />
          <text x="185" y="291" fill="var(--text-3)" fontSize={fs.label}>Point-to-Point</text>
        </svg>
      </div>

      {/* Interface table */}
      <div className="card">
        <h3 style={{ fontSize: fs.body, marginBottom: '0.3rem' }}>Interface Register</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: fs.label }}>
          <thead>
            <tr style={{ background: 'var(--bg-primary, var(--surface-0))' }}>
              <th style={th}>Target</th>
              <th style={th}>Type</th>
              <th style={th}>Protocol</th>
              <th style={th}>Data Rate</th>
              <th style={th}>Bus Address</th>
            </tr>
          </thead>
          <tbody>
            {connections.map((c, i) => (
              <tr key={i} style={{ borderBottom: '1px solid color-mix(in srgb, var(--text) 5%, transparent)' }}>
                <td style={td}>{c.target}</td>
                <td style={{ ...td, color: c.busType === 'bus' ? 'var(--interactive)' : 'var(--status-caution)' }}>{c.busType === 'bus' ? 'Bus' : 'P2P'}</td>
                <td style={{ ...td, color: 'var(--text-2)' }}>{c.protocol}</td>
                <td style={{ ...td, fontFamily: 'monospace' }}>{c.dataRate}</td>
                <td style={{ ...td, fontFamily: 'monospace', color: 'var(--text-3)' }}>{c.address || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

const th: React.CSSProperties = { padding: '0.25rem 0.5rem', textAlign: 'left', fontSize: fs.label, color: 'var(--text-2)', textTransform: 'uppercase' }
const td: React.CSSProperties = { padding: '0.2rem 0.5rem' }
