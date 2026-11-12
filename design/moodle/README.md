# ORBIT NORTH open Moodle course

A bilingual (EN/FR) Moodle 5.2 course holding the course videos (H5P), lecture
slides, handouts, the assignment instructions with the program rubrics, the open
textbook and a project space shared by all teams. It has **no place to submit
graded work**: it is meant for a site outside the university firewall, so every
assignment page ends with "upload this to Brightspace for grading and feedback".

| Section | Contents |
|---|---|
| General | Welcome, how the videos work, syllabus, announcements |
| Assignments, rubrics and AI use | How to use and declare generative AI (AIG/GIA levels); how the assessments map to the program outcomes; one page per assignment A1–A9: week, who, why, what to produce, the steps, the videos and handouts that help, the CLO rubric rows with the expected levels outlined, the AI declaration and the Brightspace step |
| Weeks 1–12 (12-week term, the default) | Week summary with the lecture and studio and the textbook chapters; lecture slides (L01–L14); the videos for that week; operations handouts. Introduction weeks 1–2 (the CDF opens in the week 2 studio), design to the PDR in week 7, operations training weeks 8–9, simulations weeks 10–11, review of the whole mission in week 12 |
| or Week 1 · Days 1–2, Week 2 · Days 1–5, Week 3 · Days 1–5 (`C2O_COURSE_LAYOUT=intensive`) | The same items for the three-week summer intensive, day by day |
| Project space | Shared by all teams: how to use it; *Team documents* database (team, kind, made with C2O tool, file, decision or summary, **AI use** — required, status, *ready for the public site*); *Team room* forum; *Showcase drafts* collaborative wiki |
| Textbook, workbook and references | Open textbook (CC BY 4.0), course workbook, course textbook with the operations part |

Every name and text is a pair of `<span lang="en|fr" class="multilang">` spans
(longer pages carry two blocks, one shown per language).

## Videos, tracking and progressive release

Each video is two tracked H5P activities, English and French (`mod_h5pactivity`,
idnumbers `<VIDEO>-EN` / `<VIDEO>-FR`). Everything is visible from day one, but
each video and the handouts that follow it **open once the previous video is
finished in either language**; a locked item shows what unlocks it.

- *Finished* means the answers were recorded (videos with questions) or the video
  was opened (the walkthroughs V-SCDF-08…24 have no questions and send no score).
- Answers are practice only: the grade items are hidden and the gradebook is off.
  They are kept to unlock the next item and for the anonymous statistics below.
- Completion tracking is on for the course; nothing is required for a grade.

## Instructor statistics (report_c2ostats)

`plugins/report_c2ostats` is a small course report: *Course → Reports → Course
video statistics* (teachers and managers only). Per video and language: students
who opened it, finished it, the mean first-attempt score; finished in either
language; then every question ordered hardest first (share right first time,
first attempts only). **Counts only, no names; any group under 5 shows as "<5"
and no rate is computed from it.** Both tables download as CSV.

Install: copy the folder to `<moodle>/public/report/c2ostats` (Moodle 5.x; to
`<moodle>/report/c2ostats` on 4.5), then `php admin/cli/upgrade.php`. It stores
nothing of its own.

## Team documents to the public site

Entries in *Team documents* marked *Ready for the public site* are the candidates
for the WordPress community site: export them from the database activity
(*Export entries*, CSV with the files) and publish after checking the AI-use field
and the team's consent.

## Restore on the site

Before restoring, as a site admin:

1. **Filters**: enable *Multi-Language Content* and set it to apply to
   *content and headings* (Site administration → Plugins → Filters). Enable *Display
   H5P* too.
2. **Language**: install the French language pack and turn on the language menu.
3. Restore as an admin so the H5P libraries in the packages can deploy.

4. Install `report_c2ostats` (below) if you want the statistics.

Then, from the Moodle directory (5.2 keeps CLI scripts under `admin/cli`, the web
root under `public/`):

```bash
php admin/cli/restore_backup.php --file=/path/to/orbit_north.mbz --categoryid=<id>
```

The web restore works too if the upload limit allows an ~880 MB file.

## Rebuilding

```bash
# 1. slides: design/moodle/decks/src/L01..L14.yaml -> decks/out/*.{en,fr}.pdf
cd design/moodle/decks && npm install && python3 render.py
# 2. fresh PDFs of the books and handouts (writes design/docs/pdf/{en,fr})
cd design/docs && python3 build_course_books.py --lang en --only textbook workbook week3 \
  && python3 build_course_books.py --lang fr --only textbook workbook week3
# 3. manifest (needs the built videos in video/out/<id>/<id>.{en,fr}.h5p);
#    12-week term by default, C2O_COURSE_LAYOUT=intensive for the three-week version
cd design/moodle/course && python3 manifest.py
# 4. build the course on a Moodle and back it up without users
MOODLE_CONFIG=/path/to/moodle/config.php php build_course.php --category=1 --out=orbit_north.mbz
```

### Updating the course on the live site

Step 3 can gather everything the server needs into one folder instead
(`manifest.json`, `build_course.php`, `files/`):

```bash
cd design/moodle/course && python3 manifest.py --bundle ~/orbit_north_bundle
rsync -av --delete ~/orbit_north_bundle/ <server>:orbit_north_bundle/
# on the server
MOODLE_CONFIG=/path/to/moodle/config.php php ~/orbit_north_bundle/build_course.php \
    --category=<id> --shortname=ORBIT-NORTH-NEW --nobackup
```

That builds the new version as a second course next to the old one (`--shortname`
avoids the clash with the existing `ORBIT-NORTH`; `--nobackup` skips the .mbz).
Check it, then hide or delete the old course and give the new one its shortname
back. Deleting the old course deletes its forum posts and wiki pages: copy anything
students wrote first.

The video packages must carry the H5P editor libraries (`python -m c2ovideo repack`)
or Moodle refuses them.

## Section banners (Edwiser card format)

`banners/make_banners.py` draws 15 text-free 1200×675 banners (course, the 12
days numbered 1.1–3.5, team workspace, references) in the deck palette, so one
image serves both languages. Set them per section in the card format's section
settings after restore.
