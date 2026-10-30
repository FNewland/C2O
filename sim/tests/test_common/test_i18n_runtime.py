"""i18n packet S0 — the browser runtime (/static/shared/i18n.js) under node.

Covers: t() interpolation + HTML escaping (+ raw `{{- x}}` / tText),
plurals via Intl.PluralRules (fr one/many/other, en via vars.plural),
context keys, English identity, missing-key fallback + I18n.missing,
language resolution order (?lang > localStorage > data-default-lang > en,
storage:false for the wall display), applyDom round trip FR -> EN restoring
the exact English, setLang (persist, <html lang>, smo:langchange), tdb(),
the shared EN|FR toggle, and format.js fmtNum/fmtProse.

Each case runs in a fresh node process (i18n.js keeps its state on
globalThis). components.js imports /static/shared/i18n.js, so the shared
modules are copied with that specifier rewritten (as modern_harness.js does).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SHARED = REPO / "packages/smo-common/src/smo_common/ui"
NODE = shutil.which("node") or shutil.which("nodejs")
pytestmark = pytest.mark.skipif(NODE is None, reason="node is required")

FR_CAT = {
    "no limit defined": "aucune limite définie",
    "rejected — {{reason}}": "refusé — {{reason}}",
    "{{count}} pass": "{{count}} passage (sans pluriel)",
    "{{count}} pass_one": "{{count}} passage",
    "{{count}} pass_other": "{{count}} passages",
    "Mode_spacecraft": "Mode satellite",
    "Mode": "Mode générique",
    "Close": "Fermer",
    "Save": "",                       # untranslated entry == missing
    "Keyboard & design": "Clavier et conception",
}
DB_CAT = {"tm:eps.bat_voltage:description": "Tension batterie"}

PRELUDE = r"""
console.debug = (...a) => process.stderr.write(a.join(' ') + '\n');   // keep stdout = JSON
const __cats = { '/static/shared/i18n/fr.json': %(fr)s,
                 '/static/modern/i18n/fr.json': {},
                 '/static/shared/i18n/fr.db.json': %(db)s };
globalThis.__fetched = [];
globalThis.fetch = async (url) => { __fetched.push(String(url));
  const j = __cats[String(url)];
  return j ? { ok: true, json: async () => j } : { ok: false, json: async () => ({}) }; };
globalThis.location = { search: %(search)s, href: 'http://h/x' + %(search)s };
globalThis.history = { state: null, replaceState(s, t, u) { globalThis.__replaced = String(u); } };
const __ls = %(ls)s;
globalThis.localStorage = { getItem: (k) => (k in __ls ? __ls[k] : null),
  setItem: (k, v) => { __ls[k] = String(v); } };
globalThis.__events = [];
globalThis.addEventListener = (n, f) => { (globalThis.__h ||= {})[n] = [...((globalThis.__h || {})[n] || []), f]; };
globalThis.removeEventListener = () => {};
globalThis.dispatchEvent = (e) => { __events.push(e.type + ':' + e.detail.lang);
  ((globalThis.__h || {})[e.type] || []).forEach((f) => f(e)); return true; };
globalThis.CustomEvent ||= class { constructor(t, i) { this.type = t; this.detail = (i || {}).detail; } };
// --- tiny DOM: elements with attributes + text-node children ---
class TNode { constructor(v) { this.nodeType = 3; this.nodeValue = v; } }
class El {
  constructor(attrs, kids) { this.attrs = { ...attrs }; this.childNodes = kids.map((k) => typeof k === 'string' ? new TNode(k) : k); this.nodeType = 1; }
  getAttribute(a) { return a in this.attrs ? this.attrs[a] : null; }
  setAttribute(a, v) { this.attrs[a] = String(v); }
  hasAttribute(a) { return a in this.attrs; }
  get textContent() { return this.childNodes.map((n) => n.nodeType === 3 ? n.nodeValue : n.textContent).join(''); }
  set textContent(v) { this.childNodes = [new TNode(String(v))]; }
  get innerHTML() { return this._html ?? this.textContent; }
  set innerHTML(v) { this._html = String(v); }
  all() { return this.childNodes.filter((n) => n.nodeType === 1).flatMap((n) => [n, ...n.all()]); }
  querySelectorAll(sel) { const names = [...sel.matchAll(/\[([\w-]+)\]/g)].map((m) => m[1]);
    return this.all().filter((e) => names.some((n) => e.hasAttribute(n))); }
}
globalThis.El = El;
const __html = new El(%(htmlattrs)s, []);
globalThis.document = { documentElement: __html, querySelectorAll: (s) => (globalThis.__root ? __root.querySelectorAll(s) : []),
  activeElement: null };
Object.defineProperty(__html, 'lang', { get() { return this.attrs.lang || 'en'; }, set(v) { this.attrs.lang = v; } });
"""


def run_js(tmp_path: Path, body: str, *, search="", ls=None, html_attrs=None):
    for f in SHARED.glob("*.js"):
        src = f.read_text(encoding="utf-8")
        src = re.sub(r"""(["'])/static/shared/([\w.-]+\.js)(\?[^"']*)?\1""",
                     r'"./\2"', src)
        (tmp_path / f.name).write_text(src, encoding="utf-8")
    prelude = PRELUDE % {
        "fr": json.dumps(FR_CAT, ensure_ascii=False),
        "db": json.dumps(DB_CAT, ensure_ascii=False),
        "search": json.dumps(search), "ls": json.dumps(ls or {}),
        "htmlattrs": json.dumps(html_attrs or {"lang": "en"}),
    }
    script = (prelude
              + "const M = await import('./i18n.js');\n"
              + "const out = await (async () => {\n" + body + "\n})();\n"
              + "process.stdout.write(JSON.stringify(out));\n")
    p = tmp_path / "case.mjs"
    p.write_text(script, encoding="utf-8")
    r = subprocess.run([NODE, str(p)], capture_output=True, text=True,
                       timeout=60, cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


# ── t(): English identity, interpolation, escaping ───────────────────────

def test_english_is_identity_and_fetches_nothing(tmp_path):
    out = run_js(tmp_path, """
      await M.I18n.ready;
      return [M.getLang(), M.t('no limit defined'),
              M.t('rejected — {{reason}}', {reason: '<b>&'}),
              M.tText('rejected — {{reason}}', {reason: '<b>&'}),
              M.t('a {{- html}} b', {html: '<i>x</i>'}),
              M.t('left {{missing}} alone'),
              M.t('{{count}} pass', {count: 1, plural: '{{count}} passes'}),
              M.t('{{count}} pass', {count: 3, plural: '{{count}} passes'}),
              M.t('Mode', {context: 'spacecraft'}),
              globalThis.__fetched, [...M.I18n.missing]];
    """)
    assert out == ["en", "no limit defined", "rejected — &lt;b&gt;&amp;",
                   "rejected — <b>&", "a <i>x</i> b", "left {{missing}} alone",
                   "1 pass", "3 passes", "Mode", [], []]


def test_french_lookup_plurals_context_and_fallback(tmp_path):
    out = run_js(tmp_path, """
      await M.I18n.ready;
      const p = (n) => M.t('{{count}} pass', {count: n, plural: '{{count}} passes'});
      return [M.getLang(), M.t('no limit defined'),
              M.t('rejected — {{reason}}', {reason: 'a<b'}),
              p(0), p(1), p(2), p(1000000),
              M.t('Mode', {context: 'spacecraft'}), M.t('Mode', {context: 'other'}),
              M.t('Mode'), M.t('Save'), M.t('Not in catalog'),
              M.tdb('tm:eps.bat_voltage:description', 'Battery voltage'),
              M.tdb('tm:x:description', 'Fallback EN'),
              [...M.I18n.missing].sort(), document.documentElement.lang];
    """, search="?lang=fr")
    assert out[0] == "fr"
    assert out[1] == "aucune limite définie"
    assert out[2] == "refusé — a&lt;b"
    # fr: 0 and 1 are "one"; 2 "other"; 1e6 "many" -> falls back to _other
    assert out[3:7] == ["0 passage", "1 passage", "2 passages", "1000000 passages"]
    assert out[7:10] == ["Mode satellite", "Mode générique", "Mode générique"]
    assert out[10] == "Save" and out[11] == "Not in catalog"
    assert out[12:14] == ["Tension batterie", "Fallback EN"]
    # Mode_other fell back to the plain "Mode" entry: translated, not missing
    assert out[14] == ["Not in catalog", "Save", "db:tm:x:description"]
    assert out[15] == "fr"


# ── language resolution order ────────────────────────────────────────────

@pytest.mark.parametrize("search,ls,attrs,expected", [
    ("?lang=fr", {"smo.lang": "en"}, {"data-default-lang": "en"}, "fr"),
    ("?lang=en", {"smo.lang": "fr"}, {"data-default-lang": "fr"}, "en"),
    ("", {"smo.lang": "fr"}, {"data-default-lang": "en"}, "fr"),
    ("", {}, {"data-default-lang": "fr"}, "fr"),
    ("", {}, {}, "en"),
    ("?lang=de", {"smo.lang": "xx"}, {"data-default-lang": "fr-CA"}, "fr"),
    ("?lang=FR-fr", {}, {}, "fr"),
])
def test_resolution_order(tmp_path, search, ls, attrs, expected):
    assert run_js(tmp_path, "return M.resolveLang();", search=search, ls=ls,
                  html_attrs=attrs) == expected


def test_wall_display_storage_false_ignores_localstorage(tmp_path):
    out = run_js(tmp_path, """
      await M.I18n.init({ storage: false });
      return [M.getLang(), M.resolveLang({storage: true})];
    """, ls={"smo.lang": "fr"})
    assert out == ["en", "fr"]


# ── applyDom round trip + setLang ────────────────────────────────────────

def test_apply_dom_round_trip_restores_exact_english(tmp_path):
    out = run_js(tmp_path, """
      const btn = new El({'data-i18n': '', 'data-i18n-title': '', title: 'Close'},
                         [new El({class: 'n'}, ['0']), '\\n   Close  ']);
      const inp = new El({'data-i18n-placeholder': 'Save', placeholder: 'Save it'}, []);
      const amp = new El({'data-i18n': ''}, ['Keyboard & design']);
      const ctx = new El({'data-i18n': '', 'data-i18n-context': 'spacecraft'}, ['Mode']);
      globalThis.__root = new El({}, [btn, inp, amp, ctx]);
      const snap = () => [btn.textContent, btn.getAttribute('title'),
                          inp.getAttribute('placeholder'), amp.textContent, ctx.textContent];
      const en0 = snap();
      await M.I18n.ready;                         // English: no DOM writes
      const en1 = snap();
      const r = await M.setLang('fr');
      const fr = snap();
      await M.setLang('en');
      const en2 = snap();
      return { en0, en1, fr, en2, r, events: __events, ls: __ls['smo.lang'],
               lang: document.documentElement.lang };
    """)
    assert out["en0"] == out["en1"] == out["en2"]
    assert out["en0"] == ["0\n   Close  ", "Close", "Save it", "Keyboard & design", "Mode"]
    # child element kept, surrounding whitespace kept, text translated
    assert out["fr"] == ["0\n   Fermer  ", "Fermer", "Save it",
                         "Clavier et conception", "Mode satellite"]
    assert out["r"] == "fr"
    assert out["events"] == ["smo:langchange:fr", "smo:langchange:en"]
    assert out["ls"] == "en" and out["lang"] == "en"


def test_setlang_keeps_explicit_query_in_step(tmp_path):
    out = run_js(tmp_path, "await M.setLang('en'); return globalThis.__replaced;",
                 search="?lang=fr&ui=modern")
    assert out == "http://h/x?lang=en&ui=modern"


def test_unsupported_setlang_is_a_no_op(tmp_path):
    assert run_js(tmp_path, "return [await M.setLang('de'), __events];") == ["en", []]


# ── shared components: English unchanged, French via shared catalog ──────

def test_components_english_unchanged_french_translated(tmp_path):
    out = run_js(tmp_path, """
      const C = await import('./components.js');
      const en = [C.renderParam({name: 'V', hex: '0x0001'}, 1), C.renderLangToggle()];
      await M.setLang('fr');
      return [...en, C.renderParam({name: 'V', hex: '0x0001'}, 1), C.renderLangToggle()];
    """)
    assert '<span class="nolimit">no limit defined</span>' in out[0]
    assert 'aria-pressed="true" aria-label="English"' in out[1]
    assert '>EN</button>' in out[1] and '>FR</button>' in out[1]
    assert 'role="group" aria-label="Language"' in out[1]
    assert "aucune limite définie" in out[2]
    assert 'data-lang="fr" lang="fr" aria-pressed="true"' in out[3]


def test_fmtnum_engineering_point_and_fmtprose_locale(tmp_path):
    out = run_js(tmp_path, """
      const F = await import('./format.js');
      return [F.fmtNum(7.26, 1), F.fmtNum(12345.678, 2), F.fmtNum(null),
              F.fmtNum(3), F.fmtProse(12345.6, 1, 'fr'), F.fmtProse(3.5, 1, 'en')];
    """)
    assert out[:4] == ["7.3", "12345.68", "—", "3"]
    assert out[4] in ("12 345,6", "12 345,6")
    assert out[5] == "3.5"
