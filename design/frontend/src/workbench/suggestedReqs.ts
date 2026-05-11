/** Suggested requirement templates by level and type. */
export const SUGGESTED_REQS: Record<number, Array<{ type: string; text: string; method: string }>> = {
  0: [
    { type: 'functional', text: 'The mission shall acquire and deliver [data type] within [timeframe]', method: 'A' },
    { type: 'performance', text: 'The mission shall operate for a minimum of [N] years', method: 'A' },
    { type: 'performance', text: 'The total mission mass shall not exceed [N] kg', method: 'I' },
    { type: 'interface', text: 'The space segment shall communicate with the ground segment via [band]', method: 'T' },
    { type: 'regulatory', text: 'The mission shall comply with [ISED/ITU] frequency coordination requirements', method: 'R' },
    { type: 'regulatory', text: 'The mission shall deorbit within 5 years of end-of-life per ECSS-U-AS-10C', method: 'A' },
    { type: 'process', text: 'The mission shall conduct a System Requirements Review (SRR) before PDR', method: 'R' },
  ],
  1: [
    { type: 'functional', text: 'The [system] shall provide [function] during [mode]', method: 'T' },
    { type: 'performance', text: 'The [system] mass shall not exceed [N] kg', method: 'I' },
    { type: 'performance', text: 'The [system] power consumption shall not exceed [N] W average', method: 'T' },
    { type: 'interface', text: 'The [system] shall interface with [other system] via [interface type]', method: 'I' },
    { type: 'regulatory', text: 'The [system] shall comply with [ECSS standard] requirements', method: 'R' },
    { type: 'process', text: 'The [system] design shall be reviewed at PDR', method: 'R' },
  ],
  2: [
    { type: 'functional', text: 'The [subsystem] shall provide [specific function]', method: 'T' },
    { type: 'performance', text: 'The [subsystem] mass shall not exceed [N] kg', method: 'I' },
    { type: 'performance', text: 'The [subsystem] power consumption shall not exceed [N] W', method: 'T' },
    { type: 'interface', text: 'The [subsystem] shall interface with [other subsystem] via [type]', method: 'I' },
    { type: 'process', text: 'The [subsystem] shall be reviewed at PDR', method: 'R' },
  ],
  3: [
    { type: 'functional', text: 'The [component] shall provide [specific function]', method: 'T' },
    { type: 'performance', text: 'The [component] shall operate within [temp range] deg C', method: 'T' },
    { type: 'performance', text: 'The [component] TRL shall be >= [N] at CDR', method: 'R' },
    { type: 'interface', text: 'The [component] shall connect via [connector/protocol]', method: 'I' },
    { type: 'process', text: 'The [component] shall be acceptance-tested per [standard]', method: 'T' },
  ],
  4: [],
}
