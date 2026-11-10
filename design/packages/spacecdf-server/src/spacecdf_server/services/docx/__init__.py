"""SpaceCDF -- Word document generators, one module per document family (W0.1).

Was the single ``services/docx_generator.py`` (that module is now a re-export shim kept for
old imports). Modules:

``_common``     styles, cover, footer, ToC, rich content, tables, sections, diagram figures
``did``         ``generate_did_docx`` (universal DID renderer; the VCD uses it)
``bom``         ``_render_bom_docx``
``mrd``         ``generate_mrd_docx``
``conops``      ``generate_conops_docx``
``vp``          ``generate_vp_docx``
``ts``          ``generate_ts_docx``
``ird``         ``generate_ird_docx``
``semp``        ``generate_semp_docx``
``rmp``         ``generate_rmp_docx``
``testplan``    ``generate_testplan_docx``
``regulatory``  ``_generate_regulatory_docx`` (shared stub, replaced in W5.04)
``review``      ``_generate_review_package_docx`` (stub, retired in W4.14)

New document families (``conops`` rework, ``trades``, ``review_report``, ``ait``, ...) are new
modules in this package, owned by one agent each (design/docs/dev/W0_SEAMS.md). New generators
should take a ``StudyExport`` from ``services.export_context.collect`` rather than ad-hoc dicts.

``DOCX_GENERATORS`` is the registry behind ``POST /api/exports/docx/{doc_type}``: type ->
(display name, generator). Its key order is part of the API (the 400 message lists it).
"""
from __future__ import annotations

from ._common import *  # noqa: F401,F403  (public names only; helpers stay in _common)
from .bom import _render_bom_docx
from .conops import generate_conops_docx
from .did import generate_did_docx
from .ird import generate_ird_docx
from .mrd import generate_mrd_docx
from .regulatory import _generate_regulatory_docx
from .review import _generate_review_package_docx
from .rmp import generate_rmp_docx
from .semp import generate_semp_docx
from .testplan import generate_testplan_docx
from .ts import generate_ts_docx
from .vp import generate_vp_docx

__all__ = [
    "DOCX_GENERATORS",
    "generate_conops_docx", "generate_did_docx", "generate_ird_docx", "generate_mrd_docx",
    "generate_rmp_docx", "generate_semp_docx", "generate_testplan_docx", "generate_ts_docx",
    "generate_vp_docx", "_generate_regulatory_docx", "_generate_review_package_docx", "_render_bom_docx",
]

# Map of available document types
DOCX_GENERATORS = {
    "mrd": ("Mission Requirements Document", generate_mrd_docx),
    "conops": ("Concept of Operations", generate_conops_docx),
    "vp": ("Verification Plan", generate_vp_docx),
    "ts": ("Technical Specification", generate_ts_docx),
    "ird": ("Interface Requirements Document", generate_ird_docx),
    "semp": ("Systems Engineering Management Plan", generate_semp_docx),
    "rmp": ("Risk Management Plan", generate_rmp_docx),
    "testplan": ("Test Plan", generate_testplan_docx),
    # Regulatory filings
    "itu_api": ("ITU API Filing Template", _generate_regulatory_docx),
    "iaru": ("IARU Coordination Request", _generate_regulatory_docx),
    "rsssa": ("RSSSA Filing (Canada)", _generate_regulatory_docx),
    "export": ("Export Control Assessment", _generate_regulatory_docx),
    "copuos": ("UN Registration (COPUOS)", _generate_regulatory_docx),
    "eol": ("End-of-Life Compliance Report", _generate_regulatory_docx),
    # Review packages
    "srr": ("SRR Design Review Package", _generate_review_package_docx),
    "pdr": ("PDR Design Review Package", _generate_review_package_docx),
    "cdr": ("CDR Design Review Package", _generate_review_package_docx),
}
