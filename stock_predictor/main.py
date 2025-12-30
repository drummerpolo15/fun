"""
Stock Predictor Main Script

Main entry point for the stock prediction system. Fetches stock data,
news, social media posts, trains a predictive model, and generates
buy/sell/hold recommendations.
"""

import argparse
import os
import sys
from datetime import datetime
from stock_price_fetcher import StockPriceFetcher
from news_analyzer import NewsAnalyzer
from social_media_analyzer import SocialMediaAnalyzer
from price_predictor import StockPricePredictor
from improved_predictor import ImprovedStockPredictor
from recommendation_engine import RecommendationEngine
from performance_db import PerformanceDB


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_recommendation(recommendation: dict, fundamental_data: dict = None):
    """Print the final recommendation in a formatted way."""
    print_section("TRADING RECOMMENDATION")
    
    rec = recommendation['recommendation']
    confidence = recommendation['confidence']
    current_price = recommendation['current_price']
    pred_price = recommendation['predicted_price']
    expected_return = recommendation['expected_return_pct']
    risk = recommendation['risk_level']
    
    # Color coding for recommendation (using ANSI codes)
    if rec == "BUY":
        rec_color = "\033[92m"  # Green
    elif rec == "SELL":
        rec_color = "\033[91m"  # Red
    else:
        rec_color = "\033[93m"  # Yellow
    
    reset_color = "\033[0m"
    
    print(f"\n{rec_color}RECOMMENDATION: {rec}{reset_color}")
    print(f"Confidence: {confidence:.1%}")
    print(f"\nCurrent Price: ${current_price:.2f}")
    print(f"Predicted Price: ${pred_price:.2f}")
    print(f"Expected Return: {expected_return:+.2f}%")
    print(f"Risk Level: {risk}")
    
    # Display fundamental metrics if available
    if fundamental_data and fundamental_data.get('pe_ratio', 0) > 0:
        print(f"\nFundamental Metrics:")
        print(f"  P/E Ratio: {fundamental_data.get('pe_ratio', 0):.2f}")
        if fundamental_data.get('peg_ratio', 0) > 0:
            print(f"  PEG Ratio: {fundamental_data.get('peg_ratio', 0):.2f}")
        if fundamental_data.get('dividend_yield', 0) > 0:
            div_yield = fundamental_data.get('dividend_yield', 0)
            # Some sources return as decimal (0.0383), others as percentage (3.83)
            div_yield_pct = div_yield * 100 if div_yield < 1 else div_yield
            print(f"  Dividend Yield: {div_yield_pct:.2f}%")
        if fundamental_data.get('price_to_book', 0) > 0:
            print(f"  Price-to-Book: {fundamental_data.get('price_to_book', 0):.2f}")
        if fundamental_data.get('52_week_high', 0) > 0:
            price_in_range = (current_price - fundamental_data.get('52_week_low', 0)) / (fundamental_data.get('52_week_high', 1) - fundamental_data.get('52_week_low', 1)) * 100
            print(f"  Price Position in 52W Range: {price_in_range:.1f}%")
    
    print(f"\nReasoning: {recommendation['reasoning']}")
    
    # Prediction interval
    if recommendation.get('prediction_interval'):
        interval = recommendation['prediction_interval']
        print(f"\nPrediction Interval (95% confidence):")
        print(f"  Lower: ${interval['lower']:.2f}")
        print(f"  Upper: ${interval['upper']:.2f}")
    
    # Signal breakdown
    print("\nSignal Breakdown:")
    signals = recommendation['signals']
    print(f"  Technical: {signals['technical']['signal']:+.2f} (strength: {signals['technical']['strength']:.2f})")
    print(f"  Sentiment: {signals['sentiment']['signal']:+.2f} (strength: {signals['sentiment']['strength']:.2f})")
    print(f"  Prediction: {signals['prediction']['signal']:+.2f} (strength: {signals['prediction']['strength']:.2f})")
    print(f"  Combined: {signals['combined']:+.2f}")


def main():
    """Main function to run the stock prediction system."""
    parser = argparse.ArgumentParser(
        description='Stock Price Predictor with News and Social Media Analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py AAPL
  python main.py TSLA --days-ahead 5
  python main.py MSFT --no-reddit --no-twitter
  python main.py GOOGL --news-api-key YOUR_KEY
        """
    )
    
    parser.add_argument('symbol', type=str, help='Stock ticker symbol (e.g., AAPL, TSLA)')
    parser.add_argument('--days-ahead', type=int, default=1, 
                       help='Number of days ahead to predict (default: 1)')
    parser.add_argument('--period', type=str, default='1y',
                       help='Historical data period (default: 1y)')
    parser.add_argument('--news-api-key', type=str, default=None,
                       help='NewsAPI key (get from newsapi.org)')
    parser.add_argument('--no-reddit', action='store_true',
                       help='Skip Reddit analysis')
    parser.add_argument('--no-twitter', action='store_true',
                       help='Skip Twitter analysis')
    parser.add_argument('--model-type', type=str, default='ensemble',
                       choices=['rf', 'gb', 'ensemble'],
                       help='ML model type (default: ensemble)')
    parser.add_argument('--use-improved', action='store_true',
                       help='Use improved model with better feature engineering')
    parser.add_argument('--save-to-db', action='store_true',
                       help='Save predictions to database')
    
    args = parser.parse_args()
    
    symbol = args.symbol.upper()
    
    print_section(f"STOCK PREDICTOR - {symbol}")
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Prediction Horizon: {args.days_ahead} day(s) ahead")
    
    try:
        # Step 1: Fetch stock price data
        print_section("Fetching Stock Price Data")
        print(f"Fetching historical data for {symbol}...")
        price_fetcher = StockPriceFetcher(symbol, period=args.period)
        price_data = price_fetcher.get_processed_data()
        current_price = price_fetcher.get_current_price()
        
        print(f"✓ Fetched {len(price_data)} days of historical data")
        print(f"✓ Current price: ${current_price:.2f}")
        print(f"✓ Calculated technical indicators")
        
        # Step 1.5: Fetch fundamental data
        print_section("Fundamental Analysis")
        print(f"Fetching fundamental metrics for {symbol}...")
        fundamental_data = price_fetcher.get_fundamental_data()
        
        if fundamental_data.get('pe_ratio', 0) > 0:
            print(f"✓ Fundamental data retrieved")
            print(f"  P/E Ratio: {fundamental_data.get('pe_ratio', 0):.2f}")
            if fundamental_data.get('dividend_yield', 0) > 0:
                div_yield = fundamental_data.get('dividend_yield', 0)
                div_yield_pct = div_yield * 100 if div_yield < 1 else div_yield
                print(f"  Dividend Yield: {div_yield_pct:.2f}%")
            if fundamental_data.get('price_to_book', 0) > 0:
                print(f"  Price-to-Book: {fundamental_data.get('price_to_book', 0):.2f}")
            if fundamental_data.get('52_week_high', 0) > 0:
                print(f"  52-Week Range: ${fundamental_data.get('52_week_low', 0):.2f} - ${fundamental_data.get('52_week_high', 0):.2f}")
        else:
            print("⚠ Limited fundamental data available")
        
        # Step 2: Fetch and analyze news
        print_section("Analyzing News Sentiment")
        news_sentiment = None
        news_analyzer = None
        
        # Try to get API key from environment or argument
        news_api_key = args.news_api_key or os.getenv('NEWS_API_KEY')
        
        # Always try to fetch news (Yahoo Finance is free, no API key needed)
        try:
            news_analyzer = NewsAnalyzer(api_key=news_api_key)
            print(f"Fetching news for {symbol}...")
            news_df = news_analyzer.get_news_sentiment(symbol, days_back=7)
            news_sentiment = news_analyzer.get_aggregate_sentiment(symbol, days_back=7)
            
            if news_sentiment['article_count'] > 0:
                print(f"✓ Analyzed {news_sentiment['article_count']} news articles")
                print(f"  Average sentiment: {news_sentiment['average_sentiment']:+.2f}")
                print(f"  Positive ratio: {news_sentiment['positive_ratio']:.1%}")
                print(f"  Negative ratio: {news_sentiment['negative_ratio']:.1%}")
            else:
                print("⚠ No recent news articles found")
        except Exception as e:
            print(f"⚠ Error fetching news: {str(e)}")
            print("  Note: Yahoo Finance news should work without API keys")
        
        # Step 3: Fetch and analyze social media
        print_section("Analyzing Social Media Sentiment")
        social_sentiment = None
        
        # Try to get credentials from environment
        reddit_client_id = os.getenv('REDDIT_CLIENT_ID')
        reddit_client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        reddit_user_agent = os.getenv('REDDIT_USER_AGENT', 'StockPredictor/1.0')
        twitter_bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        
        if reddit_client_id and reddit_client_secret and not args.no_reddit:
            try:
                social_analyzer = SocialMediaAnalyzer(
                    reddit_client_id=reddit_client_id,
                    reddit_client_secret=reddit_client_secret,
                    reddit_user_agent=reddit_user_agent,
                    twitter_bearer_token=twitter_bearer_token if not args.no_twitter else None
                )
                
                social_df = social_analyzer.get_social_sentiment(
                    symbol,
                    include_reddit=not args.no_reddit,
                    include_twitter=not args.no_twitter and twitter_bearer_token is not None
                )
                social_sentiment = social_analyzer.get_aggregate_sentiment(
                    symbol,
                    include_reddit=not args.no_reddit,
                    include_twitter=not args.no_twitter and twitter_bearer_token is not None
                )
                
                if social_sentiment['post_count'] > 0:
                    print(f"✓ Analyzed {social_sentiment['post_count']} social media posts")
                    print(f"  Average sentiment: {social_sentiment['average_sentiment']:+.2f}")
                    print(f"  Positive ratio: {social_sentiment['positive_ratio']:.1%}")
                else:
                    print("⚠ No recent social media posts found")
            except Exception as e:
                print(f"⚠ Error fetching social media: {str(e)}")
        else:
            print("⚠ Social media credentials not provided. Skipping social media analysis.")
            print("  Set REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, and optionally TWITTER_BEARER_TOKEN")
        
        # Step 4: Train prediction model
        print_section("Training Prediction Model")
        model_name = "improved" if args.use_improved else "standard"
        print(f"Training {model_name} {args.model_type} model...")
        
        if args.use_improved:
            predictor = ImprovedStockPredictor(model_type=args.model_type, use_feature_selection=True)
        else:
            predictor = StockPricePredictor(model_type=args.model_type)
        metrics = predictor.train(
            price_data,
            news_sentiment=news_sentiment,
            social_sentiment=social_sentiment,
            fundamental_data=fundamental_data,
            days_ahead=args.days_ahead
        )
        
        print("✓ Model training completed")
        if 'rf_mae' in metrics:
            print(f"  Random Forest MAE: ${metrics['rf_mae']:.2f}")
            print(f"  Random Forest R²: {metrics['rf_r2']:.3f}")
        if 'gb_mae' in metrics:
            print(f"  Gradient Boosting MAE: ${metrics['gb_mae']:.2f}")
            print(f"  Gradient Boosting R²: {metrics['gb_r2']:.3f}")
        
        # Step 5: Make prediction
        print_section("Making Price Prediction")
        prediction = predictor.predict(
            price_data,
            news_sentiment=news_sentiment,
            social_sentiment=social_sentiment,
            fundamental_data=fundamental_data,
            days_ahead=args.days_ahead
        )
        
        print(f"✓ Prediction completed")
        if 'ensemble_prediction' in prediction:
            print(f"  Ensemble prediction: ${prediction['ensemble_prediction']:.2f}")
        elif 'rf_prediction' in prediction:
            print(f"  Random Forest prediction: ${prediction['rf_prediction']:.2f}")
        elif 'gb_prediction' in prediction:
            print(f"  Gradient Boosting prediction: ${prediction['gb_prediction']:.2f}")
        
        # Step 6: Generate recommendation
        print_section("Generating Recommendation")
        recommendation_engine = RecommendationEngine()
        recommendation = recommendation_engine.generate_recommendation(
            current_price=current_price,
            prediction=prediction,
            price_data=price_data,
            news_sentiment=news_sentiment,
            social_sentiment=social_sentiment
        )
        
        # Print final recommendation
        print_recommendation(recommendation, fundamental_data)
        
        # Save to database if using improved model or if explicitly requested
        if args.use_improved or args.save_to_db:
            try:
                db = PerformanceDB()
                today = datetime.now().strftime('%Y-%m-%d')
                db.save_prediction(
                    symbol=symbol,
                    prediction_date=today,
                    current_price=current_price,
                    predicted_price=recommendation['predicted_price'],
                    predicted_return_pct=recommendation['expected_return_pct'],
                    confidence=recommendation['confidence'],
                    model_type=model_name
                )
                print(f"\n✓ Prediction saved to database")
            except Exception as e:
                print(f"\n⚠ Could not save to database: {str(e)}")
        
        # Feature importance (optional, for debugging)
        if '--debug' in sys.argv:
            print_section("Feature Importance")
            if hasattr(predictor, 'get_feature_importance'):
                importance_df = predictor.get_feature_importance()
                print(importance_df.head(10).to_string())
        
        print("\n" + "=" * 70)
        print("Analysis Complete!")
        print("=" * 70 + "\n")
        
        return recommendation
        
    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

