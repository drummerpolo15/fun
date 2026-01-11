#!/usr/bin/env python3
"""
Database Connection Module
Handles MySQL database connections and SQL query execution.
"""

import logging
from typing import Dict, Any, Optional, List
import pandas as pd

logger = logging.getLogger(__name__)

try:
    import pymysql
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False
    logger.warning("pymysql not available. Install with: pip install pymysql")


class DatabaseConnection:
    """Handles MySQL database connections and operations."""
    
    def __init__(self, host: str, user: str, password: str, database: str, port: int = 3306):
        """
        Initialize database connection.
        
        Args:
            host: MySQL server host
            user: MySQL username
            password: MySQL password
            database: Database name
            port: MySQL port (default: 3306)
        """
        if not PYMYSQL_AVAILABLE:
            raise ImportError(
                "pymysql is required for database connections. "
                "Install with: pip install pymysql"
            )
        
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.connection = None
        self.last_query: Optional[str] = None
        
        self._connect()
    
    def _connect(self):
        """Establish connection to MySQL database."""
        try:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            logger.info(f"Connected to MySQL database: {self.database} at {self.host}")
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            raise
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """
        Execute a SQL query and return results as DataFrame.
        
        Args:
            query: SQL query string
            params: Optional parameters for parameterized queries
            
        Returns:
            DataFrame containing query results
            
        Raises:
            ConnectionError: If database connection is not available
        """
        if self.connection is None:
            raise ConnectionError("Database connection is not established")
        
        # Store the query for display/logging
        self.last_query = query
        
        try:
            logger.debug(f"Executing SQL query: {query}")
            
            # Use pandas read_sql for easier DataFrame conversion
            if params:
                df = pd.read_sql(query, self.connection, params=params)
            else:
                df = pd.read_sql(query, self.connection)
            
            logger.info(f"Query returned {len(df)} rows")
            return df
            
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            logger.error(f"Query was: {query}")
            raise
    
    def get_tables(self) -> List[str]:
        """
        Get list of all tables in the database.
        
        Returns:
            List of table names
        """
        query = "SHOW TABLES"
        df = self.execute_query(query)
        
        # The column name depends on the database name
        if len(df.columns) > 0:
            table_col = df.columns[0]
            tables = df[table_col].tolist()
            return tables
        return []
    
    def get_table_schema(self, table_name: str) -> pd.DataFrame:
        """
        Get schema information for a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            DataFrame containing column information
        """
        query = f"DESCRIBE `{table_name}`"
        return self.execute_query(query)
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary containing table information
        """
        # Get row count
        count_query = f"SELECT COUNT(*) as row_count FROM `{table_name}`"
        count_df = self.execute_query(count_query)
        row_count = count_df.iloc[0]['row_count'] if not count_df.empty else 0
        
        # Get schema
        schema_df = self.get_table_schema(table_name)
        
        # Get sample data
        sample_query = f"SELECT * FROM `{table_name}` LIMIT 5"
        sample_df = self.execute_query(sample_query)
        
        # Get column types
        column_info = {}
        for _, row in schema_df.iterrows():
            col_name = row['Field']
            col_type = row['Type']
            is_null = row['Null'] == 'YES'
            is_key = row['Key'] != ''
            
            column_info[col_name] = {
                'type': col_type,
                'nullable': is_null,
                'is_key': is_key,
                'default': row.get('Default'),
                'extra': row.get('Extra', '')
            }
        
        return {
            'table_name': table_name,
            'row_count': row_count,
            'columns': list(schema_df['Field']),
            'column_info': column_info,
            'sample_data': sample_df
        }
    
    def get_database_schema(self) -> Dict[str, Any]:
        """
        Get schema information for all tables in the database.
        
        Returns:
            Dictionary containing schema information for all tables
        """
        tables = self.get_tables()
        
        schema = {
            'database': self.database,
            'tables': {}
        }
        
        for table in tables:
            try:
                schema['tables'][table] = self.get_table_info(table)
            except Exception as e:
                logger.warning(f"Error getting schema for table {table}: {e}")
                continue
        
        return schema
    
    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Database connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def __del__(self):
        """Cleanup on deletion."""
        self.close()

