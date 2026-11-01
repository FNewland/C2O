"""The modern console's PUS payload key must match what the server reads.

FIELD DEFECT 2026-08-20 (owner: "a number of commands do not seem to work,
whereas they work first time in classic"). ``_handle_pus_command`` reads
``body["data_hex"]``; every one of the 20 ``/api/pus-command`` call sites in
the modern page sent ``body["data"]``. The key silently defaulted to ``""``,
so EVERY PUS command from the modern console went out with an EMPTY data
field: HK ENABLE with no SID, S11 schedule inserts with no time tag,
S20 parameter sets with no value.

It failed silently in both directions -- the POST returned 200 because the
packet was well-formed, and the spacecraft either ignored it or, worse,
applied an argument-less default (this is where the beacon-mode command that
latched the ladder to SAFE came from: func 70 with no argument byte defaulted
to ON).

A shape mismatch between a client and its own server is exactly the class the
manual page hit the same week (``pages`` vs ``sections``), so pin it: assert
the key the server reads and the key every client sends are the same string.
"""
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
MCS_JS = REPO / "packages/smo-mcs/src/smo_mcs/static/modern/mcs.js"
SERVER = REPO / "packages/smo-mcs/src/smo_mcs/server.py"


def _object_at(js: str, start: int) -> str:
    depth, j = 0, start
    while j < len(js):
        if js[j] == "{":
            depth += 1
        elif js[j] == "}":
            depth -= 1
            if depth == 0:
                break
        j += 1
    return js[start:j + 1]


def _pus_payloads(js: str):
    """Yield (line_no, object-literal) for each PUS send.

    Since ed2d82c every send goes through ONE wrapper, ``sendPus(body)``,
    which POSTs the body to /api/pus-command (R4 G7). So the call sites are
    ``sendPus({...})``; a direct ``postJSON("/api/pus-command", {...})``
    literal is still scanned in case one is ever reintroduced.
    """
    for pat in (r'sendPus\(\s*\{', r'postJSON\("/api/pus-command",\s*\{'):
        for m in re.finditer(pat, js):
            start = m.end() - 1
            yield js[:start].count("\n") + 1, _object_at(js, start)


def test_the_send_wrapper_forwards_the_body_unchanged():
    """sendPus must POST the caller's body (with data_hex) to the route the
    server reads, not rebuild it under another key."""
    js = MCS_JS.read_text(encoding="utf-8")
    m = re.search(r"async function sendPus\((\w+)\)\s*\{(.*?)\n\}", js, re.S)
    assert m, "the sendPus wrapper is gone — rescan the call sites"
    arg, body = m.group(1), m.group(2)
    assert re.search(r"Object\.assign\(\{[^}]*\},\s*" + arg + r"\)", body), (
        "sendPus no longer copies the caller's body verbatim")
    assert 'postJSON("/api/pus-command"' in body
    assert "data_hex" in body, "the wrapper's history record must read data_hex"


def test_server_still_reads_data_hex():
    """If the server ever renames the key, this test names the new contract."""
    assert 'body.get("data_hex"' in SERVER.read_text(encoding="utf-8"), (
        "the PUS handler no longer reads 'data_hex' — update every modern "
        "call site AND this test together, or the console goes silent again")


def test_every_modern_pus_payload_uses_data_hex():
    js = MCS_JS.read_text(encoding="utf-8")
    payloads = list(_pus_payloads(js))
    assert payloads, "no /api/pus-command call sites found — did the path change?"

    offenders = []
    for line, obj in payloads:
        if "data_hex" in obj:
            continue
        # a bare `data:` or shorthand `data,` means an empty field on the wire
        if re.search(r"(?<![\w.])data\s*[:,]", obj):
            offenders.append(line)
    assert not offenders, (
        f"{len(offenders)} /api/pus-command payload(s) send 'data' instead of "
        f"'data_hex' (lines {offenders}) — the server reads 'data_hex', so "
        f"these commands go out with an EMPTY data field")


def test_the_argument_carrying_commands_are_covered():
    """Guard the specific ones the owner found broken."""
    js = MCS_JS.read_text(encoding="utf-8")
    for needle in ("data_hex: sidToHex(sid)",):          # HK enable/disable/oneshot
        assert needle in js, f"expected {needle!r} — HK SID commands need their SID"
