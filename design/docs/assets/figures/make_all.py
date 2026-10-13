"""Regenerate every textbook figure in this directory.

Usage:  python3 make_all.py            # all fig_*.py
        python3 make_all.py gsd fspl   # only the named generators

Each generator is run as its own process (so one failure does not stop the
rest) with this directory as cwd and on sys.path, so `from oer_style import …`
resolves. A non-zero exit code is returned if any generator fails.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main(argv: list[str]) -> int:
    scripts = sorted(HERE.glob("fig_*.py"))
    if argv:
        wanted = {a.removeprefix("fig_").removesuffix(".py") for a in argv}
        scripts = [s for s in scripts if s.stem.removeprefix("fig_") in wanted]
    failed: list[str] = []
    for script in scripts:
        res = subprocess.run([sys.executable, script.name], cwd=HERE,
                             capture_output=True, text=True)
        if res.returncode == 0:
            print(res.stdout.strip() or f"OK {script.stem}")
        else:
            failed.append(script.name)
            print(f"FAIL {script.name}\n{res.stderr.strip()}", file=sys.stderr)
    print(f"\n{len(scripts) - len(failed)}/{len(scripts)} generators succeeded.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
