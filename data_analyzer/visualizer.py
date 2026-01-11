#!/usr/bin/env python3
"""
Visualization Generator Module
Creates visualizations based on analysis results.
"""

import logging
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)

# Set style for better-looking plots
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10


class Visualizer:
    """Generates visualizations from analysis results."""
    
    def __init__(self, output_dir: str = "visualizations"):
        """
        Initialize the visualizer.
        
        Args:
            output_dir: Directory to save visualization files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.figure_count = 0
    
    def create_visualization(self, analysis_result: Dict[str, Any], query_params: Dict[str, Any]) -> str:
        """
        Create a visualization based on analysis results.
        
        Args:
            analysis_result: Results from DataAnalyzer
            query_params: Original query parameters from QueryAnalyzer
            
        Returns:
            Path to saved visualization file
        """
        analysis_type = analysis_result.get('analysis_type', 'value')
        chart_type = query_params.get('chart_type', 'bar')
        
        # If there's an error, create an error message visualization
        if 'error' in analysis_result:
            return self._create_error_visualization(analysis_result['error'])
        
        # Route to appropriate visualization method
        if analysis_type == 'statistics':
            return self._visualize_statistics(analysis_result, chart_type)
        elif analysis_type == 'aggregation':
            return self._visualize_aggregation(analysis_result, chart_type)
        elif analysis_type == 'distribution':
            return self._visualize_distribution(analysis_result, chart_type)
        elif analysis_type == 'comparison':
            return self._visualize_comparison(analysis_result, chart_type)
        elif analysis_type == 'correlation':
            return self._visualize_correlation(analysis_result, chart_type)
        elif analysis_type == 'trend':
            return self._visualize_trend(analysis_result, chart_type)
        elif analysis_type == 'value':
            return self._visualize_values(analysis_result, chart_type)
        else:
            return self._visualize_default(analysis_result, chart_type)
    
    def _get_filepath(self, chart_type: str) -> str:
        """Generate a filepath for saving the visualization."""
        self.figure_count += 1
        filename = f"chart_{self.figure_count:03d}_{chart_type}.png"
        return str(self.output_dir / filename)
    
    def _create_error_visualization(self, error_message: str) -> str:
        """Create a visualization showing an error message."""
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, f"Error: {error_message}", 
                ha='center', va='center', fontsize=14, 
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        ax.axis('off')
        
        filepath = self._get_filepath('error')
        plt.tight_layout()
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        return filepath
    
    def _visualize_statistics(self, analysis_result: Dict[str, Any], chart_type: str) -> str:
        """Visualize statistical measures."""
        results = analysis_result.get('results', {})
        columns = analysis_result.get('columns_analyzed', [])
        
        if not results:
            return self._create_error_visualization("No statistics to visualize")
        
        # Create bar chart of means or first available statistic
        if 'mean' in results:
            data_to_plot = results['mean']
        elif 'median' in results:
            data_to_plot = results['median']
        elif 'sum' in results:
            data_to_plot = results['sum']
        else:
            # Use first available statistic
            data_to_plot = list(results.values())[0]
        
        fig, ax = plt.subplots(figsize=(12, 6))
        bars = ax.bar(data_to_plot.keys(), data_to_plot.values(), color='steelblue', alpha=0.7)
        ax.set_xlabel('Columns', fontsize=12)
        ax.set_ylabel('Value', fontsize=12)
        ax.set_title('Statistical Summary', fontsize=14, fontweight='bold')
        ax.tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2f}', ha='center', va='bottom', fontsize=9)
        
        filepath = self._get_filepath('statistics')
        plt.tight_layout()
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        return filepath
    
    def _visualize_aggregation(self, analysis_result: Dict[str, Any], chart_type: str) -> str:
        """Visualize aggregated data."""
        data = analysis_result.get('data')
        grouping = analysis_result.get('grouping_column')
        
        if data is None or data.empty:
            return self._create_error_visualization("No data to visualize")
        
        if not isinstance(data, pd.DataFrame):
            data = pd.DataFrame(data)
        
        # Get numeric columns (excluding grouping column)
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        if grouping in numeric_cols:
            numeric_cols.remove(grouping)
        
        if not numeric_cols:
            return self._create_error_visualization("No numeric columns for aggregation visualization")
        
        # Use first numeric column
        y_col = numeric_cols[0]
        x_col = grouping if grouping and grouping in data.columns else data.columns[0]
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        if chart_type == 'bar':
            bars = ax.bar(data[x_col].astype(str), data[y_col], color='steelblue', alpha=0.7)
            ax.tick_params(axis='x', rotation=45)
            # Add value labels
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.2f}', ha='center', va='bottom', fontsize=9)
        elif chart_type == 'line':
            ax.plot(data[x_col].astype(str), data[y_col], marker='o', linewidth=2, markersize=8)
            ax.tick_params(axis='x', rotation=45)
        else:
            bars = ax.bar(data[x_col].astype(str), data[y_col], color='steelblue', alpha=0.7)
            ax.tick_params(axis='x', rotation=45)
        
        ax.set_xlabel(x_col, fontsize=12)
        ax.set_ylabel(y_col, fontsize=12)
        ax.set_title(f'{y_col} by {x_col}', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        filepath = self._get_filepath(chart_type)
        plt.tight_layout()
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        return filepath
    
    def _visualize_distribution(self, analysis_result: Dict[str, Any], chart_type: str) -> str:
        """Visualize distribution of values."""
        data = analysis_result.get('data')
        column = analysis_result.get('column')
        
        if data is None or column is None or column not in data.columns:
            return self._create_error_visualization("No data column for distribution visualization")
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        if chart_type == 'histogram' or chart_type == 'bar':
            ax.hist(data[column].dropna(), bins=30, color='steelblue', alpha=0.7, edgecolor='black')
            ax.set_xlabel(column, fontsize=12)
            ax.set_ylabel('Frequency', fontsize=12)
            ax.set_title(f'Distribution of {column}', fontsize=14, fontweight='bold')
        elif chart_type == 'box':
            ax.boxplot(data[column].dropna(), vert=True)
            ax.set_ylabel(column, fontsize=12)
            ax.set_title(f'Box Plot of {column}', fontsize=14, fontweight='bold')
        else:
            ax.hist(data[column].dropna(), bins=30, color='steelblue', alpha=0.7, edgecolor='black')
            ax.set_xlabel(column, fontsize=12)
            ax.set_ylabel('Frequency', fontsize=12)
            ax.set_title(f'Distribution of {column}', fontsize=14, fontweight='bold')
        
        ax.grid(True, alpha=0.3, axis='y')
        
        filepath = self._get_filepath(chart_type)
        plt.tight_layout()
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        return filepath
    
    def _visualize_comparison(self, analysis_result: Dict[str, Any], chart_type: str) -> str:
        """Visualize comparisons."""
        data = analysis_result.get('data')
        grouping = analysis_result.get('grouping_column')
        comparison_cols = analysis_result.get('comparison_columns', [])
        
        if data is None or data.empty:
            return self._create_error_visualization("No data to visualize")
        
        if not isinstance(data, pd.DataFrame):
            data = pd.DataFrame(data)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        if grouping and grouping in data.columns:
            # Grouped comparison
            numeric_cols = [col for col in data.columns if col != grouping and pd.api.types.is_numeric_dtype(data[col])]
            if not numeric_cols:
                numeric_cols = comparison_cols[:1] if comparison_cols else []
            
            if numeric_cols:
                y_col = numeric_cols[0]
                x_pos = np.arange(len(data))
                bars = ax.bar(x_pos, data[y_col], color='steelblue', alpha=0.7)
                ax.set_xticks(x_pos)
                ax.set_xticklabels(data[grouping].astype(str), rotation=45, ha='right')
                ax.set_ylabel(y_col, fontsize=12)
                ax.set_xlabel(grouping, fontsize=12)
                ax.set_title(f'{y_col} by {grouping}', fontsize=14, fontweight='bold')
        else:
            # Direct column comparison
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()[:2]
            if len(numeric_cols) >= 2:
                x_col, y_col = numeric_cols[0], numeric_cols[1]
                ax.scatter(data[x_col], data[y_col], alpha=0.6, s=50)
                ax.set_xlabel(x_col, fontsize=12)
                ax.set_ylabel(y_col, fontsize=12)
                ax.set_title(f'{y_col} vs {x_col}', fontsize=14, fontweight='bold')
            else:
                return self._create_error_visualization("Need at least 2 numeric columns for comparison")
        
        ax.grid(True, alpha=0.3)
        
        filepath = self._get_filepath(chart_type)
        plt.tight_layout()
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        return filepath
    
    def _visualize_correlation(self, analysis_result: Dict[str, Any], chart_type: str) -> str:
        """Visualize correlation matrix."""
        data = analysis_result.get('data')
        columns = analysis_result.get('columns', [])
        
        if data is None or data.empty:
            return self._create_error_visualization("No correlation data to visualize")
        
        if not isinstance(data, pd.DataFrame):
            data = pd.DataFrame(data)
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Create heatmap
        sns.heatmap(data, annot=True, fmt='.2f', cmap='coolwarm', center=0,
                   square=True, linewidths=1, cbar_kws={"shrink": 0.8}, ax=ax)
        ax.set_title('Correlation Matrix', fontsize=14, fontweight='bold')
        
        filepath = self._get_filepath('heatmap')
        plt.tight_layout()
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        return filepath
    
    def _visualize_trend(self, analysis_result: Dict[str, Any], chart_type: str) -> str:
        """Visualize trends over time."""
        data = analysis_result.get('data')
        date_col = analysis_result.get('date_column')
        value_cols = analysis_result.get('value_columns', [])
        
        if data is None or data.empty:
            return self._create_error_visualization("No trend data to visualize")
        
        if not isinstance(data, pd.DataFrame):
            data = pd.DataFrame(data)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Use first value column
        if not value_cols:
            value_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        
        if not value_cols:
            return self._create_error_visualization("No numeric columns for trend visualization")
        
        y_col = value_cols[0]
        
        # Plot line chart
        if date_col in data.columns:
            if pd.api.types.is_datetime64_any_dtype(data[date_col]):
                ax.plot(data[date_col], data[y_col], marker='o', linewidth=2, markersize=4)
            else:
                ax.plot(data[date_col], data[y_col], marker='o', linewidth=2, markersize=4)
                ax.tick_params(axis='x', rotation=45)
            ax.set_xlabel(date_col, fontsize=12)
        else:
            ax.plot(data.index, data[y_col], marker='o', linewidth=2, markersize=4)
            ax.set_xlabel('Index', fontsize=12)
        
        ax.set_ylabel(y_col, fontsize=12)
        ax.set_title(f'Trend of {y_col}', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        filepath = self._get_filepath('line')
        plt.tight_layout()
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        return filepath
    
    def _visualize_values(self, analysis_result: Dict[str, Any], chart_type: str) -> str:
        """Visualize specific values."""
        data = analysis_result.get('data')
        
        if data is None or data.empty:
            return self._create_error_visualization("No values to visualize")
        
        if not isinstance(data, pd.DataFrame):
            data = pd.DataFrame(data)
        
        # Try to create a simple bar or line chart
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        
        if numeric_cols:
            fig, ax = plt.subplots(figsize=(12, 6))
            y_col = numeric_cols[0]
            x_pos = np.arange(len(data))
            
            bars = ax.bar(x_pos, data[y_col], color='steelblue', alpha=0.7)
            ax.set_xticks(x_pos)
            if len(data) <= 20:
                labels = [str(i) for i in range(len(data))]
                ax.set_xticklabels(labels, rotation=45, ha='right')
            ax.set_ylabel(y_col, fontsize=12)
            ax.set_xlabel('Row Index', fontsize=12)
            ax.set_title(f'Values of {y_col}', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')
            
            filepath = self._get_filepath('bar')
            plt.tight_layout()
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()
            return filepath
        else:
            return self._create_error_visualization("No numeric columns to visualize")
    
    def _visualize_default(self, analysis_result: Dict[str, Any], chart_type: str) -> str:
        """Default visualization method."""
        data = analysis_result.get('data')
        
        if data is None:
            return self._create_error_visualization("No data available for visualization")
        
        # Try to create a simple visualization
        return self._visualize_values(analysis_result, chart_type)

