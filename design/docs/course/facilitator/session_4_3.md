# Session 4.3: Risk Management

**Duration:** 2 hours
**Prerequisites:** Sessions 4.1-4.2
**References:** ECSS-M-ST-80C; NASA SEH §6.4 (Process 13); NPR 8000.4

---

## Learning Objectives

By the end of this session, participants will be able to:
1. Identify technical risks from the design state
2. Assess risks using a 5×5 likelihood × consequence matrix
3. Develop mitigation strategies (accept, mitigate, transfer, avoid)
4. Perform a simplified FMECA (failure modes, effects, criticality)
5. Identify single-point failures and assess mission reliability

---

## 1. Risk Management Process (20 min)

### Teaching Notes

*[Source: ECSS-M-ST-80C; NASA SEH §6.4 (Process 13: Technical Risk Management)]*

### Four Steps

1. **Identify** — What can go wrong?
2. **Assess** — How likely is it? How bad is it?
3. **Mitigate** — What can we do about it?
4. **Monitor** — Is it getting better or worse?

### Risk Sources for CubeSats

| Source | Example Risks |
|--------|--------------|
| **Technical** | Component failure, interface mismatch, performance shortfall |
| **Schedule** | Component delivery delay, test facility unavailable |
| **Cost** | Component price increase, scope creep, test campaign overrun |
| **Programmatic** | Funding cut, personnel turnover, regulatory delay |
| **External** | Launch delay/failure, spectrum interference, export control denial |

---

## 2. Risk Assessment: The 5×5 Matrix (25 min)

### Teaching Notes

### Likelihood Scale

| Level | Likelihood | Description | Probability |
|-------|-----------|-------------|-------------|
| 1 | Remote | Very unlikely; no precedent | < 5% |
| 2 | Unlikely | Could happen but improbable | 5-20% |
| 3 | Possible | Has happened on similar missions | 20-50% |
| 4 | Likely | Expected to occur at least once | 50-80% |
| 5 | Almost certain | Will almost certainly occur | > 80% |

### Consequence Scale

| Level | Consequence | Technical | Cost | Schedule |
|-------|-----------|-----------|------|----------|
| 1 | Negligible | No performance impact | < 1% overrun | < 1 week slip |
| 2 | Minor | Minor performance degradation | 1-5% overrun | 1-4 week slip |
| 3 | Moderate | Significant performance loss | 5-15% overrun | 1-3 month slip |
| 4 | Major | Mission capability severely degraded | 15-30% overrun | 3-6 month slip |
| 5 | Catastrophic | Mission failure | > 30% overrun | > 6 month slip or cancellation |

### Risk Rating

```
Risk Score = Likelihood × Consequence
```

| Score | Category | Action |
|-------|----------|--------|
| 1-4 | **Low** (green) | Accept; monitor |
| 5-9 | **Medium** (amber) | Mitigate; plan B |
| 10-15 | **High** (orange) | Active mitigation required |
| 16-25 | **Critical** (red) | Redesign or descope required |

---

## 3. CubeSat-Specific Risks (20 min)

### Teaching Notes

Common CubeSat risks ranked by historical frequency:

| Risk | L | C | Score | Typical Mitigation |
|------|---|---|-------|--------------------|
| Deployment failure (antenna, SA) | 3 | 4 | 12 | Redundant deployment mechanisms; test cycling |
| Communication loss after deployment | 2 | 5 | 10 | Beacon mode; multiple ground stations; timer-based recovery |
| ADCS not achieving pointing spec | 3 | 3 | 9 | Margin in pointing budget; on-orbit calibration |
| Power budget negative in eclipse | 2 | 4 | 8 | Conservative duty cycling; battery margin |
| Thermal exceedance (hot case) | 2 | 3 | 6 | Additional radiator area; duty cycle limit |
| Launch delay (vehicle failure) | 3 | 2 | 6 | Manifest on multiple vehicles; schedule buffer |
| Spectrum licensing delay | 3 | 2 | 6 | Start filing early (12+ months before launch) |
| COTS component failure in radiation | 2 | 4 | 8 | Radiation testing; watchdog resets; latchup protection |
| Software bug causing safe mode entry | 4 | 2 | 8 | Testing; staged deployment; safe mode must work |

### FMECA (Simplified)

*[Source: ECSS-Q-ST-30-02C]*

For each critical component, assess:
1. **Failure mode**: How can it fail? (open circuit, short, stuck, degraded)
2. **Effect**: What happens to the subsystem? To the mission?
3. **Criticality**: Is it a single-point failure (mission loss)?
4. **Detection**: Can we detect it in telemetry?
5. **Mitigation**: Redundancy, graceful degradation, operational workaround

### Single-Point Failure (SPF) Analysis

A single-point failure is any single component whose failure causes mission loss.

CubeSat typical SPFs:
- OBC (usually only one) → mitigate with watchdog + safe mode
- Battery (usually one pack) → mitigate with balanced cell monitoring
- Antenna (if single non-deployable) → mitigate with redundant deployment

**Discussion prompt:** *List the single-point failures in your design. Which ones are acceptable? Which need mitigation?*

---

## 4. Mitigation Strategies (15 min)

### Teaching Notes

| Strategy | Description | Example | Cost Impact |
|----------|-------------|---------|-------------|
| **Accept** | Risk is within tolerance; no action | Low-priority science instrument degradation | None |
| **Mitigate** | Reduce likelihood or consequence | Add redundant deployment mechanism | Moderate |
| **Transfer** | Pass risk to another party | Insurance; supplier warranty | Premium cost |
| **Avoid** | Change design to eliminate risk | Use lower orbit to avoid radiation | May affect performance |

### Decision Framework

```
Is the risk score ≤ 4? → Accept (monitor)
Is the risk score 5-9? → Mitigate if cost-effective; accept if not
Is the risk score 10-15? → Must mitigate (active plan required)
Is the risk score 16-25? → Redesign, descope, or don't proceed
```

---

## 5. SpaceCDF Risk Exercise (40 min)

### Instructions

1. Review the **Dashboard** — check reliability score and conflict count
2. Go to the **Q&A** tab — answer the risk-related questions for your position:
   - Systems: "Are there unresolved cross-domain conflicts?"
   - Each subsystem: "Is [budget] closing with adequate margin?"
3. Create a **risk register** (Worksheet 4.3):
   - Identify 5 risks for your mission design
   - Score each (Likelihood × Consequence)
   - Define mitigation for any scoring ≥ 10
4. Identify **single-point failures** in your design
5. For each SPF, determine: is it acceptable? If not, what redundancy is needed?

### Worksheet 4.3 Tasks

| # | Risk | L (1-5) | C (1-5) | Score | Mitigation | Owner |
|---|------|---------|---------|-------|------------|-------|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |
| 4 | | | | | | |
| 5 | | | | | | |

Single-point failures identified:
1. ___________________ Acceptable? Y/N  Mitigation: _______________
2. ___________________ Acceptable? Y/N  Mitigation: _______________
3. ___________________ Acceptable? Y/N  Mitigation: _______________

---

## Session Summary

| Topic | Key Takeaway |
|-------|-------------|
| Process | Identify → Assess → Mitigate → Monitor (continuous) |
| 5×5 matrix | Likelihood × Consequence = Risk Score (1-25) |
| CubeSat risks | Deployment, comms loss, ADCS, power — most common |
| FMECA | Failure mode → effect → criticality → detection → mitigation |
| SPF | Single-point failures must be identified and accepted or mitigated |
| Strategies | Accept / Mitigate / Transfer / Avoid — cost-benefit decision |
