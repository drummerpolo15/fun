#!/usr/bin/env python3
"""
Query Analyzer Module
Analyzes natural language queries and extracts intent and parameters.
"""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)


class QueryAnalyzer:
    """Analyzes natural language queries to extract intent and parameters."""
    
    # Patterns for different query types
    PATTERNS = {
        'statistics': [
            r'(what|show|give|tell).*(mean|average|median|sum|count|min|max|std|standard deviation|statistics|stats)',
            r'(mean|average|median|sum|count|min|max|std|standard deviation).*(of|for)',
            r'describe|summary|statistics'
        ],
        'distribution': [
            r'(show|plot|visualize|graph|chart).*(distribution|histogram|density)',
            r'(what|how).*(distribution|spread|range)',
            r'histogram|density plot'
        ],
        'comparison': [
            r'(compare|comparison|difference|vs|versus)',
            r'(which|what).*(higher|lower|larger|smaller|better|worse)',
            r'(show|plot).*(by|grouped by|compared)'
        ],
        'correlation': [
            r'(correlation|relationship|correlate|related)',
            r'(how).*(related|correlated|connected)',
            r'scatter.*plot'
        ],
        'trend': [
            r'(trend|over time|time series|over time)',
            r'(how).*(changed|evolved|increased|decreased)',
            r'(show|plot).*(over time|by date|by time)'
        ],
        'aggregation': [
            r'(group|aggregate|summarize|total|count).*(by|per)',
            r'(how many|what number).*(by|per|group)',
            r'(show|list).*(top|bottom|highest|lowest)'
        ],
        'filter': [
            r'(where|when|filter|show only|only show)',
            r'(what|which|show).*(where|when|if).*(is|are|equals|greater|less)',
        ],
        'value': [
            r'(what is|what are|find|get|show).*(value|values)',
            r'(how much|how many|what number)'
        ]
    }
    
    # Keywords for chart types
    CHART_KEYWORDS = {
        'bar': ['bar', 'bars', 'column'],
        'line': ['line', 'trend', 'time', 'series'],
        'scatter': ['scatter', 'correlation', 'relationship'],
        'histogram': ['histogram', 'distribution', 'frequency'],
        'box': ['box', 'boxplot', 'quartile'],
        'pie': ['pie', 'percentage', 'proportion'],
        'heatmap': ['heatmap', 'correlation matrix', 'correlation']
    }
    
    def __init__(self):
        """Initialize the query analyzer."""
        pass
    
    def analyze(self, query: str, available_columns: List[str]) -> Dict[str, Any]:
        """
        Analyze a natural language query and extract intent and parameters.
        
        Args:
            query: Natural language query string
            available_columns: List of available column names in the dataset
            
        Returns:
            Dictionary containing:
                - intent: Type of query (statistics, visualization, etc.)
                - chart_type: Suggested chart type (if applicable)
                - columns: List of relevant columns
                - filters: Dictionary of filters to apply
                - aggregations: Aggregation operations to perform
                - grouping: Column to group by
        """
        query_lower = query.lower()
        
        # Determine intent
        intent = self._detect_intent(query_lower)
        
        # Extract columns
        columns = self._extract_columns(query_lower, available_columns)
        
        # Detect chart type if visualization intent
        chart_type = None
        if intent in ['distribution', 'comparison', 'correlation', 'trend', 'aggregation']:
            chart_type = self._detect_chart_type(query_lower)
        
        # Extract filters
        filters = self._extract_filters(query_lower, available_columns)
        
        # Extract aggregations
        aggregations = self._extract_aggregations(query_lower)
        
        # Extract grouping
        grouping = self._extract_grouping(query_lower, available_columns)
        
        # Extract ordering (top N, bottom N)
        ordering = self._extract_ordering(query_lower)
        
        result = {
            'intent': intent,
            'chart_type': chart_type,
            'columns': columns,
            'filters': filters,
            'aggregations': aggregations,
            'grouping': grouping,
            'ordering': ordering,
            'original_query': query
        }
        
        logger.debug(f"Analyzed query: {result}")
        return result
    
    def _detect_intent(self, query: str) -> str:
        """Detect the primary intent of the query."""
        scores = {}
        
        for intent, patterns in self.PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    score += 1
            if score > 0:
                scores[intent] = score
        
        if not scores:
            # Default to value query if no pattern matches
            return 'value'
        
        # Return intent with highest score
        return max(scores, key=scores.get)
    
    def _extract_columns(self, query: str, available_columns: List[str]) -> List[str]:
        """Extract column names mentioned in the query."""
        found_columns = []
        
        # Check for exact column name matches (case insensitive)
        query_words = re.split(r'[\s,]+', query.lower())
        for col in available_columns:
            col_lower = col.lower()
            # Check if column name appears in query
            if col_lower in query or any(word == col_lower for word in query_words):
                found_columns.append(col)
        
        return found_columns if found_columns else available_columns[:2]  # Default to first 2 columns
    
    def _detect_chart_type(self, query: str) -> str:
        """Detect the appropriate chart type from the query."""
        scores = {}
        
        for chart_type, keywords in self.CHART_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in query)
            if score > 0:
                scores[chart_type] = score
        
        if not scores:
            # Default based on common patterns
            if 'trend' in query or 'time' in query:
                return 'line'
            elif 'compare' in query or 'vs' in query:
                return 'bar'
            else:
                return 'bar'  # Default to bar chart
        
        return max(scores, key=scores.get)
    
    def _extract_filters(self, query: str, available_columns: List[str]) -> Dict[str, Any]:
        """Extract filter conditions from the query."""
        filters = {}
        
        # Simple pattern matching for common filters
        # This is basic - could be enhanced with NLP
        for col in available_columns:
            col_lower = col.lower()
            # Look for patterns like "where column = value" or "column is value"
            pattern = rf'{col_lower}\s*(?:is|equals?|==|=)\s*["\']?([^"\']+)["\']?'
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                filters[col] = {'operator': '==', 'value': match.group(1).strip()}
        
        return filters
    
    def _extract_aggregations(self, query: str) -> List[str]:
        """Extract aggregation operations from the query."""
        aggregations = []
        
        agg_keywords = {
            'mean': ['mean', 'average', 'avg'],
            'median': ['median'],
            'sum': ['sum', 'total'],
            'count': ['count', 'number'],
            'min': ['min', 'minimum', 'smallest', 'lowest'],
            'max': ['max', 'maximum', 'largest', 'highest'],
            'std': ['std', 'standard deviation']
        }
        
        query_lower = query.lower()
        for agg, keywords in agg_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                aggregations.append(agg)
        
        return aggregations if aggregations else ['mean']  # Default to mean
    
    def _extract_grouping(self, query: str, available_columns: List[str]) -> Optional[str]:
        """Extract grouping column from the query."""
        # Look for "by column" or "group by column" patterns
        for col in available_columns:
            col_lower = col.lower()
            pattern = rf'(?:by|group\s+by|per)\s+{col_lower}'
            if re.search(pattern, query, re.IGNORECASE):
                return col
        
        return None
    
    def _extract_ordering(self, query: str) -> Dict[str, Any]:
        """Extract ordering preferences (top N, bottom N)."""
        ordering = {}
        
        # Look for "top N" or "bottom N" patterns
        top_match = re.search(r'top\s+(\d+)', query, re.IGNORECASE)
        if top_match:
            ordering['type'] = 'top'
            ordering['n'] = int(top_match.group(1))
            return ordering
        
        bottom_match = re.search(r'bottom\s+(\d+)', query, re.IGNORECASE)
        if bottom_match:
            ordering['type'] = 'bottom'
            ordering['n'] = int(bottom_match.group(1))
            return ordering
        
        # Look for "highest" or "lowest"
        if 'highest' in query.lower() or 'largest' in query.lower():
            ordering['type'] = 'top'
            ordering['n'] = 10
        elif 'lowest' in query.lower() or 'smallest' in query.lower():
            ordering['type'] = 'bottom'
            ordering['n'] = 10
        
        return ordering

