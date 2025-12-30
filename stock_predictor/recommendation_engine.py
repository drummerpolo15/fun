"""
Stock Recommendation Engine Module

Combines price predictions, sentiment analysis, and technical indicators
to generate buy/sell/hold recommendations with confidence scores.
"""

from typing import Dict, Tuple
import numpy as np


class RecommendationEngine:
    """
    Generates trading recommendations based on multiple signals.
    
    Combines:
    - Price predictions (expected future price vs current price)
    - News sentiment (positive/negative news coverage)
    - Social media sentiment (public opinion)
    - Technical indicators (RSI, MACD, etc.)
    - Risk metrics (volatility, confidence intervals)
    """
    
    def __init__(self, 
                 price_threshold: float = 0.02,
                 sentiment_weight: float = 0.3,
                 technical_weight: float = 0.2,
                 prediction_weight: float = 0.5):
        """
        Initialize the recommendation engine.
        
        Args:
            price_threshold: Minimum expected price change (%) to trigger buy/sell (default: 2%)
            sentiment_weight: Weight for sentiment signals (0-1)
            technical_weight: Weight for technical indicators (0-1)
            prediction_weight: Weight for price predictions (0-1)
        """
        self.price_threshold = price_threshold
        self.sentiment_weight = sentiment_weight
        self.technical_weight = technical_weight
        self.prediction_weight = prediction_weight
        
        # Normalize weights to sum to 1
        total_weight = sentiment_weight + technical_weight + prediction_weight
        if total_weight > 0:
            self.sentiment_weight /= total_weight
            self.technical_weight /= total_weight
            self.prediction_weight /= total_weight
    
    def analyze_technical_signals(self, price_data) -> Dict[str, float]:
        """
        Analyze technical indicators to generate trading signals.
        
        Technical analysis uses price patterns and indicators to identify
        potential buy/sell opportunities.
        
        Args:
            price_data: DataFrame with technical indicators
            
        Returns:
            Dictionary with technical signal scores
        """
        if price_data.empty:
            return {'signal': 0.0, 'strength': 0.0}
        
        latest = price_data.iloc[-1]
        signals = []
        strengths = []
        
        # RSI signals
        # RSI < 30 suggests oversold (buy signal), RSI > 70 suggests overbought (sell signal)
        if 'RSI' in latest:
            rsi = latest['RSI']
            if rsi < 30:
                signals.append(1.0)  # Buy signal
                strengths.append((30 - rsi) / 30)  # Stronger signal the lower RSI
            elif rsi > 70:
                signals.append(-1.0)  # Sell signal
                strengths.append((rsi - 70) / 30)  # Stronger signal the higher RSI
            else:
                signals.append(0.0)
                strengths.append(0.0)
        
        # MACD signals
        # MACD crossing above signal line suggests bullish momentum
        if 'MACD' in latest and 'MACD_signal' in latest:
            macd = latest['MACD']
            macd_signal = latest['MACD_signal']
            if macd > macd_signal:
                signals.append(1.0)  # Buy signal
                strengths.append(min(abs(macd - macd_signal) / abs(macd_signal) if macd_signal != 0 else 0, 1.0))
            else:
                signals.append(-1.0)  # Sell signal
                strengths.append(min(abs(macd - macd_signal) / abs(macd_signal) if macd_signal != 0 else 0, 1.0))
        
        # Moving average signals
        # Price above moving averages suggests uptrend
        if 'SMA_20' in latest and 'SMA_50' in latest and 'Close' in latest:
            close = latest['Close']
            sma20 = latest['SMA_20']
            sma50 = latest['SMA_50']
            
            if close > sma20 > sma50:
                signals.append(1.0)  # Strong buy signal
                strengths.append(0.8)
            elif close < sma20 < sma50:
                signals.append(-1.0)  # Strong sell signal
                strengths.append(0.8)
            else:
                signals.append(0.0)
                strengths.append(0.0)
        
        # Bollinger Bands signals
        # Price near lower band suggests potential bounce (buy), near upper band suggests potential drop (sell)
        if 'BB_lower' in latest and 'BB_upper' in latest and 'Close' in latest:
            close = latest['Close']
            bb_lower = latest['BB_lower']
            bb_upper = latest['BB_upper']
            bb_middle = latest.get('BB_middle', (bb_upper + bb_lower) / 2)
            
            if close <= bb_lower:
                signals.append(1.0)  # Buy signal (oversold)
                strengths.append(0.6)
            elif close >= bb_upper:
                signals.append(-1.0)  # Sell signal (overbought)
                strengths.append(0.6)
            else:
                signals.append(0.0)
                strengths.append(0.0)
        
        # Calculate weighted average signal
        if signals:
            weighted_signal = np.average(signals, weights=strengths)
            avg_strength = np.mean(strengths)
        else:
            weighted_signal = 0.0
            avg_strength = 0.0
        
        return {
            'signal': float(weighted_signal),  # -1 to 1 (sell to buy)
            'strength': float(avg_strength)  # 0 to 1
        }
    
    def analyze_sentiment_signals(self, news_sentiment: Dict, social_sentiment: Dict) -> Dict[str, float]:
        """
        Analyze sentiment from news and social media.
        
        Args:
            news_sentiment: Dictionary with news sentiment metrics
            social_sentiment: Dictionary with social media sentiment metrics
            
        Returns:
            Dictionary with sentiment signal scores
        """
        signals = []
        weights = []
        
        # News sentiment
        if news_sentiment:
            news_sent = news_sentiment.get('average_sentiment', 0.0)
            news_positive = news_sentiment.get('positive_ratio', 0.0)
            news_negative = news_sentiment.get('negative_ratio', 0.0)
            
            # Convert sentiment to signal (-1 to 1)
            # Positive sentiment = buy signal, negative = sell signal
            news_signal = news_sent  # Already in -1 to 1 range
            news_weight = news_sentiment.get('article_count', 0) / 100.0  # More articles = more weight
            news_weight = min(news_weight, 1.0)  # Cap at 1.0
            
            signals.append(news_signal)
            weights.append(news_weight)
        
        # Social media sentiment
        if social_sentiment:
            social_sent = social_sentiment.get('average_sentiment', 0.0)
            social_positive = social_sentiment.get('positive_ratio', 0.0)
            
            # Convert sentiment to signal
            social_signal = social_sent
            social_weight = social_sentiment.get('post_count', 0) / 200.0  # More posts = more weight
            social_weight = min(social_weight, 1.0)  # Cap at 1.0
            
            signals.append(social_signal)
            weights.append(social_weight)
        
        # Calculate weighted average
        if signals and sum(weights) > 0:
            weighted_signal = np.average(signals, weights=weights)
            avg_weight = np.mean(weights) if weights else 0.0
        else:
            weighted_signal = 0.0
            avg_weight = 0.0
        
        return {
            'signal': float(weighted_signal),  # -1 to 1 (sell to buy)
            'strength': float(avg_weight)  # 0 to 1
        }
    
    def analyze_prediction_signals(self, current_price: float, prediction: Dict) -> Dict[str, float]:
        """
        Analyze price prediction to generate trading signal.
        
        Args:
            current_price: Current stock price
            prediction: Dictionary with price predictions
            
        Returns:
            Dictionary with prediction signal scores
        """
        pred_price = prediction.get('prediction', current_price)
        
        # Calculate expected return
        expected_return = (pred_price - current_price) / current_price
        
        # Calculate confidence based on prediction intervals
        confidence = 1.0
        if 'rf_std' in prediction and pred_price > 0:
            # Lower standard deviation = higher confidence
            cv = prediction['rf_std'] / pred_price  # Coefficient of variation
            confidence = max(0.1, 1.0 - cv)  # Confidence decreases with volatility
        
        # Signal strength based on expected return and confidence
        signal = np.sign(expected_return) * min(abs(expected_return) / self.price_threshold, 1.0)
        signal = signal * confidence  # Scale by confidence
        
        return {
            'signal': float(signal),  # -1 to 1 (sell to buy)
            'strength': float(confidence),  # 0 to 1
            'expected_return': float(expected_return)  # Percentage return
        }
    
    def generate_recommendation(self,
                                current_price: float,
                                prediction: Dict,
                                price_data,
                                news_sentiment: Dict = None,
                                social_sentiment: Dict = None) -> Dict[str, any]:
        """
        Generate final trading recommendation.
        
        Combines all signals (technical, sentiment, prediction) to generate
        a buy/sell/hold recommendation with confidence score and reasoning.
        
        Args:
            current_price: Current stock price
            prediction: Dictionary with price predictions
            price_data: DataFrame with technical indicators
            news_sentiment: Dictionary with news sentiment metrics
            social_sentiment: Dictionary with social media sentiment metrics
            
        Returns:
            Dictionary with recommendation details
        """
        # Analyze each signal type
        technical = self.analyze_technical_signals(price_data)
        sentiment = self.analyze_sentiment_signals(news_sentiment or {}, social_sentiment or {})
        prediction_signal = self.analyze_prediction_signals(current_price, prediction)
        
        # Combine signals with weights
        combined_signal = (
            self.prediction_weight * prediction_signal['signal'] +
            self.sentiment_weight * sentiment['signal'] +
            self.technical_weight * technical['signal']
        )
        
        # Calculate overall confidence
        confidence = (
            self.prediction_weight * prediction_signal['strength'] +
            self.sentiment_weight * sentiment['strength'] +
            self.technical_weight * technical['strength']
        )
        
        # Determine recommendation
        if combined_signal > 0.3:
            recommendation = "BUY"
            reasoning = "Strong positive signals from multiple sources"
        elif combined_signal > 0.1:
            recommendation = "BUY"
            reasoning = "Moderate positive signals"
        elif combined_signal < -0.3:
            recommendation = "SELL"
            reasoning = "Strong negative signals from multiple sources"
        elif combined_signal < -0.1:
            recommendation = "SELL"
            reasoning = "Moderate negative signals"
        else:
            recommendation = "HOLD"
            reasoning = "Mixed or neutral signals"
        
        # Get predicted price
        pred_price = prediction.get('prediction', current_price)
        expected_return_pct = ((pred_price - current_price) / current_price) * 100
        
        # Risk assessment
        risk_level = "LOW"
        if 'rf_std' in prediction:
            volatility = prediction['rf_std'] / current_price if current_price > 0 else 0
            if volatility > 0.05:
                risk_level = "HIGH"
            elif volatility > 0.02:
                risk_level = "MEDIUM"
        
        return {
            'recommendation': recommendation,
            'confidence': float(confidence),
            'predicted_price': float(pred_price),
            'current_price': float(current_price),
            'expected_return_pct': float(expected_return_pct),
            'risk_level': risk_level,
            'reasoning': reasoning,
            'signals': {
                'technical': technical,
                'sentiment': sentiment,
                'prediction': prediction_signal,
                'combined': float(combined_signal)
            },
            'prediction_interval': {
                'lower': prediction.get('rf_lower', pred_price),
                'upper': prediction.get('rf_upper', pred_price)
            } if 'rf_lower' in prediction else None
        }

