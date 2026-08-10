import json
from app.core.config import settings

def analyze_shopping_trends():
    """
    Analyzes shopping trends for RRVDXB.
    """
    mock_data = {
        "trendingCategories": ["Electronics", "Shoes", "Perfumes"],
        "popularBrands": ["Adidas", "Sony", "Chanel"],
        "seasonalTrends": ["Summer fashion", "Tech accessories"],
        "recommendedProducts": ["P001", "P005", "P010"]
    }
    
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "sk-placeholder":
        return mock_data
        
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        prompt = "Analyze the current e-commerce shopping trends in UAE and provide a JSON response with the following keys: trendingCategories (list of strings), popularBrands (list of strings), seasonalTrends (list of strings), recommendedProducts (list of strings, use fake product IDs like P001)."
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"AI Trend Analyzer error: {e}")
        return mock_data
