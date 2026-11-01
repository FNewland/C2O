# C2O user interface brief: "modern flight deck"

Author direction (Franz Newland, 1 Nov 2026): **a modern, clean interface that does not look AI-generated.** It uses progressive disclosure, puts visualisations and plots ahead of raw data wherever they cannot be misread, and makes enabled, disabled and stale states unmistakable. Think of a modern flight deck.

This brief applies to every C2O screen: mission control, planner, instructor console, the tool pages and SpaceCDF. It builds on the existing display standard, `sim/docs/design_2026-08/PRINCIPLES.md` (P1–P10: grey is the resting state, limits with every number, freshness, managed alarms, and so on), which stays in force. Where this brief is more specific, it wins.

## 1. Flight-deck rules

1. **Show the picture first, the number on demand.** A gauge, bar against limits, trend sparkline, timeline or schematic is the first thing a user sees. The exact value sits beside it in tabular figures. Raw tables are one click deeper. Use a plot only where it cannot be misread: always with a scale, limits and units, and never a decorative chart.
2. **Progressive disclosure, three levels.**
   - Overview: is everything nominal? What is next?
   - Subsystem: what is off and why?
   - Detail: parameters, history, raw packets.
   - Nothing at a deeper level competes for attention at a shallower one. Expanding something never moves what the user was looking at.
3. **States are unmistakable.** Each control and value is in exactly one of these states, each with its own visual treatment:

   | State | Treatment |
   |---|---|
   | Enabled | Solid outline or fill, full contrast |
   | Disabled | 40 % contrast, no hover, `cursor: not-allowed`, and a reason on hover or focus ("No procedure loaded") |
   | Armed / critical | Distinct border colour and an explicit two-step: arm, then execute |
   | Active / running | Filled with the accent colour, plus a text label |
   | Stale | Last value kept, dimmed and italic, with an age chip ("82.1 % · 59 s") |
   | No data | A distinct "no data" label (never an em-dash on a hatch) |
   | Alarm | Status colour **plus** shape or icon **plus** text (P6) |

4. **Calm when nominal.** At rest a screen is greys with one accent. Colour, motion and sound mean something has changed or needs a decision. There are no pulsing or animated idle states.
5. **Every number has units, limits and a source.** Ground-derived values are labelled "ground". Instructor-only values never appear on operator screens.

## 2. What "not AI-generated" means in practice

**Avoid:**
- purple, indigo or teal gradients;
- glass, blur and frosted cards;
- big soft drop shadows;
- rounded-everything (radius above 6 px), pill buttons everywhere;
- emoji and decorative icons;
- "hero" banners and marketing copy inside a working tool;
- centred card grids of equal-weight tiles;
- generic sparkle or "AI" iconography;
- vague labels such as "Insights" or "Smart panel";
- Inter-on-everything with no typographic hierarchy;
- the same blue on every interactive element.

**Prefer:**
- a strict grid, aligned edges, and hairline 1 px rules instead of boxes;
- a real typographic hierarchy: IBM Plex Sans for the interface, IBM Plex Mono with tabular figures for values and identifiers, three or four sizes only, weight for emphasis;
- square-ish geometry (2–4 px radius);
- density that respects expert users;
- labels in the operator's vocabulary (ECSS and PUS terms, procedure IDs).

**Colour:**
- a neutral grey ramp;
- one accent for "interactive / selected";
- status colours only for status;
- dark control-room theme for operations, light theme for design work, both from the same tokens;
- WCAG 2.2 AA contrast minimum (7:1 for values on consoles, as P-standard).

**Motion:** 120–160 ms, only for state changes and disclosure; nothing decorative.

## 3. Type and spacing (to be turned into tokens in the design-system phase)
- **Type scale:** 12 / 13 / 15 / 20 px, with a 12 px floor everywhere. Line height 1.4 for text, 1.2 for values.
- **Spacing:** a 4 px base (4, 8, 12, 16, 24, 32).
- **Language:** French strings run 20–30 % longer. Lay out for French first.

## 4. Review checklist for any UI change
- [ ] Does the first glance answer "nominal or not, and what's next" without reading numbers?
- [ ] Is every interactive element clearly enabled or disabled, with a reason when disabled?
- [ ] Is stale distinguishable from live and from never-received?
- [ ] Does colour appear only for status or selection?
- [ ] Are the layouts checked with screenshots in EN and FR at 1440 px (and 390 px for monitor views)?
- [ ] Are there zero critical or serious axe violations?
- [ ] Would a reviewer guess "made by a careful team", not "generated"?
