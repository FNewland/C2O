/** Suggested requirement templates by level and type. */

/**
 * i18n extraction marker: returns the English text unchanged. Template texts become requirement
 * text in the database when used, so the stored value stays English (LIVE_FILES.md, C3); the
 * suggestion list in RequirementsPanel shows t(text) at display time.
 */
const t = (english: string): string => english

export const SUGGESTED_REQS: Record<number, Array<{ type: string; text: string; method: string }>> = {
  0: [
    { type: 'functional', text: t('The mission shall acquire and deliver [data type] within [timeframe]'), method: 'A' },
    { type: 'performance', text: t('The mission shall operate for a minimum of [N] years'), method: 'A' },
    { type: 'performance', text: t('The total mission mass shall not exceed [N] kg'), method: 'I' },
    { type: 'interface', text: t('The space segment shall communicate with the ground segment via [band]'), method: 'T' },
    { type: 'regulatory', text: t('The mission shall comply with [ISED/ITU] frequency coordination requirements'), method: 'R' },
    { type: 'regulatory', text: t('The mission shall deorbit within 5 years of end-of-life per ECSS-U-AS-10C'), method: 'A' },
    { type: 'process', text: t('The mission shall conduct a System Requirements Review (SRR) before PDR'), method: 'R' },
  ],
  1: [
    { type: 'functional', text: t('The [system] shall provide [function] during [mode]'), method: 'T' },
    { type: 'performance', text: t('The [system] mass shall not exceed [N] kg'), method: 'I' },
    { type: 'performance', text: t('The [system] power consumption shall not exceed [N] W average'), method: 'T' },
    { type: 'interface', text: t('The [system] shall interface with [other system] via [interface type]'), method: 'I' },
    { type: 'regulatory', text: t('The [system] shall comply with [ECSS standard] requirements'), method: 'R' },
    { type: 'process', text: t('The [system] design shall be reviewed at PDR'), method: 'R' },
  ],
  2: [
    { type: 'functional', text: t('The [subsystem] shall provide [specific function]'), method: 'T' },
    { type: 'performance', text: t('The [subsystem] mass shall not exceed [N] kg'), method: 'I' },
    { type: 'performance', text: t('The [subsystem] power consumption shall not exceed [N] W'), method: 'T' },
    { type: 'interface', text: t('The [subsystem] shall interface with [other subsystem] via [type]'), method: 'I' },
    { type: 'process', text: t('The [subsystem] shall be reviewed at PDR'), method: 'R' },
  ],
  3: [
    { type: 'functional', text: t('The [component] shall provide [specific function]'), method: 'T' },
    { type: 'performance', text: t('The [component] shall operate within [temp range] deg C'), method: 'T' },
    { type: 'performance', text: t('The [component] TRL shall be >= [N] at CDR'), method: 'R' },
    { type: 'interface', text: t('The [component] shall connect via [connector/protocol]'), method: 'I' },
    { type: 'process', text: t('The [component] shall be acceptance-tested per [standard]'), method: 'T' },
  ],
  4: [],
}
