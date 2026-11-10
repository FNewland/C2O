/**
 * ThermalModelPanel — the thermal nodal model with its hot and cold cases (wave 3, 3.A6).
 *
 * Picture first: each node's calculated range in the hot and cold case against its limits, with
 * the uncertainty margin; then the margins (design, acceptance, qualification), the heater the
 * cold case asks for, the cases (β, eclipse, where they come from) and the couplings.
 *
 * Server: routers/thermal_model.py. Mounted in AitPanel.
 */
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import i18n from '../i18n'
import { Button, DataTable, Disclosure, Note, Panel, StatusBadge, fmtNum } from '../components/ui'

const API = '/api'

interface Margins { t_min_c?: number; t_max_c?: number; design?: number | null; acceptance?: number | null; qualification?: number | null; status?: string; uncertainty_c?: number }
interface TNode { id: string; code: string; name: string; op_min_c: number | null; op_max_c: number | null; heater_w: number | null; limits_source: string; data_json: { margins?: Margins; heater_needed_w?: number | null; name_fr?: string; external?: boolean } | null }
interface TCase { id: string; code: string; kind: string; beta_deg: number | null; eclipse_min: number | null; source: string; status: string }
interface Summary { solved: boolean; out_of_design_range: string[]; worst_design_margin_c: number | null; uncertainty_c: number | null; heaters: { node: string; needed_w: number | null; installed_w: number | null }[] }

export function ThermalModelPanel({ studyId }: { studyId: string | null }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const fr = i18n.language === 'fr'
  const [busy, setBusy] = useState(false)
  const { data } = useQuery<{ nodes: TNode[]; cases: TCase[]; couplings: unknown[]; summary: Summary }>({
    queryKey: ['thermal-model', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/thermal-model`).then(r => r.json()),
    enabled: !!studyId,
  })
  if (!studyId) return null
  const refresh = () => qc.invalidateQueries({ queryKey: ['thermal-model', studyId] })
  const post = async (path: string) => {
    setBusy(true)
    try { await fetch(`${API}/studies/${studyId}/thermal-model/${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' }) }
    finally { setBusy(false); refresh() }
  }
  const nodes = data?.nodes ?? []
  const s = data?.summary
  const lo = Math.min(-40, ...nodes.map(n => (n.data_json?.margins?.t_min_c ?? 0) - 15))
  const hi = Math.max(60, ...nodes.map(n => (n.data_json?.margins?.t_max_c ?? 0) + 15))
  const x = (v: number) => `${((v - lo) / (hi - lo)) * 100}%`
  const needHeaters = (s?.heaters ?? []).some(h => h.needed_w)
  return (
    <Panel level={2} title={t('Thermal model')}
      meta={t('Nodes, hot and cold cases, margins and heaters')}
      actions={<div className="row gap-2">
        <Button size="sm" onClick={() => post('propose')} busy={busy}>{nodes.length ? t('Add missing cases') : t('Build the model')}</Button>
        <Button size="sm" onClick={() => post('run')} busy={busy}>{t('Solve')}</Button>
        {needHeaters && <Button size="sm" onClick={() => post('heaters/accept')} busy={busy}>{t('Take the sized heaters')}</Button>}
      </div>}>
      {!nodes.length ? (
        <Note>{t('No thermal model yet. Build it from the product tree (one node per unit group, KB limits), then solve the hot and cold cases.')}</Note>
      ) : (
        <>
          {s?.solved && (
            <p className="t-13 m-0" data-testid="thermal-summary">
              <StatusBadge status={s.out_of_design_range.length ? 'alarm' : 'ok'}>
                {s.out_of_design_range.length ? t('{{n}} node(s) outside the design range', { n: s.out_of_design_range.length }) : t('every node inside its design range')}
              </StatusBadge>{' '}
              {t('Uncertainty margin {{u}} °C; worst design margin {{w}} °C.', { u: s.uncertainty_c ?? '—', w: s.worst_design_margin_c != null ? fmtNum(s.worst_design_margin_c, 1) : '—' })}
            </p>
          )}
          <div role="list" aria-label={t('Node temperatures against their limits')} className="stack gap-1 mt-2">
            {nodes.map(n => {
              const m = n.data_json?.margins
              return (
                <div key={n.id} role="listitem" className="row gap-2 t-12" title={n.limits_source}>
                  <span style={{ width: '16em' }} className="ellipsis">{n.code} · {(fr ? n.data_json?.name_fr : n.name) || n.name}</span>
                  <span style={{ position: 'relative', flex: 1, height: 12, background: 'var(--c2o-line, #8882)' }} aria-hidden="true">
                    {n.op_min_c != null && n.op_max_c != null && (
                      <span style={{ position: 'absolute', left: x(n.op_min_c), width: `calc(${x(n.op_max_c)} - ${x(n.op_min_c)})`, top: 0, bottom: 0, outline: '1px solid var(--ok, #4a7)' }} />
                    )}
                    {m?.t_min_c != null && m?.t_max_c != null && (
                      <span style={{ position: 'absolute', left: x(m.t_min_c), width: `calc(${x(m.t_max_c)} - ${x(m.t_min_c)})`, top: 3, bottom: 3, background: m.status === 'ok' ? 'var(--interactive, #48c)' : 'var(--alarm, #c44)' }} />
                    )}
                  </span>
                  <span className="mono" style={{ width: '9em' }}>{m?.t_min_c != null ? `${fmtNum(m.t_min_c, 0)}…${fmtNum(m.t_max_c ?? 0, 0)} °C` : '—'}</span>
                </div>
              )
            })}
          </div>
          <Disclosure summary={t('Margins and heaters')} meta={t('{{n}} nodes', { n: nodes.length })} ruled>
            <DataTable dense caption={t('Margins and heaters')} rows={nodes} rowKey={n => n.id} columns={[
              { key: 'n', header: t('Node'), render: n => `${n.code} · ${(fr ? n.data_json?.name_fr : n.name) || n.name}` },
              { key: 'l', header: t('Limits (°C)'), render: n => n.op_min_c != null ? `${n.op_min_c} … ${n.op_max_c}` : '—' },
              { key: 'd', header: t('Design'), num: true, render: n => fmtNum(n.data_json?.margins?.design ?? 0, 1), sort: n => n.data_json?.margins?.design ?? null },
              { key: 'a', header: t('Acceptance'), num: true, render: n => fmtNum(n.data_json?.margins?.acceptance ?? 0, 1) },
              { key: 'q', header: t('Qualification'), num: true, render: n => fmtNum(n.data_json?.margins?.qualification ?? 0, 1) },
              { key: 'h', header: t('Heater (W)'), num: true, render: n => n.data_json?.heater_needed_w ? `${t('needs')} ${fmtNum(n.data_json.heater_needed_w, 2)}` : (n.heater_w ? fmtNum(n.heater_w, 2) : '—') },
              { key: 's', header: t('Limit source'), render: n => <span className="t-12 c-2">{n.limits_source}</span> },
            ]} />
          </Disclosure>
          <Disclosure summary={t('Design cases')} meta={t('{{n}} cases', { n: data?.cases?.length ?? 0 })} ruled>
            <DataTable dense caption={t('Design cases')} rows={data?.cases ?? []} rowKey={c => c.id} columns={[
              { key: 'c', header: t('Case'), render: c => c.code },
              { key: 'b', header: 'β (°)', num: true, render: c => fmtNum(c.beta_deg ?? 0, 1) },
              { key: 'e', header: t('Eclipse (min)'), num: true, render: c => fmtNum(c.eclipse_min ?? 0, 1) },
              { key: 's', header: t('Source'), render: c => c.source === 'orbit_season' ? t('orbit season') : c.source === 'sso_geometry' ? t('sun-synchronous geometry') : c.source },
              { key: 'st', header: t('State'), render: c => c.status },
            ]} />
          </Disclosure>
        </>
      )}
    </Panel>
  )
}
