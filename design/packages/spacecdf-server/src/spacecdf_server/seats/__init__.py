"""SpaceCDF seats (redesign WP9): identity → seat → permissions, per study.

    config.py      configs/seats.yaml: seats, team-size presets, ownership
    identity.py    IAP e-mail or laptop name → Person; instructor list from the environment
    store.py       team documents, presence, audit trail, pending changes (DB write-through)
    service.py     claiming, handover, active seat, write rules (rulings 4 and 5)
    changes.py     direct edits vs pending changes; applying an accepted change
    guard.py       middleware: frozen studies, seatless / Observer / Customer writes
    router.py      /api/seats/*, /api/studies/{id}/team/*
    instructor.py  /api/instructor/*: class board, interventions, timeline export
    export.py      timeline CSV / Markdown
"""
from .guard import SeatGuard
from .instructor import router as instructor_router
from .router import router

__all__ = ["SeatGuard", "router", "instructor_router"]
