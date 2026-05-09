/**
 * Phase and segment type definitions for the System-V frontend architecture.
 */

export type Phase = 0 | 1 | 2 | 3 | 4 | 5

export type Segment = 'space' | 'ground' | 'operations' | 'fleet'

export type Lens = 'mechanical' | 'electrical' | 'rf_comms' | 'thermal' | 'data' | 'mission' | 'software'

export const PHASE_LABELS: Record<Phase, string> = {
  0: 'Mission Need',
  1: 'Mission Architecture',
  2: 'System Architecture',
  3: 'Subsystem Design',
  4: 'Integration & Test',
  5: 'Verification & Ops',
}

export const PHASE_SHORT: Record<Phase, string> = {
  0: 'Need',
  1: 'Mission',
  2: 'System',
  3: 'Subsystem',
  4: 'I&T',
  5: 'V&V',
}

export const PHASE_COLORS: Record<Phase, string> = {
  0: '#8b5cf6',
  1: '#3b82f6',
  2: '#06b6d4',
  3: '#10b981',
  4: '#f59e0b',
  5: '#ef4444',
}

export const SEGMENT_LABELS: Record<Segment, string> = {
  space: 'Space Segment',
  ground: 'Ground Segment',
  operations: 'Operations',
  fleet: 'Fleet / Constellation',
}

export const LENS_LABELS: Record<Lens, { name: string; icon: string; color: string }> = {
  mechanical: { name: 'Mechanical', icon: '⚙', color: '#6b7280' },
  electrical: { name: 'Electrical', icon: '⚡', color: '#f59e0b' },
  rf_comms: { name: 'RF / Comms', icon: '📡', color: '#3b82f6' },
  thermal: { name: 'Thermal', icon: '🌡', color: '#ef4444' },
  data: { name: 'Data', icon: '💾', color: '#06b6d4' },
  mission: { name: 'Mission', icon: '🎯', color: '#8b5cf6' },
  software: { name: 'Software / Ops', icon: '💻', color: '#10b981' },
}
