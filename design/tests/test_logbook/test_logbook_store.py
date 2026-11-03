

def test_compaction_keeps_ops_check_and_form():
    """The ops tools write ``check`` (checklist step) and ``form`` records into
    the shared file; SpaceCDF's fold and compaction must keep them."""
    from spacecdf_server.logbook.store import compacted, fold
    recs = [
        {"v": 1, "id": "c1", "op": "add", "ts": "2026-11-02T10:00:00.000Z", "tool": "mcs",
         "kind": "worksheet", "text": "NOM-001 step 1 pass", "context": {},
         "check": {"procedure": "NOM-001", "step": "1", "result": "pass"}, "lang": "en"},
        {"v": 1, "id": "c1", "op": "edit", "ts": "2026-11-02T10:01:00.000Z",
         "check": {"note": "late AOS"}},
        {"v": 1, "id": "f1", "op": "add", "ts": "2026-11-02T10:02:00.000Z", "tool": "mcs",
         "kind": "worksheet", "text": "Anomaly ticket", "context": {},
         "form": {"instance": "AT-1", "fields": [{"q": "q1", "value": "bus OV"}]}, "lang": "en"},
    ]
    f = fold(compacted(recs))
    c1, f1 = f.entries["c1"], f.entries["f1"]
    assert c1["check"] == {"procedure": "NOM-001", "step": "1", "result": "pass", "note": "late AOS"}
    assert c1["text"] == "NOM-001 step 1 pass"
    assert f1["form"]["fields"][0]["value"] == "bus OV"
