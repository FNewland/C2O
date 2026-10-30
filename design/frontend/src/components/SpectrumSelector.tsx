/**
 * SpectrumSelector — Interactive frequency band selection as a design constraint.
 *
 * Shows available bands filtered by license type and mission type.
 * Selection constrains equipment browser (transponders/antennas).
 */
import { useState, useEffect } from 'react'
import { useDesignStore } from '../stores/designStore'
import { useApplyToDesign } from '../hooks/useApplyToDesign'

interface FreqBand {
  name: string; band: string; freq_min_mhz: number; freq_max_mhz: number
  direction: string; service: string; typical_data_rate: string; notes: string
  requires_itu_filing: boolean; suitable_for_data_rate: boolean; license_types: string[]
}

const LICENSE_OPTIONS = [
  { id: 'amateur', label: 'Amateur (IARU)', description: 'Free, no encryption, open data, non-commercial' },
  { id: 'experimental', label: 'Experimental', description: 'R&D, time-limited, no revenue' },
  { id: 'commercial', label: 'Commercial', description: 'Full ITU filing, national license, revenue OK' },
]

export function SpectrumSelector() {
  const missionType = useDesignStore(s => s.requirements.mission_type)
  const [licenseType, setLicenseType] = useState('commercial')
  const [bands, setBands] = useState<FreqBand[]>([])
  const [selectedBand, setSelectedBand] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const markStale = useDesignStore(s => s.markStale)

  const dataRate = useDesignStore(s => s.requirements.payloads?.[0]?.data_rate_mbps || 10)

  useEffect(() => {
    setLoading(true)
    fetch(`/api/lifecycle/spectrum/bands?mission_type=${missionType}&license_type=${licenseType}&data_rate_mbps=${dataRate}`)
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data?.bands) setBands(data.bands) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [missionType, licenseType, dataRate])

  const setParam = useDesignStore(s => s.setParameter)
  const setRfBand = useDesignStore(s => (s as any).setRfBand)
  const handleSelectBand = (bandName: string) => {
    setSelectedBand(bandName)
    // Store in designStore so EquipmentBrowser can filter
    useDesignStore.setState({ selectedRfBand: bandName, selectedLicenseType: licenseType })
    // Immediately write frequency constraints to design store
    const bandInfo = bands.find(b => b.band === bandName)
    if (bandInfo) {
      setParam('spectrum.band', bandName, 'spectrum-selector')
      setParam('spectrum.freq_min_mhz', bandInfo.freq_min_mhz, 'spectrum-selector')
      setParam('spectrum.freq_max_mhz', bandInfo.freq_max_mhz, 'spectrum-selector')
      setParam('spectrum.license_type', licenseType, 'spectrum-selector')
    }
    markStale('spectrum')
  }

  const [applied, setApplied] = useState(false)

  const selectedBandInfo = bands.find(b => b.band === selectedBand)
  const apply = useApplyToDesign({
    events: selectedBandInfo ? [
      { kind: 'spectrum_band_selection' as any, target_id: 'spectrum.band', new_value: selectedBandInfo.band },
      { kind: 'parameter_override', target_id: 'spectrum.freq_min_mhz', new_value: selectedBandInfo.freq_min_mhz },
      { kind: 'parameter_override', target_id: 'spectrum.freq_max_mhz', new_value: selectedBandInfo.freq_max_mhz },
      { kind: 'parameter_override', target_id: 'spectrum.license_type', new_value: licenseType },
    ] : [],
    correlation_id: 'spectrum-selector',
    rationale: selectedBandInfo ? `Selected ${selectedBandInfo.band} band (${selectedBandInfo.name})` : 'No band selected',
  })

  const BAND_COLORS: Record<string, string> = {
    VHF: '#10b981', UHF: '#3b82f6', S: '#f59e0b', X: '#ec4899', Ka: '#8b5cf6', L: '#f97316',
  }

  return (
    <div className="card">
      <h3 style={{ fontSize: '0.9rem', marginBottom: '0.3rem' }}>Frequency & Licensing</h3>
      <p style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.5rem' }}>
        License type constrains which frequency bands and equipment are available.
      </p>

      {/* License type selector */}
      <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.5rem' }}>
        {LICENSE_OPTIONS.map(opt => (
          <button key={opt.id} onClick={() => { setLicenseType(opt.id); setParam('spectrum.license_type', opt.id, 'spectrum-selector') }}
            title={opt.description}
            style={{
              padding: '0.25rem 0.6rem', fontSize: '0.72rem', borderRadius: '4px', cursor: 'pointer',
              background: licenseType === opt.id ? '#3b82f6' : 'var(--bg-primary, #0a0e1a)',
              color: licenseType === opt.id ? 'white' : '#9ca3af',
              border: `1px solid ${licenseType === opt.id ? '#3b82f6' : '#374151'}`,
            }}>{opt.label}</button>
        ))}
      </div>

      {/* Available bands */}
      {loading ? (
        <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Loading bands...</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          {bands.map(b => (
            <div key={b.name} onClick={() => handleSelectBand(b.band)}
              style={{
                display: 'flex', alignItems: 'center', gap: '0.5rem',
                padding: '0.35rem 0.5rem', borderRadius: '4px', cursor: 'pointer',
                background: selectedBand === b.band ? `${BAND_COLORS[b.band] || '#3b82f6'}15` : 'transparent',
                border: `1px solid ${selectedBand === b.band ? BAND_COLORS[b.band] || '#3b82f6' : '#37415180'}`,
                opacity: b.suitable_for_data_rate ? 1 : 0.5,
              }}>
              <span style={{
                width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                background: BAND_COLORS[b.band] || '#6b7280',
              }} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: '0.78rem', fontWeight: 500 }}>{b.name}</div>
                <div style={{ fontSize: '0.65rem', color: '#6b7280' }}>
                  {b.freq_min_mhz}–{b.freq_max_mhz} MHz · {b.direction} · {b.typical_data_rate}
                </div>
              </div>
              {b.requires_itu_filing && (
                <span style={{ fontSize: '0.6rem', color: '#f59e0b', whiteSpace: 'nowrap' }}>ITU filing</span>
              )}
              {!b.suitable_for_data_rate && (
                <span style={{ fontSize: '0.6rem', color: '#ef4444', whiteSpace: 'nowrap' }}>too slow</span>
              )}
              {selectedBand === b.band && (
                <span style={{ fontSize: '0.65rem', color: '#10b981', fontWeight: 600 }}>Selected</span>
              )}
            </div>
          ))}
          {bands.length === 0 && (
            <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>No bands available for this configuration.</div>
          )}
        </div>
      )}

      <button className="btn" onClick={async () => { await apply(); setApplied(true); setTimeout(() => setApplied(false), 2000) }}
        style={{ marginTop: '0.5rem', width: '100%', background: applied ? '#10b981' : '#3b82f6', fontSize: '0.78rem' }}>
        {applied ? 'Applied — reconverging...' : 'Apply to Design'}
      </button>
    </div>
  )
}
