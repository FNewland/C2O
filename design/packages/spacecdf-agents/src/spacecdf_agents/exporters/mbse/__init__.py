"""SpaceCDF — MBSE (ECSS-E-TM-10-25A-style) export.

Phase 5 — research-credibility lever.

Produces a structured JSON that carries the study's SysML-like model:
  - Blocks (Spacecraft → Subsystems → Equipment)
  - Requirements (with ID, text, rationale, verification method)
  - Parameters (values with units, sources, and ownership)
  - Traceability links (requirement ↔ parameter ↔ block)

Loosely aligned to ECSS-E-TM-10-25A Annex A's data model so that the output
can be round-tripped into Cameo / Capella via a lightweight importer. The
ECSS-E-TM-10-25A ReferenceDataLibrary, SiteDirectory, and EngineeringModel
constructs are mapped here as JSON objects under the same names.

This is NOT a full ECSS-E-TM-10-25A emitter — that requires binary-coded
STEP AP233 and is out of scope. This JSON is intended for interchange +
research reproducibility, not tool certification.
"""
from .generator import generate_mbse_export

__all__ = ["generate_mbse_export"]
