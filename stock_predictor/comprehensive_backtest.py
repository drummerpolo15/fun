"""
Comprehensive Backtesting Framework

Tests model performance across multiple stocks and time periods
to identify weaknesses and measure improvements.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from stock_price_fetcher import StockPriceFetcher
from price_predictor import StockPricePredictor
from news_analyzer import NewsAnalyzer
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict
import warnings
warnings.filterwarnings('ignore')


def calculate_metrics(actual: float, predicted: float, actual_return: float, predicted_return: float) -> Dict:
    """Calculate comprehensive performance metrics."""
    price_error = abs(predicted - actual)
    price_error_pct = (price_error / actual) * 100 if actual > 0 else 0
    
    return_error = abs(predicted_return - actual_return)
    direction_correct = np.sign(predicted_return) == np.sign(actual_return)
    
    return {
        'price_error': price_error,
        'price_error_pct': price_error_pct,
        'return_error': return_error,
        'direction_correct': direction_correct,
        'predicted_return': predicted_return,
        'actual_return': actual_return
    }


def backtest_stock(symbol: str, period: str = "5y", test_days: int = 30) -> Dict:
    """
    Backtest a single stock over multiple days.
    
    Args:
        symbol: Stock ticker
        period: Historical data period
        test_days: Number of recent days to test
        
    Returns:
        Dictionary with backtest results
    """
    print(f"\n{'='*70}")
    print(f"Backtesting {symbol}")
    print(f"{'='*70}")
    
    try:
        # Fetch all data
        price_fetcher = StockPriceFetcher(symbol, period=period)
        all_data = price_fetcher.get_processed_data()
        fundamental_data = price_fetcher.get_fundamental_data()
        
        if len(all_data) < test_days + 50:  # Need enough data for training
            print(f"⚠ Insufficient data: {len(all_data)} days")
            return None
        
        # Get news sentiment (current as proxy)
        news_analyzer = NewsAnalyzer()
        news_sentiment = news_analyzer.get_aggregate_sentiment(symbol, days_back=7)
        
        results = []
        
        # Test on last test_days
        for i in range(test_days, 0, -1):
            # Split data: train on everything up to i days ago, predict i days ago
            train_data = all_data.iloc[:-i].copy()
            test_idx = len(all_data) - i
            
            if len(train_data) < 50:
                continue
            
            # Get actual prices
            if test_idx >= len(all_data):
                continue
                
            actual_today = float(all_data.iloc[test_idx]['Close'])
            if test_idx > 0:
                actual_yesterday = float(all_data.iloc[test_idx - 1]['Close'])
                actual_return = ((actual_today - actual_yesterday) / actual_yesterday) * 100
            else:
                actual_return = 0.0
            
            try:
                # Train model
                predictor = StockPricePredictor(model_type='ensemble')
                predictor.train(
                    train_data,
                    news_sentiment=news_sentiment,
                    fundamental_data=fundamental_data,
                    days_ahead=1,
                    test_size=0.2
                )
                
                # Predict
                prediction = predictor.predict(
                    train_data,
                    news_sentiment=news_sentiment,
                    fundamental_data=fundamental_data,
                    days_ahead=1
                )
                
                pred_price = prediction.get('prediction', actual_today)
                pred_return = ((pred_price - actual_yesterday) / actual_yesterday) * 100 if test_idx > 0 else 0
                
                metrics = calculate_metrics(actual_today, pred_price, actual_return, pred_return)
                metrics['date'] = all_data.iloc[test_idx]['Date'] if 'Date' in all_data.columns else None
                results.append(metrics)
                
            except Exception as e:
                print(f"  Error on day {i}: {str(e)}")
                continue
        
        if not results:
            print(f"⚠ No successful predictions")
            return None
        
        # Aggregate results
        df_results = pd.DataFrame(results)
        
        avg_price_error = df_results['price_error_pct'].mean()
        avg_return_error = df_results['return_error'].mean()
        direction_accuracy = df_results['direction_correct'].mean() * 100
        
        print(f"\nResults for {symbol}:")
        print(f"  Test days: {len(results)}")
        print(f"  Average price error: {avg_price_error:.2f}%")
        print(f"  Average return error: {avg_return_error:.2f} percentage points")
        print(f"  Direction accuracy: {direction_accuracy:.1f}%")
        
        return {
            'symbol': symbol,
            'test_days': len(results),
            'avg_price_error_pct': avg_price_error,
            'avg_return_error': avg_return_error,
            'direction_accuracy': direction_accuracy,
            'results': df_results
        }
        
    except Exception as e:
        print(f"⚠ Error backtesting {symbol}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def comprehensive_backtest(symbols: List[str] = None, period: str = "5y", test_days: int = 20):
    """Run backtests on multiple stocks."""
    if symbols is None:
        symbols = ['SPY', 'AAPL', 'MSFT', 'GOOGL', 'TSLA']
    
    print(f"\n{'='*70}")
    print(f"COMPREHENSIVE BACKTEST")
    print(f"{'='*70}")
    print(f"Testing {len(symbols)} stocks")
    print(f"Period: {period}, Test days: {test_days}")
    
    all_results = []
    
    for symbol in symbols:
        result = backtest_stock(symbol, period, test_days)
        if result:
            all_results.append(result)
    
    if not all_results:
        print("\n⚠ No successful backtests")
        return
    
    # Aggregate across all stocks
    print(f"\n{'='*70}")
    print(f"AGGREGATE RESULTS")
    print(f"{'='*70}")
    
    avg_price_error = np.mean([r['avg_price_error_pct'] for r in all_results])
    avg_return_error = np.mean([r['avg_return_error'] for r in all_results])
    avg_direction = np.mean([r['direction_accuracy'] for r in all_results])
    
    print(f"\nAcross {len(all_results)} stocks:")
    print(f"  Average price error: {avg_price_error:.2f}%")
    print(f"  Average return error: {avg_return_error:.2f} percentage points")
    print(f"  Average direction accuracy: {avg_direction:.1f}%")
    
    print(f"\nPer-stock breakdown:")
    for r in all_results:
        print(f"  {r['symbol']:6s}: {r['avg_price_error_pct']:5.2f}% error, {r['direction_accuracy']:5.1f}% direction")
    
    return all_results


if __name__ == "__main__":
    symbols = sys.argv[1:] if len(sys.argv) > 1 else None
    comprehensive_backtest(symbols=symbols, period="5y", test_days=20)

