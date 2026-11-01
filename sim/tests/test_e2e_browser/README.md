# E2E browser tests (Agent 5 verification gate)

Playwright + headless Chromium tests that boot the REAL stack (simulator,
MCS, planner — `configs/eosat1`, `--ui modern`) and drive the modern pages
in a browser.

They are **excluded from the default test run**:

- marked `@pytest.mark.e2e` (registered in `pyproject.toml`);
- skipped unless the environment sets `SMO_E2E=1`.

Run them with:

```bash
SMO_E2E=1 PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers \
    .venv/bin/python -m pytest tests/test_e2e_browser -q
```

Requirements: a working `.venv` with the SMO packages plus `playwright`,
and a Playwright Chromium install (do NOT run `playwright install` on the
verification container — the browsers are pre-provisioned under
`/opt/pw-browsers`). The suite binds 127.0.0.1 ports 8080/8001/8002 (sim),
9090 (MCS) and 9091 (planner); nothing else may hold them.

`conftest.py` marks **every** test in this directory `e2e` and skips it
unless `SMO_E2E=1`, so nothing here can run in the default or parallel tier.

The two legacy modules, `test_full_mission_validation.py` and
`test_leop_commissioning.py`, drive the **classic** console (`#tab-commanding`,
`#cmd-send-btn`) through the RF bridge. Their `system_stack` fixture starts
every server with `--ui classic` and resolves the console scripts next to
`sys.executable`, so no activated venv is needed. They are also marked
`legacy_ui`: `-m "e2e and not legacy_ui"` runs the modern suite only.
See `docs/TESTING.md` at the repository root.

`inventory_checklist.md` in this directory is the Report-1 functional
inventory transcription — the acceptance checklist for the modern UI.
