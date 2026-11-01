# Testing C2O

C2O has two Python projects, each with its own `.venv` and test suite: `sim/` (the SMO simulator suite) and `design/` (SpaceCDF). There is also one frontend, `design/frontend`. CI runs the same commands as below: `.github/workflows/ci.yml` on every push and PR, and `.github/workflows/nightly.yml` nightly.

## Setup (once per venv)

```bash
# sim/  (packages as in sim/start.sh)
cd sim
python3 -m venv .venv && source .venv/bin/activate
pip install -e packages/smo-common
pip install -e packages/smo-simulator -e packages/smo-mcs -e packages/smo-planner \
            -e packages/smo-rfsim -e packages/smo-link -e packages/smo-gateway
pip install --group dev          # pytest, pytest-xdist, pytest-timeout, playwright, ...

# design/  (packages as in design/install.sh --backend)
cd design
python3 -m venv .venv && source .venv/bin/activate
pip install -e packages/spacecdf-common -e packages/spacecdf-kb \
            -e packages/spacecdf-agents -e packages/spacecdf-server
pip install --group dev
```

`pip install --group` needs pip 25.1 or later. With an older pip, install the `dev` list from the project's `pyproject.toml` by hand.

The JS-harness tests in `sim/tests/test_mcs` and `sim/tests/test_common` need `node` on PATH. Tests skip themselves when it is missing.

## sim: three tiers

Markers are registered in `sim/pyproject.toml`. `sim/tests/conftest.py` assigns tiers in three ways:

- whole heavy modules by path, in `_TIER_BY_PATH`;
- individually slow tests by node id, in `sim/tests/slow_tests.txt` (the tests that took 4 s or more in a measured fast-tier run; the file header says how to refresh it);
- any test that carries `@pytest.mark.slow` itself.

| Tier | When | Command (run from `sim/`) |
|---|---|---|
| **fast** | every push and PR; before you commit | `.venv/bin/python -m pytest -n auto -m "not slow and not e2e"` |
| **slow** | nightly | `.venv/bin/python -m pytest -n auto -m "slow and not e2e"` |
| **e2e** | nightly, and before a release | `SMO_E2E=1 .venv/bin/python -m pytest tests/test_e2e_browser -m e2e` |

- **slow** covers:
  - RF DSP (`rf_dsp`: the blind receiver and the impairments tests);
  - the acceptance flythroughs (`tests/test_acceptance/`);
  - the RF commissioning and LEOP end-to-end runs;
  - fly-a-plan;
  - the smo-link end-to-end stack (`link_e2e`);
  - every test individually marked `slow`, such as the engine-boot-heavy ones.
- **e2e** boots a real stack on the **default ports** (8001/8002/8080/9090/9091/8092–8094) and drives it with Playwright.
  - Run it **serially** (no `-n`), and never while `./start.sh` is up.
  - Every test in `tests/test_e2e_browser/` skips unless `SMO_E2E=1`.
  - `-m "e2e and not legacy_ui"` runs only the modern-UI suite (`test_modern_ui.py`).
  - `-m legacy_ui` runs only the two legacy modules (`test_full_mission_validation.py` and `test_leop_commissioning.py`). These drive the classic console through the RF bridge, take about 30–45 minutes, and are informative only in CI.
  - Playwright needs a Chromium. In CI it comes from `python -m playwright install --with-deps chromium`. On the course containers it is pre-provisioned: set `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers` and do not run `playwright install`.

Useful variations:

```bash
.venv/bin/python -m pytest tests/test_mcs/test_fdir_window.py -q        # one file
.venv/bin/python -m pytest -n auto -m "not slow and not e2e" --durations=25   # find new slow tests
.venv/bin/python -m pytest -m rf_dsp                                    # just the DSP
```

**Parallel safety.** The fast tier must stay `-n auto`-clean:

- servers in tests bind port 0 (aiohttp `TestServer`, `asyncio.start_server(..., 0)`);
- files go to `tmp_path`, not into the repo.

Anything that needs fixed ports belongs in `e2e`.

**Mock engines.** `ServiceDispatcher` tests that use a `MagicMock` engine must pass it through `tests.engine_doubles.wire_mock_engine()`. The helper gives the mock the real `param_visibility` and `pack_tm_segmented`. Without it, S20.3 refuses every read and every "report all" comes back empty. For segmented TM(12,13)/TM(19,128), `tests.pus_reports.report_body()` reassembles the segments.

## design: pytest

```bash
cd design
.venv/bin/python -m pytest -n auto
```

Everything runs in-process. `tests/test_level_workbench.py` drives the app through FastAPI's `TestClient` over a throw-away SQLite file, so no server is needed. To run it against a live server instead, set `SPACECDF_BASE_URL=http://localhost:8000/api`. Those runs are marked `live_server`, and they write to that server's database.

## design/frontend

```bash
cd design/frontend
npm ci
npx tsc -b        # type-check (must be zero errors)
npx vite build
```

## i18n parity (both projects)

```bash
cd sim    && python3 -m tools.i18n check
cd design && python3 -m tools.i18n check
```

See `sim/tools/i18n/README.md` for `check --files`, `accept` and the FR style rules.
