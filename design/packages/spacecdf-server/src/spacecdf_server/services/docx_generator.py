"""SpaceCDF -- Word Document Generator (compatibility shim since W0.1).

The generators moved to the package ``services/docx/`` (one module per document family; see
design/docs/dev/W0_SEAMS.md). This module re-exports the old public names so existing imports
(``from ..services.docx_generator import generate_did_docx`` / ``DOCX_GENERATORS``) keep
working. New code imports from ``spacecdf_server.services.docx`` directly.
"""
from __future__ import annotations

from .docx import (  # noqa: F401
    DOCX_GENERATORS,
    _generate_regulatory_docx,
    _generate_review_package_docx,
    _render_bom_docx,
    generate_conops_docx,
    generate_did_docx,
    generate_ird_docx,
    generate_mrd_docx,
    generate_rmp_docx,
    generate_semp_docx,
    generate_testplan_docx,
    generate_ts_docx,
    generate_vp_docx,
)
from .docx._common import *  # noqa: F401,F403
from .docx._common import (  # noqa: F401  (private helpers some callers reached for)
    _add_cover_page,
    _add_footer,
    _add_section,
    _add_table,
    _add_toc_placeholder,
    _render_rich_content,
    _setup_margins,
    _setup_styles,
)
