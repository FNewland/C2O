/**
 * InterfacesPanel — the links between the elements at this level.
 *
 * Three groups, in the order a designer works through them:
 *   1. Suggested: links the rule engine expects (C2O default interface
 *      matrix + component data). They already count in budgets and analyses;
 *      the designer accepts, edits or rejects each one, or accepts a whole
 *      type at once. Each row carries the rule's one-sentence rationale and
 *      its reference.
 *   2. Defined: accepted links (rule-made or the designer's own), with the
 *      reference-data fields one click deeper.
 *   3. Rejected: excluded from analyses and never re-proposed for that pair
 *      and type, until restored here.
 * Unmet needs and conflicts from a dry-run proposal sit above the lists.
 */
import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { RecordDecision } from '../logbook'
import { useTranslation } from 'react-i18next'
import { useUIStore } from '../stores/uiStore'
import { ArmButton, Button, Chevron, Disclosure, Field, Input, Note, Panel, Select, StatusBadge } from '../components/ui'
import {
  INTERFACE_TYPES, TYPE_META, pickLang,
  type DesignInterface, type InterfaceType,
} from '../types/interfaces'
import { displayElementName } from './BlocksPanel'
import { InterfaceGlyph } from './InterfaceGlyph'
import {
  createInterface, deleteInterface, patchInterface, proposeLinks, useInterfaces, useInvalidateLinks,
  useProposalCheck, type InterfacePatch, type ProposeResult,
} from './interfaceApi'
import { LinkEditor, LinkStatusChip, TypeLabel, linkDecision, originText, propsSummary, type EndpointOption } from './linkParts'
import { InterfaceIrLinks } from './irParts'

const API = '/api'

export function InterfacesPanel() {
  const { t, i18n } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const focusElementId = useUIStore(s => s.focusElementId)
  const currentLevel = useUIStore(s => s.currentLevel)
  const invalidate = useInvalidateLinks(studyId)

  const { data: allElements = [] } = useQuery<any[]>({
    queryKey: ['elements', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/elements`).then(r => r.json()),
    enabled: !!studyId, structuralSharing: false, refetchInterval: 3000,
  })
  const { interfaces: allInterfaces } = useInterfaces(studyId)

  const siblings = useMemo(() => allElements.filter((el: any) =>
    (focusElementId ? el.parent_id === focusElementId : !el.parent_id) && !el.deleted_at), [allElements, focusElementId])
  const siblingIds = useMemo(() => new Set(siblings.map((s: any) => s.id)), [siblings])
  const endpoints: EndpointOption[] = useMemo(() => siblings.map((el: any) => ({ id: el.id, name: displayElementName(el.name, t) })), [siblings, t])
  const nameOf = (id: string) => {
    const el = allElements.find((e: any) => e.id === id)
    return el ? displayElementName(el.name, t) : t('(outside this level)')
  }

  const here = useMemo(() => allInterfaces.filter(i => siblingIds.has(i.from_element_id) && siblingIds.has(i.to_element_id)), [allInterfaces, siblingIds])
  const suggested = here.filter(i => i.status === 'suggested')
  const accepted = here.filter(i => i.status === 'accepted')
  const rejected = here.filter(i => i.status === 'rejected')

  // Dry-run proposal: unmet needs and conflicts for this level (re-run when the link set changes).
  const stamp = useMemo(() => here.map(i => `${i.id}:${i.status}:${i.version ?? ''}`).sort().join(',') + `|${siblings.length}`, [here, siblings.length])
  const check = useProposalCheck(studyId, currentLevel, focusElementId, stamp)
  const proposerMissing = check.data === null
  const proposal = check.data as ProposeResult | null | undefined
  const unmet = (proposal?.unmet ?? []).filter(u => siblingIds.has(u.element_id))
  const conflicts = (proposal?.conflicts ?? []).filter(c => c.element_ids.some(id => siblingIds.has(id)))

  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [lastRun, setLastRun] = useState<string | null>(null)
  const run = async (key: string, fn: () => Promise<unknown>) => {
    setBusy(key); setError(null)
    try { await fn(); invalidate() } catch (e) { setError(String((e as Error).message || e)) } finally { setBusy(null) }
  }
  const setStatus = (i: DesignInterface, status: DesignInterface['status']) =>
    run(i.id, () => patchInterface(studyId!, i.id, { status, version: i.version }))
  const savePatch = (i: DesignInterface, patch: InterfacePatch) => run(i.id, () => patchInterface(studyId!, i.id, patch))
  const acceptAll = (list: DesignInterface[], type: InterfaceType) =>
    run(`all:${type}`, () => Promise.all(list.map(i => patchInterface(studyId!, i.id, { status: 'accepted', version: i.version }))))
  const propose = () => run('propose', async () => {
    const r = await proposeLinks(studyId!, { level: currentLevel, element_id: focusElementId })
    if (r) setLastRun(t('{{created}} new, {{updated}} updated, {{unchanged}} unchanged', { created: r.created.length, updated: r.updated.length, unchanged: r.unchanged }))
  })

  // Add form
  const [showAdd, setShowAdd] = useState(false)
  const [fromId, setFromId] = useState('')
  const [toId, setToId] = useState('')
  const [addType, setAddType] = useState<InterfaceType>('data')
  const [addName, setAddName] = useState('')
  const add = () => run('add', async () => {
    await createInterface(studyId!, {
      type: addType, from_element_id: fromId, to_element_id: toId,
      name: addName || `${nameOf(fromId)} → ${nameOf(toId)}`, diagram_label: addName || undefined,
    })
    setAddName(''); setShowAdd(false)
  })

  if (siblings.length < 2) {
    return <div className="c2o-pane t-13 c-2">{t('Need at least 2 elements at this level to define interfaces.')}</div>
  }

  const byType = (list: DesignInterface[]) => INTERFACE_TYPES
    .map(type => ({ type, items: list.filter(i => i.type === type) }))
    .filter(g => g.items.length > 0)

  const lang = i18n.language

  return (
    <div className="c2o-pane c2o-links">
      <Panel
        title={t('Interfaces')}
        meta={t('{{a}} accepted, {{s}} to review, {{r}} rejected', { a: accepted.length, s: suggested.length, r: rejected.length })}
        actions={<>
          <Button size="sm" onClick={propose} busy={busy === 'propose'}
            disabledReason={proposerMissing ? t('This server does not propose links yet') : undefined}
            title={t('Run the interface rules for this level. Rejected links stay rejected.')}>
            {t('Propose links')}
          </Button>
          <Button variant="primary" size="sm" onClick={() => setShowAdd(true)}
            disabledReason={showAdd ? t('The add form is already open below') : undefined}>{t('+ Add Interface')}</Button>
        </>}>
        {lastRun && <p className="t-12 c-3 m-0 pb-2" role="status">{t('Rules run: {{summary}}', { summary: lastRun })}</p>}
        {error && <Note tone="alarm" role="alert">{t('The server refused the change: {{message}}', { message: error })}</Note>}

        {showAdd && (
          <form className="c2o-blocks__add mb-3" aria-label={t('Add interface')}
            onSubmit={e => { e.preventDefault(); if (fromId && toId && fromId !== toId) add() }}>
            <Field label={t('From')}>
              <Select dense value={fromId} onChange={e => setFromId(e.target.value)}>
                <option value="">{t('From...')}</option>
                {endpoints.map(el => <option key={el.id} value={el.id}>{el.name}</option>)}
              </Select>
            </Field>
            <Field label={t('To')}>
              <Select dense value={toId} onChange={e => setToId(e.target.value)}>
                <option value="">{t('To...')}</option>
                {endpoints.filter(el => el.id !== fromId).map(el => <option key={el.id} value={el.id}>{el.name}</option>)}
              </Select>
            </Field>
            <Field label={t('Type')}>
              <Select dense value={addType} onChange={e => setAddType(e.target.value as InterfaceType)}>
                {INTERFACE_TYPES.map(id => <option key={id} value={id}>{t(TYPE_META[id].label)}</option>)}
              </Select>
            </Field>
            <Field label={t('Label (optional)')}>
              <Input dense value={addName} onChange={e => setAddName(e.target.value)} />
            </Field>
            <span className="row gap-2">
              <Button type="submit" variant="primary" size="sm" busy={busy === 'add'}
                disabledReason={!fromId || !toId ? t('Choose both ends of the interface first') : undefined}>{t('Add')}</Button>
              <Button size="sm" onClick={() => setShowAdd(false)}>{t('Cancel')}</Button>
            </span>
          </form>
        )}

        {(conflicts.length > 0 || unmet.length > 0) && (
          <div className="c2o-links__issues stack gap-1 mb-3">
            {conflicts.map((c, k) => (
              <Note key={`c${k}`} tone={c.severity === 'alarm' ? 'alarm' : 'caution'}>
                <StatusBadge status={c.severity === 'alarm' ? 'alarm' : 'caution'}>
                  {c.element_ids.map(nameOf).join(' ↔ ')}
                </StatusBadge>
                <span>{pickLang(c.reason, lang)}</span>
              </Note>
            ))}
            {unmet.length > 0 && (
              <Disclosure summary={t('Unmet needs')} meta={String(unmet.length)}>
                <ul className="list-reset c2o-links__unmet">
                  {unmet.map((u, k) => (
                    <li key={k}><span className="w-500">{nameOf(u.element_id)}</span> <span className="c-3">{u.need}</span> <span className="c-2">{pickLang(u.reason, lang)}</span></li>
                  ))}
                </ul>
              </Disclosure>
            )}
          </div>
        )}

        {/* 1. Suggested */}
        <section className="c2o-links__sec" aria-labelledby="links-sug">
          <h4 id="links-sug" className="c2o-links__h">
            <LinkStatusChip status="suggested" />
            <span>{t('{{count}} to review', { count: suggested.length })}</span>
          </h4>
          {suggested.length === 0 ? (
            <p className="t-13 c-3 m-0 py-2">{proposerMissing
              ? t('Expected links appear here once the server can propose them.')
              : t('Nothing to review. Every expected link at this level is accepted or rejected.')}</p>
          ) : (
            <>
              <p className="t-12 c-3 m-0 pb-2 measure">{t('Proposed from the C2O default interface matrix and the component data. They are defaults, not a standard, and already count in budgets and analyses until you reject them.')}</p>
              {byType(suggested).map(g => (
                <div key={g.type} className="c2o-links__group">
                  <div className="c2o-links__ghead">
                    <TypeLabel type={g.type} />
                    <span className="t-12 c-3">{t('{{count}} suggested', { count: g.items.length })}</span>
                    <span className="c2o-links__gref t-12 c-3">{t('ECSS-E-ST-10-24C nature: {{n}}', { n: TYPE_META[g.type].annexE })}</span>
                    <Button size="sm" onClick={() => acceptAll(g.items, g.type)} busy={busy === `all:${g.type}`}>
                      {t('Accept all {{count}}', { count: g.items.length })}
                    </Button>
                  </div>
                  <ul className="list-reset">
                    {g.items.map(i => (
                      <SuggestedRow key={i.id} iface={i} nameOf={nameOf} endpoints={endpoints} busy={busy === i.id}
                        onAccept={() => setStatus(i, 'accepted')} onReject={() => setStatus(i, 'rejected')}
                        onSave={p => savePatch(i, p)} />
                    ))}
                  </ul>
                </div>
              ))}
            </>
          )}
        </section>

        {/* 2. Accepted */}
        <section className="c2o-links__sec" aria-labelledby="links-acc">
          <h4 id="links-acc" className="c2o-links__h">
            <LinkStatusChip status="accepted" />
            <span>{t('{{count}} defined', { count: accepted.length })}</span>
          </h4>
          {accepted.length === 0
            ? <p className="t-13 c-3 m-0 py-2">{t('No interfaces defined. Click "Add Interface" to connect elements.')}</p>
            : (
              <ul className="list-reset c2o-ifaces">
                {accepted.map(i => (
                  <AcceptedRow key={i.id} iface={i} nameOf={nameOf} endpoints={endpoints} busy={busy === i.id}
                    onSave={p => savePatch(i, p)} onDelete={() => run(i.id, () => deleteInterface(i.id))}
                    onReject={() => setStatus(i, 'rejected')} />
                ))}
              </ul>
            )}
        </section>

        {/* 3. Rejected */}
        {rejected.length > 0 && (
          <Disclosure ruled summary={<span className="row gap-2"><LinkStatusChip status="rejected" />{t('Restore rejected')}</span>}
            meta={String(rejected.length)}>
            <p className="t-12 c-3 m-0 pb-2">{t('Rejected links are left out of budgets and analyses, and the rules do not propose them again.')}</p>
            <ul className="list-reset c2o-ifaces">
              {rejected.map(i => (
                <li key={i.id} className="c2o-links__row is-rejected">
                  <TypeLabel type={i.type} short />
                  <Ends iface={i} nameOf={nameOf} />
                  <span className="c2o-links__why t-12 c-3">{pickLang(i.rationale, lang) || originText(i, t)}</span>
                  <span className="c2o-links__acts">
                    <Button size="sm" onClick={() => setStatus(i, 'suggested')} busy={busy === i.id}
                      aria-label={t('Restore link {{from}} to {{to}}', { from: nameOf(i.from_element_id), to: nameOf(i.to_element_id) })}>{t('Restore')}</Button>
                    <RecordDecision decision="D-2.4-INTERFACES" capture="interfaces:link" label={t('Record')}
                      prefill={() => linkDecision(i, nameOf, t, lang, 'reject')} />
                  </span>
                </li>
              ))}
            </ul>
          </Disclosure>
        )}
      </Panel>
    </div>
  )
}

function Ends({ iface, nameOf }: { iface: DesignInterface; nameOf: (id: string) => string }) {
  const { t } = useTranslation()
  const one = iface.direction === 'unidirectional' || iface.direction === 'out'
  return (
    <span className="c2o-links__ends">
      <span className="w-500">{nameOf(iface.from_element_id)}</span>
      <span className="c-3" aria-hidden="true">{one ? '→' : '↔'}</span>
      <span className="sr-only">{one ? t('to') : t('and')}</span>
      <span className="w-500">{nameOf(iface.to_element_id)}</span>
    </span>
  )
}

function SuggestedRow({ iface, nameOf, endpoints, busy, onAccept, onReject, onSave }: {
  iface: DesignInterface; nameOf: (id: string) => string; endpoints: EndpointOption[]; busy: boolean
  onAccept: () => void; onReject: () => void; onSave: (p: InterfacePatch) => void
}) {
  const { t, i18n } = useTranslation()
  const [editing, setEditing] = useState(false)
  const summary = propsSummary(iface, t)
  const why = pickLang(iface.rationale, i18n.language)
  const pair = { from: nameOf(iface.from_element_id), to: nameOf(iface.to_element_id) }
  return (
    <li className={`c2o-links__row is-suggested${editing ? ' is-editing' : ''}`}>
      <InterfaceGlyph type={iface.type} />
      <Ends iface={iface} nameOf={nameOf} />
      {summary && <span className="c2o-links__sum mono t-12 c-2">{summary}</span>}
      <span className="c2o-links__why">
        <span className="t-13 c-2">{why || t('No rationale given by the rule.')}</span>
        <span className="c2o-links__ref t-12 c-3">{[iface.standard_ref, originText(iface, t)].filter(Boolean).join(' · ')}</span>
      </span>
      <span className="c2o-links__acts">
        <Button size="sm" variant="primary" onClick={onAccept} busy={busy}
          aria-label={t('Accept link {{from}} to {{to}}', pair)}>{t('Accept')}</Button>
        <Button size="sm" onClick={() => setEditing(e => !e)} aria-expanded={editing}
          aria-label={t('Edit link {{from}} to {{to}}', pair)}>{t('Edit')}</Button>
        <ArmButton label={t('Reject')} armedLabel={t('Confirm reject')} size="sm" variant="default"
          aria-label={t('Reject link {{from}} to {{to}}', pair)} onConfirm={onReject} />
        <RecordDecision decision="D-2.4-INTERFACES" capture="interfaces:link" label={t('Record')}
          prefill={() => linkDecision(iface, nameOf, t, i18n.language)} />
      </span>
      {editing && (
        <div className="c2o-links__edit">
          <LinkEditor iface={iface} endpoints={endpoints} saving={busy}
            onCancel={() => setEditing(false)} onSave={p => { onSave(p); setEditing(false) }} />
        </div>
      )}
    </li>
  )
}

function AcceptedRow({ iface, nameOf, endpoints, busy, onSave, onDelete, onReject }: {
  iface: DesignInterface; nameOf: (id: string) => string; endpoints: EndpointOption[]; busy: boolean
  onSave: (p: InterfacePatch) => void; onDelete: () => void; onReject: () => void
}) {
  const { t, i18n } = useTranslation()
  const [open, setOpen] = useState(false)
  const summary = propsSummary(iface, t)
  const fromRule = iface.origin.startsWith('rule:')
  const pair = { from: nameOf(iface.from_element_id), to: nameOf(iface.to_element_id) }
  return (
    <li className="c2o-ifaces__item">
      <div className="c2o-ifaces__row">
        <button type="button" className="c2o-ifaces__toggle" aria-expanded={open} onClick={() => setOpen(o => !o)}>
          <Chevron />
          <TypeLabel type={iface.type} short className="c2o-links__tcol" />
          <Ends iface={iface} nameOf={nameOf} />
          {summary ? <span className="mono t-12 c-2 ellipsis">{summary}</span> : <span className="t-12 c-3">{t('no properties')}</span>}
        </button>
        <span className="t-12 c-3 nowrap c2o-links__origin">{originText(iface, t)}</span>
        <RecordDecision decision="D-2.4-INTERFACES" capture="interfaces:link" label={t('Record')}
          prefill={() => linkDecision(iface, nameOf, t, i18n.language, 'accept')} />
        {fromRule
          ? <ArmButton label={t('Reject')} armedLabel={t('Confirm reject')} aria-label={t('Reject link {{from}} to {{to}}', pair)} onConfirm={onReject} />
          : <ArmButton variant="icon" label="×" armedLabel={t('Delete')} aria-label={t('Delete interface {{from}} → {{to}}', pair)} onConfirm={onDelete} />}
      </div>
      <InterfaceIrLinks interfaceId={iface.id} />
      {open && (
        <div className="c2o-ifaces__props">
          <LinkEditor iface={iface} endpoints={endpoints} saving={busy}
            onCancel={() => setOpen(false)} onSave={p => { onSave(p); setOpen(false) }} />
        </div>
      )}
    </li>
  )
}
