"""capellambse 0.8.x compatibility shims (SCDF-160 Phase 2c).

``capellambse`` 0.8.1 declares ``PhysicalFunction.functions`` as a
containment of *PhysicalComponent* in ``ownedPhysicalComponents`` (a
copy-paste slip in ``metamodel/pa/__init__.py``).  As a result

* ``model.pa.root_function.functions.create(name=...)`` silently creates a
  ``PhysicalComponent`` under the root function, and
* ``functions.create("PhysicalFunction", ...)`` raises ``Invalid type hint``.

:func:`patch_capellambse` replaces the descriptor with the correct
``ownedFunctions`` containment.  It is a no-op once upstream fixes the bug
(detected by inspecting the descriptor's XML tag) and is idempotent.

Everything else this package relies on was verified against 0.8.1 in the
sandbox: ``decl.apply`` with ``!uuid`` / ``!promise`` / ``_type`` / ``sync``,
``owned_components`` / ``ports`` / ``component_exchanges`` /
``convoyed_informations``, ``inputs`` / ``outputs`` / ``exchanges`` /
``exchanged_items``, ``allocated_functions``, core property value groups
(``property_value_groups`` + ``applied_property_value_groups`` with
``FloatPropertyValue`` / ``StringPropertyValue``) and the Requirements
viewpoint (``oa.requirement_modules`` -> ``CapellaModule`` ->
``Requirement`` with ``CapellaOutgoingRelation`` / ``CapellaIncomingRelation``
/ ``InternalRelation`` typed by a ``RelationType`` in a
``CapellaTypesFolder``).
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_PATCHED = False


def patch_capellambse() -> bool:
    """Fix ``PhysicalFunction.functions`` if the installed capellambse has the bug.

    Returns True when a patch was (or had already been) applied.
    """
    global _PATCHED
    if _PATCHED:
        return True
    try:
        import capellambse.model as m
        from capellambse.metamodel import pa
    except Exception:  # pragma: no cover - capellambse missing
        logger.debug("capellambse not importable; nothing to patch")
        return False

    desc = pa.PhysicalFunction.__dict__.get("functions")
    # In 0.8.1 the containment is declared on 'ownedPhysicalComponents'.
    try:
        buggy = "ownedPhysicalComponents" in repr(desc)
    except Exception:  # pragma: no cover
        buggy = False
    if not buggy:
        _PATCHED = True
        return True

    fixed = m.Containment["PhysicalFunction"](
        "ownedFunctions", (pa.NS, "PhysicalFunction")
    )
    fixed.__set_name__(pa.PhysicalFunction, "functions")
    pa.PhysicalFunction.functions = fixed  # type: ignore[assignment]
    logger.info("Patched capellambse PhysicalFunction.functions (ownedFunctions)")
    _PATCHED = True
    return True
