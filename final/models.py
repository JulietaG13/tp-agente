"""Data models for multi-agent system."""

from typing import TypedDict, Annotated
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages


class QuestionOutput(BaseModel):
    """Question Creator output schema."""
    question: str = Field(description="Question text")
    options: list[str] = Field(description="4 answer options")
    correct_index: int = Field(description="Correct answer index (0-3)", ge=0, le=3)


class DifficultyReviewOutput(BaseModel):
    """Difficulty Reviewer output schema."""
    approved: bool = Field(description="Whether question is approved")
    feedback: str = Field(description="Review feedback")


class AgentState(TypedDict):
    """Shared state for multi-agent workflow."""
    messages: Annotated[list, add_messages]
    current_question: str
    question_options: list
    question_correct_index: int
    difficulty_feedback: str
    user_feedback: str
    score_data: dict
    iteration_count: int
    question_approved: bool
    next_action: str
