"""ECSS-E-TM-10-25 exchange adapter (SCDF-160 Phase 2d).

Public API::

    from spacecdf_agents.exporters.ecss_10_25 import (
        export_study_to_10_25, build_10_25_model, AnnexCClient, push_study,
    )

    zip_bytes = await export_study_to_10_25(study_id)         # Annex C.3 zip
    model = await build_10_25_model(study_id)                 # pydantic objects
    await push_study(study_id, AnnexCClient(url, auth))       # Annex C.2 POST
"""
from .client import AnnexCClient, push_study
from .exporter import Model1025, build_10_25_model, export_study_to_10_25, write_annex_c3_zip
from .model import ALL_CLASSES, Thing, parse_thing

__all__ = [
    "AnnexCClient", "push_study", "Model1025", "build_10_25_model",
    "export_study_to_10_25", "write_annex_c3_zip", "ALL_CLASSES", "Thing", "parse_thing",
]
