"""
S&P 500 Stock Analyzer

Analyzes all S&P 500 stocks and ranks them by predicted return and confidence.
Uses the improved model for best accuracy.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from stock_price_fetcher import StockPriceFetcher
from improved_predictor import ImprovedStockPredictor
from news_analyzer import NewsAnalyzer
from recommendation_engine import RecommendationEngine
from performance_db import PerformanceDB
import pandas as pd
import numpy as np
from datetime import datetime
import time
from typing import List, Dict, Optional
import warnings
warnings.filterwarnings('ignore')


def get_sp500_tickers() -> List[str]:
    """
    Get list of S&P 500 ticker symbols.
    
    Returns:
        List of ticker symbols
    """
    # S&P 500 tickers - you can also fetch this from a web source
    # For now, using a comprehensive list
    # In production, you might want to fetch this dynamically from:
    # - Wikipedia: https://en.wikipedia.org/wiki/List_of_S%26P_500_companies
    # - Or use a library like yfinance to get the list
    
    # Common S&P 500 tickers (sample - you may want to fetch full list)
    sp500_tickers = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK.B',
        'V', 'UNH', 'JNJ', 'WMT', 'JPM', 'MA', 'PG', 'XOM', 'HD', 'CVX',
        'LLY', 'AVGO', 'COST', 'MRK', 'ABBV', 'PEP', 'ADBE', 'TMO', 'CSCO',
        'ACN', 'NFLX', 'MCD', 'DHR', 'VZ', 'ABT', 'WFC', 'LIN', 'NKE',
        'PM', 'TXN', 'CMCSA', 'NEE', 'RTX', 'DIS', 'HON', 'AMGN', 'COP',
        'AMAT', 'BMY', 'INTU', 'GE', 'LOW', 'BKNG', 'PLD', 'SPGI', 'DE',
        'ADP', 'SBUX', 'GS', 'AXP', 'ELV', 'C', 'BLK', 'MDT', 'TJX',
        'MO', 'ZTS', 'EQIX', 'REGN', 'CI', 'ICE', 'SHW', 'WM', 'PSA',
        'KLAC', 'APH', 'CDNS', 'SNPS', 'FTNT', 'CTSH', 'APH', 'ANET',
        'CDW', 'MCHP', 'MPWR', 'ON', 'SWKS', 'QRVO', 'OLED', 'OLED',
        # Add more tickers - this is a sample
        # For full list, consider fetching from Wikipedia or a data provider
    ]
    
    # Try to fetch from Wikipedia if available
    try:
        import requests
        from bs4 import BeautifulSoup
        
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', {'id': 'constituents'})
            if table:
                tickers = []
                for row in table.find_all('tr')[1:]:  # Skip header
                    cells = row.find_all('td')
                    if cells:
                        ticker = cells[0].text.strip()
                        # Handle special cases like BRK.B -> BRK-B
                        ticker = ticker.replace('.', '-')
                        tickers.append(ticker)
                if len(tickers) > 100:  # Valid list
                    return tickers[:500]  # Limit to 500
    except Exception as e:
        print(f"Could not fetch from Wikipedia: {str(e)}")
        print("Using sample list...")
    
    # Return sample list if fetch fails
    return sp500_tickers[:500]


def analyze_stock(symbol: str, period: str = "5y", 
                 timeout: int = 60) -> Optional[Dict]:
    """
    Analyze a single stock and return prediction results.
    
    Args:
        symbol: Stock ticker symbol
        period: Historical data period
        timeout: Maximum time to spend on this stock (seconds)
        
    Returns:
        Dictionary with prediction results or None if failed
    """
    try:
        start_time = time.time()
        
        # Fetch price data
        price_fetcher = StockPriceFetcher(symbol, period=period)
        price_data = price_fetcher.get_processed_data()
        
        if len(price_data) < 50:
            return None
        
        current_price = price_fetcher.get_current_price()
        fundamental_data = price_fetcher.get_fundamental_data()
        
        # Fetch news sentiment
        news_analyzer = NewsAnalyzer()
        news_sentiment = news_analyzer.get_aggregate_sentiment(symbol, days_back=7)
        
        # Train and predict
        predictor = ImprovedStockPredictor(model_type='ensemble', use_feature_selection=True)
        predictor.train(
            price_data,
            news_sentiment=news_sentiment,
            fundamental_data=fundamental_data,
            days_ahead=1,
            test_size=0.2
        )
        
        prediction = predictor.predict(
            price_data,
            news_sentiment=news_sentiment,
            fundamental_data=fundamental_data,
            days_ahead=1
        )
        
        # Generate recommendation
        engine = RecommendationEngine()
        recommendation = engine.generate_recommendation(
            current_price=current_price,
            prediction=prediction,
            price_data=price_data,
            news_sentiment=news_sentiment
        )
        
        elapsed = time.time() - start_time
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'predicted_price': recommendation['predicted_price'],
            'predicted_return_pct': recommendation['expected_return_pct'],
            'confidence': recommendation['confidence'],
            'recommendation': recommendation['recommendation'],
            'risk_level': recommendation['risk_level'],
            'pe_ratio': fundamental_data.get('pe_ratio', 0),
            'dividend_yield': fundamental_data.get('dividend_yield', 0),
            'news_sentiment': news_sentiment.get('average_sentiment', 0),
            'analysis_time': elapsed
        }
        
    except Exception as e:
        # Silently skip failed stocks
        return None


def analyze_sp500(limit: int = 500, period: str = "5y", 
                  min_confidence: float = 0.5,
                  save_to_db: bool = True):
    """
    Analyze S&P 500 stocks and rank by predicted return and confidence.
    
    Args:
        limit: Maximum number of stocks to analyze
        period: Historical data period
        min_confidence: Minimum confidence threshold
        save_to_db: Whether to save predictions to database
    """
    print(f"\n{'='*70}")
    print(f"S&P 500 STOCK ANALYSIS")
    print(f"{'='*70}\n")
    print(f"Analyzing up to {limit} stocks...")
    print(f"Period: {period}, Min confidence: {min_confidence:.0%}")
    print(f"This may take a while...\n")
    
    # Get ticker list
    tickers = get_sp500_tickers()
    if len(tickers) > limit:
        tickers = tickers[:limit]
    
    print(f"Found {len(tickers)} stocks to analyze\n")
    
    results = []
    db = PerformanceDB() if save_to_db else None
    
    # Analyze each stock
    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{len(tickers)}] Analyzing {ticker}...", end=' ', flush=True)
        
        result = analyze_stock(ticker, period=period)
        
        if result:
            # Filter by confidence
            if result['confidence'] >= min_confidence:
                results.append(result)
                
                # Save to database
                if db:
                    try:
                        today = datetime.now().strftime('%Y-%m-%d')
                        db.save_prediction(
                            symbol=ticker,
                            prediction_date=today,
                            current_price=result['current_price'],
                            predicted_price=result['predicted_price'],
                            predicted_return_pct=result['predicted_return_pct'],
                            confidence=result['confidence'],
                            model_type='improved'
                        )
                    except:
                        pass
            
            print(f"✓ Return: {result['predicted_return_pct']:+.2f}%, Confidence: {result['confidence']:.1%}")
        else:
            print("✗ Failed or insufficient data")
        
        # Small delay to avoid rate limiting
        time.sleep(0.5)
    
    if not results:
        print("\n⚠ No stocks met the confidence threshold")
        return
    
    # Create DataFrame and rank
    df = pd.DataFrame(results)
    
    # Calculate composite score (weighted by return and confidence)
    df['composite_score'] = (df['predicted_return_pct'] * df['confidence']) / 100
    
    # Sort by composite score (best opportunities)
    df_sorted = df.sort_values('composite_score', ascending=False)
    
    # Display results
    print(f"\n{'='*70}")
    print(f"TOP STOCKS BY PREDICTED RETURN & CONFIDENCE")
    print(f"{'='*70}\n")
    print(f"Found {len(results)} stocks with confidence >= {min_confidence:.0%}\n")
    
    # Top 20
    top_n = min(20, len(df_sorted))
    print(f"Top {top_n} Opportunities:\n")
    print(f"{'Rank':<6} {'Symbol':<8} {'Return %':<12} {'Confidence':<12} {'Price':<12} {'Rec':<6} {'P/E':<8}")
    print("-" * 80)
    
    for idx, row in df_sorted.head(top_n).iterrows():
        rank = df_sorted.index.get_loc(idx) + 1
        pe_str = f"{row['pe_ratio']:.1f}" if row['pe_ratio'] > 0 else "N/A"
        print(f"{rank:<6} {row['symbol']:<8} {row['predicted_return_pct']:>+10.2f}%  "
              f"{row['confidence']:>10.1%}  ${row['current_price']:>9.2f}  "
              f"{row['recommendation']:<6} {pe_str:<8}")
    
    # Save to CSV
    csv_filename = f"sp500_analysis_{datetime.now().strftime('%Y%m%d')}.csv"
    df_sorted.to_csv(csv_filename, index=False)
    print(f"\n✓ Full results saved to: {csv_filename}")
    
    # Summary statistics
    print(f"\n{'='*70}")
    print(f"SUMMARY STATISTICS")
    print(f"{'='*70}\n")
    print(f"Total analyzed: {len(tickers)}")
    print(f"Successful: {len(results)}")
    print(f"Average predicted return: {df['predicted_return_pct'].mean():+.2f}%")
    print(f"Average confidence: {df['confidence'].mean():.1%}")
    print(f"Best opportunity: {df_sorted.iloc[0]['symbol']} "
          f"({df_sorted.iloc[0]['predicted_return_pct']:+.2f}% return, "
          f"{df_sorted.iloc[0]['confidence']:.1%} confidence)")
    
    return df_sorted


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze S&P 500 stocks')
    parser.add_argument('--limit', type=int, default=500,
                       help='Maximum number of stocks to analyze (default: 500)')
    parser.add_argument('--period', type=str, default='5y',
                       help='Historical data period (default: 5y)')
    parser.add_argument('--min-confidence', type=float, default=0.5,
                       help='Minimum confidence threshold (default: 0.5)')
    parser.add_argument('--no-db', action='store_true',
                       help='Do not save to database')
    
    args = parser.parse_args()
    
    analyze_sp500(
        limit=args.limit,
        period=args.period,
        min_confidence=args.min_confidence,
        save_to_db=not args.no_db
    )

