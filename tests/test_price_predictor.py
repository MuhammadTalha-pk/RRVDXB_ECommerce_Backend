from app.ai.price_predictor import price_predictor_service


def test_price_predictor_returns_numeric_prediction():
    product = {
        "id": 11,
        "name": "Apple Watch Series 9",
        "price": 1799.0,
        "currency": "AED",
        "category": "Electronics",
        "brand": "Apple",
        "stock": 9,
        "average_rating": 4.8,
    }

    result = price_predictor_service.predict(product)

    assert result["success"] is True
    assert result["currency"] == "AED"
    assert isinstance(result["predicted_price"], float)
    assert result["predicted_price"] > 0
    assert "summary" in result
