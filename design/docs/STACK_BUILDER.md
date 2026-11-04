# CubeSat stack builder

How SpaceCDF turns the selected parts into a CubeSat layout, checks it, and shows it.
Design rules: `docs/plan_2026-11/design_sim/spacecdf_design_rules.md` §4 (and §2.2, D9, D13).
Code: `packages/spacecdf-server/src/spacecdf_server/services/stack_builder.py` (pure),
`routers/stack.py` (API, persistence, seats), `packages/spacecdf-kb/src/spacecdf_kb/mechanical.py`
(KB schema v2), `configs/stack_rules.yaml` (rules, weights), UI `frontend/src/spacecraft/stack/`,
3D `shared/ui-viz/stack3d.js`.

## 1. Frames (read this first)

| Frame | Used by | Origin | Axes | Units |
|---|---|---|---|---|
| **Stack frame** = simulator body frame (`sim/configs/eosat1/geometry.yaml`, ruling Q4) | stack builder, elevation, face map, 3D, `geometry.yaml` export | envelope geometric centre | +X ~ velocity, +Y = orbit normal, **+Z = zenith, −Z = nadir**; X is the short side (100 mm), Y the 226 mm side of a 6U, Z the rail axis | mm inside the builder, m in the export |
| **Design frame** = SpaceCDF `position_json` | `physics_closure` (mass properties, AOCS), `cds_checks` CDS-COG, `mass_properties.py` | envelope **corner** | axes in the body-frame order of `cds_rules.yaml envelope_mm` (reordered by `body_frame.order`, as `cds_checks` CDS-COG; a 6U has X = 100 mm), **+Z = nadir** along the rails | m |

`stack_builder.to_design_m` is the only conversion. It is a proper rotation plus the corner
offset: 180° about X (`x, −y, −z`) when the body-frame envelope lists the short side first
(every form factor today: the 6U `body_frame.order` puts 100 mm on X, F1/D15), and the X/Y
swap with the Z flip (`y, x, −z`) otherwise. The design frame follows `cds_checks`, so the
approved positions give CDS-COG the same answer as STACK-COG. Nothing else converts frames.

## 2. Placement model

A layout **spec** is what the auto-placer and the user edit:

```json
{"columns": [["pl", "eps", "bat"], ["gps", "trx", "obc", "st"]],
 "layers":  {"nadir": [], "zenith": []},
 "faces":   {"sp": [{"face": "py", "count": 1}, {"face": "my", "count": 1}]},
 "locks":   {"obc": true},
 "origins": {"obc": "user", "pl": "rule:STACK-AUTO"}}
```

* `columns`: one list per stack column, nadir end first (1U–3U: 1 column; 6U: 2 columns
  side by side along Y; 12U: 2 × 2). Units anchored to an end (`anchor: nadir` — imager
  aperture; `zenith` — star tracker baffle) always return to that end. The free units form
  a block centred in the remaining length (standoffs above and below).
* `layers`: units wider than one column (they span all columns at an end).
* `faces`: face items (body cells, patches, sun sensors) and stowed deployables, grouped
  per face; a group of `count` units is tiled on the face around the ports of internal
  units (aperture, baffle, nozzle).
* `locks`: placement ids kept by the auto-placer. Placement id = element id, or
  `<element id>@<face>` for a face group.

`realise(spec)` derives every **placement**: mount class, column, slot, layer, face, box
(centre and size, stack frame), z range, protrusion, deployed geometry (wings unfold
outward in the plane of the face normal and Z, as the simulator's wings; antenna elements
unfold in the face plane), mass/power share, assumptions. Structure and distributed mass
(harness, MLI) sit at the centre.

Persistence: table `stack_layouts` (one row per study): `approved_json` and `proposal_json`,
each a spec + who/when + the auto-placement report. Placements are always re-derived from
the current elements, so a part added after approval is placed by rule and reported in
`notes`. (Not option-scoped yet.)

## 3. KB schema v2 — mechanical block

Optional `mechanical:` on a KB component; every field falls back, in order, to the v1
fields (`dimensions_mm`, `form_factor`, `interfaces`, `performance.deployment/band/fov_deg`),
then the category default and the domain default in
`packages/spacecdf-kb/src/spacecdf_kb/data/mechanical_defaults.yaml`. Fields:
`mount_class` (pc104_board, pc104_module, u_module, face_panel, deployable, bracket,
structure, distributed, none), `envelope_mm` [a, b, h] (h along the mounting normal / stack
axis), `stack_height_mm`, `u_size`, `face` (stack-frame face: px mx py my pz mz), `anchor`,
`boresight`, `fov_deg`, `spread` (one_per_face | tile), `deployable` {kind, wings, panels,
length_mm, hinge}, `connector`. Every default used is returned in `assumptions` and shown
in the UI as "C2O defaults used". Defaults are C2O values to calibrate per vendor
(PC/104 pitch 15.24 mm, end allowance 6 mm, wall 1 mm, star tracker 55 × 55 × 75 mm…).

New category `payload_imager` (`data/components/payload_imagers.yaml`): three
representative classes (0.5U, 1U, 2U = the simulator's EOSAT-1 imager), schema v2.

## 4. Auto-placement (`POST /stack/auto-place`, origin `rule:STACK-AUTO`)

1. Classify by mount class (KB schema v2).
2. Faces by rule (`stack_rules.yaml faces`): imager aperture and radiator nadir (−Z);
   S/X-band patch nadir; GNSS and UHF zenith (+Z); wings on ±Y (simulator); body cells
   on the largest free faces; sun sensors one per face, not under a stowed wing.
3. Columns: anchors first, then the tallest units to the least-loaded column; order by
   rank (payload, propulsion, radio near a nadir antenna, battery, EPS, ADCS, OBC, radio
   near a zenith antenna, GNSS).
4. Swap search: swaps of two free units and moves to any slot of any column, first
   improvement, deterministic order, up to `max_passes`; score =
   `w_cog·Σ(offset/limit)² + w_harness·harness + w_thermal·thermal` (+ penalties for a CoG
   outside the box and a column overflow). Harness = weighted distances of role pairs
   (battery–EPS 3, radio–antenna coax 2, …) and of the study's power/data/RF links.
   Thermal = dissipation-weighted distance to the radiator face + a hot-spot term.
   Locked and anchored units do not move.

The result is a **proposal**. Anyone who may edit proposes (also by hand: drag, keyboard,
lock — `PUT /stack/proposal`); the **Structures & configuration** seat (or its fallback when
the study does not use it, or the instructor) approves (`POST /stack/approve`, ruling 5).
Approval writes every unit's `position_json` (design frame), so mass properties, CDS-COG and
the AOCS closure use real positions instead of the +z auto-stack (F14).

## 5. Checks (`STACK-*`, design rules §4.4)

| Id | What | Source |
|---|---|---|
| STACK-HEIGHT | column length used ≤ envelope length − 2 × end allowance | rules §4.4, C2O default allowance |
| STACK-ENV | every unit fits its column / face; wide units fit the envelope | CDS 14.1 App. B |
| STACK-PROTR | stowed face items ≤ 6.5 mm beyond the rail plane (end faces keep the end allowance as recess) | CDS 14.1 2.2.3 |
| STACK-COLL | boxes in a column, tiles on a face, deployed geometry vs body and vs each other | rules §4.4 |
| STACK-COG | stowed CoG inside the CDS Table 2 box (design-frame axes) | CDS 14.1 2.2.11 |
| STACK-KEEPOUT | star-tracker and imager FOV cones (+2°) clear of deployed geometry | rules §4.4 (EI-07) |
| STACK-ST-EARTH | star-tracker boresight ≥ 25° above the Earth limb in nadir pointing | geometry.yaml exclusions |
| STACK-PC104 | boards from several vendors on one stack: check the H1/H2 pinout (caution) | rules §4.1 |

Envelope, CoG box and protrusion are read from `configs/cds_rules.yaml` (one fix there, F1,
fixes the builder too). The approved layout's checks (all but STACK-COG, which CDS-COG
covers from the written positions) are appended to the CDS compliance matrix
(`GET /studies/{id}/rules/cds`) and feed **GC-CDS**; **GC-STACK** (PDR) asks for an approved
layout without failing checks.

## 6. Geometry export — `c2o.geometry/1`, extended additively

`GET /studies/{id}/stack/geometry?which=approved|proposal&format=yaml|json` writes the
simulator's `geometry.yaml` schema (bus, body_panels with cell areas per face, wings,
array_drive, payload, star_trackers, antennas, thrusters) from the layout, plus three
**optional** keys accepted by `smo_common.config.geometry.validate_geometry` (a file
without them is unchanged and valid):

* `frame` — the convention as text (stack frame and design frame);
* `internal` — one box per placed unit or face tile: `{id, name, subsystem, mount, column,
  slot, face, box_m: [cx, cy, cz, dx, dy, dz], mass_kg}` (stowed);
* `mass_properties` — `{mass_kg, cog_m}`.

`shared/ui-viz/stack3d.js` draws that document (stowed / deployed / exploded, keep-out cones,
CoG with the CDS box, axes and frame caption), so mission control can show the same stack
from the same file.
