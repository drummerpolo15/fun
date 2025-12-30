"""
Backtest the prediction model to see what it would have predicted for today
if run yesterday, and compare to actual price.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from stock_price_fetcher import StockPriceFetcher
from price_predictor import StockPricePredictor
from recommendation_engine import RecommendationEngine
from news_analyzer import NewsAnalyzer
import pandas as pd
from datetime import datetime, timedelta


def backtest_prediction(symbol: str, period: str = "max"):
    """
    Backtest: Train on data up to yesterday, predict today, compare to actual.
    
    Args:
        symbol: Stock ticker symbol
        period: Historical data period
    """
    print(f"\n{'='*70}")
    print(f"  BACKTESTING PREDICTION MODEL FOR {symbol}")
    print(f"{'='*70}\n")
    
    # Fetch all historical data
    print("Step 1: Fetching historical data...")
    price_fetcher = StockPriceFetcher(symbol, period=period)
    all_data = price_fetcher.get_processed_data()
    
    if len(all_data) < 2:
        print("Error: Not enough data for backtesting")
        return
    
    print(f"✓ Fetched {len(all_data)} days of historical data")
    
    # Get the last two trading days
    # The last row is "today", second-to-last is "yesterday"
    today_data = all_data.iloc[-1:]
    yesterday_data = all_data.iloc[-2:-1]
    
    # Get actual prices
    actual_today_price = float(today_data['Close'].iloc[0])
    actual_yesterday_price = float(yesterday_data['Close'].iloc[0])
    
    print(f"\nActual Prices:")
    print(f"  Yesterday's close: ${actual_yesterday_price:.2f}")
    print(f"  Today's close: ${actual_today_price:.2f}")
    print(f"  Actual change: {((actual_today_price - actual_yesterday_price) / actual_yesterday_price * 100):+.2f}%")
    
    # Fetch news sentiment (using current news as proxy for yesterday's news)
    print(f"\nStep 2: Fetching news sentiment...")
    news_sentiment = None
    try:
        news_analyzer = NewsAnalyzer()  # Uses free Yahoo Finance news
        news_sentiment = news_analyzer.get_aggregate_sentiment(symbol, days_back=7)
        if news_sentiment['article_count'] > 0:
            print(f"✓ Fetched {news_sentiment['article_count']} news articles")
            print(f"  Average sentiment: {news_sentiment['average_sentiment']:+.2f}")
        else:
            print("⚠ No news articles found")
    except Exception as e:
        print(f"⚠ Error fetching news: {str(e)}")
    
    # Train on data up to yesterday (exclude the last row)
    print(f"\nStep 3: Training model on data up to yesterday...")
    training_data = all_data.iloc[:-1].copy()  # All data except last row
    
    print(f"  Training on {len(training_data)} days of data")
    
    predictor = StockPricePredictor(model_type='ensemble')
    try:
        metrics = predictor.train(
            training_data,
            news_sentiment=news_sentiment,
            days_ahead=1,
            test_size=0.2
        )
        print(f"✓ Model trained")
        print(f"  Random Forest MAE: ${metrics.get('rf_mae', 0):.2f}")
        print(f"  Random Forest R²: {metrics.get('rf_r2', 0):.3f}")
    except Exception as e:
        print(f"⚠ Training error: {str(e)}")
        return
    
    # Make prediction for "today" using data up to yesterday
    print(f"\nStep 4: Making prediction for today (as if run yesterday)...")
    
    # Use data up to yesterday to predict today
    prediction_data = training_data.copy()
    
    try:
        prediction = predictor.predict(
            prediction_data,
            news_sentiment=news_sentiment,
            days_ahead=1
        )
        
        predicted_price = prediction.get('prediction', actual_yesterday_price)
        
        print(f"✓ Prediction completed")
        print(f"\n{'='*70}")
        print(f"  PREDICTION RESULTS")
        print(f"{'='*70}\n")
        
        print(f"Predicted Price (for today): ${predicted_price:.2f}")
        print(f"Actual Price (today):        ${actual_today_price:.2f}")
        print(f"Prediction Error:            ${abs(predicted_price - actual_today_price):.2f}")
        print(f"Prediction Error %:          {abs(predicted_price - actual_today_price) / actual_today_price * 100:.2f}%")
        
        # Direction accuracy
        predicted_direction = "UP" if predicted_price > actual_yesterday_price else "DOWN"
        actual_direction = "UP" if actual_today_price > actual_yesterday_price else "DOWN"
        direction_correct = predicted_direction == actual_direction
        
        print(f"\nDirection Prediction:")
        print(f"  Predicted: {predicted_direction}")
        print(f"  Actual:    {actual_direction}")
        print(f"  Correct:   {'✓ YES' if direction_correct else '✗ NO'}")
        
        # Expected vs actual return
        predicted_return = (predicted_price - actual_yesterday_price) / actual_yesterday_price * 100
        actual_return = (actual_today_price - actual_yesterday_price) / actual_yesterday_price * 100
        
        print(f"\nReturn Prediction:")
        print(f"  Predicted return: {predicted_return:+.2f}%")
        print(f"  Actual return:   {actual_return:+.2f}%")
        print(f"  Error:           {abs(predicted_return - actual_return):.2f} percentage points")
        
        # Prediction interval
        if 'rf_lower' in prediction and 'rf_upper' in prediction:
            print(f"\n95% Prediction Interval:")
            print(f"  Lower: ${prediction['rf_lower']:.2f}")
            print(f"  Upper: ${prediction['rf_upper']:.2f}")
            in_interval = prediction['rf_lower'] <= actual_today_price <= prediction['rf_upper']
            print(f"  Actual price in interval: {'✓ YES' if in_interval else '✗ NO'}")
        
    except Exception as e:
        print(f"⚠ Prediction error: {str(e)}")
        import traceback
        traceback.print_exc()
        return


if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else "SPY"
    period = sys.argv[2] if len(sys.argv) > 2 else "max"
    
    backtest_prediction(symbol, period)

