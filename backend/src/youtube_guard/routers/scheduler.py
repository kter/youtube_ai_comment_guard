"""Scheduler API Router.

Endpoints for Cloud Scheduler triggered processing.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Request

from youtube_guard.config import settings
from youtube_guard.models import Comment, CommentCategory, ModerationStatus, ProcessingResult
from youtube_guard.services.ai_service import AIService
from youtube_guard.services.firestore_service import FirestoreService
from youtube_guard.services.youtube_service import YouTubeService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/process", response_model=ProcessingResult)
async def process_comments(request: Request):
    """Process new comments from YouTube.

    Called by Cloud Scheduler every 15 minutes.
    This is the main processing pipeline:
    1. Fetch new comments from YouTube
    2. Analyze each comment with AI
    3. Take moderation action based on toxicity
    4. Store results in Firestore
    """
    firestore: FirestoreService = request.app.state.firestore
    youtube = YouTubeService()
    ai = AIService()

    result = ProcessingResult(processed_count=0, hidden_count=0, held_count=0)

    try:
        # Get list of videos to process
        videos = await youtube.get_my_videos(max_results=5)  # Recent 5 videos

        for video in videos:
            video_id = video["video_id"]

            # Get new comments
            comments = await youtube.get_comment_threads(video_id, max_results=50)

            for comment_data in comments:
                comment_id = comment_data["id"]

                # Skip if already processed
                if await firestore.comment_exists(comment_id):
                    continue

                try:
                    # Analyze with AI
                    analysis = await ai.analyze_comment(comment_data["text"])

                    # Determine moderation action
                    moderation_status = ModerationStatus.PUBLISHED
                    if analysis.toxicity_score >= settings.toxicity_threshold:
                        moderation_status = ModerationStatus.REJECTED
                        result.hidden_count += 1
                    elif analysis.toxicity_score >= settings.hold_threshold:
                        moderation_status = ModerationStatus.HELD_FOR_REVIEW
                        result.held_count += 1

                    # Apply moderation if needed
                    if moderation_status != ModerationStatus.PUBLISHED:
                        await youtube.set_moderation_status(
                            [comment_id],
                            moderation_status,
                        )

                    # Create comment record
                    comment = Comment(
                        id=comment_id,
                        video_id=video_id,
                        author_name=comment_data["author_name"],
                        author_channel_id=comment_data["author_channel_id"],
                        original_text=comment_data["text"],
                        mild_text=analysis.mild_text or comment_data["text"],
                        category=analysis.category,
                        toxicity_score=analysis.toxicity_score,
                        moderation_status=moderation_status,
                        published_at=datetime.fromisoformat(
                            comment_data["published_at"].replace("Z", "+00:00")
                        ),
                        analyzed_at=datetime.now(timezone.utc),
                        needs_reply=analysis.category
                        in [CommentCategory.QUESTION, CommentCategory.CONSTRUCTIVE],
                    )

                    # Save to Firestore
                    await firestore.save_comment(comment)
                    result.processed_count += 1

                except Exception as e:
                    error_msg = f"Error processing comment {comment_id}: {e}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)

        # Update statistics
        await firestore.update_statistics(
            blocked_delta=result.hidden_count + result.held_count,
            processed_delta=result.processed_count,
        )

        logger.info(
            f"Processing complete: {result.processed_count} processed, "
            f"{result.hidden_count} hidden, {result.held_count} held"
        )

        return result

    except Exception as e:
        error_msg = f"Processing job failed: {e}"
        logger.error(error_msg)
        result.errors.append(error_msg)
        return result
