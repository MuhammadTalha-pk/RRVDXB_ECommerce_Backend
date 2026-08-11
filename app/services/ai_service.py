from typing import Any

from app.ai.sentiment_analyzer import (
    sentiment_analyzer,
)


class AIService:
    def analyze_sentiment(
        self,
        review: str,
    ) -> dict[str, Any]:
        return sentiment_analyzer.analyze(review)

    def get_status(self) -> dict[str, Any]:
        return {
            "success": True,
            "service": "RRVDXB AI Service",
            "status": "operational",
            "modules": {
                "sentimentAnalyzer": "available",
            },
        }


ai_service = AIService()