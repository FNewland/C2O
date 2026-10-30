# Addendum for multi-file, in-repo packets

Everything in BRIEF_DOCS.md applies. The differences:

* Your packet is a **list of English files**, each with a target French path. Create the directories you need. Write each French file **directly at its target path**.
* For a file longer than about 2,500 words, write parts first to `/home/claude/work/xlate/<PACKET>/parts/<basename>/NNN.md` and concatenate them into the target. Shorter files can be written in one go.
* After each file is done, run `python3 /home/claude/work/i18n/mdparity.py <en> <fr>` and fix the file until parity holds, apart from exceptions you have listed.
* Keep one `NOTES.md` at `/home/claude/work/xlate/<PACKET>/NOTES.md`.
* **Resuming:** if a target already exists and passes parity, skip it.
* When all files are done, run the repo's own checker from the repo root (`/home/claude/work/smo` or `/home/claude/work/cdf`): `python3 -m tools.i18n check`. Fix every error it reports for your files. Warnings about other packets' files are not your concern.
* Terminology consistency with the books already translated: when your text duplicates or closely follows a passage in the French ops book `/home/claude/work/out/course_fr/orbit_north_week3.md` or the French course textbook `/home/claude/work/out/course_fr/facilitator_book_expanded.md` (EN originals in `/home/claude/work/drive_course/`), reuse their wording. Grep them for the term or procedure title. The `NOTES.md` files under `/home/claude/work/xlate/O3`, `O4a`, `O4b` and `W2` list French procedure titles (LEOP, COM, NOM, CTG, EMG) that have already been chosen. **Use the same titles.**

## Extra rules for operations procedures (`configs/eosat1/procedures/**`)
* These French files are **display-only**: the MCS runner always executes the English procedure. Even so, keep every parsed annotation byte-identical, including the keys `**TC:**`, `**Verify:**`, `**LABEL:**`, `**BRANCH:**`, `**GO/NO-GO:**`, `**Action:**`, `**Note:**` and everything in backticks. That way a French step maps 1:1 onto the English step the runner shows as active.
* STYLE_FR §13 applies: actions use the infinitive. **Never express branching or step jumps in French prose** (no « passer à l'étape 3 », « aller à », « sauter », « reprendre à l'étape »). The checker treats them as errors. Where the English says "proceed to Step N", either keep the English-parsed BRANCH annotation as it is, or rephrase without naming a step jump and note the case.
* YAML front matter: keep the keys and any IDs; translate only `title:`/`description:`-style human text values. If unsure whether a value is parsed, leave it English and note it.
