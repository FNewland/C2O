# Decisions — SpaceCDF redesign and voice loops (Franz, 2026-11-02)

Answers to the "Decisions for Franz" table of the SpaceCDF workflow redesign
(Claude Doc "SpaceCDF workflow redesign", §6) and the voice questions in
`docs/web_2026-10/ARCHITECTURE.md` §12.

| # | Decision | Ruling |
|---|---|---|
| 1 | Default gate profile | **Full ECSS: MDR → PRR → SRR → PDR** (four separate gates). IOD and the three-gate C2O profile stay selectable per study. |
| 2 | System margin ladder | **Stricter: 25 / 20 / 20 / 10 %** (MDR / PRR–SRR / PDR / CDR), labelled "C2O default" in `margin_policy.yaml`. |
| 3 | Phase 0 gate label | **Rename MCR → MDR**; "MCR" only in the NASA skin. |
| 4 | Seat claiming | **Self-claim + instructor override**, with an instructor lock. |
| 5 | Ownership enforcement | **Warn, then owner review.** Editing a parameter owned by another seat warns the editor first ("owned by Power — your change goes to them for review"). If they continue, the edit is stored as a *pending change* the owning seat must accept or reject; until accepted, the owner's value stands in analyses. Team leader and Instructor follow the same rule unless they hold the owning seat. Every edit and review is logged. |
| 6 | SMO seat authority | **MCS on the ground**; instructor board via a local GSG route; no identity crosses the link. |
| V1 | Voice platform | **LiveKit.** |
| V2 | Voice server host | **Its own small VM** with a public IP, started/stopped with `c2o up/down`. |
| V3 | Recordings | Off by default (opt-in). |
| V4 | Loops | **FD loop** (all positions), **Ops-coord**, **one per subsystem** (EPS/TCS, AOCS/FD, TTC, Payload, FDIR/Systems, Propulsion), **Instructor/SIM** loop hidden from students; more loops to be decided — keep loops data-driven in `voice_loops.yaml`. |
| L1 | Logbook visibility | Private to the participant (instructor sees counts at most). |
| L2 | Logbook retention | 48 h after last write; 7-day hard cap. |
