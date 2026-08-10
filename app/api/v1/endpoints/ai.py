from fastapi import APIRouter
from app.ai.trend_analyzer import analyze_shopping_trends

router = APIRouter()

@router.get("/trends")
def get_shopping_trends():
    """
    AI Trend Analyzer endpoint.
    Assigned to: Muhammad Talha
    """
    return analyze_shopping_trends()
