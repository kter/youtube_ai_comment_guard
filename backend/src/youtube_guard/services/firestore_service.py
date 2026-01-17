"""Firestore Service for data persistence.

Handles storing and retrieving processed comments and statistics.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from google.cloud import firestore

from youtube_guard.config import settings
from youtube_guard.models import Comment, CommentCategory, CommentSummary, DashboardStats

logger = logging.getLogger(__name__)


class FirestoreService:
    """Service for Firestore database operations."""

    def __init__(self):
        """Initialize Firestore client."""
        if settings.google_cloud_project:
            self._db = firestore.Client(project=settings.google_cloud_project)
        else:
            self._db = firestore.Client()

    @property
    def comments_collection(self):
        """Get comments collection reference."""
        return self._db.collection("comments")

    @property
    def statistics_collection(self):
        """Get statistics collection reference."""
        return self._db.collection("statistics")

    async def save_comment(self, comment: Comment) -> str:
        """Save a processed comment.

        Args:
            comment: Comment to save

        Returns:
            Document ID
        """
        doc_ref = self.comments_collection.document(comment.id)
        doc_ref.set({
            "video_id": comment.video_id,
            "author_name": comment.author_name,
            "author_channel_id": comment.author_channel_id,
            "original_text": comment.original_text,  # Consider encryption
            "mild_text": comment.mild_text,
            "category": comment.category.value,
            "toxicity_score": comment.toxicity_score,
            "moderation_status": comment.moderation_status.value,
            "published_at": comment.published_at,
            "analyzed_at": comment.analyzed_at,
            "needs_reply": comment.needs_reply,
        })

        logger.info(f"Saved comment {comment.id}")
        return comment.id

    async def get_comment(self, comment_id: str) -> Optional[Comment]:
        """Get a comment by ID.

        Args:
            comment_id: Comment ID

        Returns:
            Comment if found, None otherwise
        """
        doc = self.comments_collection.document(comment_id).get()
        if not doc.exists:
            return None

        data = doc.to_dict()
        return Comment(
            id=doc.id,
            video_id=data["video_id"],
            author_name=data["author_name"],
            author_channel_id=data["author_channel_id"],
            original_text=data["original_text"],
            mild_text=data["mild_text"],
            category=CommentCategory(data["category"]),
            toxicity_score=data["toxicity_score"],
            moderation_status=data["moderation_status"],
            published_at=data["published_at"],
            analyzed_at=data["analyzed_at"],
            needs_reply=data.get("needs_reply", False),
        )

    async def get_comments_by_category(
        self,
        category: CommentCategory,
        limit: int = 50,
        exclude_toxic: bool = True,
    ) -> list[CommentSummary]:
        """Get comments by category (safe summaries only).

        Args:
            category: Category to filter by
            limit: Maximum number of results
            exclude_toxic: Whether to exclude toxic comments

        Returns:
            List of comment summaries (without original text)
        """
        query = self.comments_collection.where("category", "==", category.value)

        if exclude_toxic:
            query = query.where("toxicity_score", "<", settings.toxicity_threshold)

        query = query.order_by("published_at", direction=firestore.Query.DESCENDING)
        query = query.limit(limit)

        docs = query.stream()

        summaries = []
        for doc in docs:
            data = doc.to_dict()
            summaries.append(
                CommentSummary(
                    id=doc.id,
                    video_id=data["video_id"],
                    author_name=data["author_name"],
                    mild_text=data["mild_text"],  # Only show safe version
                    category=CommentCategory(data["category"]),
                    published_at=data["published_at"],
                    needs_reply=data.get("needs_reply", False),
                )
            )

        return summaries

    async def get_dashboard_comments(self, limit: int = 50) -> dict[str, list[CommentSummary]]:
        """Get all comments grouped by category for dashboard.

        Returns:
            Dict with category keys and list of summaries
        """
        result = {
            "positive": await self.get_comments_by_category(CommentCategory.POSITIVE, limit),
            "questions": await self.get_comments_by_category(CommentCategory.QUESTION, limit),
            "constructive": await self.get_comments_by_category(
                CommentCategory.CONSTRUCTIVE, limit
            ),
        }
        return result

    async def get_dashboard_stats(self) -> DashboardStats:
        """Get statistics for dashboard."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        stats_doc = self.statistics_collection.document(today).get()

        if stats_doc.exists:
            data = stats_doc.to_dict()
            return DashboardStats(
                positive_count=data.get("positive_count", 0),
                question_count=data.get("question_count", 0),
                constructive_count=data.get("constructive_count", 0),
                blocked_count=data.get("blocked_count", 0),
                total_processed=data.get("total_processed", 0),
            )

        return DashboardStats(
            positive_count=0,
            question_count=0,
            constructive_count=0,
            blocked_count=0,
            total_processed=0,
        )

    async def update_statistics(
        self,
        positive_delta: int = 0,
        question_delta: int = 0,
        constructive_delta: int = 0,
        blocked_delta: int = 0,
        processed_delta: int = 0,
    ):
        """Update daily statistics.

        Args:
            *_delta: Counts to add to each category
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        stats_ref = self.statistics_collection.document(today)

        stats_ref.set(
            {
                "positive_count": firestore.Increment(positive_delta),
                "question_count": firestore.Increment(question_delta),
                "constructive_count": firestore.Increment(constructive_delta),
                "blocked_count": firestore.Increment(blocked_delta),
                "total_processed": firestore.Increment(processed_delta),
                "updated_at": datetime.now(timezone.utc),
            },
            merge=True,
        )

    async def comment_exists(self, comment_id: str) -> bool:
        """Check if a comment has already been processed.

        Args:
            comment_id: Comment ID

        Returns:
            True if comment exists in database
        """
        doc = self.comments_collection.document(comment_id).get()
        return doc.exists

    async def mark_as_replied(self, comment_id: str):
        """Mark a comment as replied to.

        Args:
            comment_id: Comment ID
        """
        self.comments_collection.document(comment_id).update({
            "needs_reply": False,
            "replied_at": datetime.now(timezone.utc),
        })
