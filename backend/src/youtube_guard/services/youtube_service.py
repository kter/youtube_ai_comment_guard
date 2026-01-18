"""YouTube Data API v3 Service.

Handles interactions with YouTube API for comment management.
"""

import json
import logging
from typing import Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from youtube_guard.config import settings
from youtube_guard.models import ModerationStatus

logger = logging.getLogger(__name__)


class YouTubeService:
    """Service for YouTube Data API v3 operations."""

    def __init__(self, credentials_json: Optional[str] = None):
        """Initialize YouTube service with credentials."""
        self._youtube = None
        self._credentials_json = credentials_json or settings.youtube_credentials

    def _get_youtube_client(self):
        """Get authenticated YouTube API client."""
        if self._youtube is None:
            if not self._credentials_json:
                raise ValueError("YouTube credentials not configured")

            creds_data = json.loads(self._credentials_json)
            credentials = Credentials(
                token=creds_data.get("token"),
                refresh_token=creds_data.get("refresh_token"),
                token_uri=creds_data.get("token_uri", "https://oauth2.googleapis.com/token"),
                client_id=creds_data.get("client_id"),
                client_secret=creds_data.get("client_secret"),
            )
            self._youtube = build("youtube", "v3", credentials=credentials)

        return self._youtube

    async def get_my_videos(self, max_results: int = 10) -> list[dict]:
        """Get list of videos from authenticated user's channel."""
        youtube = self._get_youtube_client()

        try:
            # Get channel's uploads playlist
            channels_response = youtube.channels().list(
                part="contentDetails",
                mine=True,
            ).execute()

            if not channels_response.get("items"):
                return []

            uploads_playlist_id = channels_response["items"][0]["contentDetails"][
                "relatedPlaylists"
            ]["uploads"]

            # Get videos from uploads playlist
            videos_response = youtube.playlistItems().list(
                part="snippet",
                playlistId=uploads_playlist_id,
                maxResults=max_results,
            ).execute()

            videos = []
            for item in videos_response.get("items", []):
                snippet = item["snippet"]
                videos.append({
                    "video_id": snippet["resourceId"]["videoId"],
                    "title": snippet["title"],
                    "published_at": snippet["publishedAt"],
                    "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url"),
                })

            return videos

        except HttpError as e:
            logger.error(f"YouTube API error getting videos: {e}")
            raise

    async def get_comment_threads(
        self,
        video_id: str,
        max_results: int = 100,
        moderation_status: Optional[str] = None,
    ) -> list[dict]:
        """Get comment threads for a video.

        Args:
            video_id: YouTube video ID
            max_results: Maximum number of comments to fetch
            moderation_status: Filter by moderation status (heldForReview, likelySpam, published)
        """
        youtube = self._get_youtube_client()

        try:
            request_params = {
                "part": "snippet",
                "videoId": video_id,
                "maxResults": min(max_results, 100),
                "textFormat": "plainText",
            }

            if moderation_status:
                request_params["moderationStatus"] = moderation_status

            response = youtube.commentThreads().list(**request_params).execute()

            comments = []
            for item in response.get("items", []):
                snippet = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "id": item["id"],
                    "video_id": video_id,
                    "text": snippet["textDisplay"],
                    "author_name": snippet["authorDisplayName"],
                    "author_channel_id": snippet.get("authorChannelId", {}).get("value", ""),
                    "published_at": snippet["publishedAt"],
                    "like_count": snippet.get("likeCount", 0),
                    "reply_count": item["snippet"]["totalReplyCount"],
                    "viewer_rating": snippet.get("viewerRating", "none"),
                })

            return comments

        except HttpError as e:
            logger.error(f"YouTube API error getting comments: {e}")
            raise

    async def set_moderation_status(
        self,
        comment_ids: list[str],
        status: ModerationStatus,
        ban_author: bool = False,
    ) -> bool:
        """Set moderation status for comments.

        Args:
            comment_ids: List of comment IDs
            status: New moderation status
            ban_author: If rejecting, also ban the author
        """
        youtube = self._get_youtube_client()

        try:
            youtube.comments().setModerationStatus(
                id=",".join(comment_ids),
                moderationStatus=status.value,
                banAuthor=ban_author,
            ).execute()

            logger.info(f"Set moderation status to {status} for {len(comment_ids)} comments")
            return True

        except HttpError as e:
            logger.error(f"YouTube API error setting moderation status: {e}")
            raise

    async def reply_to_comment(self, parent_id: str, text: str) -> dict:
        """Reply to a comment.

        Args:
            parent_id: Parent comment ID
            text: Reply text
        """
        youtube = self._get_youtube_client()

        try:
            response = youtube.comments().insert(
                part="snippet",
                body={
                    "snippet": {
                        "parentId": parent_id,
                        "textOriginal": text,
                    }
                },
            ).execute()

            return {
                "id": response["id"],
                "text": response["snippet"]["textDisplay"],
            }

        except HttpError as e:
            logger.error(f"YouTube API error replying to comment: {e}")
            raise

