from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SimilarityMatch(StrictModel):
    jd_requirement: str = Field(min_length=1)
    resume_evidence: str = Field(min_length=1)
    match_explanation: str = Field(min_length=1)


class DifferenceOrGap(StrictModel):
    jd_requirement: str = Field(min_length=1)
    resume_evidence: str = Field(min_length=1)
    gap_explanation: str = Field(min_length=1)


class MissingRequirement(StrictModel):
    jd_requirement: str = Field(min_length=1)
    importance: Literal["required", "preferred"]
    reason: str = Field(min_length=1)


class PreparationPriority(StrictModel):
    priority: Literal["HIGH", "MEDIUM", "LOW"]
    topic: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class OverallAssessment(StrictModel):
    summary: str = Field(min_length=1)
    strengths: list[str]
    major_gaps: list[str]
    readiness: Literal["strong", "moderate", "needs_preparation"]


class AnalysisResult(StrictModel):
    similarity_matches: list[SimilarityMatch]
    differences_and_gaps: list[DifferenceOrGap]
    missing_requirements: list[MissingRequirement]
    preparation_priorities: list[PreparationPriority]
    overall_assessment: OverallAssessment
