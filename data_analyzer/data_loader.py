#!/usr/bin/env python3
"""
Data Loader Module
Handles loading datasets from various formats (CSV, JSON, Excel, etc.)
and MySQL database connections.
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class DataLoader:
    """Handles loading datasets from various file formats and database connections."""
    
    SUPPORTED_FORMATS = {
        '.csv': 'csv',
        '.json': 'json',
        '.xlsx': 'excel',
        '.xls': 'excel',
        '.parquet': 'parquet',
        '.feather': 'feather'
    }
    
    def __init__(self, db_connection=None):
        """
        Initialize the data loader.
        
        Args:
            db_connection: Optional database connection object
        """
        self.data: Optional[pd.DataFrame] = None
        self.metadata: Dict[str, Any] = {}
        self.db_connection = db_connection
        self.is_database_mode = db_connection is not None
    
    def load_file(self, file_path: str) -> pd.DataFrame:
        """
        Load a dataset from a file.
        
        Args:
            file_path: Path to the data file
            
        Returns:
            Loaded DataFrame
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_extension = path.suffix.lower()
        
        if file_extension not in self.SUPPORTED_FORMATS:
            supported = ', '.join(self.SUPPORTED_FORMATS.keys())
            raise ValueError(
                f"Unsupported file format: {file_extension}. "
                f"Supported formats: {supported}"
            )
        
        file_type = self.SUPPORTED_FORMATS[file_extension]
        
        try:
            logger.info(f"Loading {file_type} file: {file_path}")
            
            # Load based on file type
            if file_type == 'csv':
                self.data = pd.read_csv(file_path)
            elif file_type == 'json':
                self.data = pd.read_json(file_path)
            elif file_type == 'excel':
                self.data = pd.read_excel(file_path)
            elif file_type == 'parquet':
                self.data = pd.read_parquet(file_path)
            elif file_type == 'feather':
                self.data = pd.read_feather(file_path)
            
            # Store metadata
            self.metadata = {
                'file_path': str(path.absolute()),
                'file_name': path.name,
                'file_type': file_type,
                'rows': len(self.data),
                'columns': list(self.data.columns),
                'column_types': self.data.dtypes.to_dict(),
                'memory_usage': self.data.memory_usage(deep=True).sum()
            }
            
            logger.info(f"Loaded {self.metadata['rows']} rows and {len(self.metadata['columns'])} columns")
            return self.data
            
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {str(e)}")
            raise
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the loaded dataset.
        
        Returns:
            Dictionary containing dataset summary information
        """
        if self.data is None:
            return {'error': 'No data loaded'}
        
        summary = {
            'metadata': self.metadata.copy(),
            'shape': self.data.shape,
            'columns': list(self.data.columns),
            'dtypes': {col: str(dtype) for col, dtype in self.data.dtypes.items()},
            'missing_values': self.data.isnull().sum().to_dict(),
            'numeric_summary': {},
            'categorical_summary': {}
        }
        
        # Add numeric column statistics
        numeric_cols = self.data.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            summary['numeric_summary'] = self.data[numeric_cols].describe().to_dict()
        
        # Add categorical column info
        categorical_cols = self.data.select_dtypes(include=['object', 'category']).columns
        if len(categorical_cols) > 0:
            for col in categorical_cols:
                summary['categorical_summary'][col] = {
                    'unique_count': self.data[col].nunique(),
                    'top_values': self.data[col].value_counts().head(5).to_dict()
                }
        
        return summary
    
    def get_data(self) -> Optional[pd.DataFrame]:
        """Get the currently loaded dataset."""
        return self.data
    
    def load_from_database(self, query: str) -> pd.DataFrame:
        """
        Load data from database using a SQL query.
        
        Args:
            query: SQL query string
            
        Returns:
            DataFrame containing query results
        """
        if self.db_connection is None:
            raise ValueError("Database connection not available")
        
        self.data = self.db_connection.execute_query(query)
        
        # Store metadata
        self.metadata = {
            'source': 'database',
            'database': self.db_connection.database,
            'query': query,
            'rows': len(self.data),
            'columns': list(self.data.columns),
            'column_types': self.data.dtypes.to_dict(),
        }
        
        logger.info(f"Loaded {self.metadata['rows']} rows and {len(self.metadata['columns'])} columns from database")
        return self.data

