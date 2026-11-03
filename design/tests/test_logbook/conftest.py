"""Logbook test fixtures: every test gets its own logbook directory."""
from __future__ import annotations

import pytest


@pytest.fixture()
def lbdir(tmp_path, monkeypatch):
    d = tmp_path / "logbook"
    monkeypatch.setenv("SMO_LOGBOOK_DIR", str(d))
    monkeypatch.delenv("SMO_LOGBOOK_RETENTION_H", raising=False)
    monkeypatch.delenv("SMO_LOGBOOK_MAX_AGE_H", raising=False)
    return d


@pytest.fixture()
def store(lbdir):
    from spacecdf_server.logbook.store import LogbookStore
    return LogbookStore()
