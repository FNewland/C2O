"""One derivation of contact, mode, freshness and alarm counts (R3 #10, A3-A5).

* ``smo_common/ui/state.js`` — linkState / modeState / freshness /
  linkLimited, pure functions every console can import;
* the MCS alarm store — de-duplication (×N, last occurrence) and ONE summary
  that feeds the header, rail, FDIR page and drawer;
* the value cell — stale keeps the last value with its age, never-received
  reads "no data";
* the procedure buttons follow the runner's state machine, with reasons.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.test_mcs.test_modern_page_behaviour import run_js, requires_node

REPO = Path(__file__).resolve().parents[2]
STATE_JS = REPO / "packages/smo-common/src/smo_common/ui/state.js"
NODE = shutil.which("node") or shutil.which("nodejs")


def state_js(snippet: str, tmp_path: Path):
    mod = tmp_path / "state.mjs"
    mod.write_text(STATE_JS.read_text(encoding="utf-8"))
    run = tmp_path / "run.mjs"
    run.write_text(f'import * as S from "./state.mjs";\n'
                   f'const out = (() => {{ {snippet} }})();\n'
                   f'console.log(JSON.stringify(out));\n')
    p = subprocess.run([NODE, str(run)], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout)


@requires_node
class TestStateModule:
    def test_freshness_four_states(self, tmp_path):
        out = state_js("""
            return [S.freshness(undefined), S.freshness(null), S.freshness(5, {intervalS: 4}),
                    S.freshness(15, {intervalS: 4}), S.freshness(25, {intervalS: 4}),
                    S.freshness(50, {intervalS: 60}), S.freshness(100, {intervalS: 60}),
                    S.freshness(400)];
        """, tmp_path)
        assert out == ["nodata", "nodata", "fresh", "degraded", "stale",
                       "fresh", "stale", "degraded"]

    def test_stale_frame_lock_is_not_contact(self, tmp_path):
        """The audit's contradiction: header IN CONTACT from a frame-lock
        value left over from the last pass, overview NO CONTACT."""
        out = state_js("""
            const old = { in_contact: false, params: {"0x0512": 1}, params_age: {"1298": 400} };
            const live = { in_contact: false, params: {"0x0512": 1}, params_age: {"1298": 2} };
            const gnd = { sa: { in_contact: true, ground_station_name: "Troll",
                          last_frame_age_s: 1 }, params: {} };
            return [S.linkState(old), S.linkState(live), S.linkState(gnd)];
        """, tmp_path)
        assert out[0]["contact"] is False and out[0]["source"] == "none"
        assert out[1]["contact"] is True and out[1]["source"] == "TM frame lock"
        assert out[2]["contact"] is True and out[2]["gs"] == "Troll"
        assert out[2]["tm"] == "fresh"

    def test_mode_never_reads_fdir_level_as_mode(self, tmp_path):
        out = state_js("""
            return [S.modeState({ params: {"0x0700": 3} }),
                    S.modeState({ params: {"0x0300": 1, "0x0700": 0} }),
                    S.modeState({ params: {"0x0300": 0, "0x0700": 2} }),
                    S.modeState({ sc_mode: "safe", params: {} }, { trainingTruth: true })];
        """, tmp_path)
        assert out[0]["mode"] is None and out[0]["fdirLevel"] == 3
        assert out[0]["contingency"] is True
        assert out[1]["mode"] == "SAFE" and out[1]["source"] == "TM obdh.mode 0x0300"
        assert out[2]["mode"] == "NOMINAL" and out[2]["contingency"] is True
        assert out[3]["mode"] == "SAFE" and out[3]["source"] == "SIM (training)"

    def test_link_limited_only_when_fast_and_in_contact(self, tmp_path):
        out = state_js("""
            const st = (speed, age, c) => ({ sa: { speed, last_frame_age_s: age, in_contact: c } });
            return [S.linkLimited(st(60, 90, true)).limited, S.linkLimited(st(1, 90, true)).limited,
                    S.linkLimited(st(60, 5, true)).limited, S.linkLimited(st(60, 90, false)).limited];
        """, tmp_path)
        assert out == [True, False, False, False]


@requires_node
class TestAlarmStore:
    FIX = """
        T.S.alarms = [
          { id: 1, timestamp: 100, subsystem: "ttc", severity: 3, parameter: "0x053B",
            name: "ttc.tm_symbol_rate", value: "1000.0", units: "Bd",
            limit: "YELLOW_LOW < 16000.0", limit_status: "yellow_low", acknowledged: false,
            procedure: { id: "CTG-003", name: "TTC Link Loss Recovery", file: "contingency/ttc_link_loss.md" } },
          { id: 2, timestamp: 400, subsystem: "ttc", severity: 3, parameter: "0x053B",
            name: "ttc.tm_symbol_rate", value: "900.0", units: "Bd",
            limit: "YELLOW_LOW < 16000.0", limit_status: "yellow_low", acknowledged: false },
          { id: 3, timestamp: 300, subsystem: "aocs", severity: 4, parameter: "0x0275",
            name: "aocs.gps_pdop", value: "99.9", limit: "RED_HIGH > 6.0",
            limit_status: "red_high", acknowledged: true },
        ];
    """

    def test_dedup_counts_and_one_summary(self, tmp_path):
        out = run_js(self.FIX + """
            const g = T.alarmGroups();
            const s = T.alarmSummary();
            return { n: g.length, ttc: g.find(x => x.parameter === "0x053B"),
                     s: { active: s.active, unacked: s.unacked, alarm: s.alarm, warn: s.warn,
                          ttc: s.bySub.ttc, aocs: s.bySub.aocs } };
        """, tmp_path)
        assert out["n"] == 2
        assert out["ttc"]["count"] == 2 and out["ttc"]["last_ts"] == 400
        assert out["ttc"]["ids"] == [2, 1] and out["ttc"]["pri"] == 3
        assert out["s"] == {"active": 2, "unacked": 1, "alarm": 1, "warn": 1,
                            "ttc": {"a": 0, "w": 1}, "aocs": {"a": 1, "w": 0}}

    def test_row_template_and_group_ack(self, tmp_path):
        out = run_js(self.FIX + """
            T.renderAlarmDrawer();
            const html = __registry["alarm-list"].innerHTML;
            await T.ackAlarm(2, ["2", "1"]);
            return { html, acked: T.S.alarms.filter(a => a.acknowledged).map(a => a.id),
                     posts: __fetchLog.filter(f => f.method === "POST").map(f => f.url),
                     unack: __registry["alarm-unack-n"].textContent };
        """, tmp_path)
        h = out["html"]
        assert "ttc.tm_symbol_rate" in h and "900" in h and "Bd" in h
        assert "▽" in h and "16000" in h and "soft" in h      # direction + limit + kind
        assert "×2" in h                                        # de-duplicated
        assert "▲" in h and "hard" in h                         # red high
        assert 'data-ids="2,1"' in h
        assert "CTG-003" in h
        assert sorted(out["acked"]) == [1, 2, 3]
        assert "/api/alarms/1/ack" in out["posts"] and "/api/alarms/2/ack" in out["posts"]
        assert out["unack"] == "0"

    def test_fdir_page_and_header_agree(self, tmp_path):
        out = run_js(self.FIX + """
            T.S.state = { params: {}, sa: {} };
            T.updateSaHeader();
            T.renderFdirPage();
            return { hdr: __registry["alarm-unack-n"].textContent,
                     strip: __registry["fdir-strip"] ? __registry["fdir-strip"].innerHTML : "" };
        """, tmp_path)
        assert out["hdr"] == "1"
        if out["strip"]:
            assert "GROUND ALARMS" in out["strip"] and "ON-BOARD ALARMS" in out["strip"]


@requires_node
class TestValueCell:
    def test_live_stale_nodata(self, tmp_path):
        out = run_js("""
            T.S.state = { params: { "0x0101": 82.14, "0x0102": 9.1 },
                          params_age: { "257": 1, "258": 5000 } };
            return { live: T.valueCell("0x0101", 1, "%"), stale: T.valueCell("0x0102", 1, "°C"),
                     none: T.valueCell("0x0217", 2, "deg"),
                     triadStale: T.paramTriad("0x0102"), triadNone: T.paramTriad("0x0217") };
        """, tmp_path)
        assert 'class="vc fresh"' in out["live"] and "82.1" in out["live"]
        assert 'class="vc stale"' in out["stale"] and "9.1" in out["stale"]
        assert "ds-age" in out["stale"]                       # age chip
        assert "no data" in out["none"] and "—" not in out["none"]
        assert "held" in out["triadStale"] and "9.1" in out["triadStale"]
        assert "no data" in out["triadNone"]


@requires_node
class TestProcedureButtons:
    def test_state_machine(self, tmp_path):
        out = run_js("""
            const a = ["load","start","pause","resume","step","skip","abort"];
            const row = (st, sel) => a.map(x => T.procButtonState(x, st, sel).ok ? 1 : 0).join("");
            return { idle: row("IDLE", true), idleNoSel: row("IDLE", false),
                     loaded: row("LOADED", true), running: row("RUNNING", true),
                     paused: row("PAUSED", true), done: row("COMPLETED", true),
                     why: T.procButtonState("start", "IDLE").reason };
        """, tmp_path)
        assert out["idle"] == "1000000"
        assert out["idleNoSel"] == "0000000"
        assert out["loaded"] == "1100000"
        assert out["running"] == "0010111"
        assert out["paused"] == "0001111"
        assert out["done"] == "1000000"
        assert out["why"] == "No procedure loaded"

    def test_disabled_control_keeps_focus_and_reason(self, tmp_path):
        out = run_js("""
            const b = byId("proc-btn-start");
            T.setEnabled(b, false, "No procedure loaded");
            const off = { aria: b.getAttribute("aria-disabled"), dis: b.disabled, title: b.getAttribute("title") };
            T.setEnabled(b, true);
            return { off, on: b.getAttribute("aria-disabled") };
        """, tmp_path)
        assert out["off"] == {"aria": "true", "dis": False, "title": "No procedure loaded"}
        assert out["on"] is None
