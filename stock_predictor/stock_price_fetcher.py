"""
Stock Price Data Fetcher Module

Fetches historical stock price data and calculates technical indicators
for use in predictive modeling.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional
import ssl
import certifi
import os

# Fix SSL certificate issues on macOS
# Try system certificates first, then fall back to certifi
system_cert = '/etc/ssl/cert.pem'
cert_path = system_cert if os.path.exists(system_cert) else certifi.where()

if os.path.exists(cert_path):
    os.environ['SSL_CERT_FILE'] = cert_path
    os.environ['REQUESTS_CA_BUNDLE'] = cert_path
    # Also set for curl_cffi specifically
    os.environ['CURL_CA_BUNDLE'] = cert_path


class StockPriceFetcher:
    """
    Fetches and processes historical stock price data.
    
    Uses yfinance library to get historical price data and calculates
    technical indicators that are commonly used in stock prediction models.
    """
    
    def __init__(self, symbol: str, period: str = "1y"):
        """
        Initialize the stock price fetcher.
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
            period: Time period for historical data ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
        """
        self.symbol = symbol.upper()
        self.period = period
        self.ticker = yf.Ticker(self.symbol)
        
    def fetch_historical_data(self) -> pd.DataFrame:
        """
        Fetch historical stock price data.
        
        Returns:
            DataFrame with columns: Date, Open, High, Low, Close, Volume, Dividends, Stock Splits
        """
        try:
            # Fetch historical data
            # Use download method as fallback if history() fails due to SSL issues
            try:
                hist = self.ticker.history(period=self.period)
            except Exception as ssl_error:
                if "SSL" in str(ssl_error) or "certificate" in str(ssl_error).lower():
                    # Fallback: use download method which may handle SSL differently
                    import yfinance as yf
                    hist = yf.download(self.symbol, period=self.period, progress=False)
                    if hist.empty:
                        raise ValueError(f"No data found for symbol {self.symbol}")
                    # Download returns MultiIndex, convert to regular index
                    if isinstance(hist.columns, pd.MultiIndex):
                        hist.columns = hist.columns.droplevel(1)
                else:
                    raise
            
            if hist.empty:
                raise ValueError(f"No data found for symbol {self.symbol}")
            
            # Reset index to make Date a column
            hist.reset_index(inplace=True)
            
            # Rename Date column if it exists
            if 'Date' in hist.columns:
                hist['Date'] = pd.to_datetime(hist['Date'])
            
            return hist
            
        except Exception as e:
            raise Exception(f"Error fetching historical data for {self.symbol}: {str(e)}")
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators from price data.
        
        Technical indicators help identify trends and potential price movements:
        - Moving averages (SMA, EMA) smooth out price fluctuations
        - RSI identifies overbought/oversold conditions
        - MACD identifies momentum changes
        - Bollinger Bands identify volatility
        
        Args:
            df: DataFrame with price data (must have 'Close', 'High', 'Low', 'Volume' columns)
            
        Returns:
            DataFrame with additional technical indicator columns
        """
        df = df.copy()
        
        # Simple Moving Averages (SMA)
        # 20-day and 50-day SMAs are commonly used to identify trends
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        
        # Exponential Moving Averages (EMA)
        # EMAs give more weight to recent prices
        df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
        
        # Relative Strength Index (RSI)
        # RSI ranges from 0-100; >70 is overbought, <30 is oversold
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD (Moving Average Convergence Divergence)
        # MACD line and signal line help identify momentum changes
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_histogram'] = df['MACD'] - df['MACD_signal']
        
        # Bollinger Bands
        # Upper and lower bands indicate volatility; price near bands suggests potential reversal
        df['BB_middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
        df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
        df['BB_width'] = df['BB_upper'] - df['BB_lower']
        
        # Volume indicators
        # Volume moving average helps identify unusual trading activity
        df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
        df['Volume_ratio'] = df['Volume'] / df['Volume_MA']
        
        # Price change indicators
        # Daily returns and volatility help understand price movement patterns
        df['Daily_return'] = df['Close'].pct_change()
        df['Volatility'] = df['Daily_return'].rolling(window=20).std()
        
        # Fill NaN values created by rolling calculations
        df = df.bfill().fillna(0)
        
        return df
    
    def get_fundamental_data(self) -> Dict[str, Optional[float]]:
        """
        Get fundamental analysis metrics for the stock.
        
        Returns:
            Dictionary with fundamental metrics including:
            - P/E ratio (trailingPE)
            - Dividend yield
            - Market cap
            - 52-week high/low
            - Price-to-book ratio
            - And other valuation metrics
        """
        try:
            info = self.ticker.info
            
            fundamental_data = {
                # Valuation metrics
                'pe_ratio': info.get('trailingPE') or info.get('forwardPE'),
                'peg_ratio': info.get('pegRatio'),
                'price_to_book': info.get('priceToBook'),
                'price_to_sales': info.get('priceToSalesTrailing12Months'),
                'enterprise_to_revenue': info.get('enterpriseToRevenue'),
                'enterprise_to_ebitda': info.get('enterpriseToEbitda'),
                
                # Dividend metrics
                'dividend_yield': info.get('dividendYield') or info.get('yield'),
                'dividend_rate': info.get('dividendRate'),
                'payout_ratio': info.get('payoutRatio'),
                
                # Financial health
                'debt_to_equity': info.get('debtToEquity'),
                'current_ratio': info.get('currentRatio'),
                'quick_ratio': info.get('quickRatio'),
                'profit_margins': info.get('profitMargins'),
                'operating_margins': info.get('operatingMargins'),
                
                # Growth metrics
                'revenue_growth': info.get('revenueGrowth'),
                'earnings_growth': info.get('earningsGrowth'),
                'earnings_quarterly_growth': info.get('earningsQuarterlyGrowth'),
                
                # Market metrics
                'market_cap': info.get('marketCap'),
                'enterprise_value': info.get('enterpriseValue'),
                'shares_outstanding': info.get('sharesOutstanding'),
                'float_shares': info.get('floatShares'),
                
                # Price metrics
                '52_week_high': info.get('fiftyTwoWeekHigh'),
                '52_week_low': info.get('fiftyTwoWeekLow'),
                '50_day_avg': info.get('fiftyDayAverage'),
                '200_day_avg': info.get('twoHundredDayAverage'),
                
                # Volume metrics
                'avg_volume': info.get('averageVolume'),
                'avg_volume_10day': info.get('averageVolume10days'),
            }
            
            # Convert None values to 0 for numeric operations
            for key, value in fundamental_data.items():
                if value is None:
                    fundamental_data[key] = 0.0
                else:
                    try:
                        fundamental_data[key] = float(value)
                    except (ValueError, TypeError):
                        fundamental_data[key] = 0.0
            
            return fundamental_data
            
        except Exception as e:
            print(f"Warning: Could not fetch fundamental data: {str(e)}")
            # Return empty dict with zeros
            return {key: 0.0 for key in [
                'pe_ratio', 'peg_ratio', 'price_to_book', 'price_to_sales',
                'dividend_yield', 'debt_to_equity', 'current_ratio',
                'revenue_growth', 'earnings_growth', 'market_cap',
                '52_week_high', '52_week_low', '50_day_avg', '200_day_avg'
            ]}
    
    def get_current_price(self) -> float:
        """
        Get the current/latest stock price.
        
        Returns:
            Current stock price
        """
        try:
            info = self.ticker.info
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            if current_price:
                return float(current_price)
            
            # Fallback: get from recent history
            hist = self.ticker.history(period="1d")
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
            
            raise ValueError(f"Could not retrieve current price for {self.symbol}")
            
        except Exception as e:
            raise Exception(f"Error fetching current price for {self.symbol}: {str(e)}")
    
    def get_processed_data(self) -> pd.DataFrame:
        """
        Get fully processed stock data with technical indicators.
        
        Returns:
            DataFrame with historical prices and technical indicators
        """
        hist_data = self.fetch_historical_data()
        processed_data = self.calculate_technical_indicators(hist_data)
        return processed_data

