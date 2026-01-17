import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from youtube_guard.main import app
from youtube_guard.services.firestore_service import FirestoreService
from youtube_guard.services.youtube_service import YouTubeService
from youtube_guard.services.ai_service import AIService
from youtube_guard.models import DashboardStats, CommentSummary, CommentCategory, Comment

@pytest.fixture
def mock_firestore():
    # Create the mock object
    mock = AsyncMock(spec=FirestoreService)
    
    # Configure mock responses
    mock.get_dashboard_comments = AsyncMock(return_value=[
        CommentSummary(
            id="1", 
            video_id="v1", 
            author_name="u1", 
            mild_text="mild text", 
            published_at="2024-01-01T00:00:00Z", 
            category=CommentCategory.POSITIVE
        )
    ])
    
    stats = DashboardStats(
        positive_count=10,
        question_count=5,
        constructive_count=3,
        blocked_count=2,
        total_processed=20
    )
    mock.get_dashboard_stats = AsyncMock(return_value=stats)
    mock.get_comments_by_category = AsyncMock(return_value=[])
    
    mock_comment = Comment(
        id="c1",
        video_id="v1",
        author_name="u1",
        author_channel_id="ch1",
        original_text="original",
        mild_text="mild",
        category=CommentCategory.POSITIVE,
        toxicity_score=0,
        moderation_status="published",
        published_at="2024-01-01T00:00:00Z",
        analyzed_at="2024-01-01T00:00:00Z",
        needs_reply=True
    )
    mock.get_comment = AsyncMock(return_value=mock_comment)
    mock.mark_as_replied = AsyncMock()
    
    return mock

@pytest.fixture
def mock_youtube():
    mock = MagicMock(spec=YouTubeService)
    mock.reply_to_comment = AsyncMock(return_value={"id": "reply_123"})
    return mock

@pytest.fixture
def mock_ai():
    mock = AsyncMock(spec=AIService)
    mock.generate_reply_suggestion = AsyncMock(return_value="Suggested reply")
    return mock

@pytest.fixture
def client(mock_firestore):
    # Patch the FirestoreService class used in main.py's lifespan
    with patch("youtube_guard.main.FirestoreService", return_value=mock_firestore):
        with TestClient(app) as test_client:
            yield test_client
