"""
Example usage script for the Stock Predictor

This script demonstrates how to use the stock predictor programmatically
instead of using the command-line interface.
"""

from stock_price_fetcher import StockPriceFetcher
from news_analyzer import NewsAnalyzer
from social_media_analyzer import SocialMediaAnalyzer
from price_predictor import StockPricePredictor
from recommendation_engine import RecommendationEngine
import os


def example_basic_prediction(symbol: str):
    """Basic example using only price data (no API keys needed)."""
    print(f"\n=== Basic Prediction for {symbol} ===")
    
    # Fetch price data
    price_fetcher = StockPriceFetcher(symbol, period='1y')
    price_data = price_fetcher.get_processed_data()
    current_price = price_fetcher.get_current_price()
    
    print(f"Current price: ${current_price:.2f}")
    print(f"Historical data points: {len(price_data)}")
    
    # Train model
    predictor = StockPricePredictor(model_type='ensemble')
    metrics = predictor.train(price_data, days_ahead=1)
    print(f"Model trained. R² score: {metrics.get('rf_r2', 0):.3f}")
    
    # Make prediction
    prediction = predictor.predict(price_data, days_ahead=1)
    print(f"Predicted price: ${prediction['prediction']:.2f}")
    
    # Generate recommendation
    engine = RecommendationEngine()
    recommendation = engine.generate_recommendation(
        current_price=current_price,
        prediction=prediction,
        price_data=price_data
    )
    
    print(f"Recommendation: {recommendation['recommendation']}")
    print(f"Confidence: {recommendation['confidence']:.1%}")
    print(f"Expected return: {recommendation['expected_return_pct']:+.2f}%")
    
    return recommendation


def example_full_analysis(symbol: str):
    """Full example with news and social media (requires API keys)."""
    print(f"\n=== Full Analysis for {symbol} ===")
    
    # Fetch price data
    price_fetcher = StockPriceFetcher(symbol, period='1y')
    price_data = price_fetcher.get_processed_data()
    current_price = price_fetcher.get_current_price()
    
    # Fetch news (if API key available)
    news_sentiment = None
    news_api_key = os.getenv('NEWS_API_KEY')
    if news_api_key:
        news_analyzer = NewsAnalyzer(api_key=news_api_key)
        news_sentiment = news_analyzer.get_aggregate_sentiment(symbol, days_back=7)
        print(f"News sentiment: {news_sentiment['average_sentiment']:+.2f}")
        print(f"Articles analyzed: {news_sentiment['article_count']}")
    else:
        print("News API key not found. Skipping news analysis.")
    
    # Fetch social media (if credentials available)
    social_sentiment = None
    reddit_client_id = os.getenv('REDDIT_CLIENT_ID')
    reddit_client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    
    if reddit_client_id and reddit_client_secret:
        social_analyzer = SocialMediaAnalyzer(
            reddit_client_id=reddit_client_id,
            reddit_client_secret=reddit_client_secret,
            reddit_user_agent=os.getenv('REDDIT_USER_AGENT', 'StockPredictor/1.0'),
            twitter_bearer_token=os.getenv('TWITTER_BEARER_TOKEN')
        )
        social_sentiment = social_analyzer.get_aggregate_sentiment(symbol)
        print(f"Social sentiment: {social_sentiment['average_sentiment']:+.2f}")
        print(f"Posts analyzed: {social_sentiment['post_count']}")
    else:
        print("Social media credentials not found. Skipping social media analysis.")
    
    # Train model with all data
    predictor = StockPricePredictor(model_type='ensemble')
    metrics = predictor.train(
        price_data,
        news_sentiment=news_sentiment,
        social_sentiment=social_sentiment,
        days_ahead=1
    )
    
    # Make prediction
    prediction = predictor.predict(
        price_data,
        news_sentiment=news_sentiment,
        social_sentiment=social_sentiment,
        days_ahead=1
    )
    
    # Generate recommendation
    engine = RecommendationEngine()
    recommendation = engine.generate_recommendation(
        current_price=current_price,
        prediction=prediction,
        price_data=price_data,
        news_sentiment=news_sentiment,
        social_sentiment=social_sentiment
    )
    
    print(f"\nFinal Recommendation: {recommendation['recommendation']}")
    print(f"Confidence: {recommendation['confidence']:.1%}")
    print(f"Predicted price: ${recommendation['predicted_price']:.2f}")
    print(f"Expected return: {recommendation['expected_return_pct']:+.2f}%")
    print(f"Risk level: {recommendation['risk_level']}")
    
    return recommendation


if __name__ == "__main__":
    # Example 1: Basic prediction (no API keys needed)
    example_basic_prediction("AAPL")
    
    # Example 2: Full analysis (requires API keys)
    # Uncomment and set API keys to use:
    # example_full_analysis("TSLA")

