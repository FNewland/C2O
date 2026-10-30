# Brief for document translation agents (EN to FR)

You are translating one packet of English Markdown teaching or operations material into **international/European French**. The aim is publication quality: a French aerospace engineer at CNES or ESA should find the result natural, precise and consistent.

## Read first (mandatory)
1. `/home/claude/work/i18n/STYLE_FR.md`, the binding style guide. Read all of it.
2. `/home/claude/work/i18n/glossary.csv`, the binding terminology. When a term is in the glossary, use the glossary rendering. Before starting, grep it for the domain terms in your packet.
3. `/home/claude/work/i18n/PLAN.md` for context, especially the owner rulings R1–R6.

## Hard rules
* **Translate everything a reader reads**, and nothing a machine reads.
  * Translate: prose, headings, table cells containing words, captions, alt text, list items, callouts, quiz questions and answers, and `\text{...}` words inside maths.
  * Do not translate (copy byte-for-byte): fenced code blocks, inline `code` spans, LaTeX maths, URLs and link targets, image paths, `{: .class}` / `{#id}` attribute blocks, HTML comments, HTML tags and attributes, front-matter keys, mnemonics, parameter IDs, mode enum names, procedure IDs (LEOP-001, NOM-007, WB-5.6-C012), figure and table numbers, and file names.
  * Link text in `[text](target)` is translated; the target is not.
* **Preserve structure 1:1.** Keep the same headings in the same order at the same levels, with any `{#id}` or `{: …}` suffix kept exactly. Keep the same tables with the same row and column counts, and the same lists. Do not merge, split, drop, reorder or "improve" content. **Do not fix technical errors** you notice. Record them in `NOTES.md` (see below), because the English and French must stay aligned.
* **Numbers:** every number in the English must appear in the French. Prose uses the French decimal comma and NBSP grouping (3,5 kg; 12 500 km). Values inside code, maths, procedure annotations, command arguments and telemetry thresholds an operator types keep the point (STYLE_FR §4). Times of day keep their digits.
* Typography per STYLE_FR §3, using the **real U+202F/U+00A0 characters**, never `&nbsp;`.
* Voice-loop callouts (Go/No-Go, Standby, Hold, Mark, Roger, Copy) stay in English, set in italics where the source uses them inline, per STYLE_FR.
* For proper names of Canadian organisations and laws, use their official French names where they exist (e.g. Agence spatiale canadienne (ASC); Loi sur les systèmes de télédétection spatiale (LSTS)). Keep university and company names as they are.

## How to work (resumable and chunked)
1. Your packet directory holds `en.md`. Split it mentally at `##` headings, or at `#` headings for small sections. Translate **one section at a time** and write each to `fr_parts/NNN.md` (NNN = 001, 002…, in order). Use the Write tool, one part per call, of up to about 2,500 English words. Never reconstruct the source from memory; read the exact lines with Read (offset/limit) right before translating them.
2. If `fr_parts/` already has files when you start, you are resuming. Check the last part is complete, then continue after it.
3. When all parts are written, concatenate them: `cat fr_parts/*.md > fr.md`. Make sure part boundaries reproduce the source's line breaks: each part should end exactly where the English section ended, and the joined file must have the same heading count.
4. Run `python3 /home/claude/work/i18n/mdparity.py en.md fr.md` and fix every reported problem. A reported number mismatch that is a legitimate French form (e.g. `9:00` → `9 h 00`) may stay; list it in NOTES.md. Iterate until only such justified items remain.
5. Write `NOTES.md` in the packet directory with:
   * terms you had to decide that are not in the glossary (EN → FR, with reason); these will be merged into the glossary
   * technical errors or inconsistencies spotted in the English, with line references
   * justified parity exceptions
6. Final reply, at most 150 words: word counts EN/FR, the parity result, and the most important notes.

## Quality bar
* Read each French sentence as a French engineer would. Avoid calques: « adresser », « supporter » (in the sense of "support"), « opérer un satellite », « éventuellement » (in the sense of "eventually"), noun stacks, and English word order.
* Be consistent within your packet: once a rendering is chosen for a term not in the glossary, keep it.
* Tables of telemetry or limits: translate column headers and word cells; leave IDs and values unchanged except decimal commas in reading tables per STYLE_FR §4.
* Pedagogical tone: books are formal, using « vous »; worksheets are direct imperative using « vous »; procedures use the infinitive.
