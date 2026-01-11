#!/usr/bin/env python3
"""
Question Suggester Module
Analyzes database schema and data to suggest interesting questions.
"""

import logging
from typing import Dict, Any, List
from db_connection import DatabaseConnection

logger = logging.getLogger(__name__)


class QuestionSuggester:
    """Analyzes database schema and suggests interesting questions."""
    
    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize the question suggester.
        
        Args:
            db_connection: Database connection object
        """
        self.db_connection = db_connection
        self.schema: Dict[str, Any] = {}
    
    def analyze_database(self) -> Dict[str, Any]:
        """
        Analyze the entire database to understand its structure.
        
        Returns:
            Dictionary containing database analysis results
        """
        logger.info("Analyzing database schema...")
        self.schema = self.db_connection.get_database_schema()
        return self.schema
    
    def suggest_questions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Generate suggested questions based on database analysis.
        
        Args:
            limit: Maximum number of questions to suggest
            
        Returns:
            List of suggested questions with SQL queries
        """
        if not self.schema:
            self.analyze_database()
        
        suggestions = []
        tables = self.schema.get('tables', {})
        
        if not tables:
            return suggestions
        
        # Analyze each table to generate suggestions
        for table_name, table_info in tables.items():
            table_suggestions = self._suggest_for_table(table_name, table_info)
            suggestions.extend(table_suggestions)
            
            if len(suggestions) >= limit:
                break
        
        # Also generate cross-table suggestions if multiple tables exist
        if len(tables) > 1:
            cross_table_suggestions = self._suggest_cross_table_questions(tables, limit - len(suggestions))
            suggestions.extend(cross_table_suggestions)
        
        return suggestions[:limit]
    
    def _suggest_for_table(self, table_name: str, table_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate suggestions for a single table."""
        suggestions = []
        columns = table_info.get('columns', [])
        column_info = table_info.get('column_info', {})
        row_count = table_info.get('row_count', 0)
        
        if row_count == 0:
            return suggestions
        
        # Identify numeric columns
        numeric_cols = []
        categorical_cols = []
        date_cols = []
        
        for col in columns:
            col_type = column_info.get(col, {}).get('type', '').lower()
            
            if any(keyword in col_type for keyword in ['int', 'decimal', 'float', 'double', 'numeric']):
                numeric_cols.append(col)
            elif any(keyword in col_type for keyword in ['date', 'time', 'datetime', 'timestamp']):
                date_cols.append(col)
            else:
                categorical_cols.append(col)
        
        # Suggest statistics questions for numeric columns
        for col in numeric_cols[:3]:  # Limit to first 3 numeric columns
            # Average/Mean
            suggestions.append({
                'question': f"What is the average {col} in {table_name}?",
                'query': f"SELECT AVG(`{col}`) as avg_{col} FROM `{table_name}`",
                'category': 'statistics'
            })
            
            # Min/Max
            suggestions.append({
                'question': f"What are the minimum and maximum values of {col} in {table_name}?",
                'query': f"SELECT MIN(`{col}`) as min_{col}, MAX(`{col}`) as max_{col} FROM `{table_name}`",
                'category': 'statistics'
            })
            
            # Distribution (if row count is reasonable)
            if row_count < 100000:  # Only suggest for smaller tables
                suggestions.append({
                    'question': f"Show the distribution of {col} in {table_name}",
                    'query': f"SELECT `{col}`, COUNT(*) as frequency FROM `{table_name}` GROUP BY `{col}` ORDER BY frequency DESC LIMIT 20",
                    'category': 'distribution'
                })
        
        # Suggest aggregation questions for categorical columns
        for col in categorical_cols[:3]:  # Limit to first 3 categorical columns
            # Count by category
            suggestions.append({
                'question': f"How many records are in each {col} category in {table_name}?",
                'query': f"SELECT `{col}`, COUNT(*) as count FROM `{table_name}` GROUP BY `{col}` ORDER BY count DESC LIMIT 20",
                'category': 'aggregation'
            })
            
            # Top N categories
            if numeric_cols:
                numeric_col = numeric_cols[0]
                suggestions.append({
                    'question': f"What are the top 10 {col} categories by {numeric_col} in {table_name}?",
                    'query': f"SELECT `{col}`, SUM(`{numeric_col}`) as total FROM `{table_name}` GROUP BY `{col}` ORDER BY total DESC LIMIT 10",
                    'category': 'aggregation'
                })
        
        # Suggest trend questions for date columns
        for col in date_cols[:2]:  # Limit to first 2 date columns
            if numeric_cols:
                numeric_col = numeric_cols[0]
                suggestions.append({
                    'question': f"How has {numeric_col} changed over time in {table_name}?",
                    'query': f"SELECT DATE(`{col}`) as date, AVG(`{numeric_col}`) as avg_{numeric_col} FROM `{table_name}` GROUP BY DATE(`{col}`) ORDER BY date",
                    'category': 'trend'
                })
        
        # Suggest correlation questions if multiple numeric columns
        if len(numeric_cols) >= 2:
            col1, col2 = numeric_cols[0], numeric_cols[1]
            suggestions.append({
                'question': f"What is the correlation between {col1} and {col2} in {table_name}?",
                'query': f"SELECT `{col1}`, `{col2}` FROM `{table_name}` WHERE `{col1}` IS NOT NULL AND `{col2}` IS NOT NULL LIMIT 1000",
                'category': 'correlation'
            })
        
        return suggestions
    
    def _suggest_cross_table_questions(self, tables: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Generate suggestions that involve multiple tables."""
        suggestions = []
        table_names = list(tables.keys())
        
        if len(table_names) < 2:
            return suggestions
        
        # Simple join suggestions (basic pattern matching)
        # This is a simplified version - in practice, you'd need foreign key information
        # to generate better join suggestions
        
        # Look for common column names that might indicate relationships
        for i, table1 in enumerate(table_names):
            for table2 in table_names[i+1:]:
                table1_cols = set(tables[table1].get('columns', []))
                table2_cols = set(tables[table2].get('columns', []))
                
                # Find common column names (potential join keys)
                common_cols = table1_cols.intersection(table2_cols)
                
                if common_cols:
                    join_col = list(common_cols)[0]
                    
                    # Suggest a simple join
                    suggestions.append({
                        'question': f"Show data from {table1} and {table2} joined on {join_col}",
                        'query': f"SELECT t1.*, t2.* FROM `{table1}` t1 INNER JOIN `{table2}` t2 ON t1.`{join_col}` = t2.`{join_col}` LIMIT 100",
                        'category': 'join'
                    })
                    
                    if len(suggestions) >= limit:
                        break
            
            if len(suggestions) >= limit:
                break
        
        return suggestions
    
    def get_question_suggestions(self, current_query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get question suggestions, optionally filtered based on current query.
        
        Args:
            current_query: Optional current query to base suggestions on
            
        Returns:
            List of suggested questions
        """
        suggestions = self.suggest_questions(limit=15)
        
        # If there's a current query, we could filter or prioritize suggestions
        # For now, just return all suggestions
        return suggestions

