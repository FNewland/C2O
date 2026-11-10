/**
 * CostModel — the priced cost model at MDR/PRR (wave 3, 3.A7): labour per work package, test
 * campaigns, hardware, other, a management reserve and the launch (zero when provided), against the
 * study's cost target. "Price" proposes the lines from the WBS, the AIT test matrix and the
 * reference class (configs/cost_pricing.yaml); a line the team edits is kept by the next price.
 *
 * Server: routers/schedule.py (GET/POST /studies/{id}/cost/items, PATCH/DELETE …/{item},
 * POST …/cost/price). Mounted in ProjectPanel.
 */
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import i18n from '../i18n'
import { Button, DataTable, Disclosure, Note, StatusBadge, askText, fmtNum } from '../components/ui'

const API = '/api'

interface CostItem {
  id: string; category: string; name: string; name_fr: string; wbs_code: string; quantity: number | null; unit: string
  unit_cost_keur: number | null; percent_of_base: number | null; total_keur: number | null; source: string; basis: string; origin: string
}
interface CostSummary {
  items: CostItem[]; by_category: Record<string, number>; total_keur: number | null; total_meur: number | null
  target_meur: number | null; within_target: boolean | null; labour_person_months: number; priced: boolean
  reference_class: { en?: string; fr?: string }
}

// English text is the i18n key
const CATEGORY: Record<string, string> = {
  labour: 'Labour', test_campaign: 'Test campaigns', hardware: 'Hardware', software: 'Software', facilities: 'Facilities',
  launch: 'Launch', operations: 'Operations', reserve: 'Reserve', other: 'Other',
}

export function CostModel({ studyId }: { studyId: string | null }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const fr = i18n.language === 'fr'
  const [busy, setBusy] = useState(false)
  const { data } = useQuery<CostSummary>({
    queryKey: ['cost-items', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/cost/items`).then(r => r.json()),
    enabled: !!studyId,
  })
  if (!studyId) return null
  const refresh = () => qc.invalidateQueries({ queryKey: ['cost-items', studyId] })
  const price = async () => {
    setBusy(true)
    try { await fetch(`${API}/studies/${studyId}/cost/price`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' }) }
    finally { setBusy(false); refresh() }
  }
  const editTotal = async (it: CostItem) => {
    const v = await askText(t('New amount (kEUR)'), it.total_keur != null ? String(it.total_keur) : '')
    if (v == null || Number.isNaN(Number(v.replace(',', '.')))) return
    await fetch(`${API}/studies/${studyId}/cost/items/${it.id}`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ total_keur: Number(v.replace(',', '.')) }),
    })
    refresh()
  }
  const items = data?.items ?? []
  return (
    <section aria-label={t('Priced cost model')} className="mb-4 stack gap-2">
      <div className="row wrap gap-2">
        <h3 className="t-13 w-600 m-0">{t('Priced cost model')}</h3>
        <span className="grow" />
        <Button size="sm" onClick={price} busy={busy}
          title={t('Labour per work package, external test campaigns, spares, support equipment, fees and a management reserve; the launch is zero when provided')}>
          {data?.priced ? t('Price again') : t('Price the cost model')}
        </Button>
      </div>
      {!data?.priced ? (
        <Note>{t('The cost above is the selected hardware only. Price the model (labour, test campaigns, reserve) before judging the cost against the target at MDR and PRR.')}</Note>
      ) : (
        <>
          <dl className="c2o-stats">
            {Object.entries(data.by_category).map(([k, v]) => (
              <div key={k}><dt>{t(CATEGORY[k] ?? k)}</dt><dd>{fmtNum(v, 1)} kEUR</dd></div>
            ))}
            <div><dt>{t('Total')}</dt><dd>{fmtNum(data.total_keur ?? 0, 1)} kEUR</dd></div>
          </dl>
          <p className="t-12 c-2 m-0" data-testid="cost-target">
            {data.target_meur != null
              ? t('Total {{total}} MEUR against the {{target}} MEUR target', { total: fmtNum(data.total_meur ?? 0, 3), target: fmtNum(data.target_meur, 2) })
              : t('No cost target in the mission definition')}{' '}
            {data.within_target != null && (
              <StatusBadge status={data.within_target ? 'ok' : 'alarm'}>{data.within_target ? t('within target') : t('over target')}</StatusBadge>
            )}{' '}
            {t('{{pm}} person-months of labour', { pm: fmtNum(data.labour_person_months, 0) })}
          </p>
          <p className="t-12 c-3 m-0">{t('Reference class')}: {(fr ? data.reference_class.fr : data.reference_class.en) ?? ''}</p>
          <Disclosure summary={t('Cost lines')} meta={t('{{n}} lines', { n: items.length })} ruled>
            <DataTable dense caption={t('Cost lines')} rows={items} rowKey={i => i.id} columns={[
              { key: 'c', header: t('Category'), render: i => t(CATEGORY[i.category] ?? i.category), sort: i => i.category },
              { key: 'n', header: t('Line'), render: i => (fr ? i.name_fr : i.name) || i.name },
              { key: 'q', header: t('Quantity'), num: true, render: i => i.quantity != null ? `${fmtNum(i.quantity, 2)} ${i.unit}` : '—' },
              { key: 't', header: 'kEUR', num: true, render: i => fmtNum(i.total_keur ?? 0, 1), sort: i => i.total_keur },
              { key: 'b', header: t('Basis'), render: i => <span className="t-12 c-2">{i.basis || i.source}</span> },
              { key: 'e', header: '', render: i => <Button size="sm" variant="quiet" onClick={() => editTotal(i)}>{t('Edit')}</Button> },
            ]} />
          </Disclosure>
        </>
      )}
    </section>
  )
}
