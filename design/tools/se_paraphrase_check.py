"""Paraphrase check for the SpaceCDF coaching (wave 3, 3.S4; owner S).

PI ruling: the coaching in ``configs/se_protocol.yaml`` PARAPHRASES the systems-engineering skill;
it never quotes it. This check looks for any run of N or more consecutive words (default 12) that
appears both in a card text of the protocol and in the skill package (``SKILL.md`` and every
``references/**/*.md``). Words are compared lower-case, punctuation ignored.

    python3 -m tools.se_paraphrase_check                      # skill at $SE_SKILL_DIR or /home/claude/se-skill
    python3 -m tools.se_paraphrase_check --skill DIR --n 12   # exit 1 when a copied run is found

Where no local copy of the skill exists the check reports "skipped" and exits 0 (the skill is not
part of the repository; its licence is the author's).

Stdlib plus PyYAML only.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Iterable

DEFAULT_SKILL = "/home/claude/se-skill"
DEFAULT_N = 12
_WORD = re.compile(r"[a-z0-9]+(?:['’][a-z]+)?")
#: protocol keys whose values are prose (labels and card texts); ids, refs and kinds are skipped
_PROSE_KEYS = {"en", "fr"}


def words(text: str) -> list[str]:
    return _WORD.findall(str(text or "").lower().replace("’", "'"))


def shingles(ws: list[str], n: int) -> Iterable[tuple[str, ...]]:
    for i in range(len(ws) - n + 1):
        yield tuple(ws[i:i + n])


def skill_index(skill_dir: Path, n: int) -> dict[tuple[str, ...], str]:
    """Every n-word run of the skill package -> the file it comes from."""
    out: dict[tuple[str, ...], str] = {}
    files = [skill_dir / "SKILL.md", *sorted((skill_dir / "references").rglob("*.md"))]
    for f in files:
        if not f.is_file():
            continue
        ws = words(f.read_text(encoding="utf-8", errors="replace"))
        rel = str(f.relative_to(skill_dir))
        for sh in shingles(ws, n):
            out.setdefault(sh, rel)
    return out


def protocol_texts(protocol: dict) -> list[tuple[str, str]]:
    """(path, text) of every prose string of the protocol (labels, purposes, cards)."""
    out: list[tuple[str, str]] = []

    def walk(node, path: str) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                p = f"{path}.{k}" if path else str(k)
                if k in _PROSE_KEYS and isinstance(v, str):
                    out.append((p, v))
                else:
                    walk(v, p)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")
    walk(protocol, "")
    return out


def check(protocol: dict, skill_dir: Path, n: int = DEFAULT_N) -> list[dict]:
    """Copied runs: [{path, run, source}] (empty = the coaching paraphrases)."""
    idx = skill_index(skill_dir, n)
    hits = []
    for path, text in protocol_texts(protocol):
        for sh in shingles(words(text), n):
            if sh in idx:
                hits.append({"path": path, "run": " ".join(sh), "source": idx[sh]})
                break
    return hits


def _protocol_file() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        p = parent / "configs" / "se_protocol.yaml"
        if p.is_file():
            return p
    raise FileNotFoundError("configs/se_protocol.yaml not found")


def main(argv: list[str] | None = None) -> int:
    import yaml
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--skill", default=os.environ.get("SE_SKILL_DIR", DEFAULT_SKILL))
    ap.add_argument("--protocol", default=None)
    ap.add_argument("--n", type=int, default=DEFAULT_N)
    a = ap.parse_args(argv)
    skill = Path(a.skill)
    if not (skill / "SKILL.md").is_file():
        print(f"se_paraphrase_check: skipped (no skill package at {skill})")
        return 0
    proto = yaml.safe_load(Path(a.protocol or _protocol_file()).read_text(encoding="utf-8"))
    hits = check(proto, skill, a.n)
    for h in hits:
        print(f"COPIED {h['path']}: \"{h['run']}\" (from {h['source']})")
    print(f"se_paraphrase_check: {len(protocol_texts(proto))} texts, {len(hits)} copied run(s) of {a.n}+ words")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
