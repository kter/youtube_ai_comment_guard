"""Vertex AI Service for comment analysis.

Uses Gemini 1.5 Flash for toxicity detection, classification, and text transformation.
"""

import json
import logging
from typing import Optional

import vertexai
from vertexai.generative_models import GenerativeModel

from youtube_guard.config import settings
from youtube_guard.models import CommentAnalysis, CommentCategory

logger = logging.getLogger(__name__)


class AIService:
    """Service for AI-powered comment analysis using Vertex AI."""

    def __init__(self):
        """Initialize Vertex AI."""
        if settings.google_cloud_project:
            vertexai.init(
                project=settings.google_cloud_project,
                location=settings.gcp_region,
            )
        self._model = GenerativeModel(settings.gemini_model)

    async def analyze_comment(self, text: str) -> CommentAnalysis:
        """Analyze a comment for toxicity and classify it.

        Args:
            text: Comment text to analyze

        Returns:
            CommentAnalysis with toxicity score, category, and mild text
        """
        prompt = f"""あなたはYouTubeコメントの分析AIです。以下のコメントを分析してください。

コメント: "{text}"

以下の項目を分析してJSON形式で回答してください:

1. toxicity_score (0-100の整数):
   - 0-30: 安全（通常のコメント、応援、質問など）
   - 31-50: 軽度（やや批判的だが許容範囲）
   - 51-70: 中度（攻撃的なニュアンスを含む）
   - 71-100: 高度（明らかな暴言・誹謗中傷）

2. category (以下のいずれか):
   - "positive": 応援、褒め言葉、感謝
   - "question": 質問、疑問
   - "constructive": 建設的な批判、改善提案
   - "complaint": ただの不満、愚痴
   - "toxic": 暴言、誹謗中傷、人格攻撃

3. reason: 判定理由（日本語で簡潔に）

4. mild_text: コメントを事務的な報告形式に変換したもの
   - 攻撃的なニュアンスを除去
   - 感情的表現を中立的に
   - 要点のみを抽出
   - 「〜に関する意見」「〜の改善要望」形式で
   - ポジティブなコメントはそのまま残す

JSON形式のみで回答（説明不要）:
{{"toxicity_score": number, "category": string, "reason": string, "mild_text": string}}"""

        try:
            response = self._model.generate_content(prompt)
            response_text = response.text.strip()

            # Parse JSON from response
            # Handle potential markdown code blocks
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            result = json.loads(response_text)

            # Map category string to enum
            category_map = {
                "positive": CommentCategory.POSITIVE,
                "question": CommentCategory.QUESTION,
                "constructive": CommentCategory.CONSTRUCTIVE,
                "complaint": CommentCategory.COMPLAINT,
                "toxic": CommentCategory.TOXIC,
            }

            return CommentAnalysis(
                toxicity_score=min(100, max(0, int(result.get("toxicity_score", 0)))),
                category=category_map.get(result.get("category", ""), CommentCategory.COMPLAINT),
                reason=result.get("reason", ""),
                mild_text=result.get("mild_text", text),
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            # Return safe defaults on parse error
            return CommentAnalysis(
                toxicity_score=50,
                category=CommentCategory.COMPLAINT,
                reason="解析エラー",
                mild_text=text,
            )
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            raise

    async def batch_analyze(self, comments: list[dict]) -> list[CommentAnalysis]:
        """Analyze multiple comments.

        Args:
            comments: List of comment dicts with 'id' and 'text' keys

        Returns:
            List of CommentAnalysis results
        """
        results = []
        for comment in comments:
            try:
                analysis = await self.analyze_comment(comment["text"])
                results.append(analysis)
            except Exception as e:
                logger.error(f"Error analyzing comment {comment.get('id')}: {e}")
                # Add fallback result
                results.append(
                    CommentAnalysis(
                        toxicity_score=50,
                        category=CommentCategory.COMPLAINT,
                        reason="解析エラー",
                        mild_text=comment["text"],
                    )
                )

        return results

    async def generate_reply_suggestion(
        self,
        comment_text: str,
        category: CommentCategory,
    ) -> Optional[str]:
        """Generate a suggested reply for a comment.

        Args:
            comment_text: Original comment
            category: Comment category

        Returns:
            Suggested reply text
        """
        if category == CommentCategory.TOXIC:
            return None  # Don't suggest replies for toxic comments

        prompt = f"""あなたはYouTubeクリエイターのアシスタントです。
以下のコメントに対する返信案を1つだけ作成してください。

コメント: "{comment_text}"
カテゴリ: {category.value}

ルール:
- 丁寧で親しみやすいトーン
- 簡潔に（50文字以内）
- 質問には答える姿勢を示す
- 感謝を表現

返信テキストのみを出力（説明不要）:"""

        try:
            response = self._model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Reply generation error: {e}")
            return None
