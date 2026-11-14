"""Request validation schemas for workflow endpoints."""

import re

from pydantic import BaseModel, Field, field_validator


class EvidenceCreate(BaseModel):
    kind: str = Field(min_length=2, max_length=48)
    description: str = Field(min_length=5, max_length=2000)
    source_ref: str = Field(min_length=2, max_length=160)


class DecisionCreate(BaseModel):
    outcome: str = Field(pattern="^(substantiated|not_substantiated|inconclusive)$")
    rationale: str = Field(min_length=20, max_length=4000)


class AppealCreate(BaseModel):
    reason: str = Field(min_length=10, max_length=4000)


class AppealResolve(BaseModel):
    outcome: str = Field(pattern="^(upheld|overturned|remanded)$")
    rationale: str = Field(min_length=20, max_length=4000)


class AppealAssign(BaseModel):
    reviewer_id: int = Field(gt=0)


class ReviewerAssign(BaseModel):
    reviewer_id: int


class TextComparison(BaseModel):
    text_a: str = Field(min_length=30, max_length=100_000)
    text_b: str = Field(min_length=30, max_length=100_000)


class SubmissionCreate(BaseModel):
    assessment_id: int = Field(gt=0)
    content_text: str = Field(min_length=30, max_length=100_000)

    @field_validator("content_text")
    @classmethod
    def require_nonblank_text(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 30:
            raise ValueError("Assignment text must contain at least 30 non-whitespace characters.")
        if not re.search(r"(?u)\b\w\w+\b", value):
            raise ValueError("Assignment text must contain at least one word.")
        return value

