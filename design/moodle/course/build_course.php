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
    // Completion on: finishing a video (receiving its practice score) unlocks the next item.
    'showgrades' => 0, 'enablecompletion' => 1, 'showcompletionconditions' => 1, 'lang' => '', 'newsitems' => 3,
    'visible' => 1,
];
$course = create_course($c);
echo "course {$course->id}\n";
require_once($CFG->dirroot . '/mod/forum/lib.php');
$news = forum_get_course_forum($course->id, 'news');
$DB->set_field('forum', 'name', '<span lang="en" class="multilang">Announcements</span><span lang="fr" class="multilang">Annonces</span>', ['id' => $news->id]);

$intro = fn($html) => ['text' => $html, 'format' => FORMAT_HTML, 'itemid' => file_get_unused_draft_itemid()];
$after = [];        // cmid -> [idnumber, ...]: opens when any of these is complete
$cmids = [];        // idnumber -> [cmid, modname], for links (@@CM:id@@) and the unlock chain
$pages = [];        // page instance id -> content, resolved once every item exists
$draft = function (string $path, string $name) use ($fs) {
    global $USER;
    $itemid = file_get_unused_draft_itemid();
    $fs->create_file_from_pathname(['contextid' => context_user::instance($USER->id)->id, 'component' => 'user',
        'filearea' => 'draft', 'itemid' => $itemid, 'filepath' => '/', 'filename' => $name], $path);
    return $itemid;
};

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
                $pages[$cm->instance] = $it['content'];
                $ctx = context_module::instance($cm->coursemodule);
                foreach ($it['files'] as $f) {
                    // No owner: an ownerless .h5p is system-trusted, so its libraries can deploy.
                    $fs->create_file_from_pathname(['contextid' => $ctx->id, 'component' => 'mod_page',
                        'filearea' => 'content', 'itemid' => 0, 'filepath' => '/', 'filename' => $f['name'],
                        'userid' => null], $abs($f['path']));
                }
                break;
            case 'h5pactivity':
                // Tracked: attempts and answers are recorded (practice only; the grade item is
                // hidden and the gradebook is off). Receiving a score = the video is finished.
                $mi = (object)($base + ['modulename' => 'h5pactivity', 'introeditor' => $intro($it['intro']),
                    'packagefile' => $draft($abs($it['file']['path']), $it['file']['name']),
                    'enabletracking' => 1, 'grademethod' => 1, 'reviewmode' => 1, 'grade' => 100,
                    'displayoptions' => 0, 'showdescription' => 0,
                    'completion' => COMPLETION_TRACKING_AUTOMATIC,
                    'completionusegrade' => empty($it['graded']) ? 0 : 1,
                    'completionview' => empty($it['graded']) ? 1 : 0]);
                $cm = create_module($mi);
                break;
            case 'data':
                require_once($CFG->dirroot . '/mod/data/lib.php');
                $mi = (object)($base + ['modulename' => 'data', 'introeditor' => $intro($it['intro']),
                    'approval' => 0, 'manageapproved' => 1, 'comments' => 1, 'requiredentries' => 0,
                    'requiredentriestoview' => 0, 'maxentries' => 0, 'rssarticles' => 0, 'assessed' => 0,
                    'scale' => 0, 'timeavailablefrom' => 0, 'timeavailableto' => 0, 'timeviewfrom' => 0,
                    'timeviewto' => 0]);
                $cm = create_module($mi);
                $data = $DB->get_record('data', ['id' => $cm->instance], '*', MUST_EXIST);
                foreach ($it['fields'] as $fd) {
                    $field = data_get_field_new($fd['type'], $data);
                    $rec = (object)['name' => $fd['name'], 'description' => $fd['description'],
                                    'required' => empty($fd['required']) ? 0 : 1];
                    if (!empty($fd['options'])) {
                        $rec->param1 = implode("\n", $fd['options']);
                    }
                    if ($fd['type'] === 'file') {
                        $rec->param3 = 50 * 1024 * 1024;
                    }
                    if ($fd['type'] === 'textarea') {
                        $rec->param2 = 60;
                        $rec->param3 = 8;
                    }
                    $field->define_field($rec);
                    $field->insert_field();
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
        $cmids[$it['idnumber']] = [$cm->coursemodule, $it['type']];
        if (!empty($it['after_any'])) {
            $after[$cm->coursemodule] = $it['after_any'];
        }
        echo "  [$sn] {$it['type']} {$it['idnumber']} cm {$cm->coursemodule}\n";
    }
}

// Links between items: @@CM:<idnumber>@@ -> the item's page.
$url = function (string $id) use ($cmids) {
    if (!isset($cmids[$id])) {
        throw new coding_exception("link to unknown item $id");
    }
    [$cmid, $mod] = $cmids[$id];
    return (new moodle_url("/mod/$mod/view.php", ['id' => $cmid]))->out(false);
};
foreach ($pages as $pid => $content) {
    if (strpos($content, '@@CM:') !== false) {
        $content = preg_replace_callback('/@@CM:([A-Za-z0-9_-]+)@@/', fn($m) => $url($m[1]), $content);
        $DB->set_field('page', 'content', $content, ['id' => $pid]);
    }
}

// The unlock chain: an item opens when the previous video is finished in either language.
// Locked items stay listed (show), so students see what is coming.
foreach ($after ?? [] as $cmid => $ids) {
    $conds = array_map(fn($id) => ['type' => 'completion', 'cm' => (int)$cmids[$id][0], 'e' => COMPLETION_COMPLETE], $ids);
    $tree = ['op' => '|', 'show' => true, 'c' => $conds];
    $DB->set_field('course_modules', 'availability', json_encode($tree), ['id' => $cmid]);
}

// Practice scores are never shown as grades.
require_once($CFG->libdir . '/gradelib.php');
foreach (grade_item::fetch_all(['courseid' => $course->id, 'itemtype' => 'mod', 'itemmodule' => 'h5pactivity']) ?: [] as $gi) {
    $gi->set_hidden(1);
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
