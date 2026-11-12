<?php
namespace report_c2ostats;

defined('MOODLE_INTERNAL') || die();

/**
 * Aggregate statistics only. Nothing here returns a user id or a name: every figure is a count of
 * students (enrolled with mod/h5pactivity:submit, so teachers are left out), and any count under
 * the threshold is reported as suppressed, together with the rates computed from it.
 *
 * Videos are the course's H5P activities whose idnumber is <VIDEO>-EN or <VIDEO>-FR (the course
 * builder sets them); the language of the activity is the language the student watched in.
 */
class stats {
    /** Smallest count shown; smaller groups are hidden so no one can be singled out. */
    const MIN = 5;

    /** @var \stdClass */
    private $course;
    /** @var \context_course */
    private $context;
    /** @var array [sql, params] of the students */
    private $students;

    public function __construct(\stdClass $course, int $min = self::MIN) {
        $this->course = $course;
        $this->context = \context_course::instance($course->id);
        $this->min = $min;
        [$sql, $params] = get_enrolled_sql($this->context, 'mod/h5pactivity:submit', 0, true);
        $this->students = [$sql, $params];
    }

    /** @var int */
    public $min;

    /** Shown value of a count: the number, or null when it is under the threshold. */
    public function shown(int $n): ?int {
        return ($n === 0 || $n >= $this->min) ? $n : null;
    }

    public function student_count(): int {
        global $DB;
        [$sql, $params] = $this->students;
        return (int)$DB->count_records_sql("SELECT COUNT(1) FROM ($sql) s", $params);
    }

    /**
     * The videos in course order: [video => ['name' => ..., 'section' => ..., 'cms' => ['EN' => cm, 'FR' => cm]]].
     */
    public function videos(): array {
        $modinfo = get_fast_modinfo($this->course);
        $out = [];
        foreach ($modinfo->get_cms() as $cm) {
            if ($cm->modname !== 'h5pactivity' || $cm->deletioninprogress) {
                continue;
            }
            if (!preg_match('/^(.+)-(EN|FR)$/', (string)$cm->idnumber, $m)) {
                continue;
            }
            [$all, $vid, $lang] = $m;
            if (!isset($out[$vid])) {
                $out[$vid] = ['video' => $vid, 'section' => $cm->sectionnum,
                              'sectionname' => get_section_name($this->course, $cm->sectionnum), 'cms' => []];
            }
            $out[$vid]['cms'][$lang] = $cm;
            if ($lang === 'EN' || empty($out[$vid]['name'])) {
                // "Video · <title> · English" → "<title>"
                $name = format_string($cm->name, true, ['context' => $cm->context]);
                $parts = preg_split('/\s+·\s+/u', $name);
                $out[$vid]['name'] = count($parts) === 3 ? $parts[1] : $name;
            }
        }
        return $out;
    }

    /** Distinct students per course module for one table/column: [cmid => n]. */
    private function per_cm(string $from, string $cmcol, string $where, array $cmids, array $params = []): array {
        global $DB;
        if (!$cmids) {
            return [];
        }
        [$sql, $sparams] = $this->students;
        [$in, $inparams] = $DB->get_in_or_equal($cmids, SQL_PARAMS_NAMED, 'cm');
        $rows = $DB->get_records_sql("SELECT $cmcol AS cmid, COUNT(DISTINCT t.userid) AS n
                                        FROM $from
                                        JOIN ($sql) s ON s.id = t.userid
                                       WHERE $cmcol $in AND $where
                                    GROUP BY $cmcol", $sparams + $inparams + $params);
        return array_map(fn($r) => (int)$r->n, $rows);
    }

    /**
     * One row per video and language: opened, finished (completion), answered (an attempt with a
     * score), mean first-attempt score. Plus 'either': students who finished it in either language.
     */
    public function video_rows(): array {
        global $DB;
        $videos = $this->videos();
        $cmids = [];
        foreach ($videos as $v) {
            foreach ($v['cms'] as $cm) {
                $cmids[] = $cm->id;
            }
        }
        $opened = $this->per_cm('{course_modules_viewed} t', 't.coursemoduleid', '1 = 1', $cmids);
        $done = $this->per_cm('{course_modules_completion} t', 't.coursemoduleid', 't.completionstate > 0', $cmids);
        $answered = $this->per_cm('{h5pactivity_attempts} t JOIN {course_modules} cm ON cm.instance = t.h5pactivityid
                                   JOIN {modules} md ON md.id = cm.module AND md.name = \'h5pactivity\'',
                                  'cm.id', 't.maxscore > 0', $cmids);
        // Mean first-attempt score (scaled 0..1) per activity, over students only.
        [$sql, $sparams] = $this->students;
        $scores = [];
        if ($cmids) {
            [$in, $inparams] = $DB->get_in_or_equal($cmids, SQL_PARAMS_NAMED, 'cm');
            $scores = $DB->get_records_sql("SELECT cm.id AS cmid, AVG(t.scaled) AS mean, COUNT(1) AS n
                                              FROM {h5pactivity_attempts} t
                                              JOIN {course_modules} cm ON cm.instance = t.h5pactivityid
                                              JOIN {modules} md ON md.id = cm.module AND md.name = 'h5pactivity'
                                              JOIN ($sql) s ON s.id = t.userid
                                             WHERE cm.id $in AND t.attempt = 1 AND t.maxscore > 0
                                          GROUP BY cm.id", $sparams + $inparams);
        }
        $either = [];
        foreach ($videos as $vid => $v) {
            $ids = array_map(fn($cm) => $cm->id, array_values($v['cms']));
            [$in, $inparams] = $DB->get_in_or_equal($ids, SQL_PARAMS_NAMED, 'cm');
            $either[$vid] = (int)$DB->count_records_sql("SELECT COUNT(DISTINCT t.userid)
                                                           FROM {course_modules_completion} t
                                                           JOIN ($sql) s ON s.id = t.userid
                                                          WHERE t.coursemoduleid $in AND t.completionstate > 0",
                                                        $sparams + $inparams);
        }
        $rows = [];
        foreach ($videos as $vid => $v) {
            $row = ['video' => $vid, 'name' => $v['name'], 'section' => $v['sectionname'],
                    'either' => $this->shown($either[$vid]), 'lang' => []];
            foreach (['EN', 'FR'] as $lang) {
                if (empty($v['cms'][$lang])) {
                    continue;
                }
                $id = $v['cms'][$lang]->id;
                $sc = $scores[$id] ?? null;
                $n = $sc ? (int)$sc->n : 0;
                $row['lang'][$lang] = [
                    'cmid' => (int)$id,
                    'opened' => $this->shown($opened[$id] ?? 0),
                    'finished' => $this->shown($done[$id] ?? 0),
                    'answered' => $this->shown($answered[$id] ?? 0),
                    'meanfirst' => ($n >= $this->min) ? round(100 * (float)$sc->mean) : null,
                ];
            }
            $rows[] = $row;
        }
        return $rows;
    }

    /**
     * Per question, first attempts only: how many students answered and the share right first
     * time, hardest first. Questions answered by fewer than the threshold are left out.
     */
    public function question_rows(): array {
        global $DB;
        $videos = $this->videos();
        $bycm = [];
        foreach ($videos as $vid => $v) {
            foreach ($v['cms'] as $lang => $cm) {
                $bycm[$cm->id] = [$vid, $lang, $v['name']];
            }
        }
        if (!$bycm) {
            return [];
        }
        [$sql, $sparams] = $this->students;
        [$in, $inparams] = $DB->get_in_or_equal(array_keys($bycm), SQL_PARAMS_NAMED, 'cm');
        $rs = $DB->get_recordset_sql("SELECT r.id, cm.id AS cmid, r.subcontent, r.description, r.interactiontype,
                                             r.rawscore, r.maxscore
                                        FROM {h5pactivity_attempts_results} r
                                        JOIN {h5pactivity_attempts} a ON a.id = r.attemptid AND a.attempt = 1
                                        JOIN {course_modules} cm ON cm.instance = a.h5pactivityid
                                        JOIN {modules} md ON md.id = cm.module AND md.name = 'h5pactivity'
                                        JOIN ($sql) s ON s.id = a.userid
                                       WHERE cm.id $in AND r.subcontent <> '' AND r.maxscore > 0",
                                     $sparams + $inparams);
        $q = [];
        foreach ($rs as $r) {
            $k = $r->cmid . '|' . $r->subcontent;
            if (!isset($q[$k])) {
                [$vid, $lang, $vname] = $bycm[$r->cmid];
                $q[$k] = ['video' => $vid, 'lang' => $lang, 'videoname' => $vname, 'cmid' => (int)$r->cmid,
                          'question' => shorten_text(trim(strip_tags(html_entity_decode((string)$r->description))), 160),
                          'type' => $r->interactiontype, 'n' => 0, 'right' => 0];
            }
            $q[$k]['n']++;
            if ((float)$r->rawscore >= (float)$r->maxscore) {
                $q[$k]['right']++;
            }
        }
        $rs->close();
        $out = [];
        foreach ($q as $row) {
            if ($row['n'] < $this->min) {
                continue;
            }
            $row['pct'] = (int)round(100 * $row['right'] / $row['n']);
            unset($row['right']);
            $out[] = $row;
        }
        usort($out, fn($a, $b) => [$a['pct'], $b['n']] <=> [$b['pct'], $a['n']]);
        return $out;
    }
}
