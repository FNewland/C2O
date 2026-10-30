"""ReqIF 1.2 exchange adapter for requirements (SCDF-160 Phase 2d).

    from spacecdf_agents.exporters.reqif import (
        export_requirements_reqif, import_requirements_reqif, ImportResult,
    )
"""
from .adapter import (
    ATTRIBUTES, RELATION_KINDS, SPEC_OBJECT_TYPE_ID, ImportResult, export_requirements_reqif,
    import_requirements_reqif,
)

__all__ = ["ATTRIBUTES", "RELATION_KINDS", "SPEC_OBJECT_TYPE_ID", "ImportResult",
           "export_requirements_reqif", "import_requirements_reqif"]
