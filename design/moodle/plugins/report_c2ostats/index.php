<?php
// C2O course statistics: aggregate and anonymous, by language. No names, no individual rows.
require(__DIR__ . '/../../config.php');

$id = required_param('id', PARAM_INT);
$download = optional_param('download', '', PARAM_ALPHA);
$course = get_course($id);
require_login($course);
$context = context_course::instance($course->id);
require_capability('report/c2ostats:view', $context);

$url = new moodle_url('/report/c2ostats/index.php', ['id' => $course->id]);
$PAGE->set_url($url);
$PAGE->set_pagelayout('report');
$PAGE->set_title(get_string('pluginname', 'report_c2ostats'));
$PAGE->set_heading(format_string($course->fullname, true, ['context' => $context]));

$stats = new \report_c2ostats\stats($course);
$videos = $stats->video_rows();
$questions = $stats->question_rows();
$S = fn($k, $a = null) => get_string($k, 'report_c2ostats', $a);
$cell = fn($v) => $v === null ? '<' . $stats->min : (string)$v;

if ($download === 'videos' || $download === 'questions') {
    \core\session\manager::write_close();
    $name = clean_filename($course->shortname . '-' . $download . '.csv');
    header('Content-Type: text/csv; charset=utf-8');
    header('Content-Disposition: attachment; filename="' . $name . '"');
    $out = fopen('php://output', 'w');
    fwrite($out, "\xEF\xBB\xBF");
    if ($download === 'videos') {
        fputcsv($out, ['video', 'section', 'title', 'finished_either',
                       'en_opened', 'en_finished', 'en_answered', 'en_mean_first_pct',
                       'fr_opened', 'fr_finished', 'fr_answered', 'fr_mean_first_pct']);
        foreach ($videos as $r) {
            $row = [$r['video'], strip_tags($r['section']), strip_tags($r['name']), $cell($r['either'])];
            foreach (['EN', 'FR'] as $l) {
                $x = $r['lang'][$l] ?? null;
                $row = array_merge($row, $x ? [$cell($x['opened']), $cell($x['finished']), $cell($x['answered']),
                                               $x['meanfirst'] ?? ''] : ['', '', '', '']);
            }
            fputcsv($out, $row);
        }
    } else {
        fputcsv($out, ['video', 'language', 'question', 'type', 'students_first_attempt', 'right_first_time_pct']);
        foreach ($questions as $q) {
            fputcsv($out, [$q['video'], $q['lang'], $q['question'], $q['type'], $q['n'], $q['pct']]);
        }
    }
    fclose($out);
    exit;
}

$bar = function (?int $n, int $of, string $cls = '') {
    if ($n === null || $of <= 0) {
        return '';
    }
    $w = max(0, min(100, round(100 * $n / $of)));
    return '<div class="c2os-bar ' . $cls . '" aria-hidden="true"><span style="width:' . $w . '%"></span></div>';
};
$pctbar = function (?int $p) {
    if ($p === null) {
        return '';
    }
    $cls = $p < 50 ? 'low' : ($p < 75 ? 'mid' : 'high');
    return '<div class="c2os-bar ' . $cls . '" aria-hidden="true"><span style="width:' . $p . '%"></span></div>';
};

echo $OUTPUT->header();
echo '<style>
.c2os-bar{height:6px;background:#e9ecef;border-radius:3px;margin-top:3px;min-width:60px}
.c2os-bar span{display:block;height:100%;border-radius:3px;background:#0f6cbf}
.c2os-bar.fr span{background:#6f42c1}.c2os-bar.low span{background:#ca3120}.c2os-bar.mid span{background:#f0ad4e}
.c2os-bar.high span{background:#357a32}
.c2os table td,.c2os table th{vertical-align:top}
.c2os .num{text-align:right;white-space:nowrap;width:9%}
.c2os td.title{min-width:18rem}
.c2os .vid{font-size:.75rem;color:#6a737b;margin-right:.4rem}
.c2os-tiles{display:flex;flex-wrap:wrap;gap:12px;margin:1rem 0}
.c2os-tile{border:1px solid #dee2e6;border-radius:8px;padding:.75rem 1rem;min-width:160px}
.c2os-tile b{display:block;font-size:1.6rem}
</style>';
echo '<div class="c2os">';
echo $OUTPUT->heading($S('pluginname'));
echo html_writer::tag('p', $S('privacy', $stats->min), ['class' => 'text-muted']);

// Overview tiles.
$students = $stats->student_count();
$en = $fr = 0;
$first = $videos[0] ?? null;
$last = end($videos) ?: null;
foreach ($videos as $r) {
    $en = max($en, (int)($r['lang']['EN']['opened'] ?? 0));
    $fr = max($fr, (int)($r['lang']['FR']['opened'] ?? 0));
}
echo '<div class="c2os-tiles">';
foreach ([[$S('students'), $students], [$S('videos'), count($videos)],
          [$S('startedfirst'), $first ? $cell($first['either']) : '–'],
          [$S('finishedlast'), $last ? $cell($last['either']) : '–'],
          [$S('questionsshown'), count($questions)]] as [$label, $val]) {
    echo '<div class="c2os-tile"><span class="small text-muted">' . s($label) . '</span><b>' . s($val) . '</b></div>';
}
echo '</div>';

// Videos, in course order.
echo $OUTPUT->heading($S('videosheading'), 3);
echo html_writer::tag('p', $S('videoshelp'), ['class' => 'small text-muted']);
echo html_writer::link(new moodle_url($url, ['download' => 'videos']), $S('downloadcsv'), ['class' => 'btn btn-secondary btn-sm mb-2']);
echo '<div class="table-responsive"><table class="table table-sm table-striped generaltable"><thead><tr>'
   . '<th>' . $S('video') . '</th><th class="num">' . $S('finishedeither') . '</th>'
   . '<th class="num">EN ' . $S('opened') . '</th><th class="num">EN ' . $S('finished') . '</th><th class="num">EN ' . $S('meanfirst') . '</th>'
   . '<th class="num">FR ' . $S('opened') . '</th><th class="num">FR ' . $S('finished') . '</th><th class="num">FR ' . $S('meanfirst') . '</th>'
   . '</tr></thead><tbody>';
$section = null;
foreach ($videos as $r) {
    if ($r['section'] !== $section) {
        $section = $r['section'];
        echo '<tr><th colspan="8" class="bg-light">' . $section . '</th></tr>';
    }
    echo '<tr><td class="title"><span class="vid">' . s($r['video']) . '</span>' . $r['name'] . '</td>';
    echo '<td class="num">' . $cell($r['either']) . $bar($r['either'], max(1, $students)) . '</td>';
    foreach (['EN', 'FR'] as $l) {
        $x = $r['lang'][$l] ?? null;
        if (!$x) {
            echo '<td></td><td></td><td></td>';
            continue;
        }
        $cls = strtolower($l);
        echo '<td class="num">' . $cell($x['opened']) . '</td>';
        echo '<td class="num">' . $cell($x['finished']) . $bar($x['finished'], max(1, $students), $cls) . '</td>';
        echo '<td class="num">' . ($x['meanfirst'] === null ? '–' : $x['meanfirst'] . ' %') . $pctbar($x['meanfirst']) . '</td>';
    }
    echo '</tr>';
}
echo '</tbody></table></div>';

// Questions, hardest first.
echo $OUTPUT->heading($S('questionsheading'), 3);
echo html_writer::tag('p', $S('questionshelp', $stats->min), ['class' => 'small text-muted']);
if (!$questions) {
    echo $OUTPUT->notification($S('noquestions', $stats->min), 'info');
} else {
    echo html_writer::link(new moodle_url($url, ['download' => 'questions']), $S('downloadcsv'), ['class' => 'btn btn-secondary btn-sm mb-2']);
    echo '<div class="table-responsive"><table class="table table-sm table-striped generaltable"><thead><tr>'
       . '<th class="num">' . $S('rightfirst') . '</th><th>' . $S('question') . '</th><th>' . $S('video') . '</th>'
       . '<th>' . $S('language') . '</th><th class="num">' . $S('answeredby') . '</th></tr></thead><tbody>';
    foreach ($questions as $q) {
        $link = html_writer::link(new moodle_url('/mod/h5pactivity/view.php', ['id' => $q['cmid']]), $q['videoname']);
        echo '<tr><td class="num">' . $q['pct'] . ' %' . $pctbar($q['pct']) . '</td><td>' . s($q['question']) . '</td>'
           . '<td class="title"><span class="vid">' . s($q['video']) . '</span>' . $link . '</td>'
           . '<td>' . $q['lang'] . '</td><td class="num">' . $q['n'] . '</td></tr>';
    }
    echo '</tbody></table></div>';
}
echo '</div>';
echo $OUTPUT->footer();
