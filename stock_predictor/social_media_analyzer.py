"""
Social Media Data Fetcher and Sentiment Analyzer Module

Fetches recent social media posts (Reddit, Twitter/X) about a stock
and performs sentiment analysis to gauge public sentiment.
"""

import praw
import tweepy
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
from textblob import TextBlob
import os
import time


class SocialMediaAnalyzer:
    """
    Fetches social media posts and analyzes sentiment.
    
    Supports Reddit (via PRAW) and Twitter/X (via Tweepy v2 API).
    Analyzes sentiment of posts to gauge public opinion about stocks.
    """
    
    def __init__(self, 
                 reddit_client_id: Optional[str] = None,
                 reddit_client_secret: Optional[str] = None,
                 reddit_user_agent: Optional[str] = None,
                 twitter_bearer_token: Optional[str] = None):
        """
        Initialize the social media analyzer.
        
        Args:
            reddit_client_id: Reddit API client ID (get from reddit.com/prefs/apps)
            reddit_client_secret: Reddit API client secret
            reddit_user_agent: Reddit API user agent (e.g., 'StockAnalyzer/1.0')
            twitter_bearer_token: Twitter/X API bearer token (requires Twitter Developer account)
        """
        # Initialize Reddit client if credentials provided
        self.reddit_client = None
        if reddit_client_id and reddit_client_secret and reddit_user_agent:
            try:
                self.reddit_client = praw.Reddit(
                    client_id=reddit_client_id,
                    client_secret=reddit_client_secret,
                    user_agent=reddit_user_agent
                )
            except Exception as e:
                print(f"Warning: Could not initialize Reddit client: {str(e)}")
        
        # Initialize Twitter client if bearer token provided
        self.twitter_client = None
        if twitter_bearer_token:
            try:
                self.twitter_client = tweepy.Client(bearer_token=twitter_bearer_token, wait_on_rate_limit=True)
            except Exception as e:
                print(f"Warning: Could not initialize Twitter client: {str(e)}")
    
    def fetch_reddit_posts(self, symbol: str, subreddits: List[str] = None, limit_per_sub: int = 25) -> List[Dict]:
        """
        Fetch Reddit posts about a stock from relevant subreddits.
        
        Args:
            symbol: Stock ticker symbol
            subreddits: List of subreddit names to search (default: ['stocks', 'investing', 'StockMarket', 'wallstreetbets'])
            limit_per_sub: Maximum posts to fetch per subreddit
            
        Returns:
            List of dictionaries containing post information
        """
        if not self.reddit_client:
            print("Reddit client not initialized. Provide credentials to fetch Reddit data.")
            return []
        
        if subreddits is None:
            subreddits = ['stocks', 'investing', 'StockMarket', 'wallstreetbets', 'SecurityAnalysis']
        
        posts = []
        
        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit_client.subreddit(subreddit_name)
                
                # Search for posts containing the symbol
                # Note: Reddit search is limited, so we search recent posts
                search_query = f"{symbol} OR ${symbol}"
                
                for submission in subreddit.search(search_query, sort='relevance', limit=limit_per_sub, time_filter='month'):
                    # Check if post is recent (within last 30 days)
                    post_time = datetime.fromtimestamp(submission.created_utc)
                    if (datetime.now() - post_time).days <= 30:
                        posts.append({
                            'title': submission.title,
                            'text': submission.selftext,
                            'score': submission.score,
                            'num_comments': submission.num_comments,
                            'created_at': post_time,
                            'url': submission.url,
                            'subreddit': subreddit_name,
                            'platform': 'reddit'
                        })
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"Error fetching from r/{subreddit_name}: {str(e)}")
                continue
        
        return posts
    
    def fetch_twitter_posts(self, symbol: str, max_results: int = 100) -> List[Dict]:
        """
        Fetch Twitter/X posts about a stock.
        
        Args:
            symbol: Stock ticker symbol
            max_results: Maximum number of tweets to fetch
            
        Returns:
            List of dictionaries containing tweet information
        """
        if not self.twitter_client:
            print("Twitter client not initialized. Provide bearer token to fetch Twitter data.")
            return []
        
        posts = []
        
        try:
            # Search for tweets containing the symbol
            # Twitter API v2 search syntax
            query = f"${symbol} OR {symbol} -is:retweet lang:en"
            
            # Fetch tweets from the last 7 days
            start_time = (datetime.now() - timedelta(days=7)).isoformat() + 'Z'
            
            tweets = tweepy.Paginator(
                self.twitter_client.search_recent_tweets,
                query=query,
                tweet_fields=['created_at', 'public_metrics', 'text'],
                max_results=min(max_results, 100),  # API limit per request
                start_time=start_time
            ).flatten(limit=max_results)
            
            for tweet in tweets:
                posts.append({
                    'text': tweet.text,
                    'created_at': tweet.created_at,
                    'likes': tweet.public_metrics.get('like_count', 0),
                    'retweets': tweet.public_metrics.get('retweet_count', 0),
                    'replies': tweet.public_metrics.get('reply_count', 0),
                    'platform': 'twitter'
                })
                
        except Exception as e:
            print(f"Error fetching Twitter posts: {str(e)}")
        
        return posts
    
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
            'polarity': blob.sentiment.polarity,
            'subjectivity': blob.sentiment.subjectivity
        }
    
    def get_social_sentiment(self, symbol: str, 
                            include_reddit: bool = True,
                            include_twitter: bool = True,
                            reddit_limit: int = 50,
                            twitter_limit: int = 100) -> pd.DataFrame:
        """
        Fetch social media posts and analyze their sentiment.
        
        Args:
            symbol: Stock ticker symbol
            include_reddit: Whether to fetch Reddit posts
            include_twitter: Whether to fetch Twitter posts
            reddit_limit: Maximum Reddit posts to fetch
            twitter_limit: Maximum Twitter posts to fetch
            
        Returns:
            DataFrame with posts and sentiment scores
        """
        all_posts = []
        
        # Fetch Reddit posts
        if include_reddit:
            reddit_posts = self.fetch_reddit_posts(symbol, limit_per_sub=reddit_limit // 4)
            all_posts.extend(reddit_posts)
        
        # Fetch Twitter posts
        if include_twitter:
            twitter_posts = self.fetch_twitter_posts(symbol, max_results=twitter_limit)
            all_posts.extend(twitter_posts)
        
        if not all_posts:
            print(f"No social media posts found for {symbol}")
            return pd.DataFrame()
        
        # Analyze sentiment for each post
        results = []
        for post in all_posts:
            # Get text content (title + text for Reddit, text for Twitter)
            if post['platform'] == 'reddit':
                text = f"{post.get('title', '')} {post.get('text', '')}"
            else:
                text = post.get('text', '')
            
            sentiment = self.analyze_sentiment(text)
            
            result = {
                'text': text[:200],  # Truncate for display
                'created_at': post.get('created_at'),
                'platform': post.get('platform'),
                'sentiment_polarity': sentiment['polarity'],
                'sentiment_label': 'Positive' if sentiment['polarity'] > 0.1 else 'Negative' if sentiment['polarity'] < -0.1 else 'Neutral'
            }
            
            # Add platform-specific metrics
            if post['platform'] == 'reddit':
                result['score'] = post.get('score', 0)
                result['num_comments'] = post.get('num_comments', 0)
                result['subreddit'] = post.get('subreddit', '')
            elif post['platform'] == 'twitter':
                result['likes'] = post.get('likes', 0)
                result['retweets'] = post.get('retweets', 0)
            
            results.append(result)
        
        df = pd.DataFrame(results)
        
        # Convert created_at to datetime if possible
        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        
        return df
    
    def get_aggregate_sentiment(self, symbol: str,
                               include_reddit: bool = True,
                               include_twitter: bool = True) -> Dict[str, float]:
        """
        Get aggregate sentiment metrics from social media.
        
        Args:
            symbol: Stock ticker symbol
            include_reddit: Whether to include Reddit data
            include_twitter: Whether to include Twitter data
            
        Returns:
            Dictionary with aggregate sentiment metrics
        """
        df = self.get_social_sentiment(symbol, include_reddit, include_twitter)
        
        if df.empty:
            return {
                'average_sentiment': 0.0,
                'positive_ratio': 0.0,
                'negative_ratio': 0.0,
                'post_count': 0,
                'reddit_sentiment': 0.0,
                'twitter_sentiment': 0.0
            }
        
        avg_sentiment = df['sentiment_polarity'].mean()
        positive_count = len(df[df['sentiment_polarity'] > 0.1])
        negative_count = len(df[df['sentiment_polarity'] < -0.1])
        total_count = len(df)
        
        # Platform-specific sentiment
        reddit_sentiment = 0.0
        twitter_sentiment = 0.0
        
        if 'platform' in df.columns:
            reddit_df = df[df['platform'] == 'reddit']
            twitter_df = df[df['platform'] == 'twitter']
            
            if not reddit_df.empty:
                reddit_sentiment = reddit_df['sentiment_polarity'].mean()
            if not twitter_df.empty:
                twitter_sentiment = twitter_df['sentiment_polarity'].mean()
        
        return {
            'average_sentiment': float(avg_sentiment),
            'positive_ratio': float(positive_count / total_count) if total_count > 0 else 0.0,
            'negative_ratio': float(negative_count / total_count) if total_count > 0 else 0.0,
            'post_count': total_count,
            'reddit_sentiment': float(reddit_sentiment),
            'twitter_sentiment': float(twitter_sentiment)
        }

