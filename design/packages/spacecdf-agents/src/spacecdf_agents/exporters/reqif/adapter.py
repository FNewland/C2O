"""Requirements <-> ReqIF 1.2 via the ``reqif`` package (strictdoc, Apache-2.0).

Export
------
* one ``SPEC-OBJECT-TYPE`` "SpaceCDF Requirement" with STRING attributes
  ``code, text, rationale, level, verification_method, verification_phase,
  status`` (all ``DATATYPE-DEFINITION-STRING``);
* one ``SPEC-OBJECT`` per (non-retired) requirement, ``IDENTIFIER`` =
  ``external_id`` or a generated ``SCDF-REQ-<id>`` that is written back to the
  requirement so the next export re-uses it;
* one ``SPECIFICATION`` "SpaceCDF Requirements" whose ``SPEC-HIERARCHY`` tree
  follows ``parent_id``;
* one ``SPEC-RELATION-TYPE`` per SpaceCDF relation kind (satisfies, verifies,
  refines, derives, traces) and a ``SPEC-RELATION`` per requirement<->requirement
  relation.  Relations whose source or target is not a requirement (element,
  function, ...) cannot be expressed in ReqIF and are reported in
  ``warnings``.

Source of truth for requirements is the in-memory store the API serves
(``routers.requirements._requirements``); the ``requirements`` DB table
(``db/requirement_repo.py``) is write-through from the API (SCDF-160 N0), so the
``external_id`` write-back updates the store and mirrors into the DB row
*if* one exists (best effort, never raises).

Import
------
Upserts by identifier: an existing requirement with the same ``external_id``
(or ``SCDF-REQ-<id>`` for a requirement whose id matches) is updated,
otherwise a new one is created with the ReqIF identifier as ``external_id``.
Hierarchy comes from the SPEC-HIERARCHY tree; relations from SPEC-RELATIONs
whose type maps to a known kind (created when no identical relation exists).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4
from xml.sax.saxutils import escape as xml_escape

from reqif.models.reqif_core_content import ReqIFCoreContent
from reqif.models.reqif_data_type import ReqIFDataTypeDefinitionString
from reqif.models.reqif_namespace_info import ReqIFNamespaceInfo
from reqif.models.reqif_req_if_content import ReqIFReqIFContent
from reqif.models.reqif_reqif_header import ReqIFReqIFHeader
from reqif.models.reqif_spec_hierarchy import ReqIFSpecHierarchy
from reqif.models.reqif_spec_object import ReqIFSpecObject, SpecObjectAttribute
from reqif.models.reqif_spec_object_type import ReqIFSpecObjectType, SpecAttributeDefinition
from reqif.models.reqif_spec_relation import ReqIFSpecRelation
from reqif.models.reqif_spec_relation_type import ReqIFSpecRelationType
from reqif.models.reqif_specification import ReqIFSpecification
from reqif.models.reqif_specification_type import ReqIFSpecificationType
from reqif.models.reqif_types import SpecObjectAttributeType
from reqif.parser import ReqIFParser
from reqif.reqif_bundle import ReqIFBundle
from reqif.unparser import ReqIFUnparser

logger = logging.getLogger(__name__)

ATTRIBUTES = ("code", "text", "rationale", "level", "verification_method", "verification_phase", "status")
RELATION_KINDS = ("satisfies", "verifies", "refines", "derives", "traces")
SPEC_OBJECT_TYPE_ID = "SCDF-TYPE-REQUIREMENT"
SPECIFICATION_TYPE_ID = "SCDF-TYPE-SPECIFICATION"
SPECIFICATION_ID = "SCDF-SPEC-REQUIREMENTS"
DATATYPE_STRING_ID = "SCDF-DT-STRING"


def _attr_id(name: str) -> str:
    return f"SCDF-ATTR-{name.upper()}"


def _rel_type_id(kind: str) -> str:
    return f"SCDF-REL-{kind.upper()}"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class ImportResult:
    study_id: str
    created: int = 0
    updated: int = 0
    relations_created: int = 0
    warnings: list[str] = field(default_factory=list)
    #: ReqIF identifier -> requirement id
    id_map: dict[str, str] = field(default_factory=dict)


# ── spine gateway ───────────────────────────────────────────────────────

def _store() -> dict[str, dict]:
    from spacecdf_server.routers.requirements import _requirements
    return _requirements


def _study_requirements(study_id: str) -> list[dict]:
    return [r for r in _store().values() if r.get("study_id") == study_id and r.get("status") != "retired"]


def requirement_identifier(req: dict) -> str:
    return req.get("external_id") or f"SCDF-REQ-{req['id']}"


async def _mirror_external_id_to_db(req_id: str, external_id: str) -> None:
    """Best-effort mirror into ``RequirementRow.external_id`` when a row exists."""
    try:
        from spacecdf_server.db.engine import get_session_factory
        from spacecdf_server.db.models import RequirementRow
        factory = get_session_factory()
        async with factory() as db:
            row = await db.get(RequirementRow, req_id)
            if row is not None and row.external_id != external_id:
                row.external_id = external_id
                await db.commit()
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("external_id mirror skipped for %s: %s", req_id, exc)


async def _ensure_external_ids(reqs: list[dict]) -> None:
    for r in reqs:
        if not r.get("external_id"):
            r["external_id"] = f"SCDF-REQ-{r['id']}"
            live = _store().get(r["id"])
            if live is not None:
                live["external_id"] = r["external_id"]
            await _mirror_external_id_to_db(r["id"], r["external_id"])


# ── export ──────────────────────────────────────────────────────────────

def _s(v: Any) -> str:
    return "" if v is None else str(v)


def _x(v: Any) -> str:
    """XML-escaped text for the header fields the ``reqif`` unparser writes
    verbatim (attribute values are escaped by the library itself)."""
    return "" if v is None else xml_escape(str(v), {'"': "&quot;"})


def _spec_object(req: dict) -> ReqIFSpecObject:
    attrs = [SpecObjectAttribute(attribute_type=SpecObjectAttributeType.STRING,
                                 definition_ref=_attr_id(a), value=_s(req.get(a)))
             for a in ATTRIBUTES]
    return ReqIFSpecObject(identifier=requirement_identifier(req), attributes=attrs,
                           spec_object_type=SPEC_OBJECT_TYPE_ID, long_name=_s(req.get("code")),
                           last_change=_now())


def _hierarchy(reqs: list[dict]) -> list[ReqIFSpecHierarchy]:
    by_parent: dict[str | None, list[dict]] = {}
    ids = {r["id"] for r in reqs}
    for r in reqs:
        pid = r.get("parent_id") if r.get("parent_id") in ids else None
        by_parent.setdefault(pid, []).append(r)

    def node(r: dict, level: int) -> ReqIFSpecHierarchy:
        kids = [node(c, level + 1) for c in by_parent.get(r["id"], [])]
        return ReqIFSpecHierarchy(identifier=f"SCDF-HIER-{requirement_identifier(r)}",
                                  spec_object=requirement_identifier(r), level=level,
                                  children=kids or None, is_self_closed=not kids, last_change=_now())

    return [node(r, 1) for r in by_parent.get(None, [])]


async def export_requirements_reqif(study_id: str) -> bytes:
    """ReqIF 1.2 XML (UTF-8 bytes) of the study's requirements."""
    from spacecdf_server.db.relation_repo import load_all_relations

    reqs = _study_requirements(study_id)
    await _ensure_external_ids(reqs)
    ident = {r["id"]: requirement_identifier(r) for r in reqs}

    data_types = [ReqIFDataTypeDefinitionString(identifier=DATATYPE_STRING_ID, long_name="String",
                                                max_length="65535", last_change=_now())]
    attr_defs = [SpecAttributeDefinition(attribute_type=SpecObjectAttributeType.STRING, identifier=_attr_id(a),
                                         datatype_definition=DATATYPE_STRING_ID, long_name=a, last_change=_now())
                 for a in ATTRIBUTES]
    spec_types: list[Any] = [
        ReqIFSpecObjectType(identifier=SPEC_OBJECT_TYPE_ID, long_name="SpaceCDF Requirement",
                            attribute_definitions=attr_defs, last_change=_now()),
        ReqIFSpecificationType(identifier=SPECIFICATION_TYPE_ID, long_name="SpaceCDF Specification",
                               is_self_closed=True, last_change=_now()),
    ]
    spec_types += [ReqIFSpecRelationType(identifier=_rel_type_id(k), long_name=k, last_change=_now())
                   for k in RELATION_KINDS]

    spec_objects = [_spec_object(r) for r in reqs]

    warnings: list[str] = []  # plain text; escaped when written to the header
    spec_relations: list[ReqIFSpecRelation] = []
    for rel in (await load_all_relations(study_id)).values():
        kind = rel.get("kind")
        if kind not in RELATION_KINDS:
            warnings.append(f"relation {rel.get('id')}: kind '{kind}' has no ReqIF SPEC-RELATION-TYPE")
            continue
        if rel.get("source_kind") != "requirement" or rel.get("target_kind") != "requirement":
            warnings.append(f"relation {rel.get('id')}: {rel.get('source_kind')}->{rel.get('target_kind')} "
                            "is not requirement<->requirement; not expressible in ReqIF")
            continue
        s, t = ident.get(rel["source_id"]), ident.get(rel["target_id"])
        if not s or not t:
            warnings.append(f"relation {rel.get('id')}: endpoint not in this study")
            continue
        spec_relations.append(ReqIFSpecRelation(identifier=f"SCDF-RELATION-{rel['id']}",
                                                relation_type_ref=_rel_type_id(kind), source=s, target=t,
                                                last_change=_now()))
    for w in warnings:
        logger.info("reqif export %s: %s", study_id, w)

    specification = ReqIFSpecification(identifier=SPECIFICATION_ID, long_name="SpaceCDF Requirements",
                                       specification_type=SPECIFICATION_TYPE_ID, children=_hierarchy(reqs),
                                       last_change=_now())
    content = ReqIFReqIFContent(data_types=data_types, spec_types=spec_types, spec_objects=spec_objects,
                                spec_relations=spec_relations, specifications=[specification])
    header = ReqIFReqIFHeader(identifier=f"SCDF-HEADER-{study_id}", creation_time=_now(),
                              req_if_tool_id="SpaceCDF", req_if_version="1.0", source_tool_id="SpaceCDF",
                              title=_x(f"SpaceCDF requirements for study {study_id}"),
                              comment=_x("; ".join(warnings)) or None)
    bundle = ReqIFBundle(namespace_info=ReqIFNamespaceInfo.create_default(), req_if_header=header,
                         core_content=ReqIFCoreContent(content), tool_extensions_tag_exists=False,
                         lookup=None, exceptions=[])  # type: ignore[arg-type]
    return ReqIFUnparser.unparse(bundle).encode("utf-8")


# ── import ──────────────────────────────────────────────────────────────

def _attr_values(obj: ReqIFSpecObject) -> dict[str, str]:
    out: dict[str, str] = {}
    for a in obj.attributes:
        name = a.definition_ref
        if name.startswith("SCDF-ATTR-"):
            name = name[len("SCDF-ATTR-"):].lower()
        val = a.value if isinstance(a.value, str) else (a.value_stripped_xhtml or " ".join(a.value or []))
        out[name] = val
    return out


async def import_requirements_reqif(study_id: str, data: bytes | str) -> ImportResult:
    from spacecdf_server.db.relation_repo import create_relation, load_all_relations

    text = data.decode("utf-8") if isinstance(data, (bytes, bytearray)) else data
    bundle = ReqIFParser.parse_from_string(text)
    result = ImportResult(study_id=study_id)
    content = bundle.core_content.req_if_content if bundle.core_content else None
    if content is None or not content.spec_objects:
        result.warnings.append("no SPEC-OBJECTs in document")
        return result

    store = _store()
    existing_by_ident: dict[str, dict] = {}
    for r in store.values():
        if r.get("study_id") == study_id:
            existing_by_ident[requirement_identifier(r)] = r

    # parent map from SPEC-HIERARCHY
    parent_of: dict[str, str | None] = {}
    for spec in content.specifications or []:
        def walk(nodes, parent):
            for n in nodes or []:
                parent_of[n.spec_object] = parent
                walk(n.children, n.spec_object)
        walk(spec.children, None)

    # upsert requirements
    for obj in content.spec_objects:
        attrs = _attr_values(obj)
        ident = obj.identifier
        req = existing_by_ident.get(ident)
        fields = {a: (attrs.get(a) or None) for a in ATTRIBUTES}
        if fields.get("level") is None:
            fields["level"] = "system"
        if fields.get("status") is None:
            fields["status"] = "draft"
        if req is None:
            req_id = ident[len("SCDF-REQ-"):] if ident.startswith("SCDF-REQ-") else ident
            if req_id in store:
                req_id = f"REQ-{uuid4().hex[:8]}"
            req = {
                "id": req_id, "study_id": study_id, "parent_id": None, "element_id": None,
                "level": fields["level"], "code": fields.get("code") or ident, "text": fields.get("text") or "",
                "rationale": fields.get("rationale"), "threshold_param_path": None, "threshold_op": None,
                "threshold_value": None, "verification_method": fields.get("verification_method"),
                "verification_phase": fields.get("verification_phase"), "responsible_position": None,
                "status": fields["status"], "derived_from_requirement_id": None, "external_id": ident,
            }
            store[req_id] = req
            existing_by_ident[ident] = req
            result.created += 1
        else:
            for k, v in fields.items():
                if v is not None or k in ("rationale", "verification_method", "verification_phase"):
                    req[k] = v
            req["external_id"] = ident
            result.updated += 1
        result.id_map[ident] = req["id"]
        await _mirror_external_id_to_db(req["id"], ident)

    # hierarchy (second pass, all ids known)
    for ident, parent_ident in parent_of.items():
        rid = result.id_map.get(ident)
        if rid is None:
            continue
        pid = result.id_map.get(parent_ident) if parent_ident else None
        store[rid]["parent_id"] = pid
        if pid and not store[rid].get("derived_from_requirement_id"):
            store[rid]["derived_from_requirement_id"] = pid

    # write-through (SCDF-160 N0): imported requirements must survive a restart
    from spacecdf_server.db.requirement_repo import db_upsert_requirement
    for rid in result.id_map.values():
        if rid in store:
            await db_upsert_requirement(store[rid])

    # relations
    existing_rels = {(r["kind"], r["source_id"], r["target_id"]) for r in (await load_all_relations(study_id)).values()
                     if r.get("source_kind") == "requirement" and r.get("target_kind") == "requirement"}
    for rel in content.spec_relations or []:
        t = rel.relation_type_ref
        kind = t[len("SCDF-REL-"):].lower() if t.startswith("SCDF-REL-") else t.lower()
        if kind not in RELATION_KINDS:
            result.warnings.append(f"SPEC-RELATION {rel.identifier}: unknown type {t}")
            continue
        s, d = result.id_map.get(rel.source), result.id_map.get(rel.target)
        if not s or not d:
            result.warnings.append(f"SPEC-RELATION {rel.identifier}: endpoint not imported")
            continue
        if (kind, s, d) in existing_rels:
            continue
        await create_relation({"study_id": study_id, "kind": kind, "source_kind": "requirement", "source_id": s,
                               "target_kind": "requirement", "target_id": d,
                               "external_id": f"reqif:{rel.identifier}"})
        existing_rels.add((kind, s, d))
        result.relations_created += 1
    return result
