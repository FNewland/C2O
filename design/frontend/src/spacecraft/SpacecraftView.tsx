/**
 * SpacecraftView — the current design drawn with mission control's own
 * pictorial modules (shared/ui-viz): the subsystem synoptic, the power-flow
 * mimic for a power case, and the 3D spacecraft built from the design.
 * Picture first, the numbers that matter beside it, sources and assumptions
 * one click deeper; grey at rest, colour only where the design is short.
 *
 * Every value is a design value (verdict "design"): roll-ups of the element
 * tree, KB component data and the mission requirements. Nothing here is
 * telemetry, even where the shared views use operations wording.
 */
import { useEffect, useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import { useUIStore } from '../stores/uiStore'
import { Button, Disclosure, MarginBar, Note, StatusBadge } from '../components/ui'
import { displayElementName } from '../workbench/BlocksPanel'
import { useInterfaces, useProposalCheck } from '../workbench/interfaceApi'
import * as OV from '../viz/overview.js'
import * as PF from '../viz/powerflow.js'
import * as A3 from '../viz/attitude3d.js'
import {
  designAttitude, designGeometry, designOverview, designPower, descendants, formFactor, subsystemsOf, rollup,
  DOD_LIMIT_PCT, SYSTEM_MARGIN, type El, type PowerCase, type SubsystemFlags,
} from './designAdapter'
import './spacecraft.css'

const API = '/api'

/** i18next's t in the shape the viz modules call: t(englishKey, vars). */
function vizT(t: TFunction) {
  return (en: string, vars?: Record<string, unknown>) => t(en, vars as any) as string
}

/** Mount a framework-free view once; feed it on every model change; destroy on unmount. */
function useViz<V extends { update(m: unknown): void; destroy(): void }>(make: (el: HTMLElement) => V, model: unknown, deps: unknown[]) {
  // Callback ref: the host div appears only once the design has loaded.
  const [host, ref] = useState<HTMLDivElement | null>(null)
  const view = useRef<V | null>(null)
  const [mounted, setMounted] = useState(0)
  useEffect(() => {
    if (!host) return
    view.current = make(host)
    setMounted(m => m + 1)
    return () => { view.current?.destroy(); view.current = null }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [host, ...deps])
  useEffect(() => { if (model) view.current?.update(model) }, [model, mounted])
  return { ref, view, mounted }
}

function fmt(v: number | null | undefined, d = 1) { return v === null || v === undefined || !Number.isFinite(v) ? null : v.toFixed(d) }

export function SpacecraftView() {
  const { t, i18n } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const focusElementId = useUIStore(s => s.focusElementId)
  const breadcrumb = useUIStore(s => s.breadcrumb)
  const drillInto = useUIStore(s => s.drillInto)
  const drillUp = useUIStore(s => s.drillUp)
  const setActivePanel = useUIStore(s => s.setActivePanel)
  const [pc, setPc] = useState<PowerCase>('sunlit')

  const { data: elements = [] } = useQuery<El[]>({
    queryKey: ['elements', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/elements`).then(r => r.json()),
    enabled: !!studyId, structuralSharing: false, refetchInterval: 5000,
  })
  const { data: study } = useQuery<any>({
    queryKey: ['study', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}`).then(r => (r.ok ? r.json() : null)),
    enabled: !!studyId, staleTime: 30_000,
  })
  const { data: allocations = [] } = useQuery<any[]>({
    queryKey: ['allocations', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/allocations`).then(r => (r.ok ? r.json() : [])),
    enabled: !!studyId, staleTime: 10_000,
  })
  const { interfaces } = useInterfaces(studyId)

  // Which spacecraft: the system the user is in, else the first system in a space segment.
  const live = useMemo(() => elements.filter(e => !e.deleted_at), [elements])
  const systems = useMemo(() => live.filter(e => e.element_type === 'system'), [live])
  const sc = useMemo<El | null>(() => {
    const byId = new Map(live.map(e => [e.id, e]))
    let cur = focusElementId ? byId.get(focusElementId) : undefined
    while (cur) { if (cur.element_type === 'system') return cur; cur = cur.parent_id ? byId.get(cur.parent_id) : undefined }
    const under = focusElementId ? systems.find(s => s.parent_id === focusElementId) : undefined
    const space = systems.find(s => { const p = s.parent_id ? byId.get(s.parent_id) : undefined; return p && ((p as any).segment === 'space' || /space/i.test(p.name)) })
    return under ?? space ?? systems[0] ?? null
  }, [live, systems, focusElementId])

  const subs = useMemo(() => (sc ? subsystemsOf(live, sc.id) : []), [live, sc])
  const scIds = useMemo(() => new Set(sc ? [sc.id, ...descendants(live, sc.id).map(e => e.id)] : []), [live, sc])
  const totalMass = useMemo(() => (subs.length ? subs.reduce((a, s) => a + (rollup(s, 'mass_kg') ?? 0), 0) : null), [subs])
  // The phase-appropriate system margin (margin ladder step of the gate the study prepares for)
  const { data: ladder } = useQuery<{ gate: string | null; mass_percent: number }>({
    queryKey: ['margin-ladder', studyId],
    queryFn: () => fetch(`/api/studies/${studyId}/rules/margin-ladder`).then(r => (r.ok ? r.json() : null)),
    enabled: !!studyId, staleTime: 30_000,
  })
  const sysMargin = ladder?.mass_percent != null ? ladder.mass_percent / 100 : SYSTEM_MARGIN
  const marginPct = Math.round(sysMargin * 100)
  const marginGate = (ladder?.gate ?? '').toUpperCase()
  const ff = useMemo(() => formFactor(sc, totalMass, sysMargin), [sc, totalMass, sysMargin])
  const geometry = useMemo(() => designGeometry(live, sc, ff, study), [live, sc, ff, study])
  const power = useMemo(() => designPower(live, sc, study, pc), [live, sc, study, pc])

  // Link state per subsystem: conflicts and links still to review make a block "not yet nominal".
  const linkStamp = useMemo(() => interfaces.map(i => `${i.id}:${i.status}`).join(','), [interfaces])
  const check = useProposalCheck(studyId, 3, sc?.id ?? null, linkStamp)
  const flags = useMemo(() => {
    const f: Record<string, SubsystemFlags> = {}
    const owner = new Map<string, string>()
    for (const s of subs) { owner.set(s.el.id, s.el.id); for (const p of s.parts) owner.set(p.id, s.el.id) }
    const pending = new Map<string, number>()
    for (const i of interfaces) {
      if (i.status !== 'suggested') continue
      for (const end of [i.from_element_id, i.to_element_id]) { const o = owner.get(end); if (o) pending.set(o, (pending.get(o) ?? 0) + 1) }
    }
    for (const [id, nPending] of pending) f[id] = { state: 'nominal', note: t('{{count}} links to review', { count: nPending, defaultValue_one: '{{count}} link to review' }) }
    for (const c of check.data?.conflicts ?? []) {
      for (const end of c.element_ids) {
        const o = owner.get(end); if (!o) continue
        const prev = f[o]
        f[o] = { state: c.severity === 'alarm' || prev?.state === 'alarm' ? 'alarm' : 'caution', note: t('Interface conflict') }
      }
    }
    return f
  }, [subs, interfaces, check.data, t])

  const overview = useMemo(() => designOverview(live, sc, {
    t, allocations, flags, pc, groundStation: study?.requirements?.ground_stations?.[0] ?? null,
  }), [live, sc, allocations, flags, pc, study, t])
  const attitude = useMemo(() => designAttitude(pc), [pc])

  const tv = useMemo(() => vizT(t), [t])
  const lang = i18n.language
  const navigate = (ovId: string) => {
    const sub = (overview.subsystems as any)[ovId]
    const el = sub?.elementId ? live.find(e => e.id === sub.elementId) : null
    if (!el || !sc) return
    const at = breadcrumb.findIndex(b => b.id === sc.id)
    if (at >= 0) drillUp(at)
    else if (focusElementId !== sc.id) drillInto(sc.id, sc.name)
    drillInto(el.id, displayElementName(el.name, t))
    setActivePanel('blocks')
  }
  const navRef = useRef(navigate)
  navRef.current = navigate
  const groupToOv: Record<string, string> = { obdh: 'obdh', ttc: 'ttc', payload: 'payload', tcs: 'tcs', aocs: 'aocs', prop: 'prop' }

  const ov = useViz(el => OV.mount(el, { t: tv, onNavigate: id => navRef.current(id) }), overview, [lang])
  const pf = useViz(el => PF.mount(el, { t: tv, variant: 'full', onNavigate: id => navRef.current(groupToOv[id] ?? id) }), power.model, [lang])
  const [webglOff, setWebglOff] = useState<string | null>(null)
  const a3 = useViz(el => A3.mount(el, { t: tv, geometry, frame: 'lvlh', onFallback: r => setWebglOff(r) }), attitude, [lang])
  useEffect(() => { (a3.view.current as any)?.setGeometry?.(geometry) }, [geometry, a3.view, a3.mounted])

  // Links at the spacecraft's subsystem level
  const links = interfaces.filter(i => scIds.has(i.from_element_id) && scIds.has(i.to_element_id))
  const nSug = links.filter(i => i.status === 'suggested').length
  const nAcc = links.filter(i => i.status === 'accepted').length
  const nConf = (check.data?.conflicts ?? []).length

  if (!studyId) return null
  if (!sc) {
    return (
      <div className="c2o-pane">
        <p className="t-13 c-2 m-0 measure">{t('No spacecraft in this design yet. Add a system under the space segment, or use Quick Start on the space segment to create one with its subsystems.')}</p>
      </div>
    )
  }

  const a = power.assumptions
  const withMargin = totalMass === null ? null : totalMass * (1 + sysMargin)
  const avgW = power.model.cons.v as number
  const dodOver = a.dodPct !== null && a.dodPct > DOD_LIMIT_PCT
  const net = power.model.balance.netWh.v as number | null
  const ffText = ff.how === 'mass'
    ? t('{{u}}, the smallest CubeSat size whose typical maximum mass ({{max}} kg, CDS 14.1 Table 1) holds the design mass plus the {{pct}} % system margin', { u: ff.label, max: ff.maxKg, pct: marginPct })
    : ff.how === 'design' ? t('{{u}}, from the spacecraft element', { u: ff.label }) : t('{{u}} assumed: no mass in the design yet', { u: ff.label })

  return (
    <div className="c2o-pane c2o-scv">
      {/* Identity strip: the spacecraft and its headline numbers */}
      <header className="c2o-scv__head">
        <h3 className="c2o-scv__title">{displayElementName(sc.name, t)}</h3>
        <dl className="c2o-scv__kv">
          <div><dt>{t('Form factor')}</dt><dd className="mono">{ff.label}</dd></div>
          <div><dt>{t('Dry mass')}</dt><dd className="mono">{fmt(totalMass, 2) ?? t('no data')} <span className="u">kg</span></dd></div>
          <div><dt>{pc === 'peak' ? t('Peak power') : t('Average power')}</dt><dd className="mono">{fmt(avgW, 1)} <span className="u">W</span></dd></div>
          <div><dt>{t('Links')}</dt><dd>
            {nSug > 0
              ? <button type="button" className="c2o-scv__link" onClick={() => setActivePanel('interfaces')}>
                  {t('{{n}} accepted, {{s}} to review', { n: nAcc, s: nSug })}</button>
              : <span className="mono">{t('{{n}} accepted', { n: nAcc })}</span>}
          </dd></div>
        </dl>
        <span className="c2o-scv__src t-12 c-3">{t('Design values, not telemetry')}</span>
      </header>
      {systems.length > 1 && <p className="t-12 c-3 m-0 mb-2">{t('Showing {{name}}. Open another spacecraft in the breadcrumb to draw it instead.', { name: displayElementName(sc.name, t) })}</p>}

      {/* 1. Synoptic + budget beside it */}
      <section className="c2o-scv__row" aria-labelledby="scv-ov">
        <div className="c2o-scv__pic">
          <h4 id="scv-ov" className="c2o-scv__h">{t('Subsystems')}</h4>
          <div ref={ov.ref} />
        </div>
        <aside className="c2o-scv__side" aria-label={t('Spacecraft budget')}>
          <MarginBar lead label={t('Mass')} nominal={totalMass} withMargin={withMargin}
            allocation={ff.maxKg ?? undefined} unit="kg" digits={2} />
          <p className="t-12 c-3 m-0 mt-1 measure">{t('Bar: design mass, hatched: + {{pct}} % system margin (C2O default at {{gate}}), tick: CDS limit.', { pct: marginPct, gate: marginGate || '—' })} {ffText}.</p>
          {!ff.fits && <Note tone="caution" className="mt-2">{t('Over the largest standard CubeSat mass: check the deployer limit.')}</Note>}
          <MarginBar label={t('Power')}
            nominal={avgW} allocation={a.arrayW ?? undefined} unit="W" digits={1} cautionBelowPct={10} />
          <p className="t-12 c-3 m-0 measure">{pc === 'peak' ? t('Peak consumption against the end-of-life array power.') : t('Average consumption against the end-of-life array power.')}</p>
          <div className="c2o-scv__links">
            <span className="t-12 c-3">{t('Interfaces in this spacecraft')}</span>
            <span className="row gap-2 wrap">
              {nConf > 0 && <StatusBadge status="caution">{t('{{count}} conflicts', { count: nConf, defaultValue_one: '{{count}} conflict' })}</StatusBadge>}
              {nSug > 0
                ? <StatusBadge status="neutral">{t('{{count}} suggested links to review', { count: nSug })}</StatusBadge>
                : <StatusBadge status="ok">{t('All suggested links reviewed')}</StatusBadge>}
            </span>
            <Button size="sm" onClick={() => setActivePanel('interfaces')}>{t('Open Interfaces')}</Button>
          </div>
          <p className="t-12 c-3 m-0 measure">{t('Select a subsystem block to open it. A block turns amber when one of its interfaces conflicts; its last line counts the links still to review.')}</p>
        </aside>
      </section>

      {/* 2. Power flow for a case + the energy numbers beside it */}
      <section className="c2o-scv__row" aria-labelledby="scv-pf">
        <div className="c2o-scv__pic">
          <div className="row wrap jc-sb gap-2">
            <h4 id="scv-pf" className="c2o-scv__h">{t('Power')}</h4>
            <div className="c2o-seg" role="group" aria-label={t('Power case')}>
              {(['sunlit', 'eclipse', 'peak'] as PowerCase[]).map(k => (
                <button key={k} type="button" className="c2o-seg__item" aria-pressed={pc === k} onClick={() => setPc(k)}>
                  {k === 'sunlit' ? t('Sunlit') : k === 'eclipse' ? t('Eclipse') : t('Peak')}
                </button>
              ))}
            </div>
          </div>
          <div ref={pf.ref} />
        </div>
        <aside className="c2o-scv__side" aria-label={t('Energy per orbit')}>
          <dl className="c2o-scv__facts">
            <div><dt>{t('Orbit')}</dt><dd className="mono">{fmt(a.altKm, 0)} <span className="u">km</span> · {fmt(a.periodS / 60, 1)} <span className="u">min</span></dd></div>
            <div><dt>{t('Longest eclipse')}</dt><dd className="mono">{fmt(a.eclipseS / 60, 1)} <span className="u">min</span></dd></div>
            <div><dt>{t('Array, end of life')}</dt><dd className="mono">{a.arrayW === null ? <span className="c2o-nodata">{t('no array in the design')}</span> : <>{fmt(a.arrayW, 1)} <span className="u">W</span></>}</dd></div>
            <div><dt>{t('Battery')}</dt><dd className="mono">{a.capWh === null ? <span className="c2o-nodata">{t('no battery in the design')}</span> : <>{fmt(a.capWh, 0)} <span className="u">Wh</span></>}</dd></div>
            <div className={net !== null && net < 0 ? 'is-caution' : ''}><dt>{t('Net energy per orbit')}</dt>
              <dd className="mono">{net === null ? <span className="c2o-nodata">{t('no data')}</span> : <>{net > 0 ? '+' : ''}{fmt(net, 1)} <span className="u">Wh</span></>}</dd></div>
            <div className={dodOver ? 'is-caution' : ''}><dt>{t('Depth of discharge in eclipse')}</dt>
              <dd className="mono">{a.dodPct === null ? <span className="c2o-nodata">{t('no data')}</span> : <>{fmt(a.dodPct, 1)} <span className="u">%</span></>}
                <span className="c-3 t-12"> / {DOD_LIMIT_PCT} %</span></dd></div>
          </dl>
          {net !== null && net < 0 && <Note tone="caution">{t('The arrays do not refill the battery over an orbit at average consumption. Add array area or reduce load.')}</Note>}
          {dodOver && <Note tone="caution" className="mt-2">{t('Eclipse depth of discharge is over the {{l}} % default limit.', { l: DOD_LIMIT_PCT })}</Note>}
        </aside>
      </section>

      {/* 3. The spacecraft built from the design */}
      <section className="c2o-scv__row c2o-scv__row--one" aria-labelledby="scv-3d">
        <div className="c2o-scv__pic">
          <h4 id="scv-3d" className="c2o-scv__h">{t('Spacecraft in nominal nadir pointing')}</h4>
          {webglOff && <Note>{t('3D view unavailable: {{reason}}.', { reason: t(webglOff) })}</Note>}
          <div ref={a3.ref} className="c2o-scv__a3" />
          <p className="t-12 c-3 m-0 mt-1 measure">{t('Built from the design: {{ff}} bus, solar cells, star trackers, antennas and the payload boresight from the equipment list. The attitude is the nominal one, not a simulation.', { ff: ff.label })}</p>
        </div>
      </section>

      <Disclosure ruled summary={t('Assumptions and sources')}>
        <table className="c2o-scv__tab">
          <caption className="sr-only">{t('Assumptions and sources')}</caption>
          <thead><tr><th scope="col">{t('Quantity')}</th><th scope="col" className="ta-r">{t('Value')}</th><th scope="col">{t('Source')}</th></tr></thead>
          <tbody>
            <tr><th scope="row">{t('Form factor')}</th><td className="mono ta-r">{ff.label}</td><td>{ff.how === 'mass' ? t('CubeSat Design Specification rev 14.1, 2.2.10 Table 1, with the {{pct}} % system margin of the C2O default margin ladder', { pct: marginPct }) : t('Spacecraft element')}</td></tr>
            <tr><th scope="row">{t('Orbit altitude')}</th><td className="mono ta-r">{fmt(a.altKm, 0)} km</td><td>{t('Mission requirements')}</td></tr>
            <tr><th scope="row">{t('Eclipse duration')}</th><td className="mono ta-r">{fmt(a.eclipseS / 60, 1)} min</td><td>{t('Cylindrical shadow at β = 0°, the longest eclipse')}</td></tr>
            <tr><th scope="row">{t('Array power')}</th><td className="mono ta-r">{fmt(a.arrayW, 1) ?? '0'} W</td><td>{a.arrayHow ? t('End-of-life power of {{parts}}, arrays facing the Sun', { parts: a.arrayHow }) : t('No solar array in the equipment list')}</td></tr>
            <tr><th scope="row">{t('Consumption')}</th><td className="mono ta-r">{fmt(avgW, 1)} W</td><td>{pc === 'peak' ? t('Sum of equipment peak power') : t('Sum of equipment average power')}</td></tr>
            <tr><th scope="row">{t('Depth-of-discharge limit')}</th><td className="mono ta-r">{DOD_LIMIT_PCT} %</td><td>{t('C2O default for LEO lithium-ion, not a standard value')}</td></tr>
            <tr><th scope="row">{t('Payload field of view')}</th><td className="mono ta-r">{geometry.payload ? `${fmt(geometry.payload.fov_deg, 1)}°` : t('no payload')}</td><td>{geometry.provenance.find(p => p.startsWith('payload')) ? t('Mission requirements, or the C2O default 10°') : ''}</td></tr>
            <tr><th scope="row">{t('Star-tracker Earth-limb exclusion')}</th><td className="mono ta-r">{geometry.star_tracker_earth_exclusion_deg}°</td><td>{t('C2O default, a display limit')}</td></tr>
          </tbody>
        </table>
      </Disclosure>
    </div>
  )
}
