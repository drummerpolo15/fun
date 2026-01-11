#!/usr/bin/env python3
"""
Data Analyzer Module
Performs analysis operations on datasets based on query intent.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class DataAnalyzer:
    """Performs various analysis operations on datasets."""
    
    def __init__(self, data: pd.DataFrame):
        """
        Initialize the data analyzer with a dataset.
        
        Args:
            data: DataFrame to analyze
        """
        self.data = data.copy()
    
    def analyze(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform analysis based on query parameters.
        
        Args:
            query_params: Dictionary containing query analysis results from QueryAnalyzer
            
        Returns:
            Dictionary containing analysis results and processed data
        """
        intent = query_params.get('intent', 'value')
        
        # Apply filters first
        filtered_data = self._apply_filters(query_params.get('filters', {}))
        
        # Route to appropriate analysis method
        if intent == 'statistics':
            return self._calculate_statistics(filtered_data, query_params)
        elif intent == 'aggregation':
            return self._perform_aggregation(filtered_data, query_params)
        elif intent == 'distribution':
            return self._analyze_distribution(filtered_data, query_params)
        elif intent == 'comparison':
            return self._compare_values(filtered_data, query_params)
        elif intent == 'correlation':
            return self._analyze_correlation(filtered_data, query_params)
        elif intent == 'trend':
            return self._analyze_trend(filtered_data, query_params)
        elif intent == 'value':
            return self._get_values(filtered_data, query_params)
        else:
            return self._calculate_statistics(filtered_data, query_params)
    
    def _apply_filters(self, filters: Dict[str, Any]) -> pd.DataFrame:
        """Apply filters to the dataset."""
        filtered = self.data.copy()
        
        for column, condition in filters.items():
            if column not in filtered.columns:
                logger.warning(f"Column {column} not found for filtering")
                continue
            
            operator = condition.get('operator', '==')
            value = condition.get('value')
            
            try:
                if operator == '==':
                    filtered = filtered[filtered[column] == value]
                elif operator == '!=':
                    filtered = filtered[filtered[column] != value]
                elif operator == '>':
                    filtered = filtered[filtered[column] > float(value)]
                elif operator == '<':
                    filtered = filtered[filtered[column] < float(value)]
                elif operator == '>=':
                    filtered = filtered[filtered[column] >= float(value)]
                elif operator == '<=':
                    filtered = filtered[filtered[column] <= float(value)]
            except Exception as e:
                logger.warning(f"Error applying filter {column} {operator} {value}: {e}")
        
        return filtered
    
    def _calculate_statistics(self, data: pd.DataFrame, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate statistical measures."""
        columns = query_params.get('columns', [])
        aggregations = query_params.get('aggregations', ['mean'])
        
        # Use specified columns or all numeric columns
        if columns:
            numeric_cols = [col for col in columns if col in data.columns and pd.api.types.is_numeric_dtype(data[col])]
        else:
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_cols:
            return {
                'error': 'No numeric columns found for statistical analysis',
                'data': data
            }
        
        results = {}
        
        for agg in aggregations:
            if agg == 'mean':
                results['mean'] = data[numeric_cols].mean().to_dict()
            elif agg == 'median':
                results['median'] = data[numeric_cols].median().to_dict()
            elif agg == 'sum':
                results['sum'] = data[numeric_cols].sum().to_dict()
            elif agg == 'count':
                results['count'] = data[numeric_cols].count().to_dict()
            elif agg == 'min':
                results['min'] = data[numeric_cols].min().to_dict()
            elif agg == 'max':
                results['max'] = data[numeric_cols].max().to_dict()
            elif agg == 'std':
                results['std'] = data[numeric_cols].std().to_dict()
        
        # Add full describe output
        results['describe'] = data[numeric_cols].describe().to_dict()
        
        return {
            'analysis_type': 'statistics',
            'results': results,
            'columns_analyzed': numeric_cols,
            'data': data
        }
    
    def _perform_aggregation(self, data: pd.DataFrame, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform grouped aggregations."""
        grouping = query_params.get('grouping')
        columns = query_params.get('columns', [])
        aggregations = query_params.get('aggregations', ['mean'])
        ordering = query_params.get('ordering', {})
        
        if not grouping or grouping not in data.columns:
            # If no grouping, just calculate statistics
            return self._calculate_statistics(data, query_params)
        
        # Use specified columns or all numeric columns
        if columns:
            agg_cols = [col for col in columns if col in data.columns and col != grouping and pd.api.types.is_numeric_dtype(data[col])]
        else:
            agg_cols = [col for col in data.select_dtypes(include=[np.number]).columns if col != grouping]
        
        if not agg_cols:
            agg_cols = [col for col in data.columns if col != grouping]
        
        # Build aggregation dictionary
        agg_dict = {}
        for col in agg_cols:
            agg_dict[col] = aggregations
        
        # Perform grouping
        grouped = data.groupby(grouping).agg(agg_dict)
        
        # Apply ordering
        if ordering:
            order_type = ordering.get('type')
            n = ordering.get('n', 10)
            
            if order_type == 'top':
                # Sort descending and take top N
                if len(agg_cols) > 0:
                    grouped = grouped.sort_values(by=agg_cols[0], ascending=False).head(n)
            elif order_type == 'bottom':
                # Sort ascending and take bottom N
                if len(agg_cols) > 0:
                    grouped = grouped.sort_values(by=agg_cols[0], ascending=True).head(n)
        
        return {
            'analysis_type': 'aggregation',
            'grouping_column': grouping,
            'results': grouped.to_dict(),
            'data': grouped.reset_index()
        }
    
    def _analyze_distribution(self, data: pd.DataFrame, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze distribution of values."""
        columns = query_params.get('columns', [])
        
        # Use specified columns or first numeric column
        if columns:
            numeric_cols = [col for col in columns if col in data.columns and pd.api.types.is_numeric_dtype(data[col])]
        else:
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_cols:
            return {
                'error': 'No numeric columns found for distribution analysis',
                'data': data
            }
        
        # Use first numeric column
        col = numeric_cols[0]
        
        distribution_stats = {
            'mean': float(data[col].mean()),
            'median': float(data[col].median()),
            'std': float(data[col].std()),
            'min': float(data[col].min()),
            'max': float(data[col].max()),
            'q25': float(data[col].quantile(0.25)),
            'q75': float(data[col].quantile(0.75)),
            'skewness': float(data[col].skew()),
            'kurtosis': float(data[col].kurtosis())
        }
        
        return {
            'analysis_type': 'distribution',
            'column': col,
            'statistics': distribution_stats,
            'data': data
        }
    
    def _compare_values(self, data: pd.DataFrame, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Compare values across categories or groups."""
        grouping = query_params.get('grouping')
        columns = query_params.get('columns', [])
        
        if grouping and grouping in data.columns:
            # Grouped comparison
            if columns:
                comp_cols = [col for col in columns if col in data.columns and col != grouping]
            else:
                comp_cols = data.select_dtypes(include=[np.number]).columns.tolist()
                if grouping in comp_cols:
                    comp_cols.remove(grouping)
            
            if not comp_cols:
                comp_cols = [col for col in data.columns if col != grouping][:1]
            
            comparison = data.groupby(grouping)[comp_cols].mean()
            
            return {
                'analysis_type': 'comparison',
                'grouping_column': grouping,
                'comparison_columns': comp_cols,
                'results': comparison.to_dict(),
                'data': comparison.reset_index()
            }
        else:
            # Compare specified columns directly
            if not columns:
                columns = data.select_dtypes(include=[np.number]).columns.tolist()[:2]
            
            comparison_cols = [col for col in columns if col in data.columns]
            
            comparison = data[comparison_cols].describe()
            
            return {
                'analysis_type': 'comparison',
                'comparison_columns': comparison_cols,
                'results': comparison.to_dict(),
                'data': data[comparison_cols]
            }
    
    def _analyze_correlation(self, data: pd.DataFrame, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze correlations between columns."""
        columns = query_params.get('columns', [])
        
        # Use specified columns or all numeric columns
        if columns:
            numeric_cols = [col for col in columns if col in data.columns and pd.api.types.is_numeric_dtype(data[col])]
        else:
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) < 2:
            return {
                'error': 'Need at least 2 numeric columns for correlation analysis',
                'data': data
            }
        
        correlation_matrix = data[numeric_cols].corr()
        
        return {
            'analysis_type': 'correlation',
            'columns': numeric_cols,
            'correlation_matrix': correlation_matrix.to_dict(),
            'data': correlation_matrix
        }
    
    def _analyze_trend(self, data: pd.DataFrame, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trends over time."""
        columns = query_params.get('columns', [])
        
        # Try to find date/time column
        date_cols = data.select_dtypes(include=['datetime64']).columns.tolist()
        
        # Also check string columns that might be dates
        for col in data.select_dtypes(include=['object']).columns:
            try:
                pd.to_datetime(data[col].head(10))
                date_cols.append(col)
                break
            except:
                pass
        
        # Use specified columns or first numeric column
        if columns:
            value_cols = [col for col in columns if col in data.columns and pd.api.types.is_numeric_dtype(data[col])]
        else:
            value_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        
        if not value_cols:
            return {
                'error': 'No numeric columns found for trend analysis',
                'data': data
            }
        
        # If no date column, use index
        if date_cols:
            date_col = date_cols[0]
            trend_data = data[[date_col] + value_cols].copy()
            if not pd.api.types.is_datetime64_any_dtype(trend_data[date_col]):
                trend_data[date_col] = pd.to_datetime(trend_data[date_col])
            trend_data = trend_data.sort_values(date_col)
        else:
            trend_data = data[value_cols].copy().reset_index()
            date_col = 'index'
        
        return {
            'analysis_type': 'trend',
            'date_column': date_col,
            'value_columns': value_cols,
            'data': trend_data
        }
    
    def _get_values(self, data: pd.DataFrame, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Get specific values from the dataset."""
        columns = query_params.get('columns', [])
        ordering = query_params.get('ordering', {})
        
        # Use specified columns or all columns
        if columns:
            selected_cols = [col for col in columns if col in data.columns]
        else:
            selected_cols = data.columns.tolist()
        
        result_data = data[selected_cols]
        
        # Apply ordering
        if ordering and selected_cols:
            order_type = ordering.get('type')
            n = ordering.get('n', 10)
            
            # Find first numeric column for ordering
            numeric_col = next((col for col in selected_cols if pd.api.types.is_numeric_dtype(data[col])), None)
            if numeric_col:
                ascending = order_type == 'bottom'
                result_data = result_data.sort_values(by=numeric_col, ascending=ascending).head(n)
        
        return {
            'analysis_type': 'value',
            'columns': selected_cols,
            'data': result_data
        }

