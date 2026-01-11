#!/usr/bin/env python3
"""
SQL Query Generator Module
Converts natural language queries into SQL queries.
"""

import logging
import re
from typing import Dict, Any, List, Optional
from query_analyzer import QueryAnalyzer

logger = logging.getLogger(__name__)


class SQLQueryGenerator:
    """Generates SQL queries from natural language queries."""
    
    def __init__(self, schema: Dict[str, Any]):
        """
        Initialize SQL query generator.
        
        Args:
            schema: Database schema information
        """
        self.schema = schema
        self.query_analyzer = QueryAnalyzer()
    
    def generate_query(self, query: str, table_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate SQL query from natural language query.
        
        Args:
            query: Natural language query string
            table_name: Optional table name to query (if None, uses first table)
            
        Returns:
            Dictionary containing SQL query and metadata
        """
        tables = self.schema.get('tables', {})
        
        if not tables:
            raise ValueError("No tables found in schema")
        
        # Determine table to query
        if table_name is None:
            # Try to extract table name from query, otherwise use first table
            table_name = self._extract_table_name(query, list(tables.keys()))
            if table_name is None:
                table_name = list(tables.keys())[0]
        
        if table_name not in tables:
            raise ValueError(f"Table {table_name} not found in schema")
        
        table_info = tables[table_name]
        columns = table_info.get('columns', [])
        
        # Analyze the query
        query_params = self.query_analyzer.analyze(query, columns)
        
        # Generate SQL based on intent
        sql_query = self._build_sql_query(query_params, table_name, table_info)
        
        return {
            'sql': sql_query,
            'table_name': table_name,
            'query_params': query_params
        }
    
    def _extract_table_name(self, query: str, available_tables: List[str]) -> Optional[str]:
        """Try to extract table name from query."""
        query_lower = query.lower()
        
        for table in available_tables:
            table_lower = table.lower()
            if table_lower in query_lower:
                return table
        
        return None
    
    def _build_sql_query(self, query_params: Dict[str, Any], table_name: str, table_info: Dict[str, Any]) -> str:
        """Build SQL query from query parameters."""
        intent = query_params.get('intent', 'value')
        columns = query_params.get('columns', [])
        filters = query_params.get('filters', {})
        aggregations = query_params.get('aggregations', [])
        grouping = query_params.get('grouping')
        ordering = query_params.get('ordering', {})
        
        # Build SELECT clause
        select_clause = self._build_select_clause(intent, columns, aggregations, grouping, table_info)
        
        # Build FROM clause
        from_clause = f"FROM `{table_name}`"
        
        # Build WHERE clause
        where_clause = self._build_where_clause(filters)
        
        # Build GROUP BY clause
        group_by_clause = self._build_group_by_clause(grouping, aggregations)
        
        # Build ORDER BY clause
        order_by_clause = self._build_order_by_clause(ordering, columns, aggregations, table_info)
        
        # Build LIMIT clause
        limit_clause = self._build_limit_clause(ordering, intent)
        
        # Combine all clauses
        sql = f"{select_clause} {from_clause}"
        
        if where_clause:
            sql += f" {where_clause}"
        
        if group_by_clause:
            sql += f" {group_by_clause}"
        
        if order_by_clause:
            sql += f" {order_by_clause}"
        
        if limit_clause:
            sql += f" {limit_clause}"
        
        return sql
    
    def _build_select_clause(self, intent: str, columns: List[str], aggregations: List[str], 
                            grouping: Optional[str], table_info: Dict[str, Any]) -> str:
        """Build SELECT clause."""
        available_columns = table_info.get('columns', [])
        
        if intent == 'statistics':
            # For statistics, use aggregations
            if aggregations:
                agg_funcs = []
                # Use first numeric column if no columns specified
                numeric_cols = [c for c in available_columns if self._is_numeric_column(c, table_info)]
                target_cols = columns if columns else numeric_cols[:1]
                
                for agg in aggregations:
                    for col in target_cols:
                        if col in available_columns:
                            if agg == 'mean':
                                agg_funcs.append(f"AVG(`{col}`) as avg_{col}")
                            elif agg == 'median':
                                agg_funcs.append(f"AVG(`{col}`) as median_{col}")  # MySQL doesn't have MEDIAN, use AVG approximation
                            elif agg == 'sum':
                                agg_funcs.append(f"SUM(`{col}`) as sum_{col}")
                            elif agg == 'count':
                                agg_funcs.append(f"COUNT(*) as count")
                            elif agg == 'min':
                                agg_funcs.append(f"MIN(`{col}`) as min_{col}")
                            elif agg == 'max':
                                agg_funcs.append(f"MAX(`{col}`) as max_{col}")
                            elif agg == 'std':
                                agg_funcs.append(f"STDDEV(`{col}`) as std_{col}")
                
                if agg_funcs:
                    return f"SELECT {', '.join(agg_funcs)}"
            
            # Default to COUNT if no aggregations
            return "SELECT COUNT(*) as count"
        
        elif intent == 'aggregation' and grouping:
            # Grouped aggregation
            numeric_cols = [c for c in columns if c in available_columns and self._is_numeric_column(c, table_info)]
            if not numeric_cols:
                numeric_cols = [c for c in available_columns if self._is_numeric_column(c, table_info)][:1]
            
            agg_funcs = [f"`{grouping}`"]
            for col in numeric_cols:
                for agg in aggregations[:1]:  # Use first aggregation
                    if agg == 'mean':
                        agg_funcs.append(f"AVG(`{col}`) as avg_{col}")
                    elif agg == 'sum':
                        agg_funcs.append(f"SUM(`{col}`) as sum_{col}")
                    elif agg == 'count':
                        agg_funcs.append(f"COUNT(*) as count")
            
            return f"SELECT {', '.join(agg_funcs)}"
        
        else:
            # Select specific columns or all
            if columns:
                select_cols = [f"`{col}`" for col in columns if col in available_columns]
                if select_cols:
                    return f"SELECT {', '.join(select_cols)}"
            
            return "SELECT *"
    
    def _build_where_clause(self, filters: Dict[str, Any]) -> str:
        """Build WHERE clause from filters."""
        if not filters:
            return ""
        
        conditions = []
        for column, condition in filters.items():
            operator = condition.get('operator', '=')
            value = condition.get('value')
            
            # Escape value if it's a string
            if isinstance(value, str):
                value = f"'{value.replace(chr(39), chr(39)+chr(39))}'"  # Escape single quotes
            else:
                value = str(value)
            
            conditions.append(f"`{column}` {operator} {value}")
        
        if conditions:
            return f"WHERE {' AND '.join(conditions)}"
        return ""
    
    def _build_group_by_clause(self, grouping: Optional[str], aggregations: List[str]) -> str:
        """Build GROUP BY clause."""
        if grouping:
            return f"GROUP BY `{grouping}`"
        return ""
    
    def _build_order_by_clause(self, ordering: Dict[str, Any], columns: List[str], 
                               aggregations: List[str], table_info: Dict[str, Any]) -> str:
        """Build ORDER BY clause."""
        if not ordering:
            return ""
        
        order_type = ordering.get('type')
        available_columns = table_info.get('columns', [])
        
        # Determine column to order by
        order_col = None
        if columns:
            order_col = columns[0]
        else:
            # Use first numeric column
            numeric_cols = [c for c in available_columns if self._is_numeric_column(c, table_info)]
            if numeric_cols:
                order_col = numeric_cols[0]
        
        if order_col and order_col in available_columns:
            direction = "DESC" if order_type == "top" else "ASC"
            return f"ORDER BY `{order_col}` {direction}"
        
        return ""
    
    def _build_limit_clause(self, ordering: Dict[str, Any], intent: str) -> str:
        """Build LIMIT clause."""
        if ordering:
            n = ordering.get('n', 10)
            return f"LIMIT {n}"
        elif intent == 'value':
            return "LIMIT 100"  # Default limit for value queries
        
        return ""
    
    def _is_numeric_column(self, column: str, table_info: Dict[str, Any]) -> bool:
        """Check if a column is numeric based on table info."""
        column_info = table_info.get('column_info', {})
        col_type = column_info.get(column, {}).get('type', '').lower()
        
        numeric_keywords = ['int', 'decimal', 'float', 'double', 'numeric', 'bigint', 'smallint', 'tinyint', 'mediumint']
        return any(keyword in col_type for keyword in numeric_keywords)

