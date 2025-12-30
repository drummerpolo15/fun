"""
Test Improvements

Compares old vs new model to measure improvement.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from stock_price_fetcher import StockPriceFetcher
from price_predictor import StockPricePredictor
from improved_predictor import ImprovedStockPredictor
from news_analyzer import NewsAnalyzer
from performance_db import PerformanceDB
import pandas as pd
import numpy as np
from datetime import datetime


def compare_models(symbol: str, period: str = "5y", test_days: int = 20):
    """Compare old vs improved model."""
    print(f"\n{'='*70}")
    print(f"COMPARING MODELS FOR {symbol}")
    print(f"{'='*70}\n")
    
    # Fetch data
    price_fetcher = StockPriceFetcher(symbol, period=period)
    all_data = price_fetcher.get_processed_data()
    fundamental_data = price_fetcher.get_fundamental_data()
    news_analyzer = NewsAnalyzer()
    news_sentiment = news_analyzer.get_aggregate_sentiment(symbol, days_back=7)
    
    if len(all_data) < test_days + 50:
        print(f"⚠ Insufficient data")
        return None
    
    old_results = []
    new_results = []
    
    # Test on last test_days
    for i in range(test_days, 0, -1):
        train_data = all_data.iloc[:-i].copy()
        test_idx = len(all_data) - i
        
        if test_idx >= len(all_data) or len(train_data) < 50:
            continue
        
        actual_today = float(all_data.iloc[test_idx]['Close'])
        actual_yesterday = float(all_data.iloc[test_idx - 1]['Close'])
        actual_return = ((actual_today - actual_yesterday) / actual_yesterday) * 100
        
        try:
            # Test old model
            old_predictor = StockPricePredictor(model_type='ensemble')
            old_predictor.train(train_data, news_sentiment=news_sentiment,
                               fundamental_data=fundamental_data, days_ahead=1, test_size=0.2)
            old_pred = old_predictor.predict(train_data, news_sentiment=news_sentiment,
                                            fundamental_data=fundamental_data, days_ahead=1)
            old_price = old_pred.get('prediction', actual_today)
            old_return = ((old_price - actual_yesterday) / actual_yesterday) * 100
            
            old_error = abs((old_price - actual_today) / actual_today) * 100
            old_dir = 1 if np.sign(old_return) == np.sign(actual_return) else 0
            
            old_results.append({
                'error_pct': old_error,
                'return_error': abs(old_return - actual_return),
                'direction_correct': old_dir
            })
            
            # Test new model
            new_predictor = ImprovedStockPredictor(model_type='ensemble', use_feature_selection=True)
            new_predictor.train(train_data, news_sentiment=news_sentiment,
                               fundamental_data=fundamental_data, days_ahead=1, test_size=0.2)
            new_pred = new_predictor.predict(train_data, news_sentiment=news_sentiment,
                                          fundamental_data=fundamental_data, days_ahead=1)
            new_price = new_pred.get('prediction', actual_today)
            new_return = new_pred.get('return_pct', 0)
            
            new_error = abs((new_price - actual_today) / actual_today) * 100
            new_dir = 1 if np.sign(new_return) == np.sign(actual_return) else 0
            
            new_results.append({
                'error_pct': new_error,
                'return_error': abs(new_return - actual_return),
                'direction_correct': new_dir
            })
            
        except Exception as e:
            print(f"  Error on day {i}: {str(e)}")
            continue
    
    if not old_results or not new_results:
        print("⚠ No successful predictions")
        return None
    
    # Compare results
    old_df = pd.DataFrame(old_results)
    new_df = pd.DataFrame(new_results)
    
    print(f"Results over {len(old_results)} test days:\n")
    print(f"{'Metric':<25} {'Old Model':<15} {'New Model':<15} {'Improvement':<15}")
    print("-" * 70)
    
    old_avg_error = old_df['error_pct'].mean()
    new_avg_error = new_df['error_pct'].mean()
    error_improvement = ((old_avg_error - new_avg_error) / old_avg_error) * 100
    
    old_dir_acc = old_df['direction_correct'].mean() * 100
    new_dir_acc = new_df['direction_correct'].mean() * 100
    dir_improvement = new_dir_acc - old_dir_acc
    
    old_return_err = old_df['return_error'].mean()
    new_return_err = new_df['return_error'].mean()
    return_improvement = ((old_return_err - new_return_err) / old_return_err) * 100
    
    print(f"{'Avg Price Error %':<25} {old_avg_error:>6.2f}%      {new_avg_error:>6.2f}%      {error_improvement:>6.1f}%")
    print(f"{'Direction Accuracy %':<25} {old_dir_acc:>6.1f}%      {new_dir_acc:>6.1f}%      {dir_improvement:>+6.1f}%")
    print(f"{'Return Error (pp)':<25} {old_return_err:>6.2f}      {new_return_err:>6.2f}      {return_improvement:>6.1f}%")
    
    return {
        'symbol': symbol,
        'old_error': old_avg_error,
        'new_error': new_avg_error,
        'improvement': error_improvement,
        'old_dir': old_dir_acc,
        'new_dir': new_dir_acc,
        'dir_improvement': dir_improvement
    }


if __name__ == "__main__":
    symbols = sys.argv[1:] if len(sys.argv) > 1 else ['SPY', 'AAPL']
    
    all_comparisons = []
    for symbol in symbols:
        result = compare_models(symbol, period="5y", test_days=15)
        if result:
            all_comparisons.append(result)
    
    if all_comparisons:
        print(f"\n{'='*70}")
        print(f"SUMMARY ACROSS {len(all_comparisons)} STOCKS")
        print(f"{'='*70}\n")
        
        avg_improvement = np.mean([c['improvement'] for c in all_comparisons])
        avg_dir_improvement = np.mean([c['dir_improvement'] for c in all_comparisons])
        
        print(f"Average Error Reduction: {avg_improvement:.1f}%")
        print(f"Average Direction Accuracy Improvement: {avg_dir_improvement:+.1f} percentage points")

