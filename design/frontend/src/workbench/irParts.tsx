/**
 * irParts — interface ↔ interface requirement links, visible both ways (design rules
 * IF-01 … IF-05):
 *   - <InterfaceIrLinks> under an accepted link (Interfaces tab): its requirements with
 *     status, "needs review" when the link changed, and the agreement of both seats;
 *   - <RequirementIrInfo> on an interface requirement (Requirements tab): the text in the
 *     current language, the interface it is allocated to, and the review actions.
 */
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Button, StatusBadge, Tag, type Status } from '../components/ui'
import { pickLang } from '../types/interfaces'
import { useUIStore } from '../stores/uiStore'
import { useInterfaces } from './interfaceApi'
import {
  irText, irUpdate, setAgreement, useInterfaceRequirements, useInvalidateElectrical,
  type Agreement, type InterfaceRequirement,
} from './electricalApi'
import './electrical.css'

// English text is the i18n key
const AGREEMENT_LABEL: Record<Agreement['state'], string> = {
  identified: 'Identified', defined: 'Defined', agreed: 'Agreed', verified: 'Verified',
}
const AGREEMENT_STATUS: Record<Agreement['state'], Status> = {
  identified: 'nodata', defined: 'neutral', agreed: 'info', verified: 'ok',
}
const REQ_STATUS: Record<string, Status> = { draft: 'neutral', approved: 'info', verified: 'ok', violated: 'alarm' }
const SEAT_LABEL: Record<string, string> = {
  power_engineer: 'Power', comms_engineer: 'Comms & OBDH', aocs_engineer: 'AOCS', thermal_engineer: 'Thermal',
  structures_engineer: 'Structures & config', payload_lead: 'Payload', propulsion_engineer: 'Propulsion',
  systems_engineer: 'Systems', team_leader: 'Team leader', mission_analyst: 'Mission analysis & ops',
}

/** Requirements + agreement under one accepted interface. */
export function InterfaceIrLinks({ interfaceId }: { interfaceId: string }) {
  const { t, i18n } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const setActivePanel = useUIStore(s => s.setActivePanel)
  const { data } = useInterfaceRequirements(studyId)
  const invalidate = useInvalidateElectrical(studyId)
  const [busy, setBusy] = useState(false)
  if (!data) return null
  const irs = data.requirements.filter(r => r.ir_json?.interface_id === interfaceId)
  const ag = data.agreements[interfaceId]
  const seat = (s: string | null) => (s ? t(SEAT_LABEL[s] ?? s) : t('no seat'))
  const agree = async (side: 'provider' | 'consumer', on: boolean) => {
    setBusy(true)
    try { await setAgreement(studyId!, interfaceId, side, on); invalidate() } finally { setBusy(false) }
  }
  return (
    <div className="c2o-irlinks" data-testid={`ir-links-${interfaceId}`}>
      <span className="t-12 c-3">{t('Interface requirements')}</span>
      {irs.length === 0
        ? <span className="t-12 c-3">{t('none yet')}</span>
        : irs.map(r => (
          <button key={r.id} type="button" className="c2o-irchip" onClick={() => setActivePanel('requirements')}
            title={irText(r, i18n.language)}>
            <StatusBadge status={r.ir_json?.review ? 'stale' : (REQ_STATUS[r.status] ?? 'neutral')}>
              <span className="mono">{r.code}</span>
            </StatusBadge>
          </button>
        ))}
      {ag && (
        <span className="c2o-irlinks__ag">
          <StatusBadge status={AGREEMENT_STATUS[ag.state]} title={t('ECSS-E-ST-10-24C: identified → defined → agreed → verified')}>
            {t(AGREEMENT_LABEL[ag.state])}
          </StatusBadge>
          {(['provider', 'consumer'] as const).map(side => {
            const who = ag[side]
            const label = side === 'provider' ? t('Provider: {{seat}}', { seat: seat(ag.provider_seat) }) : t('Consumer: {{seat}}', { seat: seat(ag.consumer_seat) })
            return (
              <label key={side} className="c2o-irlinks__side t-12" title={who ? t('Agreed by {{who}}', { who: who.by || seat(who.seat) }) : undefined}>
                <input type="checkbox" checked={!!who} disabled={busy} onChange={e => agree(side, e.target.checked)} />
                {label}
              </label>
            )
          })}
        </span>
      )}
    </div>
  )
}

/** Text in the current language + the allocated interface + review actions (Requirements tab). */
export function RequirementIrInfo({ req }: { req: Pick<InterfaceRequirement, 'id' | 'text' | 'ir_json'> }) {
  const { t, i18n } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const setActivePanel = useUIStore(s => s.setActivePanel)
  const { interfaces } = useInterfaces(studyId, { poll: false })
  const invalidate = useInvalidateElectrical(studyId)
  const [busy, setBusy] = useState(false)
  const ir = req.ir_json
  const iface = interfaces.find(i => i.id === ir?.interface_id)
  const act = async (a: 'accept-update' | 'dismiss-update') => {
    setBusy(true)
    try { await irUpdate(studyId!, req.id, a); invalidate() } finally { setBusy(false) }
  }
  return (
    <span className="c2o-reqs__text">
      {irText(req, i18n.language)}
      <span className="c2o-irlinks c2o-irlinks--inline">
        {iface
          ? <button type="button" className="c2o-irchip" onClick={() => setActivePanel('interfaces')}
              title={t('Allocated to interface {{name}}', { name: iface.name })}>
              <Tag>{t('Interface: {{name}}', { name: iface.name })}</Tag>
            </button>
          : <StatusBadge status="caution">{t('No interface: name two elements to propose one')}</StatusBadge>}
        {ir?.missing && ir.missing.length > 0 && <Tag title={ir.missing.join(', ')}>{t('{{n}} TBD', { n: ir.missing.length })}</Tag>}
        {ir?.review === 'stale' && (
          <>
            <StatusBadge status="stale" title={pickLang(ir.proposed_text ?? null, i18n.language) || undefined}>{t('Interface changed: review')}</StatusBadge>
            <Button size="sm" busy={busy} onClick={() => act('accept-update')}
              title={pickLang(ir.proposed_text ?? null, i18n.language) || undefined}>{t('Take new text')}</Button>
            <Button size="sm" variant="quiet" busy={busy} onClick={() => act('dismiss-update')}>{t('Keep mine')}</Button>
          </>
        )}
        {ir?.review === 'retire' && (
          <>
            <StatusBadge status="caution">{t('Interface rejected: retire?')}</StatusBadge>
            <Button size="sm" busy={busy} onClick={() => act('accept-update')}>{t('Retire')}</Button>
            <Button size="sm" variant="quiet" busy={busy} onClick={() => act('dismiss-update')}>{t('Keep')}</Button>
          </>
        )}
      </span>
    </span>
  )
}
