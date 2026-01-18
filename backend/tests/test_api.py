import pytest
from unittest.mock import patch, AsyncMock
from youtube_guard.models import CommentCategory, CommentSummary, DashboardStats, Comment

def test_get_summary(client, mock_firestore):
    mock_firestore.get_dashboard_comments.return_value = [
        CommentSummary(
            id="1", 
            video_id="v1", 
            author_name="u1", 
            mild_text="mild text", 
            published_at="2024-01-01T00:00:00Z", 
            category=CommentCategory.POSITIVE
        )
    ]
    
    response = client.get("/api/comments/summary")
    assert response.status_code == 200
    data = response.json()
    assert "comments" in data
    assert "stats" in data
    assert len(data["comments"]) == 1

def test_get_category_toxic_error(client):
    response = client.get(f"/api/comments/category/{CommentCategory.TOXIC.value}")
    assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"

def test_get_category_safe(client, mock_firestore):
    mock_firestore.get_comments_by_category.return_value = []
    response = client.get(f"/api/comments/category/{CommentCategory.POSITIVE.value}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert response.json() == []

def test_get_stats(client, mock_firestore):
    mock_stat = DashboardStats(
        positive_count=10,
        question_count=5,
        constructive_count=3,
        blocked_count=2,
        total_processed=20
    )
    mock_firestore.get_dashboard_stats.return_value = mock_stat
    
    response = client.get("/api/comments/stats")
    assert response.status_code == 200
    assert response.json()["total_processed"] == 20
    assert response.json()["positive_count"] == 10

@patch("youtube_guard.routers.comments.get_user_credentials")
@patch("youtube_guard.routers.comments.YouTubeService")
def test_reply_to_comment(MockYouTubeService, mock_get_credentials, client, mock_firestore):
    # Setup mock credentials
    mock_get_credentials.return_value = '{"token": "fake"}'
    # Setup mock
    mock_youtube_instance = MockYouTubeService.return_value
    # MUST be AsyncMock because it is awaited
    mock_youtube_instance.reply_to_comment = AsyncMock(return_value={"id": "reply_123"})
    
    # Mock comment existence
    mock_firestore.get_comment.return_value = Comment(
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

    response = client.post("/api/comments/c1/reply", json={"text": "Thanks!", "comment_id": "c1"})
    
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["reply_id"] == "reply_123"
    
    mock_firestore.mark_as_replied.assert_called_with("c1")

@patch("youtube_guard.routers.comments.AIService")
def test_suggest_reply(MockAIService, client, mock_firestore):
    # Setup mock
    mock_ai_instance = MockAIService.return_value
    mock_ai_instance.generate_reply_suggestion = AsyncMock(return_value="AI Suggestion")
    
    mock_firestore.get_comment.return_value = Comment(
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

    response = client.post("/api/comments/c1/suggest-reply")
    assert response.status_code == 200
    assert response.json()["suggestion"] == "AI Suggestion"
