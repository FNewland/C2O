"""The video page follows the 12-week term: every storyboard is placed once, in its own week."""
from c2ovideo import order, storyboard


def test_every_storyboard_is_placed_once_in_its_week():
    assert order.problems(storyboard.all_storyboards()) == []


def test_catalogue_is_sorted_into_term_order():
    cat = {"videos": [{"id": "V-OPS-10", "week": 5}, {"id": "V-SCDF-24", "week": 4}, {"id": "V-DES-01", "week": 1},
                      {"id": "V-OPS-01", "week": 2}]}
    order.sort_catalog(cat)
    assert [v["id"] for v in cat["videos"]] == ["V-DES-01", "V-SCDF-24", "V-OPS-01", "V-OPS-10"]
    assert [v["week"] for v in cat["videos"]] == [1, 7, 8, 11]
    assert cat["weeks"][0]["week"] == 1 and cat["weeks"][0]["title"]["fr"]


def test_operations_come_after_the_design_videos():
    last_design = max(order.place(sb.id)[0] for sb in storyboard.all_storyboards() if sb.id.startswith(("V-DES", "V-SCDF")))
    first_ops = min(order.place(sb.id)[0] for sb in storyboard.all_storyboards() if sb.id.startswith("V-OPS"))
    assert first_ops >= last_design


def test_moodle_course_lists_the_videos_in_the_same_order():
    import re
    from c2ovideo.storyboard import REPO
    ids = re.findall(r'"(V-[A-Z]+-\d+)"', (REPO / "design/moodle/course/manifest.py").read_text(encoding="utf-8"))
    term = sorted(order._load()["place"], key=lambda v: order.place(v)[1])
    assert ids == term


def test_moodle_term_layout_follows_the_twelve_weeks():
    """The Moodle course's 12-week layout: one section per week, in the calendar's order,
    with the operations weeks starting at week 8."""
    import importlib.util
    import os
    from pathlib import Path
    from c2ovideo.storyboard import REPO
    spec = importlib.util.spec_from_file_location("moodle_manifest", REPO / "design/moodle/course/manifest.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert m.LAYOUT == os.environ.get("C2O_COURSE_LAYOUT", "term")
    assert len(m.TERM) == len(m.SECTIONS) == 12
    names = [t[0] for t in m.TERM]
    assert all(n.startswith(f"Week {i} — ") for i, n in enumerate(names, 1))
    assert "Operations training" in names[7] and "PDR" in names[6] and "Review" in names[11]
    # the week each video sits in on the Moodle course is its week on the video page
    for i, s in enumerate(m.SECTIONS, 1):
        for item in s["items"]:
            if item.startswith("V-"):
                assert order.place(item)[0] == i, (item, i)
