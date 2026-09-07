"""
Pydantic v2 request/response schemas for the Rulebook QA API.
"""

from pydantic import BaseModel, Field
from typing import Optional


class QuestionRequest(BaseModel):
    """Request body for the /ask endpoint."""
    question: str = Field(..., min_length=1, description="The question to ask the rulebook.")


class PassageResult(BaseModel):
    """A single retrieved passage with metadata."""
    section_id: str = Field(..., description="Section identifier (e.g. ATT-2, HOSTEL-4-REFUND-A)")
    source_file: str = Field(..., description="Filename of the source corpus document")
    text: str = Field(..., description="The passage text")
    score: float = Field(..., description="Cosine similarity score")


class QAResponse(BaseModel):
    """Response from the /ask endpoint."""
    type: str = Field(
        ...,
        description="Classification: 'answered', 'not_covered', or 'conflict'",
        pattern="^(answered|not_covered|conflict)$"
    )
    answer: Optional[str] = Field(None, description="Answer text (null for conflict/not_covered)")
    passages: list[PassageResult] = Field(default_factory=list, description="Retrieved passages with scores")
    conflict_note: Optional[str] = Field(None, description="Explanation for conflict type responses")
