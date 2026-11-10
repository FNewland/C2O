"""W0.5: ``stack up spacecdf`` refuses a frontend build older than its sources.

Run from ``video/``:  python -m pytest -q tests
"""
from __future__ import annotations

import os

import pytest

from c2ovideo import stack


def _tree(tmp_path, built_at: float, src_at: float):
    fe = tmp_path / "frontend"
    (fe / "src").mkdir(parents=True)
    (fe / "dist").mkdir()
    (fe / "src" / "App.tsx").write_text("x")
    (fe / "dist" / "index.html").write_text("<html>")
    os.utime(fe / "src" / "App.tsx", (src_at, src_at))
    os.utime(fe / "dist" / "index.html", (built_at, built_at))
    return fe


def test_fresh_build_passes(tmp_path):
    assert stack.frontend_build_problem(_tree(tmp_path, built_at=2_000_000, src_at=1_000_000)) is None


def test_stale_build_names_the_file(tmp_path):
    msg = stack.frontend_build_problem(_tree(tmp_path, built_at=1_000_000, src_at=1_000_600))
    assert msg and "stale" in msg and "src/App.tsx" in msg and "npm run build" in msg


def test_missing_build(tmp_path):
    fe = tmp_path / "frontend"
    (fe / "src").mkdir(parents=True)
    assert "build the SpaceCDF frontend first" in stack.frontend_build_problem(fe)


def test_stack_up_exits_nonzero_on_a_stale_build(tmp_path, monkeypatch):
    fe = _tree(tmp_path, built_at=1_000_000, src_at=1_000_600)
    monkeypatch.setattr(stack, "DESIGN", fe.parent)
    monkeypatch.setattr(stack, "STATE", tmp_path / "state")
    monkeypatch.setattr(stack, "_free", lambda port: True)
    monkeypatch.delenv("C2O_VIDEO_ALLOW_STALE_DIST", raising=False)
    with pytest.raises(SystemExit) as exc:
        stack.up_spacecdf()
    assert "stale" in str(exc.value.code)
    assert not (tmp_path / "state").exists()      # refused before touching any state
