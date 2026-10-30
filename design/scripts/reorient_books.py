#!/usr/bin/env python3
"""Reorient the facilitator book to textbook voice and strip
facilitator-side cues from the learner workbook.

Patterns handled:

  Facilitator book (book.md):
    - "Begin by asking the group: *\"X?\"*"          -> textbook prose
    - "Begin by asking: *\"X?\"*"                     -> textbook prose
    - "**Discussion prompt:** *X*"                    -> "**Discussion point.** X"
    - "**Exercise:** *X*"                             -> "**Exercise.** X"
    - "Expected answers:"                             -> "Worked response:"
    - "*[Discussion]*"                                -> "*[Discussion point]*"
    - "Ask the group:"                                -> "Consider:"
    - "Walk the group through"                        -> "Walk through"
    - "Have students"                                 -> "Students should"
    - "instruct students to"                          -> "students should"
    - "On a whiteboard, draw"                         -> "Sketch"

  Workbook (workbook.md):
    - "**Discussion question:**"                       -> "**Reflect:**"
    - " (group |) discussion"                          -> " your reflection"
    - "Record key points from the [group ]discussion"  -> "Record your notes"
    - "Ask yourself: \"X\""                            -> "Consider: X"
    - "(\\d+ min)" headers                             -> stripped
    - "Refer to Session N.M, Section X.Y."             -> "Refer to the relevant chapter"

  Both books (factual updates):
    - "20 automated design agents" + count fixes
    - workflow nomenclature: add "Step N" labels
    - "MCR, SRR, PDR, CDR" -> "MCR, SRR, SDR, PDR, CDR"
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Generic factual updates applied to BOTH books
# ---------------------------------------------------------------------------

FACTUAL_FIXES = [
    # Add SDR to review-gate sequences
    (re.compile(r"\b(MCR,\s*SRR),\s*(PDR,\s*CDR)\b"), r"\1, SDR, \2"),
    (re.compile(r"\b(MCR,\s*SRR)\s+(PDR,\s*CDR)\b"), r"\1, SDR, \2"),
    # Workflow names → keep concise four-step nomenclature
    (re.compile(r"\bNeed\s*->\s*Concept\s*->\s*Requirements\s*->\s*Design\b"),
     "Step 1 Mission Need · Step 2 Concept · Step 3 Requirements · Step 4 Design"),
    (re.compile(r"\bNeed → Concept → Requirements → Design\b"),
     "Step 1 Mission Need · Step 2 Concept · Step 3 Requirements · Step 4 Design"),
    # Component library count update — keep it consistent with the KB
    (re.compile(r"\b150\+\s+component[s]?\s+across\s+\d+\s+categories\b", re.I),
     "150+ COTS components across 18 categories"),
    # 20 agents — keep but disambiguate "automated design agents" vs positions
    (re.compile(r"\b20\s+automated\s+design\s+agents\b"),
     "20 background design agents (9 Tier 1 sizing, 11 Tier 2 analysis)"),
]

# ---------------------------------------------------------------------------
# Facilitator-book voice transformation
# ---------------------------------------------------------------------------

FACILITATOR_SUBS = [
    # Strip facilitator timing cues from headings/parts (textbook tone).
    (re.compile(r'^(#{1,6}\s+[^#\n]*?)\s*\(\s*\d+\s*min(?:utes)?\s*\)\s*$', re.M), r"\1"),
    (re.compile(r'^(\*\*Part[^:]+:[^\(]+?)\s*\(\s*\d+\s*min(?:utes)?\s*\)\s*\*\*', re.M), r"\1**"),
    # "Part 2: Regulatory Environment (Tuesday AM -- 2 hours)" → drop parenthetical
    (re.compile(r'^(#{1,6}\s+[^#\n]*?)\s*\((?:Monday|Tuesday|Wednesday|Thursday|Friday)[^)]*?\d+\s*hours?\)\s*$', re.M), r"\1"),
    (re.compile(r'^(#{1,6}\s+[^#\n]*?)\s*\([^)]*?\d+\s*hours?\)\s*$', re.M), r"\1"),
    # "Duration: 2 hours" annotation at the top of a session
    (re.compile(r'^\*\*Duration:\*\*\s+[\d.]+\s*hours?\s*(?:\([^)]*\))?\s*$', re.M), ""),
    # Drop "Teaching Notes" subsection headers — vestige of facilitator era.
    # Subsequent content runs straight on as textbook prose.
    (re.compile(r'^#{2,4}\s+Teaching Notes\s*\n+', re.M), ""),
    (re.compile(r'^\*\*Teaching Notes:\*\*\s*\n+', re.M), ""),
    (re.compile(r'^\*\*Teaching Notes\.\*\*\s*\n+', re.M), ""),
    # Drop any "manual review by the facilitator" → instructor/SME
    (re.compile(r'\bmanual review by the facilitator\b', re.I),
     "manual review by an engineer"),
    (re.compile(r'\bfacilitator should\b', re.I), "instructor should"),
    (re.compile(r'\bfor the facilitator\b', re.I), "for the instructor"),
    # "Begin by asking the group: *\"How is X?\"*" -> declarative version
    # Strategy: replace the trigger phrase with neutral textbook framing.
    (re.compile(r'Begin by asking the group[: ]\s*\*?"([^"]+)"\*?\.?', re.I),
     r"Consider the question: \1"),
    (re.compile(r'Begin by asking[: ]\s*\*?"([^"]+)"\*?\.?', re.I),
     r"Consider the question: \1"),
    # Bare "Ask the group:" / "Ask the cohort:"
    (re.compile(r'\bAsk the (group|cohort|class|students)[:,]\s*', re.I), "Consider: "),
    # Discussion / exercise markers — make declarative
    (re.compile(r'\*\*Discussion prompt:\*\*\s*'), "**Discussion point.** "),
    (re.compile(r'\*\*Exercise:\*\*\s*'), "**Exercise.** "),
    (re.compile(r'\*\[Discussion\]\*'), "*[Discussion point]*"),
    (re.compile(r'\bExpected answers?:\s*', re.I), "Worked response: "),
    # Whiteboard / classroom verbs → textbook verbs
    (re.compile(r'\bOn a whiteboard,?\s*draw\b', re.I), "Sketch"),
    (re.compile(r'\bOn the whiteboard,?\s*draw\b', re.I), "Sketch"),
    (re.compile(r'\bWalk the (group|cohort|class|students) through\b', re.I),
     "Walk through"),
    (re.compile(r'\bHave students\b', re.I), "Students should"),
    (re.compile(r'\binstruct students to\b', re.I), "students should"),
    (re.compile(r'\bget students to\b', re.I), "students should"),
    # Facilitator pacing — convert "Pause for X minutes" / "Allow X minutes for"
    (re.compile(r'\bPause for (\d+) (?:min(?:utes)?|s|seconds)\.?\s*', re.I), ""),
    (re.compile(r'\bAllow (\d+) (?:min(?:utes)?) for\b', re.I), "Spend approximately \\1 minutes on"),
    # Italicised cohort-only asides
    (re.compile(r'\bthe cohort\b', re.I), "students"),
]


# ---------------------------------------------------------------------------
# Learner-workbook cue removal
# ---------------------------------------------------------------------------

WORKBOOK_SUBS = [
    # "**Discussion question:**" → reflective prompt
    (re.compile(r'\*\*Discussion question:\*\*\s*'), "**Reflection:** "),
    (re.compile(r'\*\*Discussion:\*\*\s*'), "**Reflection:** "),
    # "from the group discussion" / "from the discussion" → "below"
    (re.compile(r'\bfrom the group discussion\b'), "below"),
    (re.compile(r'\bfrom the discussion\b'), "below"),
    # "Record key points ... discussion" cleanup
    (re.compile(r'Record key points from below'), "Record your notes"),
    # "Ask yourself: \"X\"" → "Consider: X"
    (re.compile(r'Ask yourself:\s*"([^"]+)"'), r"Consider: \1"),
    (re.compile(r'\bAsk yourself\b'), "Consider"),
    # "(N min)" duration cues in headers — remove
    (re.compile(r'\s*\((\d+)\s*min(?:utes)?\)', re.I), ""),
    # Strip facilitator-only references "see facilitator notes" etc
    (re.compile(r'\(see facilitator notes\)', re.I), ""),
    (re.compile(r'\bsee facilitator notes\b', re.I), "see the textbook chapter"),
    # Replace "Refer to Session N.M Section X.Y" with simpler reference
    (re.compile(r'Refer to Session (\d+\.\d+),?\s*Section\s+(\d+\.\d+)\.?',  re.I),
     r"Refer to chapter \1"),
    (re.compile(r'Refer to Session (\d+\.\d+)\.?\s*'),
     r"Refer to chapter \1. "),
    # Group/instructor cues
    (re.compile(r'\bwith your partner\b', re.I), ""),
    (re.compile(r'\bin your team\b', re.I), ""),
    (re.compile(r'\bin small groups\b', re.I), ""),
]


# ---------------------------------------------------------------------------
# New content insertions (idempotent)
# ---------------------------------------------------------------------------

FACILITATOR_NEW_GLOSSARY = """
# Agents, Positions, and the SpaceCDF Architecture

Two distinct concepts run through this textbook and they are sometimes
conflated in industry literature. Disentangling them is essential before
the first design loop.

A **position** is a *human role* assigned to a person sitting at a console
in the Concurrent Design Facility — for example *Power Engineer*, *AOCS
Lead*, or *Mission Analyst*. SpaceCDF defines fifteen positions, each
with scoped editing rights on a subset of the design parameters.

A **design agent** is a *computational solver* that runs in the
background and converges a particular subsystem or analysis. The current
release of SpaceCDF ships twenty agents grouped in two tiers:

| Tier | Purpose | Agents |
|---|---|---|
| Tier 1 — Parametric sizing | Compute the design point of one subsystem from inputs supplied by the others | orbit · link · data · power · thermal · AOCS · propulsion · mass · structure |
| Tier 2 — Cross-system analysis | Score, check or audit the converged design | cost · risk · reliability · debris · radiation · sustainability · volume · systems · conflicts · community · TRL |

Each agent publishes three things to the design state when it runs:
its **parameters** (numbers with units, margin and confidence), its
**rationale** (a paragraph of textbook-grade reasoning), and a set of
**assumptions** that downstream agents and reviewers can interrogate.
Several agents also emit *structured intermediates* — the orbit agent
exposes a ΔV breakdown, the link agent exposes a full waterfall, the
thermal agent exposes hot- and cold-case node temperatures, the
reliability agent exposes a FMECA, and so on. Most exports surface these
intermediates as tables and figures alongside the bare numbers.

When a human position assignment changes a value, that parameter becomes
*sticky* in the design state and the agents do not overwrite it during
subsequent design loops. This is the formal handover between the human
operator and the computational solver, and it is the reason a CDF
session converges so quickly: the agents do the iterative arithmetic
while the positions do the engineering judgement.

"""

FACILITATOR_NEW_HOW_GENERATED = """
# How This Textbook Was Generated

This textbook is itself an artefact of the same Concurrent Design Facility
methodology that students will exercise during the 40-hour intensive. Its
preparation pipeline mirrors a CDF design loop in three respects: the
*source* is a structured set of Markdown chapters that describe each
session as a self-contained module; the *transformation layer* is a
Python toolchain — reorientation scripts, matplotlib figure generators,
python-docx and WeasyPrint renderers — shared with the design-review
exporters used inside the tool; and the *review layer* consists of the
SpaceCDF teaching team, who own the prose voice, the worked examples,
and the editorial judgement on what to include or omit.

## Source — per-session Markdown chapters

The textbook is assembled from forty-odd Markdown chapter files under
`docs/course/facilitator/`. Each chapter is self-contained — learning
objectives, references, key equations, worked examples, exercises — so
that an instructor can lift any one of them out and use it on its own.
The single-source build script (`docs/build_course_pdfs.sh`) concatenates
these chapter files, appends the appendices, and feeds them through the
PDF renderer.

## Voice reorientation

The book began life as a *Facilitator's Book* filled with stage
directions ("Begin by asking the group…", "Have students draw the
V-model on the whiteboard…"). A scripted reorientation pass — driven by
`scripts/reorient_books.py` — converted those directions into textbook
prose, stripped timing cues from headings, removed embedded
"Teaching Notes" subsection markers, and made the volume self-paced and
self-contained. The same pass keeps the volume aligned with the current
tool: it updates the agent count, restores the four-step workflow
nomenclature, and inserts the SDR gate into all review-gate tables.

The reorientation rules are documented in the script itself. Each rule
is a regular-expression substitution applied to the per-chapter Markdown
sources, with the *expanded* book and the workbook kept in lock-step.
If a pedagogical decision changes — say, the team chooses to keep
discussion prompts as live prompts rather than reflective questions —
the rule is edited in one place and the book is regenerated.

## Procedural figure generation

Every diagram in this volume (V-model, lifecycle gates, beta-angle
eclipse geometry, Tsiolkovsky curves, free-space path loss, antenna
patterns, ground-track sketches, link-budget waterfalls, thermal node
bars, risk index maps) is generated procedurally by a matplotlib script
under `docs/assets/figures/` using the uOttawa Horizon palette
(`uottawa_brand.py`). The procedural figures are sources of truth in the
same sense as a code listing: they can be re-rendered by re-running the
script when the underlying numerics change. There are no hand-drawn
diagrams — every line on the page is derived from a small Python
program with a reproducible numerical input.

The same matplotlib styling is used by the SpaceCDF design-review
exporters: when a study generates a Word SRR, its donut charts and link
waterfalls are drawn by the same helpers, with the same colours, that
produce the figures in this textbook. The intent is that a student
looking at a *figure* on the page of an SRR has already encountered the
same kind of figure in the textbook chapter that introduced the
underlying physics.

## Numerical worked examples — generated by running the tool

Every numerical worked example in this textbook — UniSat-1, the 3U EO
CubeSat (the running "EOSAT-1" example), ground-track timings,
link-budget closures, thermal radiator sizings — was computed by running
the SpaceCDF tool itself, so the textbook and the tool stay numerically
consistent. The relevant YAML mission descriptors live under
`configs/examples/`. If a Tier 1 agent is updated and a worked-example
number changes, the textbook reference can be regenerated by running
`python scripts/run_design.py configs/examples/<mission>.yaml` and
copying the new values into the chapter source.

This convention applies to the *Course Workbook* too: every answer key
hint in the workbook is derived from running the tool on the same YAML
mission descriptor used in the textbook.

## Document rendering

The PDF you are reading is built by `docs/build_course_pdfs.sh`:
Markdown chapters are concatenated, parsed by `python-markdown` (with
tables, fenced code, and table-of-contents extensions enabled), wrapped
in a uOttawa-styled HTML scaffold (cover banner, bilingual EN/FR
"Page X of / de Y" footer, crimson page-header rule), and rendered to
A4 PDF by WeasyPrint. The cover banner, the running header, and the
SCDF document code are the same elements you will find on every
SRR / PDR / CDR design-review bundle that the tool exports during your
design study. A reviewer holding both the textbook and a freshly
exported SRR side by side should immediately recognise that they
belong to the same documentary family.

## Validation and citation

Although AI assistance is used at every step of this pipeline, no claim
in this textbook is left ungoverned by a human author. ECSS standards,
NASA references and SMAD-4 are cited at the point of use; numerical
results are reproducible by running the tool against the published
YAML; pedagogical framing is owned by the teaching team. The AIG badge
(see the *Acknowledgement* section) is attached to every exported
document so that downstream readers can trace which contributions are
AI-assisted.

## What this means for learners

The textbook is generated by the same kind of human-plus-AI loop that
the SpaceCDF tool exposes to students. Learning to *read* AI-assisted
documents critically — checking the citations, re-deriving the numbers,
asking which voice authored which passage — is itself part of the
curriculum. The first time a student in the cohort generates an SRR
from a converged design state, they should recognise the layout, the
voice and the figure conventions of this volume in the document the
tool has just produced for them.

In other words: this is not a book *about* a tool, it is a *companion
volume* to the tool. The same hands that wrote the chapters wrote the
tool, and the same loop that closes a CubeSat design loop closes the
loop on the next edition of this book.

"""


FACILITATOR_NEW_AIG = """
# Acknowledgement — Generative AI (AIG)

This textbook was produced with the assistance of generative AI as part
of the SpaceCDF Concurrent Design Facility workflow. The design-loop
convergence, agent rationales, embedded figures and document rendering
are generated by the SpaceCDF backend (Python · matplotlib · python-docx
· WeasyPrint) guided by ECSS, NASA SEH and SMAD-4 references. Editorial
framing, worked examples, and pedagogical commentary remain owned by
the SpaceCDF teaching team. The chapter *How This Textbook Was
Generated* describes the pipeline in detail.

*Attribution follows the AIG (Assisted by Generative AI) framework —
Peters (2023), Logos IA-EN, CC BY-NC-SA 4.0 —
https://mpeters.uqo.ca/en/logos-ia-en-peters-2023/*

Any course deliverable that incorporates content from this textbook —
or from any document exported by SpaceCDF — must carry the AIG badge
and a short note describing how generative AI was used. Refusing to
use AI where it is permitted is fine; what is not acceptable is using
it without saying so.

"""


FACILITATOR_NEW_EXPORTS = """
# Design Reviews and the SpaceCDF Exports

A review gate is not merely a meeting. It is a *document set* whose
existence and contents are agreed in advance, whose generation is
traceable to a converged design state, and whose acceptance moves the
project from one ECSS phase to the next. SpaceCDF treats each review
gate as the natural anchor of an export bundle.

| Review | ECSS phase | Exported bundle | Principal contents |
|---|---|---|---|
| MCR | Pre-Phase A | Mission Concept Report | Stakeholders, MoP/TPM, alternatives, ConOps draft |
| SRR | Phase A | SRR Design-Review Pack (Word + Excel + Markdown) | Mass / power / data / cost budgets with margin, orbit and architecture figures, compliance matrix, equipment list, TRL roll-up, risk matrix, cost P-curve, WBS bar |
| SDR | Phase A/B | System Design Review Pack | SRR contents plus block diagrams, derived requirements, preliminary trade studies |
| PDR | Phase B | PDR Design-Review Pack | SRR + SDR contents plus full trade-study record, verification matrix, interface control documents |
| CDR | Phase C | CDR Design-Review Pack | PDR contents plus test plan, AIT procedures, qualification status |

In addition to the design-review packs, SpaceCDF generates a family of
*data item descriptions* (DIDs) in editable Word format: the Mission
Requirements Document (MRD), Concept of Operations (ConOps), Verification
Plan (VP), Systems Engineering Management Plan (SEMP), Risk Management
Plan (RMP), Interface Requirements Document (IRD), Test Plan, and the
Bill of Materials.  Specialist reports cover the thermal analysis, the
end-of-life deorbit plan, the Remote Sensing Space Systems Act (RSSSA)
licence application, and the verification test programme.

Every exported document uses the same uOttawa SpaceCDF course identity:
garnet cover banner with the bilingual "u Ottawa · UNIVERSITÉ D'OTTAWA"
mark, slab-bold title block, crimson section headings, the SCDF-{code}
document code, and a bilingual page footer reading "Page X of / de Y".
The intent is that a converged design state, exported the day before a
review, arrives in the reviewers' hands looking and reading the same as
the supporting course material.

"""

WORKBOOK_NEW_PREFACE = """
# Note to the Learner

This workbook is the companion volume to the *SpaceCDF Textbook*. It is
designed to be used by you, alone or in a study team, at your own pace —
no facilitator or instructor is required. Each chapter contains
worksheets, calculations to perform, and reflections to write. Hints
direct you back to the textbook chapter that introduces the underlying
theory.

When the workbook mentions the SpaceCDF tool, you should have a working
installation in front of you (see the *SpaceCDF Installation Guide*).
The tool runs entirely on your own computer; instructions for navigation
are written so that you can perform the steps without supervision.

Spaces marked with a thin pencil rule are intended for your own notes.
There are no marking rubrics in this volume.

# Acknowledgement — Generative AI (AIG)

This workbook was produced with the assistance of generative AI as part
of the SpaceCDF Concurrent Design Facility workflow. The worksheet
content, calculation prompts, equation sheets and embedded figures are
generated by the SpaceCDF toolchain (Python · matplotlib · python-docx)
guided by ECSS, NASA SEH and SMAD-4 references. Editorial framing and
pedagogical commentary remain owned by the SpaceCDF teaching team.

*Attribution follows the AIG (Assisted by Generative AI) framework —
Peters (2023), Logos IA-EN, CC BY-NC-SA 4.0 —
https://mpeters.uqo.ca/en/logos-ia-en-peters-2023/*

Any course deliverable that you produce based on this workbook — or
any document exported by SpaceCDF — must carry the AIG badge and a
short note describing how generative AI was used. Refusing to use AI
where it is permitted is fine; what is not acceptable is using it
without saying so.

"""


# ---------------------------------------------------------------------------
# Apply transforms
# ---------------------------------------------------------------------------

def apply_subs(text: str, subs):
    n_total = 0
    for pat, repl in subs:
        text, n = pat.subn(repl, text)
        n_total += n
    return text, n_total


def transform_facilitator(text: str) -> tuple[str, int]:
    """Convert facilitator-side stage directions to textbook prose."""
    text, n1 = apply_subs(text, FACILITATOR_SUBS)
    text, n2 = apply_subs(text, FACTUAL_FIXES)
    # If a prior version of the front-matter (without AIG / generation chapter)
    # was injected, strip those blocks first so we can re-emit the canonical
    # versions.
    if "Agents, Positions, and the SpaceCDF Architecture" in text and "Peters (2023)" not in text:
        text = re.sub(
            r"# Agents, Positions, and the SpaceCDF Architecture.*?(?=^# Design Reviews and the SpaceCDF Exports|^# Part 1)",
            "", text, count=1, flags=re.S | re.M,
        )
        text = re.sub(
            r"# Design Reviews and the SpaceCDF Exports.*?(?=^# Part 1)",
            "", text, count=1, flags=re.S | re.M,
        )
    # Insert the new front-matter chapters (AIG + How This Textbook Was Generated
    # + glossary + exports) right before Part 1.  Idempotent on the AIG
    # sentinel.
    if "Peters (2023)" not in text:
        anchors = [
            "# Part 1 — Course Lectures",
            "# Part 1 — Per-Session Teaching Notes",
        ]
        front_matter = (
            FACILITATOR_NEW_AIG
            + FACILITATOR_NEW_HOW_GENERATED
            + FACILITATOR_NEW_GLOSSARY
            + FACILITATOR_NEW_EXPORTS
        )
        for anchor in anchors:
            if anchor in text:
                text = text.replace(anchor, front_matter + anchor, 1)
                break
    # Update front-matter title to reflect textbook orientation
    text = re.sub(r'title:\s*"SpaceCDF Facilitator\'s Book"',
                  'title: "SpaceCDF — A Course Textbook in Concurrent Spacecraft Design"', text)
    text = re.sub(r'subtitle:\s*"Teaching reference for the 40-hour Concurrent Design Facility intensive"',
                  'subtitle: "Companion textbook for the SpaceCDF 40-hour Concurrent Design Facility programme"', text)
    # Strip the redundant top-of-body H1 (the cover already shows the title).
    # This prevents the PDF builder forcing a near-empty page 3 just for the
    # book title.
    text = re.sub(r"^# Facilitator's Book\s*\n+", "", text, count=1, flags=re.M)
    text = re.sub(r"^# SpaceCDF — A Course Textbook\s*\n+", "", text, count=1, flags=re.M)
    # Rewrite the "How to use this book" intro that still mentions facilitators
    text = re.sub(
        r"The Facilitator's Book is the teaching reference for the SpaceCDF\s*\n?\s*40-hour intensive\.\s*It is organised in four\s*\n?\s*parts:",
        "This textbook is the SpaceCDF course volume. It accompanies the\n"
        "40-hour Concurrent Design Facility programme and is organised in four\nparts:",
        text,
    )
    text = re.sub(r"\bteaching notes\b", "course chapters", text)
    text = re.sub(r"per CDF session", "per course session", text)
    text = re.sub(
        r"The book is paired with the \*Learner's Workbook\*, which carries\s*\n?the worksheets the cohort fills in\.",
        "The textbook is paired with the *Course Workbook*, which contains the\n"
        "worksheets students complete.",
        text,
    )
    # General mop-up of remaining "Facilitator's Book" / "Facilitator Book" references
    text = re.sub(r"Facilitator['’]s Book", "Course Textbook", text)
    text = re.sub(r"Facilitator Book", "Course Textbook", text)
    # Rename "Part 1 — Per-Session Teaching Notes" → "Part 1 — Course Lectures"
    text = text.replace("# Part 1 — Per-Session Teaching Notes",
                        "# Part 1 — Course Lectures")
    text = text.replace("# Part 2 — Per-Role Background Briefings",
                        "# Part 2 — Engineering-Position Reference")
    text = text.replace("# Part 3 — Position Appendix",
                        "# Part 3 — Position Quick-Reference Cards")
    text = text.replace("# Part 4 — Verification Appendix",
                        "# Part 4 — Equation Verification Appendix")
    return text, n1 + n2


def transform_workbook(text: str) -> tuple[str, int]:
    text, n1 = apply_subs(text, WORKBOOK_SUBS)
    text, n2 = apply_subs(text, FACTUAL_FIXES)
    # If a previous preface (without the AIG section) was injected, strip it
    # so we can re-insert the current canonical version.
    if "Note to the Learner" in text and "Peters (2023)" not in text:
        text = re.sub(
            r"# Note to the Learner.*?(?=^#\s|\Z)",
            "", text, count=1, flags=re.S | re.M,
        )
    # Prepend the learner preface (idempotent on the new content sentinel).
    # Insert *before* the first content H1 (typically "Worksheet 1.1") so
    # that the preface and the AIG section open the volume.
    if "Peters (2023)" not in text:
        m = re.search(r'^#\s+[^\n]+', text, re.M)
        if m:
            insert_at = m.start()
            text = text[:insert_at] + WORKBOOK_NEW_PREFACE + text[insert_at:]
        else:
            text = WORKBOOK_NEW_PREFACE + text
    # Update title metadata
    text = re.sub(r'title:\s*"SpaceCDF Learner\'s Workbook"',
                  'title: "SpaceCDF — Course Workbook"', text)
    text = re.sub(r'subtitle:\s*"Worksheets, exercises and reflections for the 40-hour Concurrent Design Facility intensive"',
                  'subtitle: "Self-paced worksheets, exercises and reflections to accompany the SpaceCDF textbook"', text)
    # Strip the redundant top-of-body H1 — the cover already shows the title.
    text = re.sub(r"^# Learner's Workbook\s*\n+", "", text, count=1, flags=re.M)
    text = re.sub(r"^# SpaceCDF — Course Workbook\s*\n+", "", text, count=1, flags=re.M)
    text = re.sub(r"Learner['’]s Workbook", "Course Workbook", text)
    return text, n1 + n2


def apply_to_file(path: Path, transform, *, label: str) -> int:
    """Apply a transform function to a single file (in-place)."""
    if not path.exists():
        return 0
    src = path.read_text()
    new, n = transform(src)
    if new != src:
        path.write_text(new)
    print(f"  {label:32s} {n:>4} subs, {len(new)-len(src):+6d} bytes — {path.name}")
    return n


def transform_facilitator_chapter(text: str) -> tuple[str, int]:
    """Per-session variant: skip the global glossary insertion."""
    text, n1 = apply_subs(text, FACILITATOR_SUBS)
    text, n2 = apply_subs(text, FACTUAL_FIXES)
    return text, n1 + n2


def transform_workbook_chapter(text: str) -> tuple[str, int]:
    """Per-worksheet variant: skip the preface insertion."""
    text, n1 = apply_subs(text, WORKBOOK_SUBS)
    text, n2 = apply_subs(text, FACTUAL_FIXES)
    return text, n1 + n2


def main(argv):
    base = Path("/Users/FNewland/SpaceCDF/docs/course")
    if len(argv) > 1:
        base = Path(argv[1])
    fac = base / "facilitator_book_expanded.md"
    wb = base / "learner_workbook_expanded.md"

    if not fac.exists() or not wb.exists():
        print(f"Missing source files in {base}", file=sys.stderr)
        return 1

    # --- 1) the single-source 'expanded' books -----------------------------
    print("Single-source books:")
    total = apply_to_file(fac, transform_facilitator, label="facilitator_book_expanded")
    total += apply_to_file(wb, transform_workbook, label="learner_workbook_expanded")

    # --- 2) per-session facilitator chapters -------------------------------
    print("\nFacilitator per-session chapters:")
    fac_dir = base / "facilitator"
    if fac_dir.exists():
        for p in sorted(fac_dir.glob("*.md")):
            total += apply_to_file(p, transform_facilitator_chapter,
                                   label="facilitator/" + p.stem)

    # --- 3) per-worksheet learner chapters ---------------------------------
    print("\nLearner per-worksheet chapters:")
    wb_dir = base / "learner"
    if wb_dir.exists():
        for p in sorted(wb_dir.glob("*.md")):
            total += apply_to_file(p, transform_workbook_chapter,
                                   label="learner/" + p.stem)

    print(f"\nTotal substitutions across all files: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
