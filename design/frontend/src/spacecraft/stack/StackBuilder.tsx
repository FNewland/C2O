/**
 * Stack and configuration (design rules §4): how the selected parts become a CubeSat.
 *
 * Auto-place proposes a layout from the rules (payload aperture and radiator nadir,
 * GNSS and UHF zenith, battery and EPS together near the CoG, ADCS near the centre,
 * radio next to its antenna, star tracker clear of the Earth limb) and a swap search
 * on CoG + harness + heat; anyone edits the proposal (drag, keyboard, lock); the
 * Structures & configuration seat approves it, which writes every unit's position into
 * the design (position_json) for mass properties, CDS-COG and the AOCS closure.
 *
 * Views: side elevation (drag to reorder), unfolded face map, and the shared 3D module
 * (shared/ui-viz/stack3d.js, stowed / deployed / exploded), which mission control can
 * show from the same geometry.yaml.
 */
import { useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import * as S3 from '../../viz/stack3d.js'
import { Button, Disclosure, Note, StatusBadge } from '../../components/ui'
import { useUIStore } from '../../stores/uiStore'
import { StackElevation } from './StackElevation'
import { StackFaces } from './StackFaces'
import {
  FACES, STATUS_TONE, StackError, unitsOf, moveColumnItem, moveFaceGroup, sortChecks, subColor, toggleLock,
  useGeometry, useStack, useStackActions, type Evaluated, type Face, type Placement, type Spec,
} from './stackApi'
import './stack.css'

type View = 'elevation' | 'faces' | '3d'

// i18n-keys
const MOUNT_KEY: Record<string, string> = {
  pc104_board: 'PC/104 board', pc104_module: 'PC/104 module', u_module: 'U module', face_panel: 'face panel',
  deployable: 'deployable', bracket: 'bracket', structure: 'structure', distributed: 'distributed',
}

export function StackBuilder() {
  const { t, i18n } = useTranslation()
  const lang = i18n.language?.startsWith('fr') ? 'fr' : 'en'
  const studyId = useUIStore(s => s.studyId)
  const q = useStack(studyId)
  const act = useStackActions(studyId)
  const data = q.data
  const [view, setView] = useState<View>('elevation')
  const [which, setWhich] = useState<'proposal' | 'approved'>('proposal')
  const [selected, setSelected] = useState<string | null>(null)
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [live, setLive] = useState('')

  const shown: 'proposal' | 'approved' | null = !data ? null
    : which === 'proposal' && data.proposal ? 'proposal' : data.approved ? 'approved' : data.proposal ? 'proposal' : null
  const real: Evaluated | null = shown ? (data as any)[shown] : null
  const env = data?.envelope
  const editable = !!real && !!env
  const geo = useGeometry(studyId, shown, data?.version ?? 0)

  const run = async (label: string, fn: () => Promise<unknown>) => {
    setBusy(label); setError(null)
    try { await fn() } catch (e) {
      const err = e as StackError
      setError(err.code === 'structures_only'
        ? t('Only {{seat}} or the instructor approves the stack layout.', { seat: data?.owner_label?.[lang] ?? t('Structures & config') })
        : err.code === 'version_conflict' ? t('Someone changed the layout meanwhile: it has been reloaded.') : err.message)
      if (err.code === 'version_conflict') void act.refresh()
    } finally { setBusy(null) }
  }
  const edit = (spec: Spec, say: string) => {
    if (!data) return
    void run('edit', async () => {
      const p = await act.propose(spec, data.version)
      setWhich('proposal')
      const s = p.proposal?.summary
      setLive(`${say} ${s ? t('Checks: {{p}} pass, {{w}} caution, {{f}} fail.', { p: s.pass, w: s.warn, f: s.fail }) : ''}`)
    })
  }
  const onMove = (pid: string, c: number, i: number) => {
    if (!real) return
    const name = real.placements.find(p => p.id === pid)?.name ?? pid
    edit(moveColumnItem(real.spec, pid, c, i), t('{{name}} moved to column {{c}}, slot {{s}}.', { name, c: c + 1, s: i + 1 }))
  }
  const onLock = (pid: string) => {
    if (!real) return
    const p = real.placements.find(x => x.id === pid)
    edit(toggleLock(real.spec, pid), p?.locked ? t('{{name}} unlocked.', { name: p?.name }) : t('{{name}} locked in place.', { name: p?.name ?? pid }))
  }
  const onMoveFace = (eid: string, from: Face, to: Face) => {
    if (!real) return
    const name = real.placements.find(p => p.element_id === eid)?.name ?? eid
    edit(moveFaceGroup(real.spec, eid, from, to), t('{{name}} moved to face {{f}}.', { name, f: faceName(to, t) }))
  }

  // 3D: mounted once per language; geometry fed on change
  const [host, setHost] = useState<HTMLDivElement | null>(null)
  const view3d = useRef<ReturnType<typeof S3.mount> | null>(null)
  const [webglOff, setWebglOff] = useState<string | null>(null)
  const tv = useMemo(() => (en: string, vars?: Record<string, unknown>) => t(en, vars as any) as string, [t])
  const cogBox = env ? env.cog_limits_mm.map(x => x / 1000) as [number, number, number] : undefined
  useEffect(() => {
    if (!host || view !== '3d') return
    view3d.current = S3.mount(host, { t: tv, geometry: geo.data ?? null, cogBox_m: cogBox, height: 460,
      onSelect: (id: string | null) => setSelected(id ? String(id).split('@')[0] : null), onFallback: (r: string) => setWebglOff(r),
      preserveDrawingBuffer: true })
    return () => { view3d.current?.destroy(); view3d.current = null }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [host, view, lang])
  useEffect(() => { view3d.current?.update(geo.data ?? null) }, [geo.data])
  useEffect(() => { view3d.current?.select(selected) }, [selected])

  if (!studyId) return null
  if (q.isLoading) return <p className="t-12 c-3">{t('Loading the stack layout…')}</p>
  if (!data) return q.error ? <Note tone="caution">{t('The stack layout could not be loaded: {{e}}', { e: String((q.error as Error).message) })}</Note> : null
  if (!data.applicable) {
    return <Note>{data.reason?.[lang] ?? t('Not a CubeSat form factor.')}</Note>
  }

  const sel: Placement[] = real ? real.placements.filter(p => p.element_id === selected) : []
  const unit = data.units.find(u => u.id === selected)
  const checks = real ? sortChecks(real.checks) : []
  const meta = real?.meta ?? {}
  const pending = !!data.proposal
  const fmtDate = (s?: string) => (s ? s.replace('T', ' ').slice(0, 16) : '')
  const originLabel = (o?: string) => (o === 'rule:STACK-AUTO' ? t('auto-placement (rule:STACK-AUTO)') : o === 'user' ? t('edited by hand') : o ?? '')

  return (
    <div className="c2o-stk">
      <div className="c2o-stk__bar">
        <div className="row gap-2 wrap ai-c">
          <Button variant="primary" busy={busy === 'auto'} onClick={() => run('auto', async () => { await act.autoPlace(); setWhich('proposal') })}
            disabledReason={data.units.length === 0 ? t('Add equipment from the knowledge base first') : null}>
            {data.proposal || data.approved ? t('Re-run auto-placement') : t('Auto-place')}
          </Button>
          {pending && (
            <Button busy={busy === 'approve'} onClick={() => run('approve', async () => { await act.approve(); setWhich('approved') })}
              disabledReason={data.can_approve ? null : t('Only {{seat}} or the instructor approves', { seat: data.owner_label[lang] })}>
              {t('Approve layout')}
            </Button>
          )}
          {pending && <Button variant="quiet" busy={busy === 'reject'} onClick={() => run('reject', act.reject)}>{t('Discard proposal')}</Button>}
          {data.approved && (
            <a className="c2o-btn c2o-btn--quiet" href={`/api/studies/${studyId}/stack/geometry?which=approved&format=yaml`} download>
              {t('Export geometry.yaml')}
            </a>
          )}
        </div>
        {data.proposal && data.approved && (
          <div className="c2o-seg" role="group" aria-label={t('Layout shown')}>
            <button type="button" className="c2o-seg__item" aria-pressed={shown === 'proposal'} onClick={() => setWhich('proposal')}>{t('Proposal')}</button>
            <button type="button" className="c2o-seg__item" aria-pressed={shown === 'approved'} onClick={() => setWhich('approved')}>{t('Approved')}</button>
          </div>
        )}
      </div>

      <p className="c2o-stk__status t-13 m-0" role="status">
        {!real && t('No layout yet. Auto-place proposes one from the rules; the {{seat}} seat approves it.', { seat: data.owner_label[lang] })}
        {real && shown === 'proposal' && (
          <>
            <StatusBadge status="caution">{t('Proposal')}</StatusBadge>{' '}
            {t('{{origin}} by {{who}}{{seat}}, {{at}}. Waiting for {{owner}} to approve; until then the approved layout stands.', {
              origin: originLabel(meta.origin), who: meta.by || t('someone'), seat: meta.seat ? ` (${meta.seat})` : '', at: fmtDate(meta.at),
              owner: data.owner_label[lang],
            })}
          </>
        )}
        {real && shown === 'approved' && (
          <>
            <StatusBadge status="ok">{t('Approved')}</StatusBadge>{' '}
            {t('Approved by {{who}}{{seat}}, {{at}}. Unit positions are written to the design (position_json, design frame).', {
              who: meta.approved_by || t('someone'), seat: meta.approved_seat ? ` (${meta.approved_seat})` : '', at: fmtDate(meta.approved_at),
            })}
          </>
        )}
      </p>
      {error && <Note tone="caution" role="alert" className="mt-2">{error}</Note>}
      {real?.notes?.length ? <Note className="mt-2">{real.notes.join(' ')}</Note> : null}
      <span className="sr-only" aria-live="polite">{live}</span>

      {real && env && (
        <div className="c2o-stk__grid">
          <div className="c2o-stk__main">
            <div className="row jc-sb wrap gap-2 mb-2">
              <div className="c2o-seg" role="group" aria-label={t('Stack view')}>
                {(['elevation', 'faces', '3d'] as View[]).map(v => (
                  <button key={v} type="button" className="c2o-seg__item" aria-pressed={view === v} onClick={() => setView(v)}>
                    {v === 'elevation' ? t('Side elevation') : v === 'faces' ? t('Face map') : t('3D')}
                  </button>
                ))}
              </div>
              <span className="t-12 c-3">{t('{{ff}} · envelope {{x}} × {{y}} × {{z}} mm ({{src}})', {
                ff: env.form_factor, x: env.size_mm[0].toFixed(1), y: env.size_mm[1].toFixed(1), z: env.size_mm[2].toFixed(1), src: env.sources.envelope })}</span>
            </div>
            {view === 'elevation' && (
              <StackElevation real={real} env={env} selected={selected} onSelect={setSelected} onMove={onMove} onToggleLock={onLock}
                readOnly={!editable || !!busy} announce={setLive} />
            )}
            {view === 'faces' && (
              <StackFaces real={real} env={env} selected={selected} onSelect={setSelected} onMoveFace={onMoveFace} readOnly={!editable || !!busy} />
            )}
            {view === '3d' && (
              <div>
                {webglOff && <Note>{t('3D view unavailable: {{reason}}.', { reason: t(webglOff) })}</Note>}
                <div ref={setHost} className="c2o-stk__3d" />
              </div>
            )}
            <p className="t-12 c-3 m-0 mt-2 measure">
              {t('Frame: the simulator body frame (+X velocity, +Y orbit normal, +Z zenith, −Z nadir), origin at the envelope centre. The positions written to the design use the SpaceCDF design frame: origin at the envelope corner, +Z nadir along the rails.')}
            </p>
          </div>

          <aside className="c2o-stk__side" aria-label={t('Stack checks and details')}>
            <h5 className="c2o-stk__h">{t('Checks')}</h5>
            <ul className="c2o-stk__checks">
              {checks.map(c => (
                <li key={c.id} className={`is-${c.status}`}>
                  <button type="button" className="c2o-stk__check" onClick={() => setSelected(c.element_ids?.[0] ?? selected)}
                    aria-label={`${c.label[lang]}: ${c.detail[lang]}`}>
                    <StatusBadge status={STATUS_TONE[c.status]}>{statusText(c.status, t)}</StatusBadge>
                    <span className="c2o-stk__cl">{c.label[lang]}</span>
                  </button>
                  <span className="c2o-stk__cd t-12 c-2">{c.detail[lang]}</span>
                  <span className="t-12 c-3">{c.standard_ref}</span>
                </li>
              ))}
            </ul>
            <dl className="c2o-stk__facts">
              <div><dt>{t('Mass placed')}</dt><dd className="mono">{real.mass_kg.toFixed(2)} kg</dd></div>
              <div><dt>{t('CoG from the centre (X, Y, Z)')}</dt><dd className="mono">{real.cog_mm.map(v => v.toFixed(1)).join(', ')} mm</dd></div>
              <div><dt>{t('CDS CoG box (±X, ±Y, ±Z)')}</dt><dd className="mono">{env.cog_limits_mm.map(v => v.toFixed(0)).join(', ')} mm</dd></div>
              {real.columns.map(c => (
                <div key={c.index}><dt>{t('Column {{n}} height', { n: c.index + 1 })}</dt>
                  <dd className="mono">{c.used_mm.toFixed(1)} / {c.length_mm.toFixed(1)} mm</dd></div>
              ))}
              <div><dt>{t('Placement score (lower is better)')}</dt>
                <dd className="mono">{Number(real.score?.total ?? 0).toFixed(3)}</dd></div>
              {real.meta?.report?.end && (
                <div><dt>{t('Auto-placement: rule order → swap search')}</dt>
                  <dd className="mono">{Number(real.meta.report.start.total).toFixed(3)} → {Number(real.meta.report.end.total).toFixed(3)}</dd></div>
              )}
            </dl>

            <h5 className="c2o-stk__h mt-3">{t('Selected unit')}</h5>
            {!sel.length && <p className="t-12 c-3 m-0">{t('Select a unit in a view or in a check to see where it is and why.')}</p>}
            {sel.length > 0 && (
              <div className="c2o-stk__sel">
                <p className="m-0"><span className="c2o-stk__sw" style={{ background: subColor(sel[0].subsystem) }} /> <b>{sel[0].name}</b>
                  <span className="t-12 c-3"> · {t(MOUNT_KEY[sel[0].mount_class] ?? sel[0].mount_class)}{unit?.manufacturer ? ` · ${unit.manufacturer}` : ''}</span></p>
                {sel.map(p => (
                  <div key={p.id} className="c2o-stk__selrow">
                    <span className="t-12">
                      {p.column !== null ? t('Column {{c}}, slot {{s}}, {{z0}} to {{z1}} mm from the nadir end', { c: p.column + 1, s: (p.slot ?? 0) + 1, z0: ((p.z_mm?.[0] ?? 0) + env.size_mm[2] / 2).toFixed(0), z1: ((p.z_mm?.[1] ?? 0) + env.size_mm[2] / 2).toFixed(0) })
                        : p.layer ? t('Full-width layer at the {{end}} end', { end: p.layer === 'nadir' ? t('nadir') : t('zenith') })
                          : p.face ? t('Face {{f}}, units: {{n}}', { f: faceName(p.face, t), n: unitsOf(p) })
                            : t('Distributed over the structure (at the centre)')}
                      {' · '}{p.mass_kg.toFixed(3)} kg{p.power_w ? ` · ${p.power_w.toFixed(1)} W` : ''}
                      {' · '}<span className="c-3">{p.origin === 'user' ? t('placed by hand') : t('placed by rule')}</span>
                    </span>
                    {p.face && p.tiles && (
                      <label className="t-12 row gap-1 ai-c">{t('Face')}
                        <select value={p.face} disabled={!!busy || p.locked}
                          onChange={e => onMoveFace(p.element_id, p.face as Face, e.target.value as Face)}>
                          {FACES.map(f => <option key={f} value={f}>{faceName(f, t)}</option>)}
                        </select>
                      </label>
                    )}
                    {(p.column !== null || p.tiles || p.layer) && (
                      <label className="t-12 row gap-1 ai-c">
                        <input type="checkbox" checked={p.locked} disabled={!!busy} onChange={() => onLock(p.id)} /> {t('Locked')}
                      </label>
                    )}
                  </div>
                ))}
                {(unit?.assumptions?.length ?? 0) > 0 && (
                  <ul className="c2o-stk__asm t-12 c-3">{unit!.assumptions.map(a => <li key={a}>{a}</li>)}</ul>
                )}
              </div>
            )}
            {real.assumptions.length > 0 && (
              <Disclosure summary={t('C2O defaults used ({{n}})', { n: real.assumptions.length })}>
                <ul className="c2o-stk__asm t-12 c-3">{real.assumptions.map(a => <li key={a}>{a}</li>)}</ul>
              </Disclosure>
            )}
          </aside>
        </div>
      )}
    </div>
  )
}

function statusText(s: string, t: (k: string) => string): string {
  return s === 'pass' ? t('Pass') : s === 'warn' ? t('Caution') : s === 'fail' ? t('Fail') : t('Not evaluated')
}

function faceName(f: string, t: (k: string) => string): string {
  return ({ px: '+X', mx: '−X', py: '+Y', my: '−Y', pz: t('+Z zenith'), mz: t('−Z nadir') } as Record<string, string>)[f] ?? f
}
