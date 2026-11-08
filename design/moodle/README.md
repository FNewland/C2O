# ORBIT NORTH open Moodle course

A bilingual (EN/FR) Moodle 5.2 course holding the course videos (H5P), lecture
slides, Week 3 handouts, the open textbook and a team workspace. It has **no
assignments, quizzes or other places to submit work, and nothing is graded**: it is
meant for a site outside the university firewall.

| Section | Contents |
|---|---|
| General | Welcome, how the videos work, syllabus, announcements |
| Week 1 · Days 1–2, Week 2 · Days 1–5, Week 3 · Days 1–5 | Day summary with the agenda and textbook chapters; lecture slides (L01–L14); the videos for that day; Week 3 handouts |
| Team workspace | How to use it; *Team room* forum; *Showcase drafts* collaborative wiki |
| Textbook, workbook and references | Open textbook (CC BY 4.0), course workbook, course textbook with the operations part |

Every name and text is a pair of `<span lang="en|fr" class="multilang">` spans. Each
video page carries the EN and the FR `.h5p`; the multilang filter shows the one for
the viewer's language.

## Restore on the site

Before restoring, as a site admin:

1. **Filters**: enable *Multi-Language Content* and set it to apply to
   *content and headings* (Site administration → Plugins → Filters). Enable *Display
   H5P* too.
2. **Language**: install the French language pack and turn on the language menu.
3. Restore as an admin so the H5P libraries in the packages can deploy.

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
# 3. manifest (needs the built videos in video/out/<id>/<id>.{en,fr}.h5p)
cd design/moodle/course && python3 manifest.py
# 4. build the course on a Moodle and back it up without users
MOODLE_CONFIG=/path/to/moodle/config.php php build_course.php --category=1 --out=orbit_north.mbz
```

The video packages must carry the H5P editor libraries (`python -m c2ovideo repack`)
or Moodle refuses them.

## Section banners (Edwiser card format)

`banners/make_banners.py` draws 15 text-free 1200×675 banners (course, the 12
days numbered 1.1–3.5, team workspace, references) in the deck palette, so one
image serves both languages. Set them per section in the card format's section
settings after restore.
