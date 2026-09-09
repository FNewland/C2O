"""Study -> ECSS-E-TM-10-25 Annex C.3 exchange-file zip (SCDF-160 Phase 2d).

    zip_bytes = await export_study_to_10_25(study_id)

Zip layout (mirrors the public STARIONGROUP/CDP4-COMET-MODELS sample
exchange files; Annex C.3 itself is member-state restricted so every point
below is an assumption stated by convention, not a quote of the standard)::

    Header.json                                       exchange-file header
    SiteDirectory.json                                [SiteDirectory + everything it
                                                       contains directly: domains,
                                                       persons, model setups,
                                                       iteration setups, participants]
    SiteReferenceDataLibraries/<rdl-iid>.json         [RDL + units, scales, quantity
                                                       kinds, categories]
    EngineeringModels/<em-iid>/EngineeringModel.json  [EngineeringModel]
    EngineeringModels/<em-iid>/Iterations/<it-iid>.json
                                                      [Iteration + options, element
                                                       definitions/usages, parameters,
                                                       value sets, requirements
                                                       specification/groups/
                                                       requirements/definitions]

Layout assumptions
------------------
1. Every ``.json`` file is a JSON **array** of objects; each object has
   ``iid``, ``classKind``, ``revisionNumber`` (and ``modifiedOn``).
2. The containing object is the first entry of its file; the order of the
   remaining entries is irrelevant (consumers resolve by ``iid``).
3. ``Header.json`` is a single object:
   ``{"exchangeFileFormatVersion": "1.0.0", "createdOn", "creatorPerson":
   {"iid", "givenName", "surname", "emailAddress"}, "extensions": [],
   "remark"}``.
4. iids are deterministic (uuid5 from the spine id) so a re-export of the same
   study produces the same iids and can be diffed / re-imported.
5. Unordered containment lists are serialised as plain iid arrays;
   ``Iteration.option`` uses the ordered ``[{"k", "v"}]`` form.
6. No ``ParameterOverride`` / ``NestedElement`` / ``Publication`` are emitted.
7. ``SimpleQuantityKind`` per distinct parameter *name* (not per quantity
   kind) so a consumer can map ``mass_kg`` 1:1 to a SpaceCDF definition;
   the RDL ``shortName`` is the SpaceCDF parameter name.
8. Requirements: one ``RequirementsSpecification`` named ``SpaceCDF``, one
   ``RequirementsGroup`` per level (``mission``/``system``/``subsystem``…),
   one ``Requirement`` per spine requirement with a ``Definition`` holding
   the text; ``shortName`` is the requirement code.

Mapping
-------
* element -> ``ElementDefinition`` (``shortName`` = slug of the name,
  ``category`` = one ``Category`` per ``element_type``); child containment
  -> ``ElementUsage`` in the parent's ``containedElement``; the study root
  (the element without parent, or the first ``system``) is ``Iteration.topElement``.
* element parameter (well-known columns mirrored into rows + formulas) ->
  ``Parameter`` typed by the ``SimpleQuantityKind`` of its definition with
  one ``ParameterValueSet`` {manual, computed, reference, valueSwitch,
  published = effective value, formula}.
* ``owner`` = ``DomainOfExpertise`` of ``owner_domain`` / ``subsystem_domain``
  else the ``System`` domain.
* one ``Option`` "Baseline", one ``Iteration``.
"""
from __future__ import annotations

import io
import json
import logging
import re
import zipfile
from dataclasses import dataclass, field
from typing import Any

from ..capella._spine import load_snapshot
from ..capella.mapping import SpineSnapshot
from . import model as m
from .model import stable_iid

logger = logging.getLogger(__name__)

EXCHANGE_FILE_FORMAT_VERSION = "1.0.0"
NO_VALUE = "-"

__all__ = ["Model1025", "build_10_25_model", "export_study_to_10_25", "write_annex_c3_zip"]


@dataclass
class Model1025:
    """All objects of one export, grouped by exchange file."""
    study_id: str
    site_directory: list[m.Thing] = field(default_factory=list)
    rdl: list[m.Thing] = field(default_factory=list)
    engineering_model: list[m.Thing] = field(default_factory=list)
    iteration: list[m.Thing] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def rdl_iid(self) -> str:
        return self.rdl[0].iid

    @property
    def em_iid(self) -> str:
        return self.engineering_model[0].iid

    @property
    def iteration_iid(self) -> str:
        return self.iteration[0].iid

    def all_things(self) -> list[m.Thing]:
        return [*self.site_directory, *self.rdl, *self.engineering_model, *self.iteration]

    def by_iid(self) -> dict[str, m.Thing]:
        return {t.iid: t for t in self.all_things()}

    def header(self) -> dict[str, Any]:
        person = next(t for t in self.site_directory if isinstance(t, m.Person))
        return {
            "exchangeFileFormatVersion": EXCHANGE_FILE_FORMAT_VERSION,
            "createdOn": m.now_iso(),
            "creatorPerson": {
                "iid": person.iid, "givenName": person.givenName, "surname": person.surname,
                "emailAddress": person.emailAddress[0] if person.emailAddress else None,
            },
            "extensions": [],
            "remark": f"SpaceCDF study {self.study_id} (SCDF-160 ECSS-E-TM-10-25 export)",
        }


def _short(name: str, fallback: str = "x") -> str:
    s = re.sub(r"[^A-Za-z0-9_]+", "_", name or "").strip("_")
    if not s:
        s = fallback
    if s[0].isdigit():
        s = "_" + s
    return s[:32]


def _val(v: Any) -> str:
    if v is None:
        return NO_VALUE
    if isinstance(v, float) and v.is_integer() and abs(v) < 1e15:
        return str(v)
    return str(v)


def _dump(things: list[m.Thing]) -> list[dict]:
    return [t.model_dump(mode="json") for t in things]


# ── spine gateway (extra data not in SpineSnapshot) ─────────────────────

async def _load_raw_parameters(study_id: str) -> tuple[list[dict], dict[str, dict]]:
    """Return (element parameter rows, definitions by id) from the parameter repo."""
    from spacecdf_server.db.parameter_repo import (
        load_all_element_parameters, load_all_parameter_definitions,
    )
    defs = await load_all_parameter_definitions()
    rows = list((await load_all_element_parameters(study_id)).values())
    return rows, defs


# ── builder ─────────────────────────────────────────────────────────────

class _Builder:
    def __init__(self, snap: SpineSnapshot, params: list[dict], defs: dict[str, dict]):
        self.snap = snap
        self.params = params
        self.defs = defs
        self.sid = snap.study_id
        self.out = Model1025(study_id=self.sid)
        self.domains: dict[str, m.DomainOfExpertise] = {}
        self.units: dict[str, m.SimpleUnit] = {}
        self.scales: dict[str, m.RatioScale] = {}
        self.qkinds: dict[str, m.SimpleQuantityKind] = {}
        self.categories: dict[str, m.Category] = {}

    # reference data -----------------------------------------------------
    def domain(self, name: str | None) -> m.DomainOfExpertise:
        key = (name or "System").strip() or "System"
        d = self.domains.get(key)
        if d is None:
            d = m.DomainOfExpertise(iid=stable_iid("domain", key), name=key.title() if key.islower() else key,
                                    shortName=_short(key.upper(), "SYS"))
            self.domains[key] = d
        return d

    def unit(self, symbol: str) -> m.SimpleUnit:
        key = symbol or "1"
        u = self.units.get(key)
        if u is None:
            u = m.SimpleUnit(iid=stable_iid("unit", key), name=key if key != "1" else "one",
                             shortName=key)
            self.units[key] = u
        return u

    def scale(self, symbol: str) -> m.RatioScale:
        key = symbol or "1"
        s = self.scales.get(key)
        if s is None:
            s = m.RatioScale(iid=stable_iid("scale", key), name=f"{key} ratio scale",
                             shortName=key, unit=self.unit(key).iid)
            self.scales[key] = s
        return s

    def quantity_kind(self, pname: str, unit: str, qk: str | None) -> m.SimpleQuantityKind:
        q = self.qkinds.get(pname)
        if q is None:
            sc = self.scale(unit)
            q = m.SimpleQuantityKind(iid=stable_iid("qk", pname), name=(qk or pname).replace("_", " "),
                                     shortName=_short(pname), symbol=pname,
                                     defaultScale=sc.iid, possibleScale=[sc.iid])
            self.qkinds[pname] = q
        return q

    def category(self, name: str, permissible: str) -> m.Category:
        c = self.categories.get(name)
        if c is None:
            c = m.Category(iid=stable_iid("category", name), name=name, shortName=_short(name),
                           permissibleClass=[permissible])
            self.categories[name] = c
        return c

    # main ---------------------------------------------------------------
    def build(self) -> Model1025:
        sid = self.sid
        snap = self.snap
        sysdom = self.domain("System")

        rdl = m.SiteReferenceDataLibrary(iid=stable_iid("rdl", "spacecdf"), name="SpaceCDF RDL",
                                         shortName="SPACECDF_RDL")
        person = m.Person(iid=stable_iid("person", "spacecdf"), givenName="SpaceCDF", surname="Exporter",
                          shortName="spacecdf", defaultDomain=sysdom.iid)
        em_iid = stable_iid("em", sid)
        it_iid = stable_iid("iteration", sid, "1")
        itsetup = m.IterationSetup(iid=stable_iid("iterationsetup", sid, "1"), iterationIid=it_iid,
                                   iterationNumber=1, description="SpaceCDF export")
        participant = m.Participant(iid=stable_iid("participant", sid), person=person.iid,
                                    selectedDomain=sysdom.iid, domain=[sysdom.iid])
        setup = m.EngineeringModelSetup(iid=stable_iid("emsetup", sid), engineeringModelIid=em_iid,
                                        name=snap.study_name or sid, shortName=_short(snap.study_name or sid),
                                        iterationSetup=[itsetup.iid], participant=[participant.iid],
                                        requiredRdl=[rdl.iid])
        em = m.EngineeringModel(iid=em_iid, engineeringModelSetup=setup.iid, iteration=[it_iid])
        option = m.Option(iid=stable_iid("option", sid, "Baseline"), name="Baseline", shortName="Baseline")
        it = m.Iteration(iid=it_iid, iterationSetup=itsetup.iid, defaultOption=option.iid,
                         option=[{"k": 0, "v": option.iid}])
        iteration_things: list[m.Thing] = [it, option]

        # elements ---------------------------------------------------------
        eds: dict[str, m.ElementDefinition] = {}
        elements = [e for e in snap.elements if not e.get("deleted_at")]
        for e in elements:
            cat = self.category(e.get("element_type") or "component", "ElementDefinition")
            ed = m.ElementDefinition(iid=stable_iid("element", e["id"]), name=e.get("name") or e["id"],
                                     shortName=_short(e.get("name") or e["id"]),
                                     owner=self.domain(e.get("subsystem_domain")).iid, category=[cat.iid])
            eds[e["id"]] = ed
            iteration_things.append(ed)
        for e in elements:
            pid = e.get("parent_id")
            if pid and pid in eds:
                eu = m.ElementUsage(iid=stable_iid("usage", e["id"]), name=eds[e["id"]].name,
                                    shortName=eds[e["id"]].shortName, owner=eds[e["id"]].owner,
                                    elementDefinition=eds[e["id"]].iid, category=list(eds[e["id"]].category))
                eds[pid].containedElement.append(eu.iid)
                iteration_things.append(eu)
        roots = [e for e in elements if not e.get("parent_id") or e["parent_id"] not in eds]
        top = next((e for e in roots if e.get("element_type") == "system"), roots[0] if roots else None)
        if top is not None:
            it.topElement = eds[top["id"]].iid
        it.element = [ed.iid for ed in eds.values()]

        # parameters -------------------------------------------------------
        seen: set[tuple[str, str]] = set()
        for p in self.params:
            d = self.defs.get(p.get("definition_id") or "")
            if not d or p["element_id"] not in eds:
                continue
            self._parameter(eds[p["element_id"]], d["name"], d.get("unit") or "", d.get("quantity_kind"),
                            p.get("manual_value"), p.get("computed_value"), p.get("reference_value"),
                            p.get("value_switch") or "computed", p.get("formula"),
                            p.get("owner_domain"), iteration_things)
            seen.add((p["element_id"], d["name"]))
        # well-known columns that were never mirrored into rows
        from spacecdf_common.models.parameters import WELL_KNOWN_PARAMETERS
        wk_units = {"mass_kg": "kg", "power_avg_w": "W", "power_peak_w": "W", "volume_cm3": "cm3",
                    "cost_nre_keur": "kEUR", "cost_recurring_keur": "kEUR"}
        for e in elements:
            for name in WELL_KNOWN_PARAMETERS:
                if (e["id"], name) in seen or e.get(name) is None:
                    continue
                self._parameter(eds[e["id"]], name, wk_units.get(name, ""), None,
                                e.get(name), None, None, "manual", None, None, iteration_things)

        # requirements -----------------------------------------------------
        reqs = [r for r in snap.requirements if r.get("status") != "retired"]
        if reqs:
            spec = m.RequirementsSpecification(iid=stable_iid("reqspec", sid), name="SpaceCDF",
                                               shortName="SpaceCDF", owner=sysdom.iid)
            groups: dict[str, m.RequirementsGroup] = {}
            iteration_things.append(spec)
            for r in reqs:
                level = r.get("level") or "system"
                g = groups.get(level)
                if g is None:
                    g = m.RequirementsGroup(iid=stable_iid("reqgroup", sid, level), name=level.title(),
                                            shortName=_short(level.upper()), owner=sysdom.iid)
                    groups[level] = g
                    spec.group.append(g.iid)
                    iteration_things.append(g)
                defn = m.Definition(iid=stable_iid("reqdef", r["id"]), content=r.get("text") or "")
                req = m.Requirement(iid=stable_iid("requirement", r["id"]), name=r.get("code") or r["id"],
                                    shortName=_short(r.get("code") or r["id"]), owner=sysdom.iid,
                                    group=g.iid, definition=[defn.iid])
                spec.requirement.append(req.iid)
                iteration_things.extend([req, defn])
            it.requirementsSpecification.append(spec.iid)

        # assemble ---------------------------------------------------------
        rdl.unit = [u.iid for u in self.units.values()]
        rdl.scale = [s.iid for s in self.scales.values()]
        rdl.parameterType = [q.iid for q in self.qkinds.values()]
        rdl.definedCategory = [c.iid for c in self.categories.values()]
        setup.activeDomain = [d.iid for d in self.domains.values()]
        sd = m.SiteDirectory(iid=stable_iid("sitedirectory", "spacecdf"), name="SpaceCDF", shortName="SPACECDF",
                             domain=[d.iid for d in self.domains.values()], model=[setup.iid],
                             person=[person.iid], siteReferenceDataLibrary=[rdl.iid])
        self.out.site_directory = [sd, *self.domains.values(), person, setup, itsetup, participant]
        self.out.rdl = [rdl, *self.units.values(), *self.scales.values(), *self.qkinds.values(),
                        *self.categories.values()]
        self.out.engineering_model = [em]
        self.out.iteration = iteration_things
        return self.out

    def _parameter(self, ed: m.ElementDefinition, name: str, unit: str, qk: str | None,
                   manual, computed, reference, switch: str, formula: str | None,
                   owner_domain: str | None, sink: list[m.Thing]) -> None:
        q = self.quantity_kind(name, unit, qk)
        owner = self.domain(owner_domain).iid if owner_domain else ed.owner
        sw = switch.upper() if switch and switch.upper() in ("MANUAL", "COMPUTED", "REFERENCE") else "COMPUTED"
        effective = {"MANUAL": manual, "REFERENCE": reference}.get(sw, computed)
        if effective is None:
            effective = next((v for v in (computed, manual, reference) if v is not None), None)
        vs = m.ParameterValueSet(iid=stable_iid("valueset", ed.iid, name), valueSwitch=sw,
                                 manual=[_val(manual)], computed=[_val(computed)], reference=[_val(reference)],
                                 published=[_val(effective)], formula=[formula or NO_VALUE])
        p = m.Parameter(iid=stable_iid("parameter", ed.iid, name), owner=owner, parameterType=q.iid,
                        scale=q.defaultScale, valueSet=[vs.iid])
        ed.parameter.append(p.iid)
        sink.extend([p, vs])


async def build_10_25_model(study_id: str) -> Model1025:
    snap = await load_snapshot(study_id)
    params, defs = await _load_raw_parameters(study_id)
    return _Builder(snap, params, defs).build()


def write_annex_c3_zip(model: Model1025) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("Header.json", json.dumps(model.header(), indent=2))
        zf.writestr("SiteDirectory.json", json.dumps(_dump(model.site_directory), indent=2))
        zf.writestr(f"SiteReferenceDataLibraries/{model.rdl_iid}.json", json.dumps(_dump(model.rdl), indent=2))
        zf.writestr(f"EngineeringModels/{model.em_iid}/EngineeringModel.json",
                    json.dumps(_dump(model.engineering_model), indent=2))
        zf.writestr(f"EngineeringModels/{model.em_iid}/Iterations/{model.iteration_iid}.json",
                    json.dumps(_dump(model.iteration), indent=2))
    return buf.getvalue()


async def export_study_to_10_25(study_id: str) -> bytes:
    """Annex C.3 exchange-file zip for ``study_id``."""
    return write_annex_c3_zip(await build_10_25_model(study_id))
