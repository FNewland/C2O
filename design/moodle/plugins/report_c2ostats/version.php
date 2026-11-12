<?php
// C2O course statistics: aggregate, anonymous use of the course videos and their questions, by language.
defined('MOODLE_INTERNAL') || die();
$plugin->component = 'report_c2ostats';
$plugin->version   = 2026111200;
$plugin->requires  = 2024100700;   // Moodle 4.5 or later (5.x tested)
$plugin->maturity  = MATURITY_STABLE;
$plugin->release   = '1.0';
