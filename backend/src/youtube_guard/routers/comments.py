"""Comments API Router.

Endpoints for viewing and managing processed comments.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request

from youtube_guard.models import CommentCategory, CommentSummary, DashboardStats, ReplyRequest
from youtube_guard.routers.auth import get_user_credentials
from youtube_guard.services.ai_service import AIService
from youtube_guard.services.firestore_service import FirestoreService
from youtube_guard.services.youtube_service import YouTubeService
logger = logging.getLogger(__name__)

router = APIRouter()


def get_firestore(request: Request) -> FirestoreService:
    """Get Firestore service from app state."""
    return request.app.state.firestore


@router.get("/summary", response_model=dict)
async def get_comments_summary(
    request: Request,
    limit: int = Query(default=50, le=100),
):
    """Get categorized comment summaries for dashboard.

    Returns safe-to-view summaries only (no raw toxic content).
    """
    firestore = get_firestore(request)

    try:
        comments = await firestore.get_dashboard_comments(limit)
        stats = await firestore.get_dashboard_stats()

        return {
            "comments": comments,
            "stats": stats.model_dump(),
        }
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get comments summary")


@router.get("/category/{category}", response_model=list[CommentSummary])
async def get_comments_by_category(
    request: Request,
    category: CommentCategory,
    limit: int = Query(default=50, le=100),
):
    """Get comments for a specific category.

    Note: Toxic comments are excluded - only count is available.
    """
    if category == CommentCategory.TOXIC:
        raise HTTPException(
            status_code=400,
            detail="Toxic comments are not viewable. Check stats for count only.",
        )

    firestore = get_firestore(request)

    try:
        return await firestore.get_comments_by_category(category, limit)
    except Exception as e:
        logger.error(f"Error getting comments by category: {e}")
        raise HTTPException(status_code=500, detail="Failed to get comments")


@router.get("/stats", response_model=DashboardStats)
async def get_stats(request: Request):
    """Get dashboard statistics."""
    firestore = get_firestore(request)

    try:
        return await firestore.get_dashboard_stats()
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

@router.post("/{comment_id}/reply")
async def reply_to_comment(
    request: Request,
    comment_id: str,
    reply: ReplyRequest,
):
    """Reply to a comment via YouTube API.

    The reply is posted directly to YouTube.
    """
    firestore = get_firestore(request)

    try:
        # Get comment to verify it exists
        comment = await firestore.get_comment(comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        # Get user credentials
        credentials_json = get_user_credentials(request)
        if not credentials_json:
             raise HTTPException(status_code=401, detail="User not authenticated")

        # Post reply via YouTube API
        youtube = YouTubeService(credentials_json=credentials_json)
        result = await youtube.reply_to_comment(comment_id, reply.text)

        # Mark as replied in database
        await firestore.mark_as_replied(comment_id)

        return {
            "success": True,
            "reply_id": result["id"],
            "message": "Reply posted successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error replying to comment: {e}")
        raise HTTPException(status_code=500, detail="Failed to post reply")





@router.post("/{comment_id}/suggest-reply")
async def suggest_reply(
    request: Request,
    comment_id: str,
):
    """Get AI-generated reply suggestion for a comment."""
    firestore = get_firestore(request)

    try:
        comment = await firestore.get_comment(comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        ai = AIService()
        suggestion = await ai.generate_reply_suggestion(
            comment.mild_text,
            comment.category,
        )

        return {
            "comment_id": comment_id,
            "suggestion": suggestion,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating reply suggestion: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate suggestion")


@router.post("/sync")
async def trigger_sync(request: Request):
    """Manually trigger comment sync and processing.

    This is the same as the scheduled job but can be triggered on-demand.
    """
    from youtube_guard.routers.scheduler import process_comments

    return await process_comments(request)
