"""
RRVDXB Backend — app/schemas/recommender_schema.py
Follows the existing *_schema.py convention (chatbot_schema, product_schema...).

Recommender contract (locked — do not change without telling Sibgha + Talha):

GET /api/ai/recommendations?userId=123&limit=5
{
  "personalized":   [{"productId": "P001", "reason": "Based on your browsing history"}],
  "trending":       [{"productId": "P010", "reason": "Trending this week"}],
  "boughtTogether": [{"productId": "P005", "reason": "Often bought with iPhone"}]
}

Owner: Ubaid Ullah Farooqui (UF).
"""

from pydantic import BaseModel, Field


class RecommendedProduct(BaseModel):
    productId: str = Field(..., description="Public product identifier, e.g. P001")
    reason: str = Field(..., description="Human-readable explanation for this suggestion")

    model_config = {
        "json_schema_extra": {
            "example": {"productId": "P001", "reason": "Based on your browsing history"}
        }
    }


class RecommendationResponse(BaseModel):
    personalized: list[RecommendedProduct] = Field(default_factory=list)
    trending: list[RecommendedProduct] = Field(default_factory=list)
    boughtTogether: list[RecommendedProduct] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "example": {
                "personalized": [
                    {"productId": "P001", "reason": "Based on your browsing history"}
                ],
                "trending": [{"productId": "P010", "reason": "Trending this week"}],
                "boughtTogether": [
                    {"productId": "P005", "reason": "Often bought with iPhone"}
                ],
            }
        }
    }


class RecommenderHealth(BaseModel):
    status: str
    source: str
    productsLoaded: int
    ordersLoaded: int
    cacheAgeSeconds: float
