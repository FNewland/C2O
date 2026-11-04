# C2O pictorial displays (`shared/ui-viz/`)

Framework-free ES modules that draw C2O's pictorial mission-control displays.
The SMO consoles (vanilla JS) and SpaceCDF (React) import the **same files**,
so a picture looks and behaves the same in operations and in design.

This folder is the source of truth. `sync.py` copies it to:

| Copy | Served as | Used by |
|---|---|---|
| `sim/packages/smo-common/src/smo_common/ui/viz/` | `/static/shared/viz/` on every SMO server | MCS (`static/modern/pictorial.js`), planner, tools |
| `design/frontend/src/viz/` | Vite module | SpaceCDF |

The copies are generated. Edit here, then run `python3 shared/ui-viz/sync.py`
and commit both. `python3 shared/ui-viz/sync.py --check` exits 1 if a copy is
stale, missing or has an extra file; `sim/tests/test_common/test_ui_viz.py`
runs it.

## Modules

| File | What it draws | Model |
|---|---|---|
| `derive.js` | Nothing: pure interpretation of telemetry (quaternions, pointing error, LVLH roll/pitch/yaw, sun/nadir angles, wheels vs saturation, energy per orbit, predicted SoC/DoD, eclipse timeline, storage and link) | snapshot → model |
| `common.js` | Shared helpers: token aliases, SVG strings, readouts in their data state, the Values table | — |
| `powerflow.js` | Energy-flow mimic, `variant: "full"` (EPS page) or `"summary"` (overview) | `derivePower()` |
| `overview.js` | Spacecraft synoptic: subsystem blocks on the spacecraft outline, worst state, mode ladder; a stacked list below 640 px | host-built (see file header) |
| `attitude2d.js` | Pointing-error dial, boresight sky (sun, nadir), roll/pitch/yaw and rate tapes, wheel bars, momentum | `deriveAttitude()` |
| `attitude3d.js`, `groundtrack.js`, `skyplot.js` | 3D attitude, ground track, pass sky plot (see their headers) | `deriveAttitude()` etc. |
| `stack3d.js` | CubeSat stack in 3D: envelope, one box per placed unit by subsystem, stowed / deployed / exploded, keep-out cones, CoG with the CDS box, body axes and frame caption | `c2o.geometry/1` with the stack-builder keys `internal`, `mass_properties`, `frame` (SpaceCDF `GET /api/studies/{id}/stack/geometry`; design/docs/STACK_BUILDER.md) |

Every view: `mount(el, { t, ... }) -> { update(model), destroy() }`. Views
never read raw telemetry; they draw the plain objects `derive.js` returns, so
SpaceCDF can feed them design values (`sourceFromValues()`, verdict
`"design"`).

```js
import * as D from "/static/shared/viz/derive.js";
import * as PF from "/static/shared/viz/powerflow.js";
const view = PF.mount(document.getElementById("flow"), { t: tText, variant: "full" });
const src = D.sourceFromState(state, { limits, verdict: (hex) => freshness(hex) });
view.update(D.derivePower(src, { history }));
```

In React, mount in `useEffect` with a ref and call `destroy()` on cleanup.

## Conventions

- **Quaternions** are scalar-last `[x y z w]`, ECI→body (`v_b = C(q)·v_eci`),
  as in `smo_common/attitude.py`. `aocs.att_q1..4` (0x0200–03) is the MEKF
  **estimate**, the same as `aocs.q_est_1..4` (0x02A0–A3), not truth.
  `aocs.q_ref_*` (0x02AB–AE) is the commanded attitude. Convert any
  scalar-first source with `fromScalarFirst()`. The test suite cross-checks the
  algebra against the simulator's Python.
- **Roll/pitch/yaw** are z-y-x angles of the body relative to the commanded
  attitude; in `LVLH_NADIR` pointing that reference is the LVLH nadir frame.
  Within 5° of ±90° pitch they are flagged, not shown.
- **Battery power** is positive when charging. Array power is current × bus voltage.
- **Every quantity** carries `verdict` (worst of its inputs), `ageS`, `src`
  and `ground`; views show stale as dimmed italic with age, never-received as
  "no data".
- **Colours** come from tokens only (console names first, SpaceCDF names as
  fallback); grey at rest, colour only for status or selection.
- **Text**: English keys through `opts.t`; French in
  `smo_common/ui/i18n/fr.json`. Dynamic labels are listed in each module's
  `DYNAMIC_KEYS` for the i18n scanner.
