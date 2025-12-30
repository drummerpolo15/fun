"""
News Data Fetcher and Sentiment Analyzer Module

Fetches recent news articles about a stock and performs sentiment analysis
to gauge market sentiment from news sources.

Uses multiple free sources:
- Yahoo Finance news (via stocknews library - no API key needed)
- NewsAPI (optional, requires API key)
- Alpha Vantage (optional, requires API key)
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
from textblob import TextBlob
import time
import warnings
warnings.filterwarnings('ignore')

# Try to import stocknews for free Yahoo Finance news
try:
    from stocknews import StockNews
    STOCKNEWS_AVAILABLE = True
except ImportError:
    STOCKNEWS_AVAILABLE = False
    print("Note: stocknews library not installed. Install with: pip install stocknews")


class NewsAnalyzer:
    """
    Fetches news articles and analyzes sentiment.
    
    Uses NewsAPI (free tier available) to fetch recent news articles
    and TextBlob for sentiment analysis. Can also use Alpha Vantage
    news endpoint as an alternative.
    """
    
    def __init__(self, api_key: Optional[str] = None, use_alpha_vantage: bool = False):
        """
        Initialize the news analyzer.
        
        Args:
            api_key: NewsAPI key (get free key from newsapi.org)
                     If None, will try to use Alpha Vantage (requires separate key)
            use_alpha_vantage: If True, use Alpha Vantage news endpoint instead
        """
        self.api_key = api_key
        self.use_alpha_vantage = use_alpha_vantage
        self.newsapi_base_url = "https://newsapi.org/v2/everything"
        self.alpha_vantage_base_url = "https://www.alphavantage.co/query"
        
    def fetch_news_newsapi(self, symbol: str, days_back: int = 7, max_articles: int = 100) -> List[Dict]:
        """
        Fetch news articles using NewsAPI.
        
        Args:
            symbol: Stock ticker symbol
            days_back: Number of days to look back for news
            max_articles: Maximum number of articles to fetch
            
        Returns:
            List of dictionaries containing article information
        """
        if not self.api_key:
            raise ValueError("NewsAPI key is required. Get a free key from newsapi.org")
        
        articles = []
        from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        # Search for news about the company
        # NewsAPI searches article content, so we search for the ticker symbol
        params = {
            'q': symbol,
            'from': from_date,
            'sortBy': 'publishedAt',
            'language': 'en',
            'pageSize': min(max_articles, 100),  # NewsAPI max is 100 per request
            'apiKey': self.api_key
        }
        
        try:
            response = requests.get(self.newsapi_base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'ok':
                articles = data.get('articles', [])
                
                # If we need more articles, make additional requests
                total_pages = (max_articles // 100) + 1
                for page in range(2, min(total_pages + 1, 6)):  # NewsAPI free tier limits pages
                    params['page'] = page
                    time.sleep(0.5)  # Rate limiting
                    response = requests.get(self.newsapi_base_url, params=params, timeout=10)
                    if response.status_code == 200:
                        page_data = response.json()
                        if page_data.get('status') == 'ok':
                            articles.extend(page_data.get('articles', []))
                    if len(articles) >= max_articles:
                        break
                
                return articles[:max_articles]
            else:
                print(f"NewsAPI error: {data.get('message', 'Unknown error')}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching news from NewsAPI: {str(e)}")
            return []
    
    def fetch_news_alpha_vantage(self, symbol: str) -> List[Dict]:
        """
        Fetch news articles using Alpha Vantage (requires API key).
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            List of dictionaries containing article information
        """
        # Note: Alpha Vantage news requires a premium API key
        # This is a placeholder for the implementation
        # You would need to set ALPHA_VANTAGE_API_KEY environment variable
        import os
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        
        if not api_key:
            print("Alpha Vantage API key not found. Set ALPHA_VANTAGE_API_KEY environment variable.")
            return []
        
        params = {
            'function': 'NEWS_SENTIMENT',
            'tickers': symbol,
            'apikey': api_key,
            'limit': 50
        }
        
        try:
            response = requests.get(self.alpha_vantage_base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'feed' in data:
                articles = []
                for item in data['feed']:
                    articles.append({
                        'title': item.get('title', ''),
                        'description': item.get('summary', ''),
                        'publishedAt': item.get('time_published', ''),
                        'url': item.get('url', ''),
                        'source': {'name': item.get('source', 'Unknown')},
                        'sentiment_score': item.get('overall_sentiment_score', 0),
                        'sentiment_label': item.get('overall_sentiment_label', 'Neutral')
                    })
                return articles
            return []
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching news from Alpha Vantage: {str(e)}")
            return []
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of a text using TextBlob.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with 'polarity' (-1 to 1) and 'subjectivity' (0 to 1)
        """
        if not text or len(text.strip()) == 0:
            return {'polarity': 0.0, 'subjectivity': 0.0}
        
        blob = TextBlob(text)
        return {
            'polarity': blob.sentiment.polarity,  # -1 (negative) to 1 (positive)
            'subjectivity': blob.sentiment.subjectivity  # 0 (objective) to 1 (subjective)
        }
    
    def fetch_news_yahoo(self, symbol: str, max_articles: int = 50) -> List[Dict]:
        """
        Fetch news articles from Yahoo Finance using stocknews library (free, no API key).
        
        Args:
            symbol: Stock ticker symbol
            max_articles: Maximum number of articles to fetch
            
        Returns:
            List of dictionaries containing article information
        """
        if not STOCKNEWS_AVAILABLE:
            return []
        
        try:
            sn = StockNews(symbol, save_news=False)
            df_news = sn.read_rss()
            
            if df_news.empty:
                return []
            
            articles = []
            for idx, row in df_news.head(max_articles).iterrows():
                articles.append({
                    'title': str(row.get('title', '')),
                    'description': str(row.get('summary', '')) if 'summary' in row else '',
                    'publishedAt': str(row.get('published', '')) if 'published' in row else '',
                    'url': str(row.get('link', '')) if 'link' in row else '',
                    'source': {'name': 'Yahoo Finance'}
                })
            
            return articles
            
        except Exception as e:
            print(f"Error fetching Yahoo Finance news: {str(e)}")
            return []
    
    def get_news_sentiment(self, symbol: str, days_back: int = 7, max_articles: int = 100) -> pd.DataFrame:
        """
        Fetch news articles and analyze their sentiment.
        
        Tries multiple sources in order:
        1. Yahoo Finance (free, no API key)
        2. NewsAPI (requires API key)
        3. Alpha Vantage (requires API key)
        
        Args:
            symbol: Stock ticker symbol
            days_back: Number of days to look back for news
            max_articles: Maximum number of articles to analyze
            
        Returns:
            DataFrame with articles and sentiment scores
        """
        articles = []
        
        # Try Yahoo Finance first (free, no API key needed)
        if STOCKNEWS_AVAILABLE:
            yahoo_articles = self.fetch_news_yahoo(symbol, max_articles=max_articles)
            articles.extend(yahoo_articles)
            print(f"  Fetched {len(yahoo_articles)} articles from Yahoo Finance")
        
        # Try NewsAPI if key is available
        if self.api_key and not self.use_alpha_vantage:
            try:
                newsapi_articles = self.fetch_news_newsapi(symbol, days_back, max_articles)
                articles.extend(newsapi_articles)
                print(f"  Fetched {len(newsapi_articles)} articles from NewsAPI")
            except Exception as e:
                print(f"  NewsAPI error: {str(e)}")
        
        # Try Alpha Vantage if configured
        if self.use_alpha_vantage:
            try:
                av_articles = self.fetch_news_alpha_vantage(symbol)
                articles.extend(av_articles)
                print(f"  Fetched {len(av_articles)} articles from Alpha Vantage")
            except Exception as e:
                print(f"  Alpha Vantage error: {str(e)}")
        
        if not articles:
            print(f"No news articles found for {symbol}")
            return pd.DataFrame()
        
        # Analyze sentiment for each article
        results = []
        for article in articles:
            # Combine title and description for sentiment analysis
            text = f"{article.get('title', '')} {article.get('description', '')}"
            
            # If Alpha Vantage provided sentiment, use it; otherwise calculate
            if 'sentiment_score' in article:
                sentiment_score = float(article.get('sentiment_score', 0))
                # Convert to polarity scale (-1 to 1)
                polarity = sentiment_score / 100.0 if sentiment_score else 0
            else:
                sentiment = self.analyze_sentiment(text)
                polarity = sentiment['polarity']
            
            results.append({
                'title': article.get('title', ''),
                'description': article.get('description', ''),
                'published_at': article.get('publishedAt', ''),
                'url': article.get('url', ''),
                'source': article.get('source', {}).get('name', 'Unknown'),
                'sentiment_polarity': polarity,
                'sentiment_label': article.get('sentiment_label', 
                    'Positive' if polarity > 0.1 else 'Negative' if polarity < -0.1 else 'Neutral')
            })
        
        df = pd.DataFrame(results)
        
        # Convert published_at to datetime if possible
        if 'published_at' in df.columns:
            df['published_at'] = pd.to_datetime(df['published_at'], errors='coerce')
        
        return df
    
    def get_aggregate_sentiment(self, symbol: str, days_back: int = 7) -> Dict[str, float]:
        """
        Get aggregate sentiment metrics from recent news.
        
        Args:
            symbol: Stock ticker symbol
            days_back: Number of days to look back for news
            
        Returns:
            Dictionary with aggregate sentiment metrics
        """
        df = self.get_news_sentiment(symbol, days_back)
        
        if df.empty:
            return {
                'average_sentiment': 0.0,
                'positive_ratio': 0.0,
                'negative_ratio': 0.0,
                'article_count': 0
            }
        
        avg_sentiment = df['sentiment_polarity'].mean()
        positive_count = len(df[df['sentiment_polarity'] > 0.1])
        negative_count = len(df[df['sentiment_polarity'] < -0.1])
        total_count = len(df)
        
        return {
            'average_sentiment': float(avg_sentiment),
            'positive_ratio': float(positive_count / total_count) if total_count > 0 else 0.0,
            'negative_ratio': float(negative_count / total_count) if total_count > 0 else 0.0,
            'article_count': total_count
        }

