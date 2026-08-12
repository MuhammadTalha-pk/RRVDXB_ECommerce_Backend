import re

from vaderSentiment.vaderSentiment import (
    SentimentIntensityAnalyzer,
)


class ReviewSentimentAnalyzer:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()

    @staticmethod
    def get_sentiment(
        compound_score: float,
    ) -> str:
        if compound_score >= 0.05:
            return "positive"

        if compound_score <= -0.05:
            return "negative"

        return "neutral"

    @staticmethod
    def get_rating(
        compound_score: float,
    ) -> int:
        if compound_score >= 0.6:
            return 5

        if compound_score >= 0.2:
            return 4

        if compound_score > -0.2:
            return 3

        if compound_score > -0.6:
            return 2

        return 1

    def extract_keywords(
        self,
        review: str,
        limit: int = 5,
    ) -> list[str]:
        words = re.findall(
            r"[A-Za-z']+",
            review.lower(),
        )

        scored_words = []
        used_words = set()

        for word in words:
            if word in used_words:
                continue

            sentiment_value = (
                self.analyzer.lexicon.get(word)
            )

            if sentiment_value is None:
                continue

            scored_words.append(
                (
                    word,
                    abs(float(sentiment_value)),
                )
            )
            used_words.add(word)

        scored_words.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        return [
            word
            for word, _ in scored_words[:limit]
        ]

    def analyze(self, review: str) -> dict:
        cleaned_review = " ".join(
            review.split()
        )

        scores = self.analyzer.polarity_scores(
            cleaned_review
        )

        compound_score = round(
            scores["compound"],
            4,
        )

        sentiment = self.get_sentiment(
            compound_score
        )

        confidence = round(
            max(
                scores["pos"],
                scores["neu"],
                scores["neg"],
            )
            * 100,
            2,
        )

        return {
            "success": True,
            "sentiment": sentiment,
            "score": confidence,
            "compound_score": compound_score,
            "keywords": self.extract_keywords(
                cleaned_review
            ),
            "rating": self.get_rating(
                compound_score
            ),
            "message": (
                f"Review was classified as "
                f"{sentiment}."
            ),
        }


sentiment_analyzer = ReviewSentimentAnalyzer()