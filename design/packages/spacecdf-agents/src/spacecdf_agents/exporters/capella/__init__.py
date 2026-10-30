"""Eclipse Capella exchange adapter (SCDF-160 Phase 2c).

Public API (what ``routers/exchange.py`` calls)::

    from spacecdf_agents.exporters.capella import (
        export_study_to_capella, import_capella_model, ExportResult, ImportResult,
    )

    result = await export_study_to_capella(study_id, out_path=None)   # .zip_bytes
    result = await import_capella_model(study_id, zip_bytes_or_path)  # .created/.updated
"""
from .exporter import ExportResult, export_snapshot_to_capella, export_study_to_capella
from .importer import ImportResult, import_capella_model, read_model_summary
from .mapping import SpineSnapshot, build_instructions, guess_subsystem_domain
from .render import render_context_svgs

__all__ = [
    "ExportResult", "ImportResult", "SpineSnapshot",
    "export_study_to_capella", "export_snapshot_to_capella", "import_capella_model",
    "read_model_summary", "build_instructions", "guess_subsystem_domain", "render_context_svgs",
]
