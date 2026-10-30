"""Load i18n.yaml and expand it into concrete doc pairs, catalogs and overlay rules."""
from __future__ import annotations

import glob
import os
import re
from dataclasses import dataclass, field

from . import yamlmini


@dataclass
class DocPair:
    en: str                 # absolute path
    fr: str                 # absolute path
    group: str
    legacy: bool = False    # pre-existing hand-made pair: parity problems are warnings
    forbid_fr: list = field(default_factory=list)
    note: str = ""

    @property
    def sidecar(self):
        from .mdsync import sidecar_path
        return sidecar_path(self.fr)


@dataclass
class Catalog:
    name: str
    fr: str
    en: str | None
    sources: list
    fallback: list
    keep: list
    functions: list = field(default_factory=list)
    fr_more: list = field(default_factory=list)   # extra FR files/globs merged at runtime

    def fr_files(self) -> list:
        out = [self.fr]
        for pat in self.fr_more:
            for p in (iglob(pat) or []):
                if p not in out:
                    out.append(p)
        return out


@dataclass
class Config:
    path: str
    root: str
    raw: dict
    docs: list = field(default_factory=list)
    unavailable: list = field(default_factory=list)   # (group, root, reason)
    catalogs: list = field(default_factory=list)
    overlay: dict | None = None
    glossary: str | None = None
    style: str | None = None

    def rel(self, p: str) -> str:
        try:
            r = os.path.relpath(p, self.root)
        except ValueError:
            return p
        return p if r.startswith("..") else r

    def ref(self, p: str) -> str:
        """Path as stored in sidecars: repo-relative, or with ${VAR} for env roots."""
        r = self.rel(p)
        if r != p:
            return r
        for var in self.raw.get("env_defaults", {}) or {}:
            v = _env(var, self.raw)
            if v and p.startswith(v.rstrip("/") + "/"):
                return "${%s}/%s" % (var, p[len(v.rstrip('/')) + 1:])
        return p


def _env(var: str, raw: dict) -> str | None:
    v = os.environ.get(var)
    if v:
        return os.path.expanduser(v)
    d = (raw.get("env_defaults") or {}).get(var)
    return os.path.expanduser(d) if d else None


def expand(path: str, root: str, raw: dict) -> tuple[str | None, str | None]:
    """Return (abs_path, missing_var)."""
    missing = None

    def sub(m):
        nonlocal missing
        v = _env(m.group(1), raw)
        if v is None:
            missing = m.group(1)
            return ""
        return v
    p = re.sub(r"\$\{(\w+)\}", sub, str(path))
    if missing:
        return None, missing
    p = os.path.expanduser(p)
    if not os.path.isabs(p):
        p = os.path.join(root, p)
    return os.path.normpath(p), None


def brace_expand(pat: str) -> list[str]:
    m = re.search(r"\{([^{}]*,[^{}]*)\}", pat)
    if not m:
        return [pat]
    out = []
    for alt in m.group(1).split(","):
        out += brace_expand(pat[: m.start()] + alt + pat[m.end():])
    return out


def iglob(pattern: str) -> list[str]:
    out: list[str] = []
    for p in brace_expand(pattern):
        out += glob.glob(p, recursive=True)
    return sorted(set(out))


def find_config(start: str | None = None) -> str:
    d = os.path.abspath(start or os.getcwd())
    while True:
        for name in ("i18n.yaml", "i18n.yml", "i18n.json"):
            p = os.path.join(d, name)
            if os.path.exists(p):
                return p
        nd = os.path.dirname(d)
        if nd == d:
            raise SystemExit("i18n: no i18n.yaml found (use --config PATH)")
        d = nd


def load(path: str | None = None) -> Config:
    path = os.path.abspath(path or find_config())
    with open(path, encoding="utf-8") as f:
        text = f.read()
    raw = yamlmini.load(text) or {}
    root = os.path.dirname(path)
    if raw.get("root"):
        root = os.path.normpath(os.path.join(root, raw["root"]))
    cfg = Config(path=path, root=root, raw=raw)
    for key in ("glossary", "style"):
        if raw.get(key):
            p, _ = expand(raw[key], root, raw)
            setattr(cfg, key, p)
    _load_docs(cfg)
    for c in raw.get("catalogs") or []:
        frs = c["fr"] if isinstance(c["fr"], list) else [c["fr"]]
        fr, _ = expand(frs[0], root, raw)
        more = [expand(x, root, raw)[0] for x in frs[1:]]
        en = expand(c["en"], root, raw)[0] if c.get("en") else None
        srcs = [expand(s, root, raw)[0] for s in (c.get("sources") or [])]
        cfg.catalogs.append(Catalog(c.get("name") or os.path.relpath(fr, root), fr, en,
                                    [s for s in srcs if s], list(c.get("fallback") or []),
                                    list(c.get("keep") or []),
                                    list(c.get("functions") or raw.get("catalog_functions") or []),
                                    [m for m in more if m]))
    ov = raw.get("yaml_overlay")
    if ov:
        o = dict(ov)
        o["output_abs"] = expand(ov["output"], root, raw)[0]
        if ov.get("client_json"):
            o["client_json_abs"] = expand(ov["client_json"], root, raw)[0]
        o["base_abs"] = expand(ov.get("base", "."), root, raw)[0]
        cfg.overlay = o
    return cfg


def _load_docs(cfg: Config):
    raw, root = cfg.raw, cfg.root
    seen = set()
    for d in raw.get("docs") or []:
        group = d.get("group") or d.get("en") or d.get("en_glob")
        legacy = bool(d.get("legacy"))
        forbid = list(d.get("forbid_fr") or [])
        note = d.get("note", "")
        if "en" in d:
            en, miss = expand(d["en"], root, raw)
            fr, miss2 = expand(d["fr"], root, raw)
            if miss or miss2:
                cfg.unavailable.append((group, d["en"], f"env var ${{{miss or miss2}}} not set"))
                continue
            if not os.path.exists(en):
                cfg.unavailable.append((group, en, "EN file not found"))
                continue
            if en not in seen:
                seen.add(en)
                cfg.docs.append(DocPair(en, fr, group, legacy, forbid, note))
            continue
        en_root, miss = expand(d["en_root"], root, raw)
        fr_root, miss2 = expand(d["fr_root"], root, raw)
        pat, miss3 = expand(d["en_glob"], root, raw)
        if miss or miss2 or miss3:
            cfg.unavailable.append((group, d["en_root"], f"env var ${{{miss or miss2 or miss3}}} not set"))
            continue
        if not os.path.isdir(en_root):
            cfg.unavailable.append((group, en_root, "EN root not found"))
            continue
        excl = set()
        for x in d.get("exclude") or []:
            xp, _ = expand(x, root, raw)
            if xp:
                excl.update(iglob(xp) or [xp])
        fr_abs = os.path.abspath(fr_root)
        for en in iglob(pat):
            if not os.path.isfile(en) or en in excl or en in seen:
                continue
            ena = os.path.abspath(en)
            if ena.startswith(fr_abs + os.sep) or f"{os.sep}.i18n{os.sep}" in ena:
                continue   # never treat the FR tree as source
            rel = os.path.relpath(en, en_root)
            seen.add(en)
            cfg.docs.append(DocPair(en, os.path.join(fr_root, rel), group, legacy, forbid, note))
