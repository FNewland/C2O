"""Regenerate every textbook figure in this directory.

Usage:  python3 make_all.py                    # all fig_*.py, English and French
        python3 make_all.py gsd fspl           # only the named generators (both languages)
        python3 make_all.py --lang en|fr|all   # one language (default all)

English writes fig_<name>.png; French (FIG_LANG=fr, see i18n_fig.py) writes
fig_<name>_fr.png from the same generator, with text from i18n_fr_strings.py.
Any French string without a translation is printed as FR-MISSING and fails the run.

Each generator is run as its own process (so one failure does not stop the
rest) with this directory as cwd and on sys.path, so `from oer_style import …`
resolves. A non-zero exit code is returned if any generator fails.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main(argv: list[str]) -> int:
    langs = ["en", "fr"]
    if "--lang" in argv:
        i = argv.index("--lang")
        val = argv[i + 1] if i + 1 < len(argv) else "all"
        langs = ["en", "fr"] if val == "all" else [val]
        argv = argv[:i] + argv[i + 2:]
    scripts = sorted(HERE.glob("fig_*.py"))
    if argv:
        wanted = {a.removeprefix("fig_").removesuffix(".py") for a in argv}
        scripts = [s for s in scripts if s.stem.removeprefix("fig_") in wanted]
    failed: list[str] = []
    for lang in langs:
        env = {**os.environ, "FIG_LANG": lang}
        for script in scripts:
            res = subprocess.run([sys.executable, script.name], cwd=HERE, env=env,
                                 capture_output=True, text=True)
            missing = [l for l in res.stderr.splitlines() if l.startswith("FR-MISSING")]
            if res.returncode == 0 and not missing:
                print(res.stdout.strip() or f"OK {script.stem} [{lang}]")
            else:
                failed.append(f"{script.name} [{lang}]")
                print(f"FAIL {script.name} [{lang}]\n{res.stderr.strip()}", file=sys.stderr)
    total = len(scripts) * len(langs)
    print(f"\n{total - len(failed)}/{total} generator runs succeeded ({', '.join(langs)}).")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
