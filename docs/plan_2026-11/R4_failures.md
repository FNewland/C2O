# R4 — Failure triage and fix plan (C2O, 2026-10-30)

Scope: `sim/` full-suite log `rulings/S_full_suite.txt` (59 failed, 36 errors, 1847 s), `design/` pytest (27 errors), `design/frontend` `tsc -b` (104 errors). The repo was not modified. Individual files were re-run. The full suite was not run.

Side effects of this triage:
- `tools/procedure_audit.py` wrote `sim/workspace/audit/procedure_audit.{json,html}`. That path is gitignored.
- `design/tests/test_level_workbench.py` ran against the live SpaceCDF server on :8000 (pid 378, another worker's). The fixture created and then deleted one "Test Mission" study.

## 0. Headline findings

1. **Real regression in the modern MCS console.** Commit `bb09265` ("Final update pre-dry-run Aug20") replaced `smo-mcs/static/modern/mcs.js` with a copy taken from before the 2026-08-19 ruling. That ruling deleted the training layer and moved the capture gates and baselines to `/api/display-config`. The regression causes 14 test failures and these live defects:
   - The NOM-002 capture-readiness card and the G15 baseline-health card read `S.annotations`. `/api/annotations` now always serves `{}`, so both cards are **always "unavailable"** (`mcs.js:1565`, `:1960`).
   - **The safe-mode banner bug M8 is back.** `scModeInfo()` reads `0x0700` (that is `fdir.level`) as the spacecraft mode (`mcs.js:404-409`). FDIR-quiet therefore decodes as NOMINAL even in SAFE.
   - The client-side missing-argument length gate (`catLengthError`) is gone. The HK-enable-reset summary (`hkEnableSummaryHtml`) is gone. The GUIDED toggle has come back (24 refs in `mcs.js`, plus `guided-btn` in `modern/index.html`).
2. **Several negative tests pass without checking anything.** The MagicMock engine doubles do not provide the new `param_visibility` / `pack_tm_segmented` API, so every S20.3 / S12.12 / S19.8 / S11.17 dispatch returns `[]`. The "positive" tests fail. But the **"blocked" link-gating tests (`test_s20_get_blocked_out_of_contact`, `_link_failed`) pass without testing anything**, so the out-of-contact TM-leak protection currently has no live test.
3. **The telemetry-realism cleanup (`d99c9e2`, 2026-08-20) was only half-finished.** Parameters were reclassified `ground_derived` / `instructor`, but the following still point at them:
   - two S19 rules that can now never fire (4001, 4003);
   - three ground limit bands on parameters the ground never receives;
   - 87 procedure references.
   About 13 failures are spread over gates that do not know about `visibility:`.
4. **Four failures in the log are already fixed** by later edits from the rulings worker. They pass on re-run: config_integrity procedures count, required positions, config_validation NOM-014 `eps`, and the eclipse geometry check. **Live sim failures today: 55 + 36 errors.**
5. **`tools/vr_stub/vr_stub.py` really is missing.** It was never committed: the Mac snapshot `8d13339` carried the README, the CSV and the Unity client only. `sample_vr_frames.ndjson` is missing too. No copy exists anywhere on this machine (`spacemissionsimulator/`, `c2o_build/`, `work/` were all checked). The collection error hides **29 tests** that have not run since the body-frame ruling (+Z zenith), so expect new failures once the stub is restored.
6. **Design: the 27 errors come from a live-server test, not a seed bug.** They are `httpx.ConnectError` to `localhost:8000`. The "seed_parameter_definitions failed" message is from an older checkout (`/home/claude/work/cdf`, which was missing `reference_data_library.json`). That file exists in C2O. With a server up, all 27 pass.

## 1. Every failure — sim

Class key: **BUG** = real product bug, **STALE** = stale test (behaviour changed on purpose), **SNAP** = stale artefact or snapshot, **ENV** = environment or missing file, **FLAKY** = flaky or timing, **INFRA** = test infrastructure, **FIXED** = passes now.

### G1 — Legacy browser E2E (35 errors) · INFRA + STALE

| Tests | Cause | Fix | Eff. | Risk |
|---|---|---|---|---|
| `test_e2e_browser/test_full_mission_validation.py` — all 14 (`test_pass01…pass13`, `test_final_report`) | `system_stack` fixture spawns bare `"smo-simulator"`, `"smo-rfsim"`, `"smo-mcs"`, `"smo-planner"`, `"python"`. pytest was run as `.venv/bin/python -m pytest` without an activated venv, so the names are not on PATH. Unlike `test_modern_ui.py:34-37`, these two modules have **no `e2e` marker and no `SMO_E2E` skip**, so they run in the default suite. They also drive the *legacy* UI (`#tab-commanding`, `#cmd-send-btn`) and the RF bridge, while the MCS now defaults to the modern UI. | (a) Gate them: in `tests/test_e2e_browser/conftest.py` add `pytest_collection_modifyitems` that marks every item in the directory `e2e` and skips unless `SMO_E2E=1`. Or add `pytestmark` to both modules (after the imports, ~line 19). (b) Resolve binaries via `Path(sys.executable).with_name(...)` and use `sys.executable` for `python` (`conftest.py:69,91,102,115,123,132`). (c) Author decision: retire both modules (superseded by `test_modern_ui.py`), or port them to `/classic` with `--ui classic`. | S (gate) / L (revive) | Low (gate). Ports 8001/8002/8080/9090 collide with workers running the apps, so these must never run in the default tier. |
| `test_e2e_browser/test_leop_commissioning.py` — all 21 (`test_00…test_63`) | Same | Same | S / L | Same |

### G2 — VR bridge (1 collection error, hides 29 tests) · ENV

| Test | Cause | Fix | Eff. | Risk |
|---|---|---|---|---|
| `test_simulator/test_vr_bridge.py` (collection) | `tools/vr_stub/vr_stub.py` and `sample_vr_frames.ndjson` were never committed. The module loads the stub at import time (`test_vr_bridge.py:30-38`), so the whole file errors. | Recover both files from Franz's Mac (`tools/vr_stub/`, check a global gitignore) and commit them. Make stub loading a module fixture that `pytest.skip`s if the file is missing, so the 13 frame-builder and health tests still run. If unrecoverable, rewrite the stub against `docs/VR_INTERFACE_ICD.md` (M). | S (recover) / M (rewrite) | Medium: 29 tests are unseen since the +Z-zenith body-frame ruling, so expect follow-up failures. VR student teams develop against this stub. |

### G3 — MagicMock engine doubles do not know the new dispatcher API (14 failures) · STALE (test doubles)

Root causes:
- S20.3 now refuses any parameter whose `engine.param_visibility(pid) != "real"` (`service_dispatch.py:3073-3089`). On a `MagicMock` that call returns a mock, so every read is refused.
- S11.17, S12.12 and S19.8 now return `engine.tm_builder.pack_tm_segmented(...)` (`service_dispatch.py:2255`, `:2349`, `:2973`). On a mock builder that is a MagicMock with `len() == 0`.

| Test | Fix | Eff. |
|---|---|---|
| `test_simulator/test_tc_dispatch.py::TestServiceDispatcher::test_s20_get_param` | Add a shared helper `wire_mock_engine(engine)` to `tests/conftest.py` that sets `engine.param_visibility = lambda pid: "real"` and binds `engine.tm_builder.pack_tm_segmented = TMBuilder.pack_tm_segmented.__get__(engine.tm_builder)` (the real method calls `self._pack_tm`, which the mock already stubs). Call it from `make_mock_engine` in `test_tc_dispatch.py:7`, `test_end_to_end.py:18`, `test_mission_scenarios.py:16`, `test_s12_s19_integration.py:23`, and from the `mock_engine` fixture in `tests/conftest.py`. | S |
| `test_simulator/test_s12_s19_integration.py::TestS12Report::test_s12_report_subtype_12`, `TestS19Report::test_s19_report_subtype_8`, `TestS19Report::test_s19_report_empty` | Same helper | S |
| `test_integration/test_end_to_end.py::TestS20ParamSetReadFlow::test_s20_param_set_read`, `TestS19ReportDefinitions::test_s19_report_definitions`, `TestS12ReportDefinitions::test_s12_report_definitions`, `TestS11ScheduleList::test_s11_schedule_list` | Same helper | S |
| `test_integration/test_mission_scenarios.py::TestMonitoringScenario::test_report_monitoring_definitions`, `TestEventActionScenario::test_report_all_definitions`, `TestSchedulingScenario::test_schedule_insert_and_list`, `TestParameterManagementScenario::test_set_then_read_parameter` | Same helper | S |
| `test_simulator/test_link_gating.py::TestOnDemandTMLeak::test_s20_get_allowed_contact_and_link_ok`, `::test_s20_get_allowed_override` | These use `MagicMock(spec=SimulationEngine)` (`:500`, `:541`, …), so set `engine.param_visibility = lambda pid: "real"` in each, or in a local factory. **Also add `assert responses` before the enqueue loop in the two "blocked" tests**, so they cannot pass with nothing to block. | S |

Risk: low to change. **High value**, because it restores real link-gating regression protection.

### G4 — S12/S19 report segmentation and the 46→41 monitor count (10 failures) · STALE

Two deliberate changes broke these tests:
- `d99c9e2` removed 5 S12 monitors on ground-only parameters: rssi, link_margin, eb_n0, ber, snr. The count went from 46 to 41.
- Commit 2026-08-21 segments "report all" packets on the CCSDS grouping flags. TM(12,13) is now 3 packets.

| Test | Cause | Fix | Eff. |
|---|---|---|---|
| `test_simulator/test_pus_service_fixes.py::TestS12Definitions::test_every_config_definition_is_registered` | Asserts 46 | `test_pus_service_fixes.py:95`: 46 → 41. Better, derive the count from `len(loaded)` and update the docstring. | S |
| `…::TestS12DefinitionReport::test_report_carries_mon_id_param_id_and_enable_state` | Asserts 1 packet. There are now 3 segments. | `:250`: assert `len(responses) >= 1`, then reassemble (see below) | S |
| `test_simulator/test_s12_report_definitions.py::test_report_carries_every_configured_definition`, `::test_report_decodes_with_the_shared_ground_decoder`, `::test_report_matches_the_on_board_table` (KeyError 32784), `::test_report_tracks_an_added_definition` | The `_tm()` helper (`:43-50`) returns only the **first** segment's data field, which holds 16 of 41 records. | Rewrite `_tm` to concatenate the records of every (12,13) segment: strip each segment's u16 count, sum the counts and rebuild one body. Better still, call the MCS `_reassemble_report` logic so the test proves the ground path. | S |
| `test_mcs/test_fdir_window.py::TestFDIRModelReference::test_config_reference_is_the_starting_table` | Asserts 46 rows | `test_fdir_window.py:72`: 46 → 41 (or `len(load_s12_definitions(...))`) | S |
| `…::TestServerTelemetryPath::test_s12_13_populates_the_monitor_table`, `::test_s19_128_populates_the_rule_table`, `::test_the_legacy_endpoint_stops_reporting_zero_rules` | The `_pkt()` helper (`:36-44`) is a MagicMock with no `primary.sequence_flags`. `server._reassemble_report` (`server.py:1651-1666`) treats it as a continuation without a first segment and discards it, so the config-seeded table (41 monitors, 31 rules) stays. | `test_fdir_window.py:41`: add `p.primary.sequence_flags = 0b11`. Add one new test that feeds a 01/00/10 segment triple. | S |

Risk: low.

### G5 — Telemetry-realism follow-through (`d99c9e2` and the `visibility:` classes) (13 failures)

| Test | Class | Cause | Fix | Eff. | Risk |
|---|---|---|---|---|---|
| `test_commissioning_sequence.py::TestEngineIntegrity::test_link_margin_in_sid6` | STALE | `ttc.link_margin` 0x0503 is now `visibility: ground_derived` and was removed from SID 6 on purpose | `test_commissioning_sequence.py:925-931`: invert it to assert 0x0503 is **not** in any SID and is `ground_derived` | S | Low |
| `test_mcs_hk_round_trip.py::test_sid7_aocs_determination_round_trip` | STALE | `aocs.fidelity_mode` 0x02C6 (instructor) was removed from SID 7 | `:140`, `:155`: drop 0x02C6 from the inputs and the asserts. Optionally assert it is absent from the SID 7 structure. | S | Low |
| `test_planner/test_rate_ladder_budget.py::TestPerActivityRateSplit::test_housekeeping_is_a_channel_cost_at_the_routine_rung` | SNAP | The HK stream pin of 1699.5 bps predates the SID cleanup. It is now **1587.7 bps** (−112 bps). | `:201`: re-pin to 1587.7 and add a history comment for the 2026-08-20 removals. Check the 10%-of-LOW claim still holds (it does: ≈9.9%). | S | Low. Planner docs and the textbook quoting "~1696 bps" may need the same update. |
| `test_content/test_parameter_chain.py::test_every_parameter_is_reachable` | STALE | 33 "unreachable" parameters = 24 `instructor` + 9 `ground_derived`. The gate ignores `visibility:`. | `test_parameter_chain.py:49`: treat `p.get("visibility","real") != "real"` as legitimately not downlinked. Add a separate assert that no non-real parameter is in an HK SID. | S | Low |
| `…::test_every_limited_parameter_is_reachable` | BUG (config) | `mcs/limits.yaml` still bands `0x050C ttc.ber`, `0x051A ttc.agc_level` (ground_derived) and `0x0616 payload.snr` (instructor). The ground limit checker never sees them. | **Needs a ruling.** Either the MCS computes BER/AGC from the ground receiver (rfsim) and checks the band on that derived value, or delete the bands (`limits.yaml:74`, `:79`, `:114`). Delete the snr band either way, since it is instructor-only. | S once ruled | Low |
| `test_mcs/test_ground_limits_and_archive.py::test_every_shipped_band_reaches_the_alarm_journal[0x050C]`, `[0x051A]`, `[0x0616]` | BUG (config) | Same three bands | Same fix | (incl.) | Low |
| `…::test_ground_only_parameters_are_the_ones_with_no_s12_definition` | SNAP | The ground-only set grew from 31 to 33 because of the S12 monitors removed in `d99c9e2` | `:173`: re-pin after the limits ruling (31 if the ber/agc bands go). Update the list and docstring. | S | Low |
| `test_content/test_s19_rules_content.py::test_rule_trigger_resolves_in_its_declared_namespace[4001]`, `[4003]` | **BUG** | S19 rules 4001 (link margin → TX boost) and 4003 (BER → TX boost) trigger on 0x0503 / 0x050C. The spacecraft has no S12 monitor on either, and physically cannot measure them, so **these autonomy rules can never fire**. | **Needs a ruling.** Delete both rules, or retrigger them on something the spacecraft can observe: uplink-lock loss, the 24 h command-loss timer, or an onboard RSSI if one is added. Edit `configs/eosat1/monitoring/s19_rules.yaml:144-170`, then check `08_fdir.md` (EN+FR) and the FDIR window. | S once ruled | Medium: this touches the FDIR teaching narrative |
| `test_content/test_procedure_audit_gate.py::test_the_procedure_audit_is_clean[PARAM_NOT_REACHABLE]` | STALE tool + BUG content | 87 findings. 74 are `ground_derived` parameters, which are legitimately visible on the ground. **13 are `instructor`-only parameters that procedures tell operators to read**: `payload.snr` ×4, `payload.last_scene_quality` ×4, `prop.leak_rate` ×2, `prop.sma_km` ×2, `prop.orbit_epoch_version`, `aocs.css_head_health_py`, `aocs.gyro_bias_injected`. | (1) `tools/procedure_audit.py:524`, `:539`: treat `ground_derived` as reachable and add a new category `PARAM_INSTRUCTOR_ONLY` for `instructor`. (2) Edit the procedures that cite instructor parameters, in EN and FR, to use the observable they should diagnose from. | M | Medium: content edits in two languages |
| `…::test_no_uncategorised_finding_escapes_the_gate` | INFRA + content | The audit now emits `HK_SID_MISMATCH` (28 findings in 12 procedures, e.g. `ttc_link_verification.md` and `ber_anomaly.md` say "request SID 6, verify rssi/link_margin/ber/eb_n0"). The gate's `CATEGORIES` list does not include it. | `test_procedure_audit_gate.py:37`: add `HK_SID_MISMATCH` (and `PARAM_INSTRUCTOR_ONLY`). Rewrite those steps to read the ground-derived values from the TT&C/radio page instead of requesting SID 6 (EN+FR). | S (gate) + M (content) | Medium |

### G6 — Modern MCS console regression from `bb09265` (14 failures) · **BUG (regression)**

`cff5046` (Aug 19 19:53) had these features. `bb09265` (Aug 20 07:29) rewrote `mcs.js` (+188/−337) from a divergent copy, and they disappeared. Server-side support is still present: `/api/display-config` (`server.py:4641`) and `/api/annotations` returning `{}` (`server.py:4629-4639`).

| Test | Missing behaviour |
|---|---|
| `test_mcs/test_missing_argument_client_gate.py::TestLengthGate::test_bare_func_id_is_a_length_error_naming_the_field`, `::test_multi_field_command_names_the_first_missing_field`, `::test_send_command_refuses_and_posts_nothing`, `::test_send_command_still_sends_the_correct_form` | `catLengthError()`, plus the length gate inside `sendCommand`, plus `sendCommand` in `__test` |
| `test_mcs/test_modern_page_behaviour.py::TestSaHeader::test_sc_mode_provenance_prefers_tm` | `fdirLevelInfo()`. Linked to `scModeInfo` reading 0x0700 as the mode (**M8 safe-mode banner bug is back**, `mcs.js:404-409`; fix it to read obdh.mode 0x0300 first). |
| `…::TestDisplayConfigClient::test_table_accessors_tolerate_missing_or_malformed_config` | `S.displayConfig` is never fetched. `captureGateTable` and `baselineTable` read `S.annotations` (`mcs.js:1565`, `:1960`). |
| `…::TestCaptureReadiness::test_all_gates_met_is_go`, `::test_one_failing_gate_is_nogo`, `::test_missing_telemetry_is_unknown_not_go` | Same cause. **In production the NOM-002 capture card is always "unavailable".** |
| `…::TestBaselineHealth::test_drift_computed_and_flagged_over_5pct`, `::test_zero_baseline_flags_on_absolute_delta`, `::test_missing_tm_is_no_tm_not_zero_drift` | Same cause. The G15 baseline card is always "unavailable". |
| `…::TestStaticContracts::test_training_layer_fully_retired` | The GUIDED layer is resurrected: `guided-btn`, `data-ann`, `data-guided` in `modern/index.html` and `mcs.js`. This goes against the 2026-08-19 ruling to delete the training layer. |
| `test_mcs/test_hk_enable_reset_visibility.py::test_console_renders_the_enable_set_and_the_reason` | `hkEnableSummaryHtml()` (the console half of the HK-enable-reset record) |

**Fix:** port the missing functions from `git show cff5046:sim/packages/smo-mcs/src/smo_mcs/static/modern/mcs.js`. Do **not** revert the file, because it carries `sendPus`, procedure cards, segment handling and the 558b202 rulings. Steps:
1. Add `displayConfig` to `S`, fetch `/api/display-config` in boot, and repoint `captureGateTable` and `baselineTable` at it.
2. Restore `catLengthError` and wire it into `sendCommand`.
3. Restore `fdirLevelInfo` and fix `scModeInfo`.
4. Restore `hkEnableSummaryHtml` and its render site.
5. Strip the GUIDED layer from `mcs.js` and `index.html`.
6. Extend `__test`.
7. Add FR i18n strings for any restored text.
8. Verify with `SMO_E2E=1 … tests/test_e2e_browser/test_modern_ui.py`.

Effort **M–L** (½–1 day). Risk **medium**: a 5,094-line file, and both lineages carry operator-visible fixes. Diff `bb09265^` against HEAD function by function.

### G7 — Modern UI static contracts (3 failures) · SNAP / STALE

| Test | Class | Cause | Fix | Eff. |
|---|---|---|---|---|
| `test_content/test_modern_inventory.py::test_route_snapshot_is_current` | SNAP | New route `/api/procedure/cards` (`server.py:1442`, from `ed2d82c`) is not in `MCS_ROUTES` | Append it to `MCS_ROUTES` (`test_modern_inventory.py:64-…`) | S |
| `…::test_every_modern_js_api_path_has_a_route[mcs]` | SNAP | Same. The JS-path check resolves against the snapshot. | Same one-line fix | (incl.) |
| `test_mcs/test_pus_command_payload_contract.py::test_every_modern_pus_payload_uses_data_hex` | STALE | All PUS sends now go through one wrapper, `sendPus(body)` → `postJSON("/api/pus-command", b)` (`mcs.js:2649-2651`). The regex at `:33` wants an object literal. | Scan `sendPus\(\s*\{` call sites instead, and assert the wrapper forwards `data_hex` | S |

### G8 — Config counts (4 in log; 3 already fixed)

| Test | Class | Cause / status | Fix | Eff. |
|---|---|---|---|---|
| `test_common/test_config_integrity.py::TestManualFilesExist::test_manual_directory_has_expected_count` | STALE (pre-existing) | 20 files vs 19. `manual/commissioning_walkthrough_changelog.md` was added in `d99c9e2`. | Move the changelog out of `manual/` (it is not operator manual content; FR mirror too), or set `EXPECTED_MANUAL_FILE_COUNT = 20` (`:47`) | S |
| `…::TestAllDiskProceduresAreIndexed::test_expected_total_procedure_files` | FIXED | Test updated to 70 after the log (NOM-014, CTG-029, CTG-030) | — | — |
| `…::TestRequiredPositionsAreValid::test_required_positions_reference_valid_names` | FIXED | NOM-014 now uses `eps_tcs` | — | — |
| `test_common/test_config_validation.py::test_procedure_positions_reference_valid_positions` | FIXED | Same | — | — |
| `test_simulator/test_eclipse_single_authority.py::test_true_eclipse_geometry_at_the_current_epoch` | FIXED | Re-pinned after the 97.39° inclination ruling | — | — |

No failures were classed FLAKY. All re-runs reproduced deterministically.

## 2. Design (SpaceCDF) pytest — 27 errors · INFRA

| Tests | Cause | Fix | Eff. | Risk |
|---|---|---|---|---|
| `design/tests/test_level_workbench.py` — all 27 (`TestLevel0Mission…TestLevel3Verification`) | This is a **live-server** integration test: `httpx.Client` to `localhost:8000/api` (`:11-22`). It sits in the default `testpaths`, so it errors with ConnectError when no uvicorn is running. Verified today: **27/27 pass** against a running server. The "seed_parameter_definitions failed" log line came from an old checkout missing `reference_data_library.json`. That file is present in C2O (`spacecdf-kb/src/spacecdf_kb/data/`). | Short term: add `pytestmark = pytest.mark.live_server` plus a module-level skip when `BASE` is unreachable. Proper fix: convert to the in-process `AsyncClient(transport=ASGITransport(app))` pattern already used in `tests/test_api/conftest.py:17-26`, and drop the network dependency. | S (skip) / M (convert) | Low. While unconverted, it writes into whatever DB the :8000 server uses. |

## 3. SpaceCDF frontend — 104 `tsc -b` errors

`vite build` alone succeeds (`D_vite.txt`). Only the `tsc -b` step of `npm run build` fails. 53 files are affected.

| Category | Count | Nature | Effort |
|---|---|---|---|
| TS6133 / TS6192 unused locals, params, imports (`noUnusedLocals` / `noUnusedParameters` in `tsconfig.app.json:19-20`) | 83 | Mechanical: delete, or prefix with `_` | S (1–2 h) |
| **TS2304 cannot find name** `requirements`: `MissionDashboard.tsx:330`, `:354`, `:357` | 3 | **Runtime ReferenceError** when the mass/cost gauges render. Real bug. | S |
| TS2339 / TS2551 schema drift: `MissionRequirements` has no `num_spacecraft` (`ConstellationDesigner.tsx:36`, `Phase1MissionArch.tsx:31`) and no `payload` (should be `payloads`; `ConstraintViolationsPanel.tsx:67`) | 5 | The values are always undefined, so the UI silently uses fallbacks. Real bug, minor. | S–M |
| TS18047 / TS18046 / TS2571 null and unknown: `ExportsPanel.tsx:149` (`el.performance` may be null, so a possible crash), `SystemBudgetEditor.tsx:389` | 5 | Real or possible runtime errors | S |
| TS7006 / TS7053 implicit any: `HierarchicalDesigner.tsx:479`, `:480`, `:761`; `SystemBudgetEditor.tsx:176` | 4 | Typing only | S |
| Other: TS2739 `useActiveParameters.ts:37` (`DesignParam` missing `source`/`domain`); TS2488 `modelStore.ts:241`; TS2339 `RequirementsEditor.tsx:121` `_originalId`; TS2339 `BlocksPanel.tsx:172` (level 4 is not in the level→type map, so it silently becomes `system`) | 4 | Type and real mismatches | S–M |

Top files: `SystemBudgetEditor.tsx` 9, `EquipmentBrowser.tsx` 5, `BOMView.tsx` 5, `App.tsx` 5, `workbench/DecisionPanel.tsx` 4, then 3 each in `SystemBlockDiagram`, `RequirementsPanel`, `ProjectManagement`, `PositionAnswersPanel`, `MissionDashboard`, `HierarchicalDesigner`, `ExportsPanel`, `DesignWorkspace`, `ConstellationDesigner`, `ConOpsEditor`.

**Reaching a zero-error build takes about M (≈1 day):** about 2 h for the unused items and 3–5 h for the 21 typed errors. Fix the real bugs first: MissionDashboard, ExportsPanel, schema drift. Interim option: `"build": "vite build"` plus a separate `"typecheck": "tsc -b"` CI job that is allowed to fail until it reaches zero.

## 4. Summary by class (sim today: 55 F + 36 E; design 27 E; tsc 104)

| Class | Sim | Design | Notes |
|---|---|---|---|
| Real product bug or regression | **21 F**: 14 (G6 mcs.js) + 6 (G5: limited-param gate 1, band-to-journal 3, S19 rules 2) + 1 (audit PARAM_NOT_REACHABLE: tool is stale, but 13 instructor-only references are real content defects) | 0 | Plus live MCS defects with no failing test of their own (M8 banner via `scModeInfo`) and about 12 real TS bugs |
| Stale test (deliberate change) | **29 F**: 14 (G3) + 10 (G4) + 3 (G5: SID 6, SID 7, parameter chain) + 1 (G7 sendPus) + 1 (G8 manual count) | 0 | |
| Stale snapshot or pin | **4 F**: rate-ladder bps, ground-only set, route snapshot ×2 | 0 | |
| Environment or missing file | **1 E** (vr_stub, hiding 29 tests) | 0 | |
| Test infrastructure | **35 E** (E2E gating, bare executables) + **1 F** (audit gate category list) | **27 E** (live server) | |
| Flaky / timing | 0 | 0 | |
| Already fixed since log | 4 F | — | 55 + 4 = the 59 in the log |

## 5. Recommended fix order

1. **Unblock and de-noise (S each, ≈½ day total, low risk):**
   - G1 gating plus `sys.executable` paths;
   - design `live_server` skip;
   - G3 shared mock helper, plus a non-empty assert in the "blocked" link-gating tests;
   - G4 (`sequence_flags`, segment reassembly, 41);
   - G7 (route snapshot, sendPus regex);
   - pins: SID 6, SID 7, 1587.7 bps, manual count, `HK_SID_MISMATCH` category, `visibility`-aware parameter-chain gate.

   This alone turns about 45 of the 91 sim failures green.
2. **Recover `vr_stub.py` and `sample_vr_frames.ndjson` from the Mac**, make stub loading lazy, then triage whatever the 29 tests reveal.
3. **Restore the mcs.js regression (G6).** It has the highest product impact: the safe-mode banner, the capture and baseline cards, and the client length gate. Verify with the `SMO_E2E=1` modern-UI suite.
4. **Author rulings, then config and content (G5):**
   - S19 4001/4003;
   - ground limit bands on BER/AGC/SNR;
   - procedure steps citing instructor-only parameters and the SID 6 "verify rssi" steps, in EN and FR;
   - `procedure_audit.py` visibility awareness;
   - retire or port the legacy E2E modules.
5. **Frontend to zero tsc errors:** real bugs first, then unused.
6. **CI tiers (§6),** then convert `test_level_workbench` to ASGITransport.

## 6. Why the suite is slow, and the tier and CI plan

**Measurements (this container, 2 cores, shared with running apps):**

| Slice | Tests | Wall |
|---|---|---|
| `test_content` + `test_common` | 2,446 | **75 s** |
| `test_acceptance`, `test_commissioning`, `test_failure_clear_each`, `test_link`, `test_integration` | 654 | 323 s |
| `test_mcs` + `test_planner` + `test_rfsim` | 2,492 | 492 s |
| remainder (`test_simulator` 1,895 + top-level files), by subtraction from 1,847 s | ~2,150 | ~960 s |

**Causes:**
- **Strictly serial run.** `pytest-xdist` is not installed. Most socket tests already bind port 0, so the suite is parallel-friendly.
- **About 100 `SimulationEngine` boots at ≈0.4 s each**, often in function-scoped fixtures (17 function-scoped versus 7 module-scoped `engine` fixtures in `test_simulator`). Many tests then tick hundreds of seconds of sim time; there are 544 tick-loop sites.
- **RF DSP tests:** `test_rfsim/test_blind_receiver.py` alone takes about 150 s. `test_batch_rate_switch_mid_pass` is 66 s, `test_batch_safe_rate_long_frames` 25 s, and `test_rf_impairments … evm` 14 s.
- **Full-system flythroughs:**
  - `test_commissioning_rf` 16 s;
  - the LEOP/commissioning flythrough about 25 s;
  - link e2e about 35 s;
  - fly-a-plan about 25 s;
  - memory profile 12 s.
- **Node subprocess per JS-harness test** (14 files). Each one re-reads and rewrites `mcs.js`.
- **Only 9 tests carry `@pytest.mark.slow`.** The rest of the slow tail is unmarked.
- The earlier 60-minute run versus 31 minutes today is machine load (other workers running the apps), not the suite.

**Tiers:**
- **fast:** `-m "not slow and not rf_dsp and not e2e and not link_e2e and not live_server"`
  - Mark by path in a root `conftest.py` `pytest_collection_modifyitems`: `rf_dsp` for `test_rfsim/test_blind_receiver.py` and `test_rf_impairments.py`; `slow` for `test_acceptance/`, `test_planner/test_fly_a_plan.py`, `test_integration/test_commissioning_rf.py`, `test_acceptance/test_memory_profile.py`; `live_server` for design `test_level_workbench.py`.
  - Promote function-scoped engine fixtures to module scope where tests do not mutate state.
- **slow:** `-m "slow or rf_dsp or link_e2e"`
- **e2e:** `SMO_E2E=1 -m e2e` (Playwright modern UI), plus the design live-server workbench test against a uvicorn started in the job.

**GitHub Actions** (public repo, free standard runners: ubuntu-latest 4 vCPU):

| Workflow / job | Trigger | Contents | Budget |
|---|---|---|---|
| `ci.yml` › `sim-fast` | push, PR | Python 3.13, `pip install -e` the sim packages + pytest-xdist + pytest-timeout (`--timeout=120`), `pytest -n auto -m "<fast expr>" --durations=25`; Node 22 present for the JS harness | **≤ 8 min** (≈1,350 s serial over 4 workers ≈ 6 min + install) |
| `ci.yml` › `design-fast` | push, PR | `pytest -n auto -m "not live_server"` in `design/` | ≤ 4 min |
| `ci.yml` › `frontend` | push, PR | `npm ci && npx tsc -b && npx vite build` (tsc `continue-on-error` until zero) | ≤ 3 min |
| `ci.yml` › `sim-slow` | push to main, nightly cron | `-n auto -m "slow or rf_dsp or link_e2e"` | ≤ 15 min |
| `e2e.yml` | nightly, `workflow_dispatch`, release tags | `playwright install --with-deps chromium`, `SMO_E2E=1 pytest tests/test_e2e_browser -m e2e`; uvicorn on :8000 for the design live test; upload screenshots as artifacts | ≤ 20 min |
| `ci.yml` › `windows-smoke` (optional) | weekly | `windows-latest`, start-up and encoding smoke subset (the defect-134 class) | ≤ 10 min |

Caching: `actions/setup-python` pip cache keyed on each `pyproject.toml`, and npm cache on `package-lock.json`. Concurrency group per ref with cancel-in-progress. The required check on PRs is `sim-fast`, `design-fast` and `frontend` (`frontend` once tsc reaches zero).
