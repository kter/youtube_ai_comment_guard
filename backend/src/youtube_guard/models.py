"""Data models for YouTube Comment Guard."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class CommentCategory(str, Enum):
    """Categories for classified comments."""

    POSITIVE = "positive"  # 応援
    QUESTION = "question"  # 質問
    CONSTRUCTIVE = "constructive"  # 建設的な批判
    COMPLAINT = "complaint"  # ただの不満
    TOXIC = "toxic"  # 暴言・誹謗中傷


class ModerationStatus(str, Enum):
    """YouTube moderation statuses."""

    PUBLISHED = "published"
    HELD_FOR_REVIEW = "heldForReview"
    REJECTED = "rejected"


class CommentAnalysis(BaseModel):
    """Result of AI analysis on a comment."""

    toxicity_score: int = Field(ge=0, le=100, description="Toxicity score 0-100")
    category: CommentCategory
    reason: str
    mild_text: Optional[str] = None  # Transformed mild version


class Comment(BaseModel):
    """Processed comment model."""

    id: str
    video_id: str
    author_name: str
    author_channel_id: str
    original_text: str  # Original comment text (stored encrypted ideally)
    mild_text: str  # Mild/neutralized version
    category: CommentCategory
    toxicity_score: int
    moderation_status: ModerationStatus
    published_at: datetime
    analyzed_at: datetime
    needs_reply: bool = False


class CommentSummary(BaseModel):
    """Summary of comments for dashboard (safe to display)."""

    id: str
    video_id: str
    video_title: Optional[str] = None
    author_name: str
    mild_text: str  # Only show transformed text
    category: CommentCategory
    published_at: datetime
    needs_reply: bool = False


class DashboardStats(BaseModel):
    """Statistics for dashboard."""

    positive_count: int
    question_count: int
    constructive_count: int
    blocked_count: int  # Number only, no details
    total_processed: int


class ReplyRequest(BaseModel):
    """Request to reply to a comment."""

    comment_id: str
    text: str


class ProcessingResult(BaseModel):
    """Result of comment processing job."""

    processed_count: int
    hidden_count: int
    held_count: int
    errors: list[str] = []
