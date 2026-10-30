"""SpaceCDF — Position-based guidance data models.

Models the 10 engineering positions in a concurrent design session,
each with key questions, parameter ownership, and inter-position dependencies.
Inspired by ESA CDF workstation roles.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class DesignQuestion(BaseModel):
    """A question that an engineer in this position must answer."""

    id: str
    question: str = Field(description="The question, e.g. 'Is the link budget closed with ≥3dB margin?'")
    category: str = Field(default="sizing", description="sizing | selection | verification | trade | requirement")
    priority: Literal["must_answer", "should_answer", "nice_to_have"] = "must_answer"
    related_parameters: list[str] = Field(default_factory=list, description="Parameter IDs to check for answer status")
    guidance: str = Field(default="", description="Engineering guidance on how to approach this question")
    typical_range: str = Field(default="", description="Typical acceptable values, e.g. '3-10 dB for LEO'")
    health_check: str = Field(default="", description="Condition expression to evaluate, e.g. 'value >= 3.0'")


class ParameterOwnership(BaseModel):
    """Relationship between a position and a parameter."""

    param_pattern: str = Field(description="Parameter ID or glob pattern, e.g. 'power.*' or 'power.sa_area_m2'")
    role: Literal["owns", "consumes", "influences"] = "owns"
    description: str = ""


class Position(BaseModel):
    """An engineering position in the concurrent design facility."""

    id: str = Field(description="Unique ID, e.g. 'power_engineer'")
    name: str = Field(description="Display name, e.g. 'Power Engineer'")
    domain: str = Field(description="Primary engineering domain, e.g. 'power'")
    icon: str = Field(default="", description="Emoji or icon identifier")
    description: str = Field(default="", description="Role description")
    key_questions: list[DesignQuestion] = Field(default_factory=list)
    parameters: list[ParameterOwnership] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list, description="Position IDs this one needs input from")
    feeds_into: list[str] = Field(default_factory=list, description="Position IDs that need this one's output")


class QuestionStatus(BaseModel):
    """Status of a single design question given the current design state."""

    question_id: str
    question: str
    priority: str
    status: Literal["answered", "open", "warning", "not_applicable"] = "open"
    current_value: str = ""
    assessment: str = ""


class PositionGuidance(BaseModel):
    """Computed guidance for a position given the current design state."""

    position_id: str
    position_name: str
    answered_questions: list[QuestionStatus] = Field(default_factory=list)
    open_questions: list[QuestionStatus] = Field(default_factory=list)
    warning_questions: list[QuestionStatus] = Field(default_factory=list)
    active_conflicts: list[str] = Field(default_factory=list, description="Conflict IDs involving this position")
    owned_parameters: dict[str, Any] = Field(default_factory=dict, description="Current values of owned params")
    consumed_parameters: dict[str, Any] = Field(default_factory=dict, description="Current values of consumed params")
    recommendations: list[str] = Field(default_factory=list)
    completion_percent: float = Field(default=0.0, description="Percentage of must_answer questions answered")
