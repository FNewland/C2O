"""Study -> Eclipse Capella 7.0 project (SCDF-160 Phase 2c).

    result = await export_study_to_capella(study_id, out_path=Path("x.capella.zip"))

Pipeline: load the spine (``_spine.load_snapshot``) -> copy the vendored empty
template (or unzip ``base`` to update a previous export in place) into a temp
dir -> ``mapping.build_instructions`` -> ``capellambse.decl.apply`` ->
``model.save()`` -> rename to ``<slug>.{afm,aird,capella}`` -> zip
``{.project, .afm, .aird, .capella}`` -> write the Capella UUIDs back into the
spine (``external_ids['capella']``).

The requirements viewpoint (``org.polarsys.capella.vp.requirements``) is
referenced in the ``.afm`` when the study has requirements, so Capella opens
the module without complaining.  The version string is Capella 7.0's; adjust
:data:`REQUIREMENTS_VP_VERSION` if your Capella install reports a different
one.
"""
from __future__ import annotations

import io
import logging
import re
import shutil
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ._compat import patch_capellambse
from .mapping import (
    MappingResult, ModelAnchors, SpineSnapshot, build_instructions, candidate_uuids,
)

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent / "template"
TEMPLATE_FILES = (".project", "empty.afm", "empty.aird", "empty.capella")
REQUIREMENTS_VP = "org.polarsys.capella.vp.requirements"
REQUIREMENTS_VP_VERSION = "0.14.0"

__all__ = [
    "ExportResult", "export_study_to_capella", "export_snapshot_to_capella",
    "load_model", "TEMPLATE_DIR",
]


@dataclass
class ExportResult:
    study_id: str
    zip_bytes: bytes
    path: Path | None
    #: ``{kind: {spine_id: capella_uuid}}``
    id_map: dict[str, dict[str, str]]
    warnings: list[str] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)
    #: names of the four files inside the zip
    files: list[str] = field(default_factory=list)
    #: number of spine rows that received a new ``external_ids['capella']``
    ids_recorded: int = 0


def _slug(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_")
    return s or "spacecdf"


def _materialise_base(base: Path | bytes | None, workdir: Path) -> Path:
    """Copy the template (or a previous export) into ``workdir``; return the .aird."""
    if base is None:
        for f in TEMPLATE_FILES:
            shutil.copy(TEMPLATE_DIR / f, workdir / f)
        return workdir / "empty.aird"
    if isinstance(base, (bytes, bytearray)):
        with zipfile.ZipFile(io.BytesIO(base)) as zf:
            zf.extractall(workdir)
    else:
        base = Path(base)
        if base.is_dir():
            for f in base.iterdir():
                if f.is_file():
                    shutil.copy(f, workdir / f.name)
        elif base.suffix == ".zip":
            with zipfile.ZipFile(base) as zf:
                zf.extractall(workdir)
        elif base.suffix == ".aird":
            for f in base.parent.iterdir():
                if f.is_file():
                    shutil.copy(f, workdir / f.name)
        else:
            raise ValueError(f"Unsupported base model: {base}")
    airds = sorted(workdir.rglob("*.aird"))
    if not airds:
        raise ValueError("No .aird file found in base model")
    return airds[0]


def load_model(aird: Path):
    """Open a Capella model with the 0.8.x compatibility patch applied."""
    import capellambse
    patch_capellambse()
    return capellambse.MelodyModel(str(aird))


def _anchors(model, snap: SpineSnapshot) -> ModelAnchors:
    existing: set[str] = set()
    parents: dict[str, str] = {}
    for u in candidate_uuids(snap):
        try:
            obj = model.by_uuid(u)
        except KeyError:
            continue
        existing.add(u)
        try:
            parents[u] = obj.parent.uuid
        except Exception:
            pass
    return ModelAnchors(
        sa_root_function=model.sa.root_function.uuid,
        la_root_function=model.la.root_function.uuid,
        pa_root_function=model.pa.root_function.uuid,
        sa_root_component=model.sa.root_component.uuid,
        la_root_component=model.la.root_component.uuid,
        pa_root_component=model.pa.root_component.uuid,
        oa=model.oa.uuid,
        data_pkg=model.sa.data_pkg.uuid,
        existing_uuids=existing,
        existing_parents=parents,
    )


def _delete_objects(model, uuids: list[str], warnings: list[str]) -> None:
    for u in uuids:
        try:
            obj = model.by_uuid(u)
            elm = obj._element
            model._loader.idcache_remove(elm)
            elm.getparent().remove(elm)
        except Exception as exc:  # pragma: no cover - defensive
            warnings.append(f"could not remove reparented object {u}: {exc}")


def _reference_viewpoint(afm: Path, vp_id: str, version: str) -> bool:
    """Add a ``viewpointReferences`` entry to the ``.afm`` (textually).

    ``MelodyModel.activate_viewpoint`` is broken in capellambse 0.8.1 (its
    ``new_uuid`` helper raises ``KeyError`` on the ``.afm`` tree), so the
    reference is written after ``save()``.  Returns True when added.
    """
    if not afm.exists():
        return False
    txt = afm.read_text(encoding="utf-8")
    if f'vpId="{vp_id}"' in txt:
        return False
    import uuid as _uuid
    ref = f'  <viewpointReferences id="_{_uuid.uuid4().hex[:22]}" vpId="{vp_id}" version="{version}"/>\n'
    if "</metadata:Metadata>" not in txt:
        return False
    txt = txt.replace("</metadata:Metadata>", ref + "</metadata:Metadata>", 1)
    afm.write_text(txt, encoding="utf-8")
    return True


def _rename_project(workdir: Path, aird: Path, slug: str, project_name: str) -> list[Path]:
    """Rename ``<old>.{afm,aird,capella}`` to ``<slug>.*`` and fix cross references."""
    old = aird.stem
    if old != slug:
        for ext in (".afm", ".aird", ".capella"):
            src = workdir / f"{old}{ext}"
            if src.exists():
                src.rename(workdir / f"{slug}{ext}")
        aird_new = workdir / f"{slug}.aird"
        txt = aird_new.read_text(encoding="utf-8")
        txt = txt.replace(f"{old}.capella", f"{slug}.capella").replace(f"{old}.afm", f"{slug}.afm")
        aird_new.write_text(txt, encoding="utf-8")
    proj = workdir / ".project"
    if proj.exists():
        ptxt = proj.read_text(encoding="utf-8")
        ptxt = re.sub(r"<name>.*?</name>", f"<name>{_xml_escape(project_name)}</name>", ptxt, count=1)
        proj.write_text(ptxt, encoding="utf-8")
    return [workdir / ".project"] + [workdir / f"{slug}{ext}" for ext in (".afm", ".aird", ".capella")]


def _xml_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _counts(model) -> dict[str, int]:
    def n(x) -> int:
        try:
            return len(x)
        except Exception:
            return 0
    return {
        "sa_functions": n(model.sa.all_functions) - 1,
        "la_functions": n(model.la.all_functions) - 1,
        "pa_functions": n(model.pa.all_functions) - 1,
        "la_components": n(model.la.all_components) - 1,
        "pa_components": n(model.pa.all_components) - 1,
        "component_exchanges": n(model.la.all_component_exchanges) + n(model.pa.all_component_exchanges),
        "functional_exchanges": n(model.sa.all_function_exchanges) + n(model.la.all_function_exchanges)
        + n(model.pa.all_function_exchanges),
        "exchange_items": n(model.search("ExchangeItem")),
        "requirements": n(model.search("Requirements:Requirement", subclasses=True)),
    }


def export_snapshot_to_capella(snap: SpineSnapshot, *, out_path: Path | None = None,
                               base: Path | bytes | None = None) -> tuple[ExportResult, MappingResult]:
    """Synchronous core: snapshot -> zip. No spine access (used by tests too)."""
    from capellambse import decl

    warnings: list[str] = []
    with tempfile.TemporaryDirectory(prefix="spacecdf-capella-") as td:
        workdir = Path(td)
        aird = _materialise_base(base, workdir)
        model = load_model(aird)
        anchors = _anchors(model, snap)
        mapping = build_instructions(snap, anchors)
        warnings.extend(mapping.warnings)
        if mapping.reparented:
            _delete_objects(model, mapping.reparented, warnings)
        try:
            model.project.name = snap.study_name or snap.study_id
        except Exception:  # pragma: no cover
            pass
        yaml_text = decl.dump(mapping.instructions)
        decl.apply(model, io.StringIO(yaml_text))
        counts = _counts(model)
        model.save()
        del model
        if snap.requirements or snap.relations:
            _reference_viewpoint(workdir / f"{aird.stem}.afm", REQUIREMENTS_VP, REQUIREMENTS_VP_VERSION)

        slug = _slug(snap.study_name or snap.study_id)
        files = _rename_project(workdir, aird, slug, snap.study_name or snap.study_id)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in files:
                zf.write(f, arcname=f.name)
        zip_bytes = buf.getvalue()

    if out_path is not None:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(zip_bytes)

    by_kind: dict[str, dict[str, str]] = {}
    for (kind, sid), u in mapping.id_map.items():
        by_kind.setdefault(kind, {})[sid] = u
    result = ExportResult(
        study_id=snap.study_id, zip_bytes=zip_bytes, path=out_path, id_map=by_kind,
        warnings=warnings, counts=counts, files=[f.name for f in files],
    )
    return result, mapping


async def export_study_to_capella(study_id: str, *, out_path: Path | None = None,
                                  base: Path | bytes | None = None,
                                  record_ids: bool = True) -> ExportResult:
    """Export a study to a Capella project zip.

    Parameters
    ----------
    study_id
        Study to export (elements/functions/... are read through the repos,
        requirements from the in-memory requirements store).
    out_path
        Optional path for ``<study>.capella.zip``; the bytes are returned either way.
    base
        A previous export (zip path/bytes, project dir or ``.aird``) to update
        in place instead of starting from the empty template.
    record_ids
        Write ``external_ids['capella']`` back into the spine (default).
    """
    from ._spine import load_snapshot, record_capella_ids

    snap = await load_snapshot(study_id)
    result, mapping = export_snapshot_to_capella(snap, out_path=out_path, base=base)
    if record_ids:
        try:
            result.ids_recorded = await record_capella_ids(snap, mapping.id_map)
        except Exception as exc:
            logger.exception("recording Capella ids failed")
            result.warnings.append(f"could not record Capella ids: {exc}")
    return result
