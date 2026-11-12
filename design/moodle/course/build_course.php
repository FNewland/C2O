<?php
// Build the ORBIT NORTH course from manifest.json, then back it up (no users) to an .mbz.
//   php build_course.php [--category=1] [--out=/path/orbit_north.mbz] [--nobackup] [--shortname=ORBIT-NORTH-NEW]
// Run with the target Moodle's config: MOODLE_CONFIG=/path/to/moodle/config.php
define('CLI_SCRIPT', true);
require(getenv('MOODLE_CONFIG') ?: die("set MOODLE_CONFIG to the Moodle config.php\n"));
require_once($CFG->libdir . '/filterlib.php');
require_once($CFG->libdir . '/clilib.php');
require_once($CFG->dirroot . '/course/lib.php');
require_once($CFG->dirroot . '/course/modlib.php');
require_once($CFG->dirroot . '/backup/util/includes/backup_includes.php');

list($opts) = cli_get_params(['category' => 1, 'out' => __DIR__ . '/orbit_north.mbz', 'nobackup' => false,
                              'shortname' => '']);
\core\session\manager::set_user(get_admin());
$mfile = getenv('C2O_MANIFEST') ?: __DIR__ . '/manifest.json';
$m = json_decode(file_get_contents($mfile), true);
// a bundle (manifest.py --bundle) lists its files relative to the manifest
$abs = fn($p) => ($p !== '' && $p[0] === '/') ? $p : dirname(realpath($mfile)) . '/' . $p;
$fs = get_file_storage();

$c = (object)[
    'fullname' => $m['course']['fullname'], 'shortname' => $opts['shortname'] ?: $m['course']['shortname'],
    'category' => (int)$opts['category'], 'format' => 'topics',
    'numsections' => count($m['sections']) - 1, 'summary' => $m['course']['summary'], 'summaryformat' => FORMAT_HTML,
    'showgrades' => 0, 'enablecompletion' => 0, 'lang' => '', 'newsitems' => 3, 'visible' => 1,
];
$course = create_course($c);
echo "course {$course->id}\n";
require_once($CFG->dirroot . '/mod/forum/lib.php');
$news = forum_get_course_forum($course->id, 'news');
$DB->set_field('forum', 'name', '<span lang="en" class="multilang">Announcements</span><span lang="fr" class="multilang">Annonces</span>', ['id' => $news->id]);

$intro = fn($html) => ['text' => $html, 'format' => FORMAT_HTML, 'itemid' => file_get_unused_draft_itemid()];

foreach ($m['sections'] as $sn => $s) {
    $sec = $DB->get_record('course_sections', ['course' => $course->id, 'section' => $sn], '*', MUST_EXIST);
    $upd = ['summary' => $s['summary'], 'summaryformat' => FORMAT_HTML];
    if ($s['name'] !== null) {
        $upd['name'] = $s['name'];
    }
    course_update_section($course, $sec, $upd);
    foreach ($s['items'] as $it) {
        $base = ['course' => $course->id, 'section' => $sn, 'visible' => 1, 'name' => $it['name'],
                 'cmidnumber' => $it['idnumber'] ?? ''];
        switch ($it['type']) {
            case 'page':
                $mi = (object)($base + ['modulename' => 'page', 'introeditor' => $intro(''),
                    'content' => $it['content'], 'contentformat' => FORMAT_HTML,
                    'display' => 5, 'printintro' => 0, 'printlastmodified' => 0]);
                $cm = create_module($mi);
                $ctx = context_module::instance($cm->coursemodule);
                foreach ($it['files'] as $f) {
                    // No owner: an ownerless .h5p is system-trusted, so its libraries can deploy.
                    $fs->create_file_from_pathname(['contextid' => $ctx->id, 'component' => 'mod_page',
                        'filearea' => 'content', 'itemid' => 0, 'filepath' => '/', 'filename' => $f['name'],
                        'userid' => null], $abs($f['path']));
                }
                break;
            case 'forum':
                $mi = (object)($base + ['modulename' => 'forum', 'type' => 'general', 'introeditor' => $intro($it['intro']),
                    'assessed' => 0, 'scale' => 0, 'grade_forum' => 0, 'forcesubscribe' => 0, 'trackingtype' => 1,
                    'maxbytes' => 0, 'maxattachments' => 9]);
                $cm = create_module($mi);
                break;
            case 'wiki':
                $mi = (object)($base + ['modulename' => 'wiki', 'introeditor' => $intro($it['intro']),
                    'wikimode' => 'collaborative', 'firstpagetitle' => $it['firstpage'], 'defaultformat' => 'html',
                    'forceformat' => 0, 'editbegin' => 0, 'editend' => 0]);
                $cm = create_module($mi);
                break;
            default:
                throw new coding_exception('unknown item type ' . $it['type']);
        }
        echo "  [$sn] {$it['type']} {$it['idnumber']} cm {$cm->coursemodule}\n";
    }
}
rebuild_course_cache($course->id, true);

if (!$opts['nobackup']) {
    $bc = new backup_controller(backup::TYPE_1COURSE, $course->id, backup::FORMAT_MOODLE,
        backup::INTERACTIVE_NO, backup::MODE_GENERAL, get_admin()->id);
    foreach (['users' => 0, 'anonymize' => 0, 'role_assignments' => 0, 'activities' => 1, 'blocks' => 1,
              'filters' => 1, 'comments' => 0, 'badges' => 0, 'calendarevents' => 1, 'userscompletion' => 0,
              'logs' => 0, 'grade_histories' => 0, 'groups' => 0, 'competencies' => 0, 'contentbankcontent' => 0,
              'xapistate' => 0, 'legacyfiles' => 0] as $name => $v) {
        $plan = $bc->get_plan();
        if ($plan->setting_exists($name)) {
            $setting = $plan->get_setting($name);
            if ($setting->get_status() == base_setting::NOT_LOCKED) {
                $setting->set_value($v);
            }
        }
    }
    $bc->execute_plan();
    $file = $bc->get_results()['backup_destination'];
    $file->copy_content_to($opts['out']);
    $bc->destroy();
    printf("backup %s (%.0f MB)\n", $opts['out'], filesize($opts['out']) / 1e6);
}
