/**
 * OpsPanel — the Operations tab of the CDR model (ECSS-E-ST-70C): console positions with the
 * PUS services and S8 functions each may send (and the design seat behind each position), the
 * GO/NO-GO matrix and the flight rules. A light table: the flight operations plan itself is
 * checked by the review board. Owned by Mission analysis & ops.
 */
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Button, DataTable, Field, Input, Tag, Textarea, type Column } from '../components/ui'
import { createCdr, type CdrRow, type CdrView } from './cdrApi'
import { CdrFrame, CheckCell, OwnerTag, RowState, Section } from './cdrParts'
import { bil, rowClass, useCdrPanel, type CdrPanelCtx } from './cdrUtil'
import { PassPlan } from './PassPlan'

export function OpsPanel() {
  const { t } = useTranslation()
  const ctx = useCdrPanel()
  return (
    <CdrFrame ctx={ctx} group="ops" testId="ops-panel" title={t('Operations organisation')}
      owners={t('Owned by Mission analysis & ops.')}>
      {view => (
        <>
          <PassPlan ctx={ctx} view={view} />
          <Positions ctx={ctx} view={view} />
          <GoNoGo ctx={ctx} view={view} />
          <Rules ctx={ctx} view={view} />
        </>
      )}
    </CdrFrame>
  )
}

function Positions({ ctx, view }: { ctx: CdrPanelCtx; view: CdrView }) {
  const { t, i18n } = useTranslation()
  const cols: Column<CdrRow>[] = [
    { key: 'id', header: t('Position'), render: r => (
      <span className="stack gap-0"><span className="w-500">{bil(r.data.label, i18n.language)}</span><span className="mono t-12 c-3">{r.data.id}</span></span>) },
    { key: 'sub', header: t('Subsystems'), render: r => <span className="c2o-cdr__chips">{(r.data.subsystems ?? []).map((s: string) => <Tag key={s}>{s}</Tag>)}</span> },
    { key: 'svc', header: t('Services'), render: r => <span className="mono t-12">{(r.data.allowed_services ?? []).join(', ')}</span> },
    { key: 'fn', header: t('Functions'), render: r => (r.data.all_commands ? <Tag accent>{t('all')}</Tag>
      : <span className="mono t-12" title={(r.data.allowed_func_ids ?? []).join(', ')}>{t('{{n}} functions', { n: (r.data.allowed_func_ids ?? []).length })}</span>) },
    { key: 'seat', header: t('Design seat'), render: r => (r.data.design_seat ? <OwnerTag seat={r.data.design_seat} /> : <span className="c-3">–</span>) },
    { key: 'st', header: t('Status'), render: r => <RowState ctx={ctx} kind="positions" row={r} label={r.data.id} /> },
  ]
  return (
    <Section id="ops-pos" title={t('Console positions')}
      note={t('One position per subsystem group, each sending only its own functions; the Flight Director may send all. {{src}}', { src: view.refs.ops?.standard_ref ?? '' })}>
      <DataTable dense rows={view.rows.positions} rowKey={r => r.id} columns={cols} caption={t('Console positions')} rowClassName={rowClass}
        empty={t('No position yet.')} />
    </Section>
  )
}

function GoNoGo({ ctx, view }: { ctx: CdrPanelCtx; view: CdrView }) {
  const { t, i18n } = useTranslation()
  const cols: Column<CdrRow>[] = [
    { key: 's', header: t('Situation'), render: r => <span className="w-500">{bil(r.data.situation, i18n.language)}</span> },
    { key: 'c', header: t('Who calls'), render: r => <span className="mono t-12">{r.data.who_calls}</span> },
    { key: 'r', header: t('Who responds'), render: r => <span className="mono t-12">{(r.data.who_responds ?? []).join(', ')}</span> },
    { key: 'd', header: t('Decision'), render: r => bil(r.data.decision, i18n.language) },
    { key: 'f', header: t('Telecommands'), render: r => <span className="c2o-cdr__chips">{(r.data.functions ?? []).map((f: string) => <Tag key={f} mono>{f}</Tag>)}</span> },
    { key: 'k', header: t('Critical'), center: true, render: r => <CheckCell ctx={ctx} kind="gonogo" row={r} field="critical" label={t('Critical situation')} /> },
    { key: 'st', header: t('Status'), render: r => <RowState ctx={ctx} kind="gonogo" row={r} label={bil(r.data.situation, i18n.language)} /> },
  ]
  return (
    <Section id="ops-gng" title={t('GO/NO-GO matrix')} note={t('Every critical telecommand needs a GO/NO-GO situation or a flight rule.')}>
      <DataTable dense rows={view.rows.gonogo} rowKey={r => r.id} columns={cols} caption={t('GO/NO-GO matrix')} rowClassName={rowClass}
        empty={t('No GO/NO-GO situation yet.')} />
    </Section>
  )
}

function Rules({ ctx, view }: { ctx: CdrPanelCtx; view: CdrView }) {
  const { t, i18n } = useTranslation()
  const [id, setId] = useState('')
  const [text, setText] = useState('')
  const ref = view.dataset === 'reference'
  const cols: Column<CdrRow>[] = [
    { key: 'id', header: t('Rule'), sort: r => r.data.rule_id, render: r => <span className="mono w-500">{r.data.rule_id}</span> },
    { key: 't', header: t('Flight rule'), render: r => bil(r.data.text, i18n.language) },
    { key: 'r', header: t('Refers to'), render: r => (r.data.ref ? <span className="mono t-12">{r.data.ref}</span> : <span className="c-3">–</span>) },
    { key: 'st', header: t('Status'), render: r => <RowState ctx={ctx} kind="flight_rules" row={r} label={r.data.rule_id} /> },
  ]
  const add = () => ctx.run('add-rule', async () => {
    await createCdr(ctx.studyId!, 'flight_rules', { rule_id: id.trim(), text: { en: text.trim(), fr: text.trim() } })
    setId(''); setText('')
  })
  return (
    <Section id="ops-fr" title={t('Flight rules')}>
      <DataTable dense rows={view.rows.flight_rules} rowKey={r => r.id} columns={cols} caption={t('Flight rules')} rowClassName={rowClass}
        defaultSort={{ key: 'id', dir: 'asc' }} empty={ref ? t('The simulator has no flight-rule file; its rules live in the manual and procedures.') : t('No flight rule yet.')} />
      {!ref && (
        <form className="c2o-blocks__add mt-2" aria-label={t('Add a flight rule')} onSubmit={e => { e.preventDefault(); if (id.trim() && text.trim()) add() }}>
          <Field label={t('Rule id')}><Input dense value={id} onChange={e => setId(e.target.value)} placeholder="FR-07" /></Field>
          <Field label={t('Rule')}><Textarea rows={2} value={text} onChange={e => setText(e.target.value)} /></Field>
          <Button type="submit" size="sm" variant="primary" busy={ctx.busy === 'add-rule'}
            disabledReason={!id.trim() || !text.trim() ? t('Give the rule an id and a text') : undefined}>{t('Add rule')}</Button>
        </form>
      )}
    </Section>
  )
}
