"""Minimal git helpers (all failures → None; the tool works outside git)."""
from __future__ import annotations

import os
import subprocess


def _git(args, cwd):
    try:
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    return r.stdout


def toplevel(path: str) -> str | None:
    d = path if os.path.isdir(path) else os.path.dirname(path) or "."
    if not os.path.isdir(d):
        return None
    out = _git(["rev-parse", "--show-toplevel"], d)
    return out.decode().strip() if out else None


def head(path: str) -> str | None:
    top = toplevel(path)
    if not top:
        return None
    out = _git(["rev-parse", "--short", "HEAD"], top)
    return out.decode().strip() if out else None


def show(rev: str, path: str) -> str | None:
    top = toplevel(path)
    if not top:
        return None
    rel = os.path.relpath(os.path.abspath(path), top).replace(os.sep, "/")
    out = _git(["show", f"{rev}:{rel}"], top)
    if out is None:
        return None
    try:
        return out.decode("utf-8")
    except UnicodeDecodeError:
        return None


def staged_files(cwd: str) -> list[str]:
    out = _git(["diff", "--cached", "--name-only", "--diff-filter=ACMR"], cwd)
    return out.decode().split("\n") if out else []
