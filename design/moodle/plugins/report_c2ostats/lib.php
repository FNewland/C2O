<?php
defined('MOODLE_INTERNAL') || die();

/** Adds the report to the course's Reports page (teachers only). */
function report_c2ostats_extend_navigation_course($navigation, $course, $context) {
    if (has_capability('report/c2ostats:view', $context)) {
        $url = new moodle_url('/report/c2ostats/index.php', ['id' => $course->id]);
        $navigation->add(get_string('pluginname', 'report_c2ostats'), $url, navigation_node::TYPE_SETTING,
            null, 'c2ostats', new pix_icon('i/report', ''));
    }
}
