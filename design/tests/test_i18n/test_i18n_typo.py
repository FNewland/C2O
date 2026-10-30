"""French typography fixer: fixes prose, never touches code, maths, URLs, markup."""
from tools.i18n import typo

N, B = " ", " "


def test_prose_rules():
    assert typo.fix("Pourquoi ? Voilà ! Ainsi ; enfin : fin.") == \
        f"Pourquoi{N}? Voilà{N}! Ainsi{N}; enfin{B}: fin."
    assert typo.fix("Il dit «bonjour» puis « salut »") == f"Il dit «{N}bonjour{N}» puis «{N}salut{N}»"
    assert typo.fix("Fin?") == f"Fin{N}?"


def test_idempotent():
    s = "Pourquoi ? « oui » : non !"
    assert typo.fix(typo.fix(s)) == typo.fix(s)


def test_protected_regions_untouched():
    src = (
        "---\ntitle: Démo\nlang: fr\n---\n"
        "Code `a ? b : c;` et $f(x): x!$ puis $$y = a ? b : c$$.\n"
        "Lien [voir](https://ex.com/a?b=c:d) et https://ex.org/x?y=1 ici.\n"
        "<!-- note: keep! --> <span title=\"a: b\">x</span> {: .class} {#id}\n"
        "**TC:** `CONNECTION_TEST` puis **Verify:** ok\n"
        "\\(a ? b\\) et {{count}}?\n"
        "```\nprint('a ? b : c;')\n```\n"
        "[ref]: https://ex.com/a?b\n"
        "| a | b |\n|:---|---:|\n"
        "Heure 12:30 et ratio 3:2.\n"
    )
    out = typo.fix(src)
    for keep in ("title: Démo", "`a ? b : c;`", "$f(x): x!$", "$$y = a ? b : c$$",
                 "(https://ex.com/a?b=c:d)", "https://ex.org/x?y=1", "<!-- note: keep! -->",
                 'title="a: b"', "{: .class}", "**TC:**", "**Verify:**", "\\(a ? b\\)",
                 "print('a ? b : c;')", "[ref]: https://ex.com/a?b", "|:---|---:|", "12:30", "3:2"):
        assert keep in out, keep
    assert f"{{{{count}}}}{N}?" in out


def test_bold_label_colon():
    assert typo.fix("**Sous-système :** EPS") == f"**Sous-système{B}:** EPS"


def test_non_markdown_mode():
    assert typo.fix("Valeur {{v}} ?", markdown=False) == f"Valeur {{{{v}}}}{N}?"
