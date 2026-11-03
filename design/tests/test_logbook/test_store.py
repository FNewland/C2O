"""Logbook store: file format, identity hash, fold, limits, purge (LOGBOOK_SPEC.md §1-§2)."""
from __future__ import annotations

import hashlib
import json
import os
import stat
from datetime import datetime, timedelta, timezone

import pytest

from spacecdf_server.logbook import store as st
from spacecdf_server.logbook.store import LogbookError, LogbookStore, fold

T0 = datetime(2026, 11, 2, 12, 0, 0, tzinfo=timezone.utc)
ALICE = "alice@c2o.live"


def _add(store, text="Chose body-mounted arrays", kind="decision", now=None, **kw):
    return store.add(ALICE, {"kind": kind, "text": text, "tool": "design", **kw}, now=now)


def _lines(store, person=ALICE):
    return [json.loads(l) for l in store.path_for(person).read_text().splitlines()]


class TestIdentity:
    def test_iap_header_is_stripped_and_lower_cased(self):
        assert st.person_from_iap("accounts.google.com:Alice.Smith@C2O.live") == "alice.smith@c2o.live"
        assert st.person_from_iap("bob@c2o.live") == "bob@c2o.live"
        assert st.person_from_iap("") is None and st.person_from_iap(None) is None

    def test_cookie_accepts_prefixed_or_bare_hex_only(self):
        h = "0123456789abcdef0123456789abcdef"
        assert st.person_from_cookie(f"local:{h}") == f"local:{h}"
        assert st.person_from_cookie(h) == f"local:{h}"
        assert st.person_from_cookie("local:../../etc") is None
        assert st.person_from_cookie("x" * 32) is None

    def test_new_local_id_is_128_bit(self):
        pid = st.new_local_id()
        assert pid.startswith("local:") and len(pid) == 6 + 32
        assert st.person_from_cookie(pid) == pid

    def test_file_name_is_sha256_prefix(self, store):
        want = hashlib.sha256(ALICE.encode()).hexdigest()[:32] + ".jsonl"
        assert st.file_name(ALICE) == want
        assert store.path_for(ALICE).name == want


class TestFormat:
    def test_add_writes_one_spec_record_with_modes(self, store, lbdir):
        e = _add(store, context={"study_id": "s1", "tab": "budget"}, lang="fr", now=T0)
        recs = _lines(store)
        assert len(recs) == 1
        r = recs[0]
        assert r["v"] == 1 and r["op"] == "add" and r["id"] == e["id"]
        assert r["ts"] == "2026-11-02T12:00:00.000Z"
        assert (r["tool"], r["kind"], r["lang"]) == ("design", "decision", "fr")
        assert r["context"] == {"study_id": "s1", "tab": "budget"}
        assert stat.S_IMODE(os.stat(lbdir).st_mode) == 0o700
        assert stat.S_IMODE(os.stat(store.path_for(ALICE)).st_mode) == 0o600

    def test_edit_and_delete_are_appended_records(self, store):
        e = _add(store, now=T0)
        store.edit(ALICE, e["id"], "Changed my mind", now=T0 + timedelta(minutes=5))
        recs = _lines(store)
        assert [r["op"] for r in recs] == ["add", "edit"]
        assert recs[1] == {"v": 1, "id": e["id"], "op": "edit", "ts": "2026-11-02T12:05:00.000Z",
                           "text": "Changed my mind"}
        store.delete(ALICE, e["id"], now=T0 + timedelta(minutes=6))
        assert [r["op"] for r in _lines(store)] == ["add", "edit", "delete"]
        assert store.folded(ALICE).entries == {}

    def test_folds_a_file_written_by_the_ops_tools(self, store, lbdir):
        """Byte-for-byte the spec's example: another implementation's records fold here."""
        lbdir.mkdir(parents=True)
        uid = "6f1c2f8e-1f7a-4c1e-9d55-3c1b2b9a0001"
        raw = [
            {"v": 1, "id": uid, "op": "add", "ts": "2026-11-02T23:41:07.123Z", "sim_ts": "2026-03-10T04:18:22Z",
             "tool": "mcs", "kind": "decision", "text": "GO for burn",
             "context": {"page": "eps", "procedure": "CTG-001", "alarm_id": 42, "param": "0x0105",
                         "study_id": None, "step": None, "position": "eps_tcs", "scenario": "leop"},
             "worksheet": {"id": "WB-5.5-DB", "q": "q3"}, "lang": "en"},
            {"v": 1, "id": uid, "op": "edit", "ts": "2026-11-02T23:45:00Z", "text": "NO-GO, then GO"},
            {"v": 1, "op": "downloaded", "ts": "2026-11-02T23:50:00Z", "format": "md"},
        ]
        store.path_for(ALICE).write_text("".join(json.dumps(r) + "\n" for r in raw) + "not json\n")
        f = store.folded(ALICE)
        (e,) = f.entries.values()
        assert e["text"] == "NO-GO, then GO" and e["edited"] and e["tool"] == "mcs"
        assert e["context"]["procedure"] == "CTG-001" and e["sim_ts"] == "2026-03-10T04:18:22Z"
        assert f.last_write == datetime(2026, 11, 2, 23, 45, tzinfo=timezone.utc)
        assert f.last_download == datetime(2026, 11, 2, 23, 50, tzinfo=timezone.utc)
        assert f.unsaved == 0

    def test_fold_rules(self):
        recs = [
            {"op": "add", "id": "a", "ts": "2026-11-02T10:00:00Z", "kind": "thought", "tool": "design", "text": "1"},
            {"op": "add", "id": "a", "ts": "2026-11-02T10:01:00Z", "kind": "thought", "tool": "design", "text": "dup"},
            {"op": "edit", "id": "a", "ts": "2026-11-02T10:02:00Z", "text": "2"},
            {"op": "edit", "id": "a", "ts": "2026-11-02T10:03:00Z", "text": "3"},
            {"op": "add", "id": "b", "ts": "2026-11-02T11:00:00Z", "kind": "thought", "tool": "design", "text": "b"},
            {"op": "delete", "id": "b", "ts": "2026-11-02T11:01:00Z"},
            {"op": "edit", "id": "b", "ts": "2026-11-02T11:02:00Z", "text": "revived?"},
            {"op": "edit", "id": "zz", "ts": "2026-11-02T11:03:00Z", "text": "orphan"},
        ]
        f = fold(recs)
        assert list(f.entries) == ["a"] and f.entries["a"]["text"] == "3"
        assert f.last_write == datetime(2026, 11, 2, 11, 1, tzinfo=timezone.utc)
        assert f.unsaved == 1

    def test_newest_first(self, store):
        a = _add(store, text="first", now=T0)
        b = _add(store, text="second", now=T0 + timedelta(seconds=1))
        assert [e["id"] for e in store.folded(ALICE).newest_first()] == [b["id"], a["id"]]


class TestValidation:
    @pytest.mark.parametrize("body,status", [
        ({"kind": "rant", "text": "x", "tool": "design"}, 400),
        ({"kind": "thought", "text": "x", "tool": "excel"}, 400),
        ({"kind": "thought", "text": "   ", "tool": "design"}, 400),
        ({"kind": "worksheet", "text": "x", "tool": "design"}, 400),
        ({"kind": "thought", "text": "x", "tool": "design", "context": {"a": {"nested": 1}}}, 400),
        ({"kind": "thought", "text": "x", "tool": "design", "lang": "de"}, 400),
        ({"kind": "thought", "text": "x" * 8001, "tool": "design"}, 413),
    ])
    def test_rejects(self, store, body, status):
        with pytest.raises(LogbookError) as ei:
            store.add(ALICE, body)
        assert ei.value.status == status

    def test_8000_characters_is_allowed(self, store):
        assert len(_add(store, text="é" * 8000)["text"]) == 8000

    def test_entry_limit_is_413_with_download_hint(self, store, monkeypatch):
        monkeypatch.setattr(st, "ENTRY_LIMIT", 3)
        for i in range(3):
            _add(store, text=str(i))
        with pytest.raises(LogbookError) as ei:
            _add(store, text="one too many")
        assert ei.value.status == 413 and "Download" in ei.value.message

    def test_edit_or_delete_unknown_is_404(self, store):
        for fn in (lambda: store.edit(ALICE, "nope", "x"), lambda: store.delete(ALICE, "nope")):
            with pytest.raises(LogbookError) as ei:
                fn()
            assert ei.value.status == 404


class TestRetention:
    def _age(self, store, hours, person=ALICE):
        p = store.path_for(person)
        t = (datetime.now(timezone.utc) - timedelta(hours=hours)).timestamp()
        os.utime(p, (t, t))

    def test_file_deleted_48h_after_last_write(self, store):
        _add(store)
        self._age(store, 47)
        assert store.purge()["kept"] == 1 and store.path_for(ALICE).exists()
        self._age(store, 49)
        assert store.purge()["deleted"] == 1 and not store.path_for(ALICE).exists()

    def test_retention_is_configurable(self, store, monkeypatch):
        monkeypatch.setenv("SMO_LOGBOOK_RETENTION_H", "1")
        _add(store)
        self._age(store, 2)
        store.purge()
        assert not store.path_for(ALICE).exists()

    def test_entries_older_than_7_days_go_even_while_active(self, store):
        now = datetime.now(timezone.utc)
        old = _add(store, text="eight days ago", now=now - timedelta(days=8))
        store.edit(ALICE, old["id"], "edited yesterday", now=now - timedelta(days=1))
        new = _add(store, text="today", now=now)
        store.mark_downloaded(ALICE, "md", now=now - timedelta(days=9))
        mtime = os.stat(store.path_for(ALICE)).st_mtime_ns
        assert store.purge(now=now)["trimmed"] == 1
        assert list(store.folded(ALICE).entries) == [new["id"]]
        assert all(r.get("id") != old["id"] for r in _lines(store))
        assert not any(r["op"] == "downloaded" for r in _lines(store))
        assert os.stat(store.path_for(ALICE)).st_mtime_ns == mtime, "trim must not extend retention"
        assert store.purge(now=now)["kept"] == 1, "purge is idempotent"

    def test_file_with_only_old_entries_is_removed(self, store):
        now = datetime.now(timezone.utc)
        _add(store, now=now - timedelta(days=8))
        store.purge(now=now)
        assert not store.path_for(ALICE).exists()

    def test_download_marker_keeps_the_retention_clock(self, store):
        _add(store)
        self._age(store, 10)
        before = os.stat(store.path_for(ALICE)).st_mtime_ns
        store.mark_downloaded(ALICE, "html")
        assert os.stat(store.path_for(ALICE)).st_mtime_ns == before
        assert _lines(store)[-1]["op"] == "downloaded" and _lines(store)[-1]["format"] == "html"

    def test_download_marker_without_a_logbook_creates_nothing(self, store):
        store.mark_downloaded(ALICE, "md")
        assert not store.path_for(ALICE).exists()

    def test_delete_all(self, store):
        _add(store)
        assert store.delete_all(ALICE) is True
        assert not store.path_for(ALICE).exists()
        assert store.delete_all(ALICE) is False
        assert store.folded(ALICE).entries == {}

    def test_purge_on_missing_dir_is_a_no_op(self, store):
        assert store.purge() == {"deleted": 0, "trimmed": 0, "kept": 0}

    def test_expires_at_is_last_write_plus_retention(self, store):
        _add(store, now=T0)
        assert store.expires_at(store.folded(ALICE)) == T0 + timedelta(hours=48)


def test_concurrent_appends_are_not_lost(store):
    """Several threads (as FastAPI's pool does) appending to one file."""
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(8) as pool:
        list(pool.map(lambda i: _add(store, text=f"n{i}"), range(80)))
    assert len(store.folded(ALICE).entries) == 80
    assert len(_lines(store)) == 80


def test_default_dir_prefers_env(monkeypatch, tmp_path):
    monkeypatch.setenv("SMO_LOGBOOK_DIR", str(tmp_path / "x"))
    assert st.default_dir() == tmp_path / "x"
    assert LogbookStore().root == tmp_path / "x"


def test_dev_default_never_creates_a_dir_in_the_repo(monkeypatch):
    """The repo is public: without SMO_LOGBOOK_DIR SpaceCDF only reuses an existing ops logbook dir."""
    from pathlib import Path
    monkeypatch.delenv("SMO_LOGBOOK_DIR", raising=False)
    if st.CONTAINER_DIR.parent.is_dir():
        pytest.skip("running inside a C2O container")
    repo = Path(st.__file__).resolve().parents[6]
    d = st.default_dir()
    ops = repo / "sim" / "workspace" / "logbook"
    assert d == ops if ops.is_dir() else repo not in d.parents


def test_shared_group_modes(store, lbdir, monkeypatch):
    """Ground VM: SMO (uid 10001) and SpaceCDF (10002, smo group) share the store."""
    monkeypatch.setenv("SMO_LOGBOOK_SHARED_GROUP", "1")
    _add(store)
    assert stat.S_IMODE(os.stat(lbdir).st_mode) == 0o2770
    assert stat.S_IMODE(os.stat(store.path_for(ALICE)).st_mode) == 0o660


def test_edit_churn_is_compacted_like_smo_common(store, monkeypatch):
    monkeypatch.setattr(st, "COMPACT_SLACK", 10)
    e = _add(store, text="v0")
    keep = _add(store, text="untouched")
    store.mark_downloaded(ALICE, "md")
    for i in range(12):
        store.edit(ALICE, e["id"], f"v{i + 1}")
    recs = _lines(store)
    assert len(recs) < 10, recs
    f = store.folded(ALICE)
    assert f.entries[e["id"]]["text"] == "v12" and f.entries[e["id"]]["edited"]
    assert f.entries[keep["id"]]["text"] == "untouched" and f.last_download is not None


def test_text_is_normalised_and_lang_defaults_to_en(store):
    e = store.add(ALICE, {"kind": "thought", "tool": "design", "text": "  a\r\nb  "})
    assert e["text"] == "a\nb" and e["lang"] == "en"


def test_context_strings_are_clipped(store):
    e = _add(store, context={"element": "x" * 500})
    assert len(e["context"]["element"]) == 200
