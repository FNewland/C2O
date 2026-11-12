<?php
namespace report_c2ostats\privacy;

defined('MOODLE_INTERNAL') || die();

/** The report stores nothing and shows only aggregate counts. */
class provider implements \core_privacy\local\metadata\null_provider {
    public static function get_reason(): string {
        return 'privacy:metadata';
    }
}
