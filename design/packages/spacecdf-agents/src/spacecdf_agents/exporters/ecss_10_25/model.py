"""Pydantic mirror of the ECSS-E-TM-10-25 Annex A classes SpaceCDF exchanges.

Annex A (the UML data model) is a member-state-restricted document.  The
class and property names used here are the ones the open-source reference
implementation exposes (``CDP4Common`` in STARIONGROUP/COMET-SDK-Community-
Edition, Apache-2.0) and that appear verbatim in the public sample models in
STARIONGROUP/CDP4-COMET-MODELS.  ``classKind`` strings are therefore the
CDP4Common ``ClassKind`` enum member names.

Conventions mirrored from the JSON serialisation (Annex C):

* every object carries ``iid`` (UUID), ``classKind``, ``revisionNumber``;
  ``modifiedOn`` is an ISO-8601 UTC timestamp (present in COMET >= 6);
* containment is expressed as a list of child ``iid`` strings on the
  container (``Iteration.element``, ``ElementDefinition.parameter`` ...);
  ordered containment lists (``SiteDirectory.domain``, ``Iteration.option``)
  are serialised by CDP4 as ``[{"k": <int>, "v": <iid>}]`` — we use the
  ordered form only for ``Iteration.option`` and keep plain lists elsewhere,
  which the CDP4 deserialiser accepts for unordered containers;
* references (``owner``, ``parameterType``, ``scale``, ``elementDefinition``)
  are plain iid strings; nullable references are ``None``;
* ``ParameterValueSet.manual/computed/reference/published/formula`` are
  ``ValueArray<string>`` -> JSON list of strings, one entry per component
  (SpaceCDF only uses scalar parameters so the list has exactly one entry;
  the CDP4 "no value" sentinel is ``"-"``);
* ``valueSwitch`` is one of ``MANUAL``, ``COMPUTED``, ``REFERENCE``.

Only the properties SpaceCDF populates are modelled; unknown keys survive a
round trip because every class has ``extra="allow"``.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, ClassVar, Literal
from uuid import NAMESPACE_URL, uuid5

from pydantic import BaseModel, ConfigDict, Field

SPACECDF_NS = uuid5(NAMESPACE_URL, "https://spacecdf.org/ecss-e-tm-10-25")


def stable_iid(*parts: str) -> str:
    """Deterministic UUID (v5) from spine ids so re-exports keep the same iids."""
    return str(uuid5(SPACECDF_NS, "/".join(str(p) for p in parts)))


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class Thing(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)
    CLASS_KIND: ClassVar[str] = "Thing"

    iid: str
    classKind: str = ""
    revisionNumber: int = 1
    modifiedOn: str = Field(default_factory=now_iso)

    def model_post_init(self, __context: Any) -> None:  # noqa: D401
        if not self.classKind:
            self.classKind = self.CLASS_KIND


class DefinedThing(Thing):
    name: str = ""
    shortName: str = ""
    alias: list[str] = Field(default_factory=list)
    definition: list[str] = Field(default_factory=list)
    hyperLink: list[str] = Field(default_factory=list)


# ── Site directory ──────────────────────────────────────────────────────

class SiteDirectory(DefinedThing):
    CLASS_KIND = "SiteDirectory"
    createdOn: str = Field(default_factory=now_iso)
    lastModifiedOn: str = Field(default_factory=now_iso)
    defaultParticipantRole: str | None = None
    defaultPersonRole: str | None = None
    domain: list[str] = Field(default_factory=list)
    domainGroup: list[str] = Field(default_factory=list)
    model: list[str] = Field(default_factory=list)
    naturalLanguage: list[str] = Field(default_factory=list)
    organization: list[str] = Field(default_factory=list)
    participantRole: list[str] = Field(default_factory=list)
    person: list[str] = Field(default_factory=list)
    personRole: list[str] = Field(default_factory=list)
    siteReferenceDataLibrary: list[str] = Field(default_factory=list)
    logEntry: list[str] = Field(default_factory=list)


class DomainOfExpertise(DefinedThing):
    CLASS_KIND = "DomainOfExpertise"
    isDeprecated: bool = False
    category: list[str] = Field(default_factory=list)


class Person(Thing):
    CLASS_KIND = "Person"
    givenName: str = ""
    surname: str = ""
    shortName: str = ""
    isActive: bool = True
    isDeprecated: bool = False
    defaultDomain: str | None = None
    organization: str | None = None
    role: str | None = None
    emailAddress: list[str] = Field(default_factory=list)
    telephoneNumber: list[str] = Field(default_factory=list)
    userPreference: list[str] = Field(default_factory=list)


class Participant(Thing):
    CLASS_KIND = "Participant"
    isActive: bool = True
    person: str
    role: str | None = None
    selectedDomain: str | None = None
    domain: list[str] = Field(default_factory=list)


class EngineeringModelSetup(DefinedThing):
    CLASS_KIND = "EngineeringModelSetup"
    engineeringModelIid: str
    kind: str = "STUDY_MODEL"
    studyPhase: str = "PREPARATION_PHASE"
    sourceEngineeringModelSetupIid: str | None = None
    activeDomain: list[str] = Field(default_factory=list)
    iterationSetup: list[str] = Field(default_factory=list)
    participant: list[str] = Field(default_factory=list)
    requiredRdl: list[str] = Field(default_factory=list)


class IterationSetup(Thing):
    CLASS_KIND = "IterationSetup"
    iterationIid: str
    iterationNumber: int = 1
    description: str = ""
    createdOn: str = Field(default_factory=now_iso)
    frozenOn: str | None = None
    isDeleted: bool = False
    sourceIterationSetup: str | None = None


# ── Reference data library ──────────────────────────────────────────────

class ReferenceDataLibrary(DefinedThing):
    baseQuantityKind: list[dict] = Field(default_factory=list)
    baseUnit: list[str] = Field(default_factory=list)
    constant: list[str] = Field(default_factory=list)
    definedCategory: list[str] = Field(default_factory=list)
    fileType: list[str] = Field(default_factory=list)
    glossary: list[str] = Field(default_factory=list)
    parameterType: list[str] = Field(default_factory=list)
    referenceSource: list[str] = Field(default_factory=list)
    rule: list[str] = Field(default_factory=list)
    scale: list[str] = Field(default_factory=list)
    unit: list[str] = Field(default_factory=list)
    unitPrefix: list[str] = Field(default_factory=list)
    requiredRdl: str | None = None


class SiteReferenceDataLibrary(ReferenceDataLibrary):
    CLASS_KIND = "SiteReferenceDataLibrary"
    isDeprecated: bool = False


class MeasurementUnit(DefinedThing):
    CLASS_KIND = "MeasurementUnit"
    isDeprecated: bool = False


class SimpleUnit(MeasurementUnit):
    CLASS_KIND = "SimpleUnit"


class RatioScale(DefinedThing):
    CLASS_KIND = "RatioScale"
    isDeprecated: bool = False
    unit: str
    numberSet: str = "REAL_NUMBER_SET"
    isMinimumInclusive: bool = True
    isMaximumInclusive: bool = True
    minimumPermissibleValue: str | None = None
    maximumPermissibleValue: str | None = None
    positiveValueConnotation: str | None = None
    negativeValueConnotation: str | None = None
    mappingToReferenceScale: list[str] = Field(default_factory=list)
    valueDefinition: list[str] = Field(default_factory=list)


class SimpleQuantityKind(DefinedThing):
    CLASS_KIND = "SimpleQuantityKind"
    isDeprecated: bool = False
    symbol: str = ""
    quantityDimensionSymbol: str = ""
    defaultScale: str
    possibleScale: list[str] = Field(default_factory=list)
    category: list[str] = Field(default_factory=list)


class TextParameterType(DefinedThing):
    CLASS_KIND = "TextParameterType"
    isDeprecated: bool = False
    symbol: str = ""
    category: list[str] = Field(default_factory=list)


class Category(DefinedThing):
    CLASS_KIND = "Category"
    isDeprecated: bool = False
    isAbstract: bool = False
    permissibleClass: list[str] = Field(default_factory=list)
    superCategory: list[str] = Field(default_factory=list)


# ── Engineering model / iteration ───────────────────────────────────────

class EngineeringModel(Thing):
    CLASS_KIND = "EngineeringModel"
    engineeringModelSetup: str
    lastModifiedOn: str = Field(default_factory=now_iso)
    iteration: list[str] = Field(default_factory=list)
    book: list[dict] = Field(default_factory=list)
    commonFileStore: list[str] = Field(default_factory=list)
    logEntry: list[str] = Field(default_factory=list)
    modellingAnnotation: list[str] = Field(default_factory=list)


class Iteration(Thing):
    CLASS_KIND = "Iteration"
    iterationSetup: str
    defaultOption: str | None = None
    topElement: str | None = None
    sourceIterationIid: str | None = None
    option: list[dict] = Field(default_factory=list)  # ordered: [{"k": n, "v": iid}]
    element: list[str] = Field(default_factory=list)
    requirementsSpecification: list[str] = Field(default_factory=list)
    domainFileStore: list[str] = Field(default_factory=list)
    actualFiniteStateList: list[str] = Field(default_factory=list)
    possibleFiniteStateList: list[str] = Field(default_factory=list)
    relationship: list[str] = Field(default_factory=list)
    externalIdentifierMap: list[str] = Field(default_factory=list)
    publication: list[str] = Field(default_factory=list)
    ruleVerificationList: list[str] = Field(default_factory=list)
    stakeholder: list[str] = Field(default_factory=list)
    goal: list[str] = Field(default_factory=list)
    valueGroup: list[str] = Field(default_factory=list)
    stakeholderValue: list[str] = Field(default_factory=list)
    stakeholderValueMap: list[str] = Field(default_factory=list)
    diagramCanvas: list[str] = Field(default_factory=list)
    sharedDiagramStyle: list[str] = Field(default_factory=list)


class Option(DefinedThing):
    CLASS_KIND = "Option"
    category: list[str] = Field(default_factory=list)
    nestedElement: list[str] = Field(default_factory=list)


class ElementBase(DefinedThing):
    owner: str
    category: list[str] = Field(default_factory=list)


class ElementDefinition(ElementBase):
    CLASS_KIND = "ElementDefinition"
    containedElement: list[str] = Field(default_factory=list)
    parameter: list[str] = Field(default_factory=list)
    parameterGroup: list[str] = Field(default_factory=list)
    referencedElement: list[str] = Field(default_factory=list)
    organizationalParticipant: list[str] = Field(default_factory=list)


class ElementUsage(ElementBase):
    CLASS_KIND = "ElementUsage"
    elementDefinition: str
    interfaceEnd: str = "NONE"
    excludeOption: list[str] = Field(default_factory=list)
    parameterOverride: list[str] = Field(default_factory=list)


class Parameter(Thing):
    CLASS_KIND = "Parameter"
    owner: str
    parameterType: str
    scale: str | None = None
    group: str | None = None
    stateDependence: str | None = None
    requestedBy: str | None = None
    isOptionDependent: bool = False
    allowDifferentOwnerOfOverride: bool = False
    expectsOverride: bool = False
    valueSet: list[str] = Field(default_factory=list)
    parameterSubscription: list[str] = Field(default_factory=list)


ValueSwitch = Literal["MANUAL", "COMPUTED", "REFERENCE"]


class ParameterValueSet(Thing):
    CLASS_KIND = "ParameterValueSet"
    actualOption: str | None = None
    actualState: str | None = None
    valueSwitch: ValueSwitch = "COMPUTED"
    manual: list[str] = Field(default_factory=lambda: ["-"])
    computed: list[str] = Field(default_factory=lambda: ["-"])
    reference: list[str] = Field(default_factory=lambda: ["-"])
    published: list[str] = Field(default_factory=lambda: ["-"])
    formula: list[str] = Field(default_factory=lambda: ["-"])


# ── Requirements ────────────────────────────────────────────────────────

class RequirementsContainer(DefinedThing):
    owner: str
    category: list[str] = Field(default_factory=list)
    group: list[str] = Field(default_factory=list)
    parametricConstraint: list[str] = Field(default_factory=list)


class RequirementsSpecification(RequirementsContainer):
    CLASS_KIND = "RequirementsSpecification"
    isDeprecated: bool = False
    requirement: list[str] = Field(default_factory=list)


class RequirementsGroup(RequirementsContainer):
    CLASS_KIND = "RequirementsGroup"


class Requirement(DefinedThing):
    CLASS_KIND = "Requirement"
    owner: str
    isDeprecated: bool = False
    group: str | None = None
    category: list[str] = Field(default_factory=list)
    parametricConstraint: list[dict] = Field(default_factory=list)
    parameterValue: list[str] = Field(default_factory=list)


class Definition(Thing):
    CLASS_KIND = "Definition"
    languageCode: str = "en-GB"
    content: str = ""
    citation: list[str] = Field(default_factory=list)
    example: list[dict] = Field(default_factory=list)
    note: list[dict] = Field(default_factory=list)


class Alias(Thing):
    CLASS_KIND = "Alias"
    languageCode: str = "en-GB"
    content: str = ""
    isSynonym: bool = True


ALL_CLASSES: dict[str, type[Thing]] = {
    c.CLASS_KIND: c for c in (
        SiteDirectory, DomainOfExpertise, Person, Participant, EngineeringModelSetup,
        IterationSetup, SiteReferenceDataLibrary, MeasurementUnit, SimpleUnit, RatioScale,
        SimpleQuantityKind, TextParameterType, Category, EngineeringModel, Iteration, Option,
        ElementDefinition, ElementUsage, Parameter, ParameterValueSet,
        RequirementsSpecification, RequirementsGroup, Requirement, Definition, Alias,
    )
}


def parse_thing(d: dict) -> Thing:
    """Instantiate the right mirror class from a JSON object (by ``classKind``)."""
    cls = ALL_CLASSES.get(d.get("classKind", ""), Thing)
    return cls.model_validate(d)
